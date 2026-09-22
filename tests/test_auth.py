import os
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.auth import issue_token, verify_token

client=TestClient(app)

def test_token_roles_and_tamper_rejection():
    token=issue_token('reviewer-1','reviewer',60)
    assert verify_token(token)['role']=='reviewer'
    head,payload,sig=token.split('.')
    try: verify_token(f'{head}.{payload}.tampered')
    except Exception: pass
    else: assert False, 'tampered token accepted'

def test_token_endpoint():
    response=client.post('/api/auth/token',json={'subject':'x','role':'candidate'})
    assert response.status_code==200 and response.json()['token_type']=='bearer'

def test_auth_required_blocks_without_bearer(monkeypatch):
    monkeypatch.setenv('PROCTORSTREAM_AUTH_REQUIRED','true')
    try:
        assert client.get('/api/sessions').status_code==401
        token=issue_token('reviewer','reviewer')
        assert client.get('/api/sessions',headers={'Authorization':f'Bearer {token}'}).status_code==200
    finally: monkeypatch.delenv('PROCTORSTREAM_AUTH_REQUIRED',raising=False)

def test_candidate_cannot_access_another_candidate_session(monkeypatch):
    monkeypatch.setenv('PROCTORSTREAM_AUTH_REQUIRED','true')
    try:
        alice=issue_token('alice','candidate'); bob=issue_token('bob','candidate')
        created=client.post('/api/sessions',json={'candidate_id':'alice','consent':True},headers={'Authorization':f'Bearer {alice}'})
        assert created.status_code==200
        sid=created.json()['id']
        assert client.get(f'/api/sessions/{sid}',headers={'Authorization':f'Bearer {bob}'}).status_code==403
        assert client.get(f'/api/sessions/{sid}',headers={'Authorization':f'Bearer {alice}'}).status_code==200
    finally: monkeypatch.delenv('PROCTORSTREAM_AUTH_REQUIRED',raising=False)


def test_reviewer_decision_and_candidate_privilege_escalation(monkeypatch):
    monkeypatch.setenv('PROCTORSTREAM_AUTH_REQUIRED','true')
    try:
        candidate=issue_token('alice','candidate'); reviewer=issue_token('reviewer','reviewer')
        created=client.post('/api/sessions',json={'candidate_id':'alice','consent':True},headers={'Authorization':f'Bearer {candidate}'})
        sid=created.json()['id']
        assert client.post(f'/api/sessions/{sid}/review',json={'decision':'CONFIRMED','notes':'reviewed'},headers={'Authorization':f'Bearer {candidate}'}).status_code==403
        good=client.post(f'/api/sessions/{sid}/review',json={'decision':'CONFIRMED','notes':'reviewed'},headers={'Authorization':f'Bearer {reviewer}'})
        assert good.status_code==200 and client.get(f'/api/sessions/{sid}',headers={'Authorization':f'Bearer {reviewer}'}).json()['review']['decision']=='CONFIRMED'
        assert client.post(f'/api/sessions/{sid}/review',json={'decision':'INVALID'},headers={'Authorization':f'Bearer {reviewer}'}).status_code==422
    finally: monkeypatch.delenv('PROCTORSTREAM_AUTH_REQUIRED',raising=False)
