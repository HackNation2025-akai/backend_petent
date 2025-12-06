#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -f ".env" ]; then
  source scripts/export_env.sh .env
fi

echo "Running ruff..."
ruff check .

echo "Running mypy..."
mypy app


