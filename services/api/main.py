import hashlib, hmac, json, os, secrets, time, uuid
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from .models import SessionCreate, Event, Telemetry
from .storage import Store
from .risk import RiskEngine
from .reports import generate
from .auth import actor, issue_token
from services.storage import MinioObjectStore
from services.realtime.stream import RedisStreamBus
from services.models import WebRTCVADAdapter, make_adapter

app=FastAPI(title='ProctorStream API',version='0.1.0',description='Consent-only AI proctoring inference platform')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
store=Store(); risk=RiskEngine(); EVENT_COUNTER=Counter('proctorstream_events_total','Events received',['type'])
object_store=None
if os.getenv('PROCTORSTREAM_OBJECT_STORE','local').lower()=='minio': object_store=MinioObjectStore()
event_bus=None
if os.getenv('PROCTORSTREAM_EVENT_BUS','local').lower()=='redis': event_bus=RedisStreamBus()
face_adapter=None
audio_adapter=None
RATE_BUCKETS={}
def rate_limit(key,limit,window=60):
    now=time.time(); values=[t for t in RATE_BUCKETS.get(key,[]) if t>now-window]
    if len(values)>=limit: raise HTTPException(429,'rate limit exceeded')
    values.append(now); RATE_BUCKETS[key]=values
SECRET=os.getenv('PROCTORSTREAM_TELEMETRY_SECRET','change-me-in-development')
SESSION_KEYS={}
SESSION_KEY_EXPIRY={}
USED_NONCES={}
LAST_HEARTBEAT={}
def sign(t, key):
    raw=f"{t.session_id}|{t.ts_ms}|{t.event_type}|{t.nonce}".encode(); return hmac.new(key.encode(),raw,hashlib.sha256).hexdigest()
def auth_guard(authorization: str | None = Header(default=None)):
    if os.getenv('PROCTORSTREAM_AUTH_REQUIRED','false').lower()!='true': return {'sub':'local-development','role':'administrator'}
    return actor(authorization)
def authorize_session(sid, identity):
    session=store.get_session(sid)
    if not session: raise HTTPException(404,'session not found')
    if identity.get('role')=='candidate' and session.get('candidate_id')!=identity.get('sub'): raise HTTPException(403,'session ownership violation')
    return session
def audit_action(identity, action, resource, metadata=None):
    if hasattr(store,'audit'): store.audit(identity.get('sub','unknown'),action,resource,metadata or {})
@app.post('/api/auth/token')
def token(payload: dict):
    return {'access_token':issue_token(str(payload.get('subject','local-user')),str(payload.get('role','reviewer')),int(payload.get('ttl_seconds',3600))),'token_type':'bearer'}
@app.get('/health')
def health(): return {'status':'ok','cpu_fallback':True}
@app.get('/metrics')
def metrics(): return HTMLResponse(generate_latest(),media_type=CONTENT_TYPE_LATEST)
@app.post('/api/sessions')
def create(payload:SessionCreate,_actor=Depends(auth_guard)):
    if not payload.consent: raise HTTPException(400,'Explicit consent is required for capture sessions')
    if _actor.get('role')=='candidate' and payload.candidate_id!=_actor.get('sub'): raise HTTPException(403,'candidate_id must match authenticated subject')
    sid=f'sess_{uuid.uuid4().hex[:12]}'; session_key=secrets.token_urlsafe(32); SESSION_KEYS[sid]=session_key; SESSION_KEY_EXPIRY[sid]=int(time.time())+300
    result=store.create_session(sid,payload.candidate_id,payload.consent); audit_action(_actor,'SESSION_CREATED',sid,{'candidate_id':payload.candidate_id}); result['telemetry_key']=session_key; result['telemetry_key_expires_at']=SESSION_KEY_EXPIRY[sid]; return result
@app.get('/api/sessions')
def list_sessions(_actor=Depends(auth_guard)):
    sessions=store.sessions(); return [s for s in sessions if _actor.get('role')!='candidate' or s.get('candidate_id')==_actor.get('sub')]
@app.get('/api/sessions/{sid}')
def get_session(sid:str,_actor=Depends(auth_guard)):
    s=authorize_session(sid,_actor)
    s['events']=store.events(sid); return s
@app.post('/api/sessions/{sid}/start')
def start(sid:str,_actor=Depends(auth_guard)):
    authorize_session(sid,_actor)
    store.update_status(sid,'LIVE'); audit_action(_actor,'SESSION_STARTED',sid); return {'status':'LIVE'}
@app.post('/api/sessions/{sid}/events')
def event(sid:str,payload:Event,_actor=Depends(auth_guard)):
    authorize_session(sid,_actor)
    if payload.session_id!=sid: raise HTTPException(400,'session mismatch')
    event_data=payload.model_dump(); ok=store.add_event(event_data)
    if event_bus and ok: event_bus.publish(event_data)
    if ok: audit_action(_actor,'EVENT_ACCEPTED',sid,{'event_type':payload.event_type})
    EVENT_COUNTER.labels(payload.event_type).inc(); return {'accepted':ok,'deduplicated':not ok}
