# Current acceptance evidence

## Verified locally

- Backend: **27 passed, 4 skipped, 0 failed**.
- Chromium Playwright: **4 passed, 0 failed** with fake media devices.
- Frontend production build: passed.
- Python compilation: passed.
- Compose YAML: all nine services parsed.
- OpenCV Haar face tests: included in the backend pass; negative cases cover no-face, poor lighting, blur, and partial-frame inputs.
- WebRTC VAD tests: included in the backend pass; invalid sample-rate and API persistence cases are covered.
- Reviewer decision tests: included in the backend pass; reviewer authorization, candidate privilege escalation, persistence, and invalid-decision validation are covered.

## CPU benchmark

OpenCV Haar face inference was measured with 20 warm-up and 100 measured iterations at three resolutions:

| Resolution | Mean ms | p50 ms | p95 ms | p99 ms | FPS |
|---|---:|---:|---:|---:|---:|
| 320x240 | 4.022 | 4.003 | 4.465 | 4.595 | 248.654 |
| 640x480 | 12.471 | 12.435 | 13.018 | 13.328 | 80.187 |
| 1280x720 | 31.377 | 31.271 | 32.460 | 33.319 | 31.871 |

These are local CPU timings only. No accuracy or SRS acceptance claim is made.

## Capability boundary

Face presence/count and basic quality metrics are executable demo capabilities. WebRTC VAD is executable for audio activity only. Reviewer decisions are persistent and audited. Identity verification, anti-spoofing, gaze, head pose, speaker verification, prohibited-object detection, multi-person identity attribution, and reliable cheating detection remain blocked, partial, or stub as recorded in `docs/capability-status.md`.

## Runtime boundary

Docker is unavailable in this sandbox. PostgreSQL, Redis, MinIO, Nginx, Prometheus, Grafana, and live worker integration tests were not started locally. Four integration tests remain skipped until service containers are available through CI or a Docker-enabled environment.
