"""Application root paths for development and PyInstaller bundles."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    """Directory containing bundled config/, assets/, sample-files/, etc."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]