@app.post('/api/sessions/{sid}/telemetry')
def telemetry(sid:str,payload:Telemetry,_actor=Depends(auth_guard)):
    authorize_session(sid,_actor)
    rate_limit(f'telemetry:{sid}',120)
    if payload.session_id!=sid: raise HTTPException(400,'session mismatch')
    key=SESSION_KEYS.get(sid)
    if not key or int(time.time())>SESSION_KEY_EXPIRY.get(sid,0): raise HTTPException(401,'expired telemetry key')
    if not key or not hmac.compare_digest(payload.signature,sign(payload,key)): raise HTTPException(401,'invalid telemetry signature')
    now_ms=int(time.time()*1000)
    if abs(now_ms-payload.ts_ms)>30000: raise HTTPException(401,'stale telemetry timestamp')
    if hasattr(store,'claim_nonce'):
        if not store.claim_nonce(payload.nonce,sid): raise HTTPException(409,'replayed telemetry nonce')
    else:
        if payload.nonce in USED_NONCES: raise HTTPException(409,'replayed telemetry nonce')
        USED_NONCES[payload.nonce]=now_ms
    if payload.event_type=='HEARTBEAT':
        previous=LAST_HEARTBEAT.get(sid)
        if previous and payload.ts_ms-previous>15000:
            store.add_event({'event_id':f'heartbeat-missed:{sid}:{previous}','session_id':sid,'ts_ms':previous+15000,'channel':'telemetry','detector':'heartbeat-monitor','model_version':'telemetry-v1','event_type':'HEARTBEAT_MISSED','payload':{'gap_ms':payload.ts_ms-previous}})
        LAST_HEARTBEAT[sid]=payload.ts_ms
    store.add_telemetry(payload.model_dump()); telemetry_event={'event_id':f'tel:{sid}:{payload.ts_ms}:{payload.event_type}','session_id':sid,'ts_ms':payload.ts_ms,'channel':'telemetry','detector':'browser','model_version':'telemetry-v1','event_type':payload.event_type,'payload':payload.payload}; store.add_event(telemetry_event)
    if event_bus: event_bus.publish(telemetry_event)
    audit_action(_actor,'TELEMETRY_ACCEPTED',sid,{'event_type':payload.event_type})
    return {'accepted':True}
@app.post('/api/sessions/{sid}/media')
async def media(sid:str,file:UploadFile=File(...),_actor=Depends(auth_guard)):
    authorize_session(sid,_actor)
    rate_limit(f'media:{sid}',30)
    name=f'{sid}_{int(time.time()*1000)}_{Path(file.filename or "segment.webm").name}'; content=await file.read()
    if object_store:
        ref=object_store.put(f'{sid}/{name}',content,file.content_type or 'application/octet-stream',{'session_id':sid}); audit_action(_actor,'MEDIA_UPLOADED',sid,{'segment':name,'object_key':ref.key}); return {'stored':ref.key,'segment':name,'download_url':object_store.signed_url(ref.key)}
    target=store.media_dir/name; target.write_bytes(content); audit_action(_actor,'MEDIA_UPLOADED',sid,{'segment':name}); return {'stored':str(target),'segment':name}

@app.get('/api/sessions/{sid}/media/{name:path}')
def retrieve_media(sid:str,name:str,_actor=Depends(auth_guard)):
    authorize_session(sid,_actor); safe_name=Path(name).name
    if name!=safe_name or safe_name.startswith('.'): raise HTTPException(400,'invalid media key')
    try:
        if object_store:
            content=object_store.get(f'{sid}/{safe_name}'); return StreamingResponse(iter([content]),media_type='application/octet-stream')
        target=store.media_dir/safe_name
        if not target.exists() or not target.is_file(): raise HTTPException(404,'media evidence unavailable')
        return FileResponse(target,media_type='application/octet-stream')
    except HTTPException: raise
    except Exception as exc: raise HTTPException(404,'media evidence unavailable or corrupted') from exc

