"""Tests for bundled resource path resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from kesit.app.demo import demo_config_path, demo_dxf_path, is_demo_available
from kesit.paths import resource_root


def test_resource_root_in_development():
    root = resource_root()
    assert root.is_dir()
    assert (root / "config" / "demo_floorplan.yaml").exists()
    assert is_demo_available(root)


def test_resource_root_when_frozen(monkeypatch, tmp_path: Path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "config").mkdir()
    (bundle / "sample-files" / "dxf" / "dxf-parser").mkdir(parents=True)
    (bundle / "config" / "demo_floorplan.yaml").write_text("locale: en\n", encoding="utf-8")
    (bundle / "sample-files" / "dxf" / "dxf-parser" / "floorplan.dxf").write_text(
        "demo", encoding="utf-8"
    )

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)

    root = resource_root()
    assert root == bundle
    assert demo_config_path(root) == bundle / "config" / "demo_floorplan.yaml"
    assert demo_dxf_path(root) == bundle / "sample-files" / "dxf" / "dxf-parser" / "floorplan.dxf"
    assert is_demo_available(root)
