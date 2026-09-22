import io, importlib.util, pytest
cv2=pytest.importorskip('cv2')
import numpy as np
from fastapi.testclient import TestClient
from services.models import OpenCVHaarFaceAdapter
from services.api.main import app

def image_bytes():
    ok,encoded=cv2.imencode('.png',np.zeros((160,160,3),dtype=np.uint8)); assert ok; return encoded.tobytes()

def test_opencv_face_adapter_output_schema_and_quality():
    detection=OpenCVHaarFaceAdapter().infer(np.zeros((160,160,3),dtype=np.uint8))
    assert detection.event_type=='FACE_ABSENT'; assert detection.payload['input_schema']=='BGR uint8 image HxWx3'; assert 'quality' in detection.payload

@pytest.mark.parametrize('frame_name,frame',[('no_face',np.zeros((160,160,3),dtype=np.uint8)),('poor_lighting',np.full((160,160,3),8,dtype=np.uint8)),('blur',cv2.GaussianBlur(np.random.default_rng(7).integers(0,255,(160,160,3),dtype=np.uint8),(31,31),0)),('partial_frame',np.pad(np.zeros((80,160,3),dtype=np.uint8),((80,0),(0,0),(0,0))) )])
def test_negative_image_cases_have_schema(frame_name,frame):
    detection=OpenCVHaarFaceAdapter().infer(frame)
    assert detection.payload['input_schema']=='BGR uint8 image HxWx3'; assert 'quality' in detection.payload; assert frame_name

def test_api_face_inference_persists_traceable_event(monkeypatch):
    monkeypatch.setenv('PROCTORSTREAM_FACE_ADAPTER','opencv_haar_face')
    client=TestClient(app); session=client.post('/api/sessions',json={'candidate_id':'face-test','consent':True}).json(); sid=session['id']
    response=client.post(f'/api/sessions/{sid}/inference/face',files={'file':('frame.png',image_bytes(),'image/png')})
    assert response.status_code==200; data=response.json(); assert data['detection']['event_type']=='FACE_ABSENT'
    assert any(event['event_type']=='FACE_ABSENT' for event in client.get(f'/api/sessions/{sid}').json()['events'])
