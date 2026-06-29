#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install -e ".[desktop,build]" -q
python scripts/generate_icons.py
pyinstaller packaging/kesit.spec --noconfirm

echo "Build complete:"
echo "  Binary: $ROOT/dist/Kotline/Kotline"
echo "  Folder: $ROOT/dist/Kotline/"
