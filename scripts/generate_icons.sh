#!/usr/bin/env bash
# Generate Kotline app icons from the master PNG (assets/branding/app_icon_master.png).
# Delegates to the Python generator, which downscales the master into the PNG
# sizes + app_icon.ico (and falls back to a programmatic mark if no master).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python "$ROOT/scripts/generate_icons.py"
