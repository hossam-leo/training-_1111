import time, uuid
from fastapi.testclient import TestClient
from services.api.main import app, sign
from services.api.models import Telemetry

client=TestClient(app)

def session():
    return client.post('/api/sessions', json={'candidate_id':'security-test','consent':True}).json()

def payload(sid, key, event_type, ts, nonce):
    t=Telemetry(session_id=sid,ts_ms=ts,event_type=event_type,payload={},nonce=nonce,signature='')
    t.signature=sign(t,key)
    return t.model_dump()

def test_nonce_replay_rejected():
    s=session(); sid=s['id']; key=s['telemetry_key']; ts=int(time.time()*1000); body=payload(sid,key,'TAB_VISIBLE',ts,f'nonce-replay-{uuid.uuid4()}')
    assert client.post(f'/api/sessions/{sid}/telemetry',json=body).status_code==200
    assert client.post(f'/api/sessions/{sid}/telemetry',json=body).status_code==409

def test_stale_timestamp_rejected():
    s=session(); sid=s['id']; key=s['telemetry_key']; body=payload(sid,key,'TAB_VISIBLE',int(time.time()*1000)-60000,f'nonce-stale-{uuid.uuid4()}')
    assert client.post(f'/api/sessions/{sid}/telemetry',json=body).status_code==401

def test_heartbeat_gap_emits_event():
    s=session(); sid=s['id']; key=s['telemetry_key']; now=int(time.time()*1000)
    assert client.post(f'/api/sessions/{sid}/telemetry',json=payload(sid,key,'HEARTBEAT',now-16000,f'heartbeat-one-{uuid.uuid4()}')).status_code==200
    assert client.post(f'/api/sessions/{sid}/telemetry',json=payload(sid,key,'HEARTBEAT',now,f'heartbeat-two-{uuid.uuid4()}')).status_code==200
    events=client.get(f'/api/sessions/{sid}').json()['events']
    assert any(e['event_type']=='HEARTBEAT_MISSED' for e in events)