@app.post('/api/sessions/{sid}/inference/face')
async def face_inference(sid:str,file:UploadFile=File(...),_actor=Depends(auth_guard)):
    global face_adapter
    authorize_session(sid,_actor)
    if face_adapter is None:
        if os.getenv('PROCTORSTREAM_FACE_ADAPTER','').lower()!='opencv_haar_face': raise HTTPException(503,'face adapter is not configured; set PROCTORSTREAM_FACE_ADAPTER=opencv_haar_face and install the models extra')
        face_adapter=make_adapter('opencv_haar_face')
    try:
        import cv2, numpy as np
        frame=cv2.imdecode(np.frombuffer(await file.read(),dtype=np.uint8),cv2.IMREAD_COLOR)
        if frame is None: raise ValueError('unable to decode image')
        detection=face_adapter.infer(frame)
    except HTTPException: raise
    except Exception as exc: raise HTTPException(422,f'face inference failed: {type(exc).__name__}') from exc
    event={'event_id':f'face:{sid}:{int(time.time()*1000)}','session_id':sid,'ts_ms':int(time.time()*1000),'channel':'video','detector':face_adapter.name,'model_version':detection.model_version,'event_type':detection.event_type,'payload':detection.payload,'quality':detection.payload.get('quality',{}),'demo':False}
    accepted=store.add_event(event)
    if event_bus and accepted: event_bus.publish(event)
    audit_action(_actor,'FACE_INFERENCE',sid,{'event_type':detection.event_type,'model_version':detection.model_version})
    return {'accepted':accepted,'detection':detection.__dict__}

@app.post('/api/sessions/{sid}/inference/audio')
async def audio_inference(sid:str,file:UploadFile=File(...),_actor=Depends(auth_guard)):
    global audio_adapter
    authorize_session(sid,_actor)
    if audio_adapter is None:
        if os.getenv('PROCTORSTREAM_AUDIO_ADAPTER','').lower()!='webrtc_vad': raise HTTPException(503,'audio adapter is not configured; set PROCTORSTREAM_AUDIO_ADAPTER=webrtc_vad and install the models extra')
        audio_adapter=WebRTCVADAdapter()
    try:
        import io, wave
        with wave.open(io.BytesIO(await file.read()),'rb') as wav:
            if wav.getnchannels()!=1 or wav.getsampwidth()!=2: raise ValueError('audio must be mono PCM16 WAV')
            activity=audio_adapter.infer(wav.readframes(wav.getnframes()),wav.getframerate())
    except HTTPException: raise
    except Exception as exc: raise HTTPException(422,f'audio inference failed: {type(exc).__name__}') from exc
    event={'event_id':f'audio:{sid}:{int(time.time()*1000)}','session_id':sid,'ts_ms':int(time.time()*1000),'channel':'audio','detector':audio_adapter.name,'model_version':activity.model_version,'event_type':activity.event_type,'payload':activity.payload,'quality':{'usable':True},'demo':False}
    accepted=store.add_event(event)
    if event_bus and accepted: event_bus.publish(event)
    audit_action(_actor,'AUDIO_INFERENCE',sid,{'model_version':activity.model_version})
    return {'accepted':accepted,'activity':activity.__dict__}
@app.post('/api/sessions/{sid}/stop')
def stop(sid:str,_actor=Depends(auth_guard)):
    s=authorize_session(sid,_actor)
    events=store.events(sid); missing=[] if any(e['channel']=='video' for e in events) else ['video']; result=risk.score(events,missing); store.update_status(sid,'COMPLETED',result); audit_action(_actor,'SESSION_COMPLETED',sid,{'risk_level':result['risk_level']}); s=store.get_session(sid); report=generate(s,events,result,store.report_dir/f'{sid}.html'); return {'session':s,'report':str(report)}
@app.get('/api/sessions/{sid}/report')
def report(sid:str,_actor=Depends(auth_guard)):
    authorize_session(sid,_actor)
    p=store.report_dir/f'{sid}.html'
    if not p.exists(): raise HTTPException(404,'report not generated')
    return FileResponse(p,media_type='text/html')
@app.post('/api/sessions/{sid}/review')
def review_session(sid:str,payload:dict,_actor=Depends(auth_guard)):
    authorize_session(sid,_actor)
    if os.getenv('PROCTORSTREAM_AUTH_REQUIRED','false').lower()=='true' and _actor.get('role') not in {'reviewer','administrator'}: raise HTTPException(403,'reviewer role required')
    decision=str(payload.get('decision','')).upper(); notes=str(payload.get('notes',''))
    if decision not in {'CONFIRMED','DISMISSED','NEEDS_MORE_EVIDENCE'}: raise HTTPException(422,'invalid review decision')
    store.save_review(sid,_actor.get('sub','local-reviewer'),decision,notes); audit_action(_actor,'REVIEW_DECISION',sid,{'decision':decision}); return {'session_id':sid,'decision':decision,'notes':notes}
@app.websocket('/ws/sessions/{sid}')
async def ws(websocket:WebSocket,sid:str):
    await websocket.accept(); await websocket.send_json({'type':'connected','session_id':sid})
    try:
        while True:
            data=await websocket.receive_json(); data.setdefault('session_id',sid); data.setdefault('event_id',f'ws:{uuid.uuid4().hex}'); store.add_event(data); await websocket.send_json({'accepted':True,'event':data})
    except Exception: await websocket.close()

if Path('frontend/dist').exists():
    app.mount('/', StaticFiles(directory='frontend/dist', html=True), name='reviewer-ui')
