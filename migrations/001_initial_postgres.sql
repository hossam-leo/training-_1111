CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, ended_at TIMESTAMPTZ, consent BOOLEAN NOT NULL, result_json JSONB);
CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, ts_ms BIGINT NOT NULL, channel TEXT NOT NULL, event_type TEXT NOT NULL, payload_json JSONB NOT NULL, demo BOOLEAN NOT NULL DEFAULT FALSE);
CREATE TABLE IF NOT EXISTS telemetry (id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, ts_ms BIGINT NOT NULL, event_type TEXT NOT NULL, payload_json JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS telemetry_nonces (nonce TEXT PRIMARY KEY, session_id TEXT NOT NULL, seen_at TIMESTAMPTZ NOT NULL);
CREATE TABLE IF NOT EXISTS media_segments (id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, filename TEXT NOT NULL, object_key TEXT, created_at TIMESTAMPTZ NOT NULL);
CREATE TABLE IF NOT EXISTS audit_logs (id BIGSERIAL PRIMARY KEY, actor_id TEXT, action TEXT NOT NULL, resource_id TEXT, metadata JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL);
CREATE INDEX IF NOT EXISTS idx_events_session_ts ON events(session_id, ts_ms);
CREATE INDEX IF NOT EXISTS idx_telemetry_session_ts ON telemetry(session_id, ts_ms);
