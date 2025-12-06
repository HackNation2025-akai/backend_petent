#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "Stopping and cleaning containers + volume (docker compose down -v)..."
docker compose down -v


