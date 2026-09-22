import base64, hashlib, hmac, json, os, time
from fastapi import Header, HTTPException

ROLES={'candidate','reviewer','administrator','worker'}
SECRET=os.getenv('PROCTORSTREAM_AUTH_SECRET',os.getenv('PROCTORSTREAM_TELEMETRY_SECRET','change-me-in-development'))
def _b64(value:bytes)->str: return base64.urlsafe_b64encode(value).decode().rstrip('=')
def issue_token(subject:str,role:str,ttl_seconds:int=3600)->str:
    if role not in ROLES: raise ValueError('unknown role')
    header=_b64(json.dumps({'alg':'HS256','typ':'JWT'},separators=(',',':')).encode()); payload=_b64(json.dumps({'sub':subject,'role':role,'exp':int(time.time())+ttl_seconds},separators=(',',':')).encode()); sig=_b64(hmac.new(SECRET.encode(),f'{header}.{payload}'.encode(),hashlib.sha256).digest()); return f'{header}.{payload}.{sig}'
def verify_token(token:str):
    try: header,payload,sig=token.split('.'); expected=_b64(hmac.new(SECRET.encode(),f'{header}.{payload}'.encode(),hashlib.sha256).digest()); data=json.loads(base64.urlsafe_b64decode(payload+'==='))
    except Exception as exc: raise HTTPException(401,'invalid bearer token') from exc
    if not hmac.compare_digest(sig,expected) or int(data.get('exp',0))<int(time.time()) or data.get('role') not in ROLES: raise HTTPException(401,'expired or invalid bearer token')
    return data
def actor(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith('bearer '): raise HTTPException(401,'bearer token required')
    return verify_token(authorization.split(' ',1)[1])
def require_role(*roles):
    def dependency(authorization: str | None = Header(default=None)):
        data=actor(authorization)
        if data['role'] not in roles: raise HTTPException(403,'insufficient role')
        return data
    return dependency
