"""Tests for architectural role swatches."""

import json
from pathlib import Path

from kesit.app.project_state import LAYER_ROLES
from kesit.ui import i18n


def test_role_hint_keys_for_all_roles():
    i18n.set_locale("en")
    for role in LAYER_ROLES:
        hint = i18n.role_hint(role)
        assert hint and hint != f"role.hint.{role}"


def test_role_hint_parity_en_tr():
    root = Path(__file__).resolve().parents[1] / "src" / "kesit" / "locales"
    en = json.loads((root / "en.json").read_text(encoding="utf-8"))
    tr = json.loads((root / "tr.json").read_text(encoding="utf-8"))
    hint_keys = {k for k in en if k.startswith("role.hint.")}
    assert hint_keys == {k for k in tr if k.startswith("role.hint.")}
    assert len(hint_keys) == len(LAYER_ROLES)


def test_role_hints_distinguish_doors_and_windows():
    i18n.set_locale("en")
    doors = i18n.role_hint("doors")
    windows = i18n.role_hint("windows")
    assert doors != windows
    assert "floor" in doors.lower() or "sill" in doors.lower()
    assert "project" in windows.lower() or "gray" in windows.lower()

