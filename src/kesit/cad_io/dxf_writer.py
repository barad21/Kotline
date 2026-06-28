"""DXF export — Phase 6 stub."""

from __future__ import annotations

from pathlib import Path

from kesit.models import SectionShape


def export_section_dxf(shapes: list[SectionShape], path: str | Path) -> None:
    """Export section geometry to DXF (not yet implemented)."""
    raise NotImplementedError(
        "DXF section export is planned for Phase 6. "
        "Layers: SECTION-CUT, SECTION-PROJECTION, SECTION-HATCH, SECTION-ANNOTATION."
    )
