import io, wave, struct, math, pytest
pytest.importorskip('webrtcvad')
from fastapi.testclient import TestClient
from services.models import WebRTCVADAdapter
from services.api.main import app

def pcm_tone(rate=16000,seconds=1): return b''.join(struct.pack('<h',int(10000*math.sin(2*math.pi*440*i/rate))) for i in range(rate*seconds))
def wav_bytes(pcm,rate=16000):
    out=io.BytesIO()
    with wave.open(out,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
    return out.getvalue()

def test_vad_schema_and_invalid_format():
    adapter=WebRTCVADAdapter(); result=adapter.infer(pcm_tone(),16000); assert result.event_type=='AUDIO_ACTIVITY'; assert result.payload['input_schema']=='mono signed PCM16';
    with pytest.raises(ValueError): adapter.infer(b'\0'*1000,44100)

def test_api_audio_inference_persists_event(monkeypatch):
    monkeypatch.setenv('PROCTORSTREAM_AUDIO_ADAPTER','webrtc_vad'); client=TestClient(app); sid=client.post('/api/sessions',json={'candidate_id':'audio-test','consent':True}).json()['id']
    response=client.post(f'/api/sessions/{sid}/inference/audio',files={'file':('sample.wav',wav_bytes(pcm_tone()),'audio/wav')})
    assert response.status_code==200; assert response.json()['activity']['event_type']=='AUDIO_ACTIVITY'; assert any(e['channel']=='audio' for e in client.get(f'/api/sessions/{sid}').json()['events'])
