"""Tests for Kotline branding assets."""

from pathlib import Path

from kesit.ui import branding


def test_app_name():
    assert branding.APP_NAME == "Kotline"


def test_branding_dir_has_icons():
    bdir = branding.branding_dir()
    assert bdir.is_dir()
    assert (bdir / "app_icon_32.png").exists()
    assert (bdir / "app_icon.ico").exists()


def test_window_title():
    assert "Kotline" in branding.window_title()


def test_load_header_logo():
    logo = branding.load_header_logo(28)
    assert logo is not None
