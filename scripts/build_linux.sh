#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate 2>/dev/null || true
pip install -e ".[desktop,build]" -q
pyinstaller packaging/kesit.spec --noconfirm
echo "Build complete: $ROOT/dist/Kotline/"
