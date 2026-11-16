#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Keep the local user-service shortcut working; other installations run in the foreground.
if command -v systemctl >/dev/null && systemctl --user is-active --quiet face-lab.service; then
    exec "$ROOT/start.sh" "$@"
fi
exec "$ROOT/start.sh" "$@"
