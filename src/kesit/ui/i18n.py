"""Lightweight UI localization (English / Turkish)."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from kesit.app.project_state import LAYER_ROLES

_LOCALE = "en"
_LOCALE_CHANGE_CALLBACKS: list[Any] = []

SUPPORTED_LOCALES = ("en", "tr")


def locales_dir() -> Path:
    base = Path(__file__).resolve().parents[1] / "locales"
    if not base.is_dir():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "locales"
            if bundled.is_dir():
                return bundled
    return base


@lru_cache(maxsize=4)
def _load_catalog(locale: str) -> dict[str, str]:
    path = locales_dir() / f"{locale}.json"
    if not path.exists():
        path = locales_dir() / "en.json"
    return json.loads(path.read_text(encoding="utf-8"))


def get_locale() -> str:
    return _LOCALE


def set_locale(locale: str) -> None:
    global _LOCALE
    locale = locale if locale in SUPPORTED_LOCALES else "en"
    if locale == _LOCALE:
        return
    _LOCALE = locale
    for callback in list(_LOCALE_CHANGE_CALLBACKS):
        callback()


def register_locale_change_callback(callback) -> None:
    _LOCALE_CHANGE_CALLBACKS.append(callback)


def t(key: str, **kwargs: Any) -> str:
    catalog = _load_catalog(_LOCALE)
    text = catalog.get(key) or _load_catalog("en").get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def role_label(role: str) -> str:
    return t(f"role.{role}")


def role_hint(role: str) -> str:
    return t(f"role.hint.{role}")


def role_labels() -> list[str]:
    return [role_label(r) for r in LAYER_ROLES]


def role_from_label(label: str) -> str:
    for role in LAYER_ROLES:
        if role_label(role) == label:
            return role
    if label in LAYER_ROLES:
        return label
    return "skip"


def translate_error(message: str) -> str:
    mapping = {
        "No DXF file loaded": "error.no_dxf",
        "Project is missing DXF path or section definition": "error.missing_section",
        "Section configuration is incomplete": "error.incomplete_section",
    }
    if message.startswith("Demo config not found:"):
        path = message.split(":", 1)[-1].strip()
        return t("error.demo_config", path=path)
    if message.startswith("Demo DXF not found:"):
        path = message.split(":", 1)[-1].strip()
        return t("error.demo_dxf", path=path)
    key = mapping.get(message)
    return t(key) if key else message
