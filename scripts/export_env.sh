#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "File $ENV_FILE not found. Create it based on README." >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

echo "Loaded variables from $ENV_FILE"


