# ProctorStream

ProctorStream is a CPU-first, end-to-end AI proctoring inference platform for **consented mock exams only**. It provides a working vertical from session capture and signed telemetry through normalized events, transparent rule-based risk scoring, a reviewer timeline, and standalone HTML reports.

The repository deliberately uses deterministic CPU fallback detectors and synthetic demo events when heavyweight model weights or GPU hardware are unavailable. Those fallbacks are explicit `UNKNOWN`/demo states and are not evidence of model accuracy.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
# Optional real CPU adapters:
# pip install -e '.[models]'
python scripts/validate_environment.py
python scripts/seed_demo.py
uvicorn services.api.main:app --reload
# reviewer: http://127.0.0.1:8000/
# candidate capture: http://127.0.0.1:8000/#capture
pytest
```

Run the complete local demo in one command with `python scripts/run_demo.py`. The expanded Compose topology connects the API, realtime/batch workers, PostgreSQL, Redis, MinIO, Prometheus, Grafana, and Nginx. Start the full stack with `./scripts/start_stack.sh`; export non-development telemetry and auth secrets first. API documentation is available at `/docs`.

The backend suite is run with `pytest -q`. The mocked Chromium browser suite is run with `cd frontend && npm install && npx playwright install chromium && npm run test:e2e`. CI runs both service-container integration tests and Playwright tests.

Generate synthetic scenario metadata without creating recordings:

```bash
python datasets/generate_synthetic_scenarios.py --count 50
```

This metadata is explicitly synthetic and cannot be used as an accuracy result.

## Safety and scope

This is a systems/research platform, not an automated decision maker. It requires consent, displays recording status in the browser, stores no real student recordings in the repository, and requires human review for every flag. Missing channels never increase risk. See `docs/ethics-and-privacy.md` and `docs/IMPLEMENTATION_STATUS.md`.
