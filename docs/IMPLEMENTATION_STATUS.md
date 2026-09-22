# Implementation status after continuation

This matrix records actual implementation evidence as of 2026-09-21. It does not claim production readiness or SRS acceptance.

| Area | Status | Evidence | Remaining blocker |
|---|---|---|---|
| Candidate consent and capture UI | Partial | `frontend/src/CandidateCapture.tsx` requests consent and camera/microphone permissions, shows preview and recording indicator, and records five-second WebM segments. | Browser permission, HTTPS, cross-browser, CPU, bandwidth, reconnect, and real-device tests remain. |
| Browser telemetry | Partial | Visibility, blur/focus, paste/copy, fullscreen, device-change, heartbeat, nonce, timestamp, and HMAC paths exist. | Display/keyboard signals vary by browser; server-side nonce state is process-local; client behavior needs browser automation tests. |
| Replay protection | Complete locally | Invalid signatures, stale timestamps, and repeated nonces are tested. | Restart-safe nonce persistence and authenticated key delivery remain. |
| Heartbeat-gap detection | Complete locally | A gap greater than 15 seconds emits `HEARTBEAT_MISSED`; test coverage exists. | Cross-process/session monitoring remains. |
| Reviewer experience | Partial | Channel and event-type filters, event inspection, timeline, missing-channel result display, report links, and synthetic-data labels exist. | Severity semantics, evidence playback, human-review state transitions, and access control remain. |
| Optional real model adapters | Partial | OpenCV Haar face adapter and ONNX Runtime adapter are implemented behind explicit interfaces. | Optional dependencies, exact weights, licensing, accuracy evaluation, GPU path, and model serving remain. |
| Dataset/evaluation scaffolds | Partial | Synthetic scenario metadata generator, dataset card, annotation validation, and non-fabricating evaluation report scaffold exist. | DR-1/DR-2/DR-3 assets and executed metrics remain unavailable. |
| Resumable batch boundary | Partial | Segment checkpoint/resume function and tests exist. | Real media decoding, model execution, queue orchestration, and worker recovery remain. |
| Production topology | Partial | Compose YAML now defines API, workers, PostgreSQL, Redis, MinIO, Prometheus, Grafana, and Nginx with health checks/persistence declarations. | Docker was unavailable; workers are integration boundaries; API currently uses SQLite; service wiring and real health tests remain. |
| Privacy and security utilities | Partial | Fernet encryption helper, retention deletion helper, security/threat documentation, per-session HMAC, and license register exist. | Managed keys, encrypted production storage, biometric isolation, authentication/authorization, audit logs, and ethics approval remain. |
| Verification | Complete for local scope | 14 tests passed, Python compilation passed, Compose YAML parsed, API/UI smoke passed, synthetic metadata generated, frontend built. | GPU, browser, Docker, dataset, load, resilience, and institutional validation remain unverified. |

## SRS conclusion

The local implementation scope has been expanded materially, but the complete SRS remains **not accepted**. Model accuracy, capacity, Tier 1/Tier 2 performance, production security, real datasets, Docker runtime behavior, and the required benchmark protocol still lack objective evidence.

## Phase 3 continuation evidence

