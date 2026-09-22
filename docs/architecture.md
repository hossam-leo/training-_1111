# Architecture

The local implementation keeps the vertical intentionally small: FastAPI provides REST/WebSocket ingest, SQLite provides a durable CPU-friendly local store, the event contract is validated with Pydantic, the risk engine loads editable YAML rules, and the reviewer UI is a Vite/React client. Media segments are written to a local object-storage-compatible directory abstraction. The interfaces are replaceable with PostgreSQL, Redis Streams, MinIO, Celery, and GPU model servers in a deployment profile.
