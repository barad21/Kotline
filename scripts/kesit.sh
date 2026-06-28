#!/usr/bin/env bash
# Launcher for packaged Kotline on Linux
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/dist/Kotline/Kotline"
if [[ ! -x "$BIN" ]]; then
  echo "Kotline binary not found. Run scripts/build_linux.sh first." >&2
  exit 1
fi
exec "$BIN" "$@"
