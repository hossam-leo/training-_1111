from fastapi.testclient import TestClient
from services.api.main import app
client=TestClient(app)
def test_health(): assert client.get('/health').json()['status']=='ok'
def test_consent_required(): assert client.post('/api/sessions',json={'candidate_id':'x','consent':False}).status_code==400
def test_session_flow():
    s=client.post('/api/sessions',json={'candidate_id':'x','consent':True}).json(); sid=s['id']
    assert client.post(f'/api/sessions/{sid}/start').status_code==200
    e={'session_id':sid,'ts_ms':1,'channel':'video','detector':'x','model_version':'v','event_type':'FACE_PRESENT'}
    assert client.post(f'/api/sessions/{sid}/events',json=e).json()['accepted'] is True
    assert client.post(f'/api/sessions/{sid}/events',json=e).json()['deduplicated'] is True
    out=client.post(f'/api/sessions/{sid}/stop').json(); assert out['session']['status']=='COMPLETED'
