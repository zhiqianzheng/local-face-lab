#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
if command -v uv >/dev/null 2>&1; then
    [[ -x .venv/bin/python ]] || uv venv --python 3.12 .venv
    uv pip install --python .venv/bin/python .
else
    PYTHON="${PYTHON:-python3.12}"
    "$PYTHON" -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install .
fi
./start.sh --download-only
printf '\n安装完成。运行 ./start.sh 打开本地表情实验室。\n'
