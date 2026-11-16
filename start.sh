#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export FACE_LAB_MODEL_DIR="${FACE_LAB_MODEL_DIR:-$ROOT/models}"
export FACE_LAB_DATA_DIR="${FACE_LAB_DATA_DIR:-$ROOT}"
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
    echo '请先运行 ./install.sh / Please run ./install.sh first.' >&2
    exit 1
fi
exec "$ROOT/.venv/bin/python" -m face_lab "$@"
