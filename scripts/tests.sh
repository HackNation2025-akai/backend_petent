#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

mkdir -p logs

choice=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --unit) choice="1"; shift ;;
    --integration) choice="2"; shift ;;
    --live) choice="3"; shift ;;
    --all) choice="4"; shift ;;
    *) break ;;
  esac
done

if [[ -z "$choice" ]]; then
  echo "Choose tests to run:"
  echo " 1) Unit"
  echo " 2) Integration (ASGI transport, no real backend)"
  echo " 3) Live API (requires backend running + RUN_LIVE_API=1, API_BASE_URL)"
  echo " 4) All (unit + integration)"
  read -r -p "Enter choice [1-4]: " choice
fi

LOG_FILE="logs/pytest_$(date +%Y%m%d_%H%M%S).log"

case "$choice" in
  1)
    CMD=(env PYTEST_TARGET=tests/unit "$ROOT/scripts/test.sh" "$@")
    ;;
  2)
    CMD=(env PYTEST_TARGET=tests/integration "$ROOT/scripts/test.sh" -m "not live_api" "$@")
    ;;
  3)
    CMD=(env RUN_LIVE_API=1 PYTEST_TARGET=tests/integration "$ROOT/scripts/test.sh" -m live_api "$@")
    ;;
  4)
    CMD=(env RUN_LIVE_API=1 "$ROOT/scripts/test.sh" "$@")
    ;;
  *)
    echo "Invalid choice" >&2
    exit 1
    ;;
esac

echo "Log: $LOG_FILE"
"${CMD[@]}" | tee "$LOG_FILE"


