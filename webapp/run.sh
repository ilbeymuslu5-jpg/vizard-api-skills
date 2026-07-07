#!/usr/bin/env bash
# Local Vizard clone - setup and launch script.
set -euo pipefail
cd "$(dirname "$0")/backend"

if [ ! -d .venv ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

echo "Starting server on http://localhost:8000 ..."
exec ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
