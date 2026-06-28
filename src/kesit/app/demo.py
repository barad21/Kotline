"""Demo project loader for floorplan.dxf showcase."""

from __future__ import annotations

from pathlib import Path

from kesit.app.config_io import load_project

DEMO_CONFIG_NAME = "demo_floorplan.yaml"


def demo_config_path(root: Path) -> Path:
    return root / "config" / DEMO_CONFIG_NAME


def demo_dxf_path(root: Path) -> Path:
    return root / "sample-files" / "dxf" / "dxf-parser" / "floorplan.dxf"


def is_demo_available(root: Path) -> bool:
    return demo_config_path(root).exists() and demo_dxf_path(root).exists()


def load_demo_project(root: Path):
    """Load pre-configured demo project for floorplan.dxf."""
    config = demo_config_path(root)
    if not config.exists():
        raise FileNotFoundError(f"Demo config not found: {config}")
    project = load_project(config)
    dxf = demo_dxf_path(root)
    if not dxf.exists():
        raise FileNotFoundError(f"Demo DXF not found: {dxf}")
    project.dxf_path = str(dxf)
    project.project_path = str(config)
    return project
