import json, os, sqlite3, threading
from datetime import datetime, timezone
from pathlib import Path

class Store:
    def __init__(self, db_url=None, storage_dir=None, report_dir=None):
        self.db_path = (db_url or os.getenv("PROCTORSTREAM_DB_URL", "sqlite:///./data/proctorstream.db")).replace("sqlite:///", "", 1)
        self.media_dir = Path(storage_dir or os.getenv("PROCTORSTREAM_STORAGE_DIR", "./data/media")); self.report_dir = Path(report_dir or os.getenv("PROCTORSTREAM_REPORT_DIR", "./data/reports"))
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True); self.media_dir.mkdir(parents=True, exist_ok=True); self.report_dir.mkdir(parents=True, exist_ok=True); self.lock = threading.Lock(); self.init()
    def conn(self):
        c = sqlite3.connect(self.db_path); c.row_factory = sqlite3.Row; return c
    def init(self):
        with self.conn() as c:
            c.executescript("""CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, candidate_id TEXT, status TEXT, created_at TEXT, ended_at TEXT, consent INTEGER, result_json TEXT);
            CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, session_id TEXT, ts_ms INTEGER, channel TEXT, event_type TEXT, payload_json TEXT, demo INTEGER);
            CREATE TABLE IF NOT EXISTS telemetry (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, ts_ms INTEGER, event_type TEXT, payload_json TEXT);
            CREATE TABLE IF NOT EXISTS media_segments (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, filename TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS telemetry_nonces (nonce TEXT PRIMARY KEY, session_id TEXT, seen_at TEXT);
            CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id TEXT, action TEXT, resource_id TEXT, metadata TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS reviews (session_id TEXT PRIMARY KEY, reviewer_id TEXT, decision TEXT, notes TEXT, created_at TEXT);""")
    def create_session(self, sid, candidate, consent):
        now=datetime.now(timezone.utc).isoformat();
        with self.conn() as c: c.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?)',(sid,candidate,'CREATED',now,None,int(consent),None))
        return self.get_session(sid)
    def get_session(self,sid):
        with self.conn() as c: r=c.execute('SELECT * FROM sessions WHERE id=?',(sid,)).fetchone()
        if not r: return None
        d=dict(r); d['consent']=bool(d['consent']); d['result']=json.loads(d['result_json']) if d['result_json'] else None; d['review']=self.get_review(sid); return d
    def update_status(self,sid,status,result=None):
        ended=datetime.now(timezone.utc).isoformat() if status=='COMPLETED' else None
        with self.conn() as c: c.execute('UPDATE sessions SET status=?,ended_at=COALESCE(?,ended_at),result_json=? WHERE id=?',(status,ended,json.dumps(result) if result else None,sid))
    def add_event(self,e):
        eid=e.get('event_id') or f"{e['session_id']}:{e['ts_ms']}:{e['event_type']}"
        with self.conn() as c:
            cur=c.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?)',(eid,e['session_id'],e['ts_ms'],e['channel'],e['event_type'],json.dumps(e.get('payload',{})),int(e.get('demo',False))))
        return cur.rowcount == 1
    def events(self,sid):
        with self.conn() as c: rows=c.execute('SELECT * FROM events WHERE session_id=? ORDER BY ts_ms',(sid,)).fetchall()
        return [{**dict(r), 'payload':json.loads(r['payload_json'])} for r in rows]
    def add_telemetry(self,t):
        with self.conn() as c: c.execute('INSERT INTO telemetry(session_id,ts_ms,event_type,payload_json) VALUES (?,?,?,?)',(t['session_id'],t['ts_ms'],t['event_type'],json.dumps(t.get('payload',{}))))
    def claim_nonce(self,nonce,sid):
        with self.conn() as c:
            cur=c.execute('INSERT OR IGNORE INTO telemetry_nonces(nonce,session_id,seen_at) VALUES (?,?,?)',(nonce,sid,datetime.now(timezone.utc).isoformat()))
        return cur.rowcount==1
    def audit(self,actor_id,action,resource_id,metadata):
        with self.conn() as c: c.execute('INSERT INTO audit_logs(actor_id,action,resource_id,metadata,created_at) VALUES (?,?,?,?,?)',(actor_id,action,resource_id,json.dumps(metadata),datetime.now(timezone.utc).isoformat()))
    def save_review(self,sid,reviewer_id,decision,notes):
        with self.conn() as c: c.execute('INSERT OR REPLACE INTO reviews(session_id,reviewer_id,decision,notes,created_at) VALUES (?,?,?,?,?)',(sid,reviewer_id,decision,notes,datetime.now(timezone.utc).isoformat()))
    def get_review(self,sid):
        with self.conn() as c: row=c.execute('SELECT * FROM reviews WHERE session_id=?',(sid,)).fetchone()
        return dict(row) if row else None
    def sessions(self):
        with self.conn() as c: rows=c.execute('SELECT * FROM sessions ORDER BY created_at DESC').fetchall()
        return [self.get_session(r['id']) for r in rows]
