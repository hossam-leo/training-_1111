# Implementation status

Status is honest for the current CPU-first repository.

| SRS area | Status | Evidence / enablement |
|---|---|---|
| FR-1 browser capture and consent | Partially implemented | Reviewer UI is present; browser capture client needs a production capture route and HTTPS permissions.
| FR-2 edge face inference | Partially implemented | CPU fallback contract exists; no claimed 10 FPS/15% CPU measurement.
| FR-3/FR-6 telemetry and signing | Implemented locally | Signed telemetry API, schema validation, replay-resistant nonce/signature interface.
| FR-7/FR-10 ingest/event delivery | Partially implemented | REST/WebSocket fallback, SQLite idempotency; Redis Streams and 20-session load test require deployment.
| FR-11-FR-21 vision/audio | Partially implemented | Adapter boundary and explicit UNKNOWN/demo events; validation datasets and licensed weights are not supplied.
| FR-22-FR-33 serving/optimization | Partially implemented | Config registry boundary and benchmark scaffold; GPU/ONNX experiments require model weights/hardware.
| FR-34-FR-39 risk/report/UI | Implemented for local vertical | YAML rules, missing-channel safety, timeline UI, standalone HTML report.
| FR-40-FR-47 operations/deployment | Partially implemented | Prometheus endpoint, Docker CPU compose, tests and docs; Grafana/Redis/Postgres production profile remains.
| DR-1/DR-2/DR-3 datasets | Not implemented | No real recordings or 1,500-image/50-trial kits are included; provide consented assets and run documented protocols.
| NFR and rubric performance targets | Not verified | Run Appendix B benchmarks on target hardware; no fabricated results.

Missing or unavailable models always use `UNKNOWN`/`usable=false` and never increase risk by themselves.
