"""Kesit project file format (.kesit) — save/load workspace state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kesit.app.project_state import ProjectState
from kesit.config import load_config, save_config

KESIT_FORMAT = "kesit-project"
KESIT_VERSION = "1.0"
KESIT_EXTENSION = ".kesit"


def is_kesit_project(path: str | Path) -> bool:
    path = Path(path)
    if path.suffix.lower() == KESIT_EXTENSION:
        return True
    try:
        from kesit.config import _load_raw

        raw = _load_raw(path)
        return raw.get("kesit_format") == KESIT_FORMAT
    except (OSError, ValueError, TypeError):
        return False


def build_project_document(state: ProjectState) -> dict[str, Any]:
    """Serialize full GUI project state for disk."""
    data = state.to_config_dict()
    data["kesit_format"] = KESIT_FORMAT
    data["kesit_version"] = KESIT_VERSION
    if state.layer_roles:
        data["layer_roles"] = dict(state.layer_roles)
    return data


def save_project(path: str | Path, state: ProjectState) -> None:
    path = Path(path)
    if path.suffix.lower() not in (".yaml", ".yml", ".json", KESIT_EXTENSION):
        path = path.with_suffix(KESIT_EXTENSION)
    data = build_project_document(state)
    save_config(data, path)
    state.project_path = str(path.resolve())


def resolve_dxf_path(dxf_path: str | None, project_path: Path, root_dir: Path) -> str | None:
    if not dxf_path:
        return None
    candidate = Path(dxf_path)
    if candidate.is_absolute() and candidate.exists():
        return str(candidate)
    search_roots = (
        project_path.parent,
        project_path.parent.parent,
        root_dir,
        Path.cwd(),
    )
    for root in search_roots:
        resolved = (root / candidate).resolve()
        if resolved.exists():
            return str(resolved)
    return dxf_path


def load_project(path: str | Path, root_dir: Path | None = None) -> ProjectState:
    path = Path(path).resolve()
    root_dir = root_dir or path.parent

    preview = load_config(path)
    dxf_insunits = None
    if preview.dxf_path:
        from kesit.cad_io.dxf_reader import read_dxf

        try:
            resolved = resolve_dxf_path(preview.dxf_path, path, root_dir)
            if resolved:
                dxf_insunits = read_dxf(resolved).insunits
        except OSError:
            pass

    state = ProjectState.from_config_file(path, dxf_insunits=dxf_insunits)
    state.project_path = str(path)

    if state.dxf_path:
        state.dxf_path = resolve_dxf_path(state.dxf_path, path, root_dir) or state.dxf_path

    raw = preview.raw
    saved_roles = raw.get("layer_roles")

    if state.dxf_path:
        from kesit.app.pipeline import load_inventory

        inv = load_inventory(state)
        state.detected_layers = list(inv.layers)

        if saved_roles and isinstance(saved_roles, dict):
            state.layer_roles = {layer: str(saved_roles.get(layer, "skip")) for layer in inv.layers}
            state.rebuild_layer_mapping_from_roles()
        else:
            default_map = {}
            for candidate in (path.parent.parent, path.parent, root_dir, Path.cwd()):
                map_path = candidate / "config" / "layer_mapping.json"
                if map_path.exists():
                    default_map = ProjectState.load_default_mapping(candidate)
                    break
            state.apply_defaults_from_inventory(inv.layers, default_map)
            for layer in inv.layers:
                if layer not in state.layer_roles:
                    state.layer_roles[layer] = "skip"
    elif saved_roles and isinstance(saved_roles, dict):
        state.layer_roles = {str(k): str(v) for k, v in saved_roles.items()}

    return state
