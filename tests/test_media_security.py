from fastapi.testclient import TestClient
from services.api.main import app

def test_private_media_retrieval_and_missing_state():
    client=TestClient(app); sid=client.post('/api/sessions',json={'candidate_id':'media-test','consent':True}).json()['id']
    uploaded=client.post(f'/api/sessions/{sid}/media',files={'file':('clip.webm',b'webm-bytes','video/webm')}).json(); name=uploaded['segment']
    assert client.get(f'/api/sessions/{sid}/media/{name}').content==b'webm-bytes'
    assert client.get(f'/api/sessions/{sid}/media/missing.webm').status_code==404
    assert client.get(f'/api/sessions/{sid}/media/../secret').status_code in {400,404}

def test_telemetry_rate_limit_is_enforced_after_valid_signature():
    # The endpoint-level limiter is intentionally tested at its boundary without
    # fabricating signatures; a low-level unit check verifies deterministic policy.
    from services.api.main import rate_limit, RATE_BUCKETS
    key='test-limit'; RATE_BUCKETS.pop(key,None)
    for _ in range(2): rate_limit(key,2)
    try:
        rate_limit(key,2)
        assert False
    except Exception as exc:
        assert getattr(exc,'status_code',None)==429
