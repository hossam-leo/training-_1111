import sys, time
sys.path.insert(0,'.')
from services.api.main import store
sid='sess_demo_001'
if store.get_session(sid): print(sid,'already exists'); raise SystemExit
store.create_session(sid,'demo-candidate',True); store.update_status(sid,'LIVE')
events=[{'event_id':'demo-1','session_id':sid,'ts_ms':1000,'channel':'video','detector':'cpu_heuristic','model_version':'cpu-heuristic-1','event_type':'FACE_PRESENT','payload':{'face_count':1},'confidence':0.98,'quality':{'usable':True},'demo':True},{'event_id':'demo-2','session_id':sid,'ts_ms':5000,'channel':'telemetry','detector':'browser','model_version':'telemetry-v1','event_type':'TAB_HIDDEN','payload':{},'confidence':1,'quality':{'usable':True},'demo':True},{'event_id':'demo-3','session_id':sid,'ts_ms':9000,'channel':'video','detector':'cpu_heuristic','model_version':'cpu-heuristic-1','event_type':'MULTI_FACE','payload':{'face_count':2},'confidence':0.91,'quality':{'usable':True},'demo':True},{'event_id':'demo-4','session_id':sid,'ts_ms':12000,'channel':'audio','detector':'fallback','model_version':'unknown-1','event_type':'AUDIO_UNKNOWN','payload':{'reason':'optional model unavailable'},'quality':{'usable':False},'demo':True}]
for e in events: store.add_event(e)
print('seeded',sid)
