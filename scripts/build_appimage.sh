#!/usr/bin/env bash
# Build a portable AppImage from the PyInstaller bundle.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="0.1.0"
APPDIR="${ROOT}/Kotline.AppDir"
OUTPUT="${ROOT}/dist/Kotline-x86_64.AppImage"
ICON_SRC="${ROOT}/assets/branding/app_icon_256.png"

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "appimagetool not found." >&2
  echo "Download from https://github.com/AppImage/AppImageKit/releases" >&2
  echo "  wget -O appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" >&2
  echo "  chmod +x appimagetool && sudo mv appimagetool /usr/local/bin/" >&2
  exit 1
fi

"${ROOT}/scripts/build_linux.sh"

BIN="${ROOT}/dist/Kotline/Kotline"
if [[ ! -x "$BIN" ]]; then
  echo "Expected binary at ${BIN}" >&2
  exit 1
fi

if [[ ! -f "$ICON_SRC" ]]; then
  python scripts/generate_icons.py
fi

echo "Assembling AppDir..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR"
cp -a "${ROOT}/dist/Kotline/." "$APPDIR/"

cat > "${APPDIR}/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/Kotline" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

cp "$ICON_SRC" "${APPDIR}/kotline.png"

cat > "${APPDIR}/kotline.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Kotline
Comment=DXF floor plan to architectural section
Exec=AppRun
Icon=kotline
Terminal=false
Categories=Graphics;Engineering;
StartupWMClass=Kotline
X-AppImage-Version=${VERSION}
EOF

export ARCH=x86_64
export APPIMAGETOOL_EXTRACT_AND_RUN="${APPIMAGETOOL_EXTRACT_AND_RUN:-1}"
appimagetool "${APPDIR}" "${OUTPUT}"

echo "AppImage complete: ${OUTPUT}"
