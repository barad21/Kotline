"""Kotline branding assets and window icon helpers."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from kesit.ui import i18n

APP_NAME = "Kotline"


def window_title() -> str:
    return f"{APP_NAME} — {i18n.t('app.tagline')}"


def project_file_label() -> str:
    return i18n.t("app.project_file_label")


def branding_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / "assets" / "branding",
        Path(__file__).resolve().parents[2] / "assets" / "branding",
    ]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.insert(0, Path(meipass) / "assets" / "branding")
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


def _icon_path(size: int) -> Path | None:
    path = branding_dir() / f"app_icon_{size}.png"
    return path if path.exists() else None


def load_header_logo(size: int = 28) -> ctk.CTkImage | None:
    for candidate in (size, 32, 64, 256):
        path = _icon_path(candidate)
        if path is None:
            continue
        try:
            img = Image.open(path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        except OSError:
            continue
    return None


def apply_window_icon(window: tk.Misc) -> None:
    for size in (64, 32, 256):
        path = _icon_path(size)
        if path is None:
            continue
        try:
            photo = tk.PhotoImage(file=str(path))
            window.iconphoto(True, photo)
            window._kotline_icon = photo  # keep reference
            return
        except tk.TclError:
            continue
