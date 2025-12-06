#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET="${PYTEST_TARGET:-tests}"

if [ -f ".env" ]; then
  source scripts/export_env.sh .env
fi

echo "Running tests..."
pytest "$TARGET" "$@"

