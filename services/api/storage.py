import json, os, threading
from datetime import datetime, timezone
from pathlib import Path
from .storage_sqlite import Store as SQLiteStore

class PostgresStore:
    def __init__(self, db_url=None, storage_dir=None, report_dir=None):
        self.db_url=db_url or os.getenv('PROCTORSTREAM_DB_URL','postgresql+psycopg://proctor:proctor@localhost:5432/proctorstream')
        try:
            from sqlalchemy import create_engine, text
        except ImportError as exc: raise RuntimeError('SQLAlchemy is required for PostgreSQL persistence') from exc
        self.text=text; self.engine=create_engine(self.db_url, pool_pre_ping=True, future=True)
        self.media_dir=Path(storage_dir or os.getenv('PROCTORSTREAM_STORAGE_DIR','./data/media')); self.report_dir=Path(report_dir or os.getenv('PROCTORSTREAM_REPORT_DIR','./data/reports'))
        self.media_dir.mkdir(parents=True,exist_ok=True); self.report_dir.mkdir(parents=True,exist_ok=True); self.lock=threading.Lock(); self.init()
    def init(self):
        statements=[
        'CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, ended_at TIMESTAMPTZ, consent BOOLEAN NOT NULL, result_json JSONB)',
        'CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, ts_ms BIGINT NOT NULL, channel TEXT NOT NULL, event_type TEXT NOT NULL, payload_json JSONB NOT NULL, demo BOOLEAN NOT NULL DEFAULT FALSE)',
        'CREATE TABLE IF NOT EXISTS telemetry (id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, ts_ms BIGINT NOT NULL, event_type TEXT NOT NULL, payload_json JSONB NOT NULL)',
        'CREATE TABLE IF NOT EXISTS telemetry_nonces (nonce TEXT PRIMARY KEY, session_id TEXT NOT NULL, seen_at TIMESTAMPTZ NOT NULL)',
        'CREATE TABLE IF NOT EXISTS media_segments (id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, filename TEXT NOT NULL, object_key TEXT, created_at TIMESTAMPTZ NOT NULL)',
        'CREATE TABLE IF NOT EXISTS audit_logs (id BIGSERIAL PRIMARY KEY, actor_id TEXT, action TEXT NOT NULL, resource_id TEXT, metadata JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL)']
        statements.append('CREATE TABLE IF NOT EXISTS reviews (session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE, reviewer_id TEXT NOT NULL, decision TEXT NOT NULL, notes TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL)')
        with self.engine.begin() as c:
            for statement in statements: c.execute(self.text(statement))
            c.execute(self.text('CREATE INDEX IF NOT EXISTS idx_events_session_ts ON events(session_id, ts_ms)'))
            c.execute(self.text('CREATE INDEX IF NOT EXISTS idx_telemetry_session_ts ON telemetry(session_id, ts_ms)'))
    def create_session(self,sid,candidate,consent):
        now=datetime.now(timezone.utc)
        with self.engine.begin() as c: c.execute(self.text('INSERT INTO sessions(id,candidate_id,status,created_at,consent) VALUES (:id,:candidate,:status,:created,:consent)'),{'id':sid,'candidate':candidate,'status':'CREATED','created':now,'consent':consent})
        return self.get_session(sid)
    def _decode(self,row):
        if not row: return None
        d=dict(row._mapping); d['consent']=bool(d['consent']); d['result']=d['result_json']; d['review']=self.get_review(d['id']); return d
    def get_session(self,sid):
        with self.engine.connect() as c: row=c.execute(self.text('SELECT * FROM sessions WHERE id=:id'),{'id':sid}).first()
        return self._decode(row)
    def update_status(self,sid,status,result=None):
        ended=datetime.now(timezone.utc) if status=='COMPLETED' else None
        with self.engine.begin() as c: c.execute(self.text('UPDATE sessions SET status=:status, ended_at=COALESCE(:ended,ended_at), result_json=:result WHERE id=:id'),{'status':status,'ended':ended,'result':json.dumps(result) if result else None,'id':sid})
    def add_event(self,e):
        eid=e.get('event_id') or f"{e['session_id']}:{e['ts_ms']}:{e['event_type']}"
        with self.engine.begin() as c:
            r=c.execute(self.text('INSERT INTO events(event_id,session_id,ts_ms,channel,event_type,payload_json,demo) VALUES (:eid,:sid,:ts,:channel,:etype,:payload,:demo) ON CONFLICT (event_id) DO NOTHING'),{'eid':eid,'sid':e['session_id'],'ts':e['ts_ms'],'channel':e['channel'],'etype':e['event_type'],'payload':json.dumps(e.get('payload',{})),'demo':bool(e.get('demo',False))})
        return r.rowcount==1
    def events(self,sid):
        with self.engine.connect() as c: rows=c.execute(self.text('SELECT * FROM events WHERE session_id=:sid ORDER BY ts_ms'),{'sid':sid}).all()
        return [{**dict(r._mapping),'payload':r._mapping['payload_json']} for r in rows]
    def add_telemetry(self,t):
        with self.engine.begin() as c: c.execute(self.text('INSERT INTO telemetry(session_id,ts_ms,event_type,payload_json) VALUES (:sid,:ts,:etype,:payload)'),{'sid':t['session_id'],'ts':t['ts_ms'],'etype':t['event_type'],'payload':json.dumps(t.get('payload',{}))})
    def claim_nonce(self,nonce,sid):
        with self.engine.begin() as c:
            r=c.execute(self.text('INSERT INTO telemetry_nonces(nonce,session_id,seen_at) VALUES (:nonce,:sid,:seen) ON CONFLICT (nonce) DO NOTHING'),{'nonce':nonce,'sid':sid,'seen':datetime.now(timezone.utc)})
        return r.rowcount==1
    def audit(self,actor_id,action,resource_id,metadata):
        with self.engine.begin() as c: c.execute(self.text('INSERT INTO audit_logs(actor_id,action,resource_id,metadata,created_at) VALUES (:actor,:action,:resource,:metadata,:created)'),{'actor':actor_id,'action':action,'resource':resource_id,'metadata':json.dumps(metadata),'created':datetime.now(timezone.utc)})
    def save_review(self,sid,reviewer_id,decision,notes):
        with self.engine.begin() as c: c.execute(self.text('INSERT INTO reviews(session_id,reviewer_id,decision,notes,created_at) VALUES (:sid,:reviewer,:decision,:notes,:created) ON CONFLICT (session_id) DO UPDATE SET reviewer_id=:reviewer,decision=:decision,notes=:notes,created_at=:created'),{'sid':sid,'reviewer':reviewer_id,'decision':decision,'notes':notes,'created':datetime.now(timezone.utc)})
    def get_review(self,sid):
        with self.engine.connect() as c: row=c.execute(self.text('SELECT * FROM reviews WHERE session_id=:sid'),{'sid':sid}).first()
        return dict(row._mapping) if row else None
    def sessions(self):
        with self.engine.connect() as c: ids=[r[0] for r in c.execute(self.text('SELECT id FROM sessions ORDER BY created_at DESC')).all()]
        return [self.get_session(i) for i in ids]

class Store:
    def __new__(cls,*args,**kwargs):
        url=kwargs.get('db_url') or os.getenv('PROCTORSTREAM_DB_URL','sqlite:///./data/proctorstream.db')
        if url.startswith('postgresql'): return PostgresStore(*args,**kwargs)
        return SQLiteStore(*args,**kwargs)
