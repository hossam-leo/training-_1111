#!/usr/bin/env bash
set -euo pipefail
: "${PROCTORSTREAM_TELEMETRY_SECRET:=change-me-in-development}"
: "${PROCTORSTREAM_AUTH_SECRET:=change-me-in-development}"
if [[ "$PROCTORSTREAM_TELEMETRY_SECRET" == "change-me-in-development" || "$PROCTORSTREAM_AUTH_SECRET" == "change-me-in-development" ]]; then
  echo 'WARNING: development secrets are active; export PROCTORSTREAM_TELEMETRY_SECRET and PROCTORSTREAM_AUTH_SECRET for deployment.' >&2
fi
export PROCTORSTREAM_TELEMETRY_SECRET PROCTORSTREAM_AUTH_SECRET
exec docker compose up --build "$@"
