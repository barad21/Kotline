#!/usr/bin/env bash
# Install Kotline to the user application menu (~/.local).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${HOME}/.local/share/kotline"
SOURCE="${ROOT}/dist/Kotline/Kotline"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
ICON_SRC="${ROOT}/assets/branding/app_icon_256.png"

usage() {
  echo "Usage: $0 [--prefix DIR] [--source DIR]" >&2
  echo "  Installs the packaged Kotline binary and registers a desktop launcher." >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      PREFIX="$2"
      shift 2
      ;;
    --source)
      ROOT="$(cd "$2/.." && pwd)"
      SOURCE="$2/Kotline"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

if [[ ! -x "$SOURCE" ]]; then
  echo "Kotline binary not found at: $SOURCE" >&2
  echo "Run scripts/build_linux.sh first, or pass --source dist/Kotline." >&2
  exit 1
fi

if [[ ! -f "$ICON_SRC" ]]; then
  echo "Icon not found at: $ICON_SRC" >&2
  echo "Run scripts/generate_icons.py first." >&2
  exit 1
fi

echo "Installing Kotline to ${PREFIX}..."
rm -rf "$PREFIX"
mkdir -p "$PREFIX"
cp -a "${SOURCE%/*}/." "$PREFIX/"

mkdir -p "$ICON_DIR"
cp "$ICON_SRC" "$ICON_DIR/kotline.png"

mkdir -p "$DESKTOP_DIR"
sed "s|@EXEC@|${PREFIX}/Kotline|g" \
  "$ROOT/packaging/kotline.desktop.in" > "$DESKTOP_DIR/kotline.desktop"
chmod +x "$DESKTOP_DIR/kotline.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" || true
fi

echo "Installed."
echo "  Binary:  ${PREFIX}/Kotline"
echo "  Launcher: ${DESKTOP_DIR}/kotline.desktop"
echo "Launch Kotline from your application menu, or run: ${PREFIX}/Kotline"