| New area | Status | Evidence | Validation boundary |
|---|---|---|---|
| PostgreSQL persistence adapter | Partial | `services/api/storage.py`, `migrations/001_initial_postgres.sql`, indexed tables, foreign keys, `ON CONFLICT` idempotency, nonce table, and audit table. | No PostgreSQL server was available in the sandbox; integration test is present and skipped without `PROCTORSTREAM_TEST_POSTGRES_URL`. |
| Redis Streams | Partial | `services/realtime/stream.py` implements consumer groups, `XREADGROUP`, acknowledgements, retry counters, dead-letter stream, and pending-message recovery. API publishing and realtime worker consumption are wired when `PROCTORSTREAM_EVENT_BUS=redis`. | Redis restart/crash tests and live consumer-group execution were not run because no Redis service was available. |
| MinIO/S3 storage | Partial | `services/storage/object_store.py` implements private bucket creation, encrypted server-side upload request, metadata, retries, download, deletion, and presigned URLs. API media route uses it when `PROCTORSTREAM_OBJECT_STORE=minio`. | MinIO roundtrip and failure-recovery tests are present and skipped without `PROCTORSTREAM_TEST_MINIO_ENDPOINT`. |
| Authentication/RBAC | Partial | Signed role tokens, expiry, tamper rejection, optional production enforcement, and candidate/reviewer/administrator/worker roles exist in `services/api/auth.py`. | Session ownership, persistent user store, OAuth/identity provider, audit enforcement, and privilege tests across every route remain. |
| Restart-safe telemetry nonces | Partial | PostgreSQL `telemetry_nonces` table and `claim_nonce` path are implemented; SQLite retains process-local fallback. | PostgreSQL persistence across restart was not executed in this environment. |
| Realtime worker | Partial | `services/workers/realtime.py --once` consumes Redis messages, persists idempotently, acknowledges success, retries failures, and dead-letters exhausted messages. | Live Redis execution and model inference integration remain unavailable. |
| Batch worker | Partial | `services/workers/batch.py --once` processes persisted media files with checkpoints and emits explicit `BATCH_UNKNOWN` events when decoder/model adapters are unavailable. | Real media decoding and Tier 2 model execution remain. |

Latest local regression result: **17 passed, 3 skipped, 0 failed**. Skips correspond to external PostgreSQL, Redis, and MinIO integration tests with no service URLs configured.

## Phase 4 verification evidence

| Area | Status | Evidence | Remaining boundary |
|---|---|---|---|
| Route-level authentication and ownership | Partial | Optional production enforcement now guards session create/list/get/start/events/telemetry/media/stop/report; candidate subjects are restricted to matching `candidate_id`; cross-user test passes. | Identity-provider integration, persistent users, worker endpoint auth, and production-default enforcement still require deployment decisions. |
| Telemetry key lifetime | Partial | Session keys expire after five minutes and response includes expiry; HMAC, timestamp, nonce, tamper, and replay tests pass. | Secure non-exported browser key delivery and rotation across process restart remain. |
| Browser capture automation | Partial | Playwright Chromium suite passes 4/4 with fake camera/microphone devices, consent gate, start/record indicator, media upload assertion, copy signal dispatch, permission denial, and reviewer navigation. | Real-device camera/microphone and Firefox/Safari coverage remain. |
| Full-stack startup | Partial | `scripts/start_stack.sh`, connected Compose environment, service health checks, persistent volumes, startup dependencies, restart policies, and CI service-container workflow exist. | Docker is unavailable in the current sandbox; full runtime execution remains unverified. |
| End-to-end event flow | Partial | Gated test covers Redis publish → realtime worker → PostgreSQL persistence → RiskEngine; idempotency is asserted. | Live Redis/PostgreSQL execution is deferred to CI because local services are unavailable. |

Latest local backend result: **18 passed, 4 skipped, 0 failed**. Latest mocked browser result: **4 passed, 0 failed**. Frontend production build passed.

## Phase 5 CPU inference evidence

| Capability | Status | Evidence |
|---|---|---|
| CPU face presence/count | IMPLEMENTED for executable demo scope | `OpenCVHaarFaceAdapter` with OpenCV 4.14 Haar cascade emits `FACE_PRESENT`, `FACE_ABSENT`, `MULTI_FACE`, count, and bounding boxes. `tests/test_face_inference.py`: 2 passed. |
| Basic face quality | IMPLEMENTED for executable demo scope | Brightness and Laplacian sharpness metrics are included in the output quality schema and API event payload. |
| Face inference API integration | IMPLEMENTED for executable demo scope | `POST /api/sessions/{sid}/inference/face` decodes an uploaded image, executes the adapter, persists a traceable event, and returns the model output. |
| Face latency benchmark | MEASURED, not an SRS acceptance result | 20 warm-up and 100 measured iterations on a 640x480 CPU frame: mean 13.934 ms, p50 13.878 ms, p95 14.748 ms, p99 17.750 ms, throughput 71.767 FPS. No accuracy claim is made. |

The model extra is pinned to `opencv-python-headless>=4.10,<5` because OpenCV 5.0 in this environment removed the `CascadeClassifier` API used by the executable adapter.
