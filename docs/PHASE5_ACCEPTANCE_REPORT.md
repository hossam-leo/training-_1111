# Phase 5 acceptance evidence

## Executed evidence

Backend regression: **18 passed, 4 skipped, 0 failed** before the OpenCV extra; the four skips require live PostgreSQL, Redis, or MinIO endpoints. Face-specific tests after installing OpenCV 4.14: **2 passed**. Chromium Playwright suite: **4 passed** using fake camera/microphone devices. Frontend Vite build: passed. Compose YAML validation: passed for all nine declared services. Docker runtime: unavailable in the current environment.

The face-specific API test creates a session, uploads a generated PNG frame to `POST /api/sessions/{sid}/inference/face`, executes the OpenCV Haar cascade, persists a traceable `FACE_ABSENT` event, and reads that event back from the reviewer session endpoint.

The CPU face benchmark uses 20 warm-up iterations and 100 measured 640x480 CPU frames. It measured mean 13.934 ms, p50 13.878 ms, p95 14.748 ms, p99 17.750 ms, and 71.767 FPS on the current machine. These are local execution measurements only and do not constitute accuracy or SRS acceptance evidence.

## Capability classification

- **IMPLEMENTED:** consented capture plumbing, signed telemetry, replay/stale checks, PostgreSQL/Redis/MinIO adapters, optional route-level RBAC, OpenCV CPU face presence/count and basic quality metrics, reviewer event/report path, mocked Chromium capture tests.
- **PARTIAL:** live service integration, full authenticated identity management, worker recovery against live Redis, MinIO failure recovery, real-device browser behavior, audio/VAD, prohibited-object adapter path, and production key delivery.
- **STUB:** rule-based risk aggregation as a mock policy path; it is not validated cheating detection.
- **BLOCKED:** identity verification, anti-spoofing, gaze, head pose, speaker verification, multi-person identity attribution, required datasets, institutional approval, and live Docker/service execution in this environment.

## Acceptance conclusion

The project remains **not production-ready** and the complete SRS remains **not accepted**. Docker, PostgreSQL, Redis, and MinIO must be run in CI or a Docker-enabled environment before live infrastructure claims can be made. Real labeled datasets and model validation are still required for AI acceptance.
