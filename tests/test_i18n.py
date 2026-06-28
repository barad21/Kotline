"""Tests for UI localization."""

import json
from pathlib import Path

from kesit.app.project_state import LAYER_ROLES
from kesit.ui import i18n

LOCALES_DIR = Path(__file__).resolve().parents[1] / "src" / "kesit" / "locales"


def test_en_tr_key_parity():
    en = json.loads((LOCALES_DIR / "en.json").read_text(encoding="utf-8"))
    tr = json.loads((LOCALES_DIR / "tr.json").read_text(encoding="utf-8"))
    assert set(en.keys()) == set(tr.keys())


def test_t_interpolation():
    i18n.set_locale("en")
    assert "Demo" in i18n.t("views.saved", name="Demo")


def test_role_label_round_trip():
    i18n.set_locale("en")
    for role in LAYER_ROLES:
        label = i18n.role_label(role)
        assert i18n.role_from_label(label) == role

    i18n.set_locale("tr")
    for role in LAYER_ROLES:
        label = i18n.role_label(role)
        assert i18n.role_from_label(label) == role


def test_translate_error():
    i18n.set_locale("en")
    assert "DXF" in i18n.translate_error("No DXF file loaded")
    i18n.set_locale("tr")
    assert "DXF" in i18n.translate_error("No DXF file loaded")


def test_locale_catalog_loads():
    i18n.set_locale("en")
    assert i18n.t("tab.layers") == "Layers"
    i18n.set_locale("tr")
    assert i18n.t("tab.layers") == "Katmanlar"
