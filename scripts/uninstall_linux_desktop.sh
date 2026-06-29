#!/usr/bin/env bash
# Remove Kotline desktop launcher and installed files.
set -euo pipefail

PREFIX="${HOME}/.local/share/kotline"
DESKTOP="${HOME}/.local/share/applications/kotline.desktop"
ICON="${HOME}/.local/share/icons/hicolor/256x256/apps/kotline.png"

echo "Removing Kotline installation..."
rm -rf "$PREFIX"
rm -f "$DESKTOP" "$ICON"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${HOME}/.local/share/applications" || true
fi

echo "Uninstalled Kotline from ~/.local"
