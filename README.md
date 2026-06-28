# Kotline — 2D DXF to Section Generator

Parameter-driven tool that generates 2D architectural section drawings from 2D DXF floor plans.

## Sample files

Primary integration target:

- `sample-files/dxf/dxf-parser/floorplan.dxf`

Additional DXF test samples live in `sample-files/dxf/dxf-parser/` (MIT-licensed, from [bjnortier/dxf](https://github.com/bjnortier/dxf)).

## Setup

```bash
cd Kesit_Projesi
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For the desktop app:

```bash
pip install -e ".[dev,desktop]"
```

## Desktop application

Launch the standalone GUI:

```bash
python -m kesit.ui.app
# or
kesit-gui
```

**Demo / showcase** — loads `floorplan.dxf` with preset section line, view point, layer mapping, and units; auto-generates preview:

```bash
python -m kesit.ui.app --demo
```

Or click **Load Demo** in the toolbar. Config: [`config/demo_floorplan.yaml`](config/demo_floorplan.yaml).

**Workflow:** click **Workflow** in the toolbar for the full step-by-step guide.

**Language:** use the **Language** dropdown in the top toolbar (saved in `.kesit` project files).

1. Open DXF — load a floor plan (or **Load Demo**)
2. Layers — assign each layer a role (walls, openings, annotations, etc.); preview swatches show section appearance
3. Section — **Section Line** (drag) + **View Point** (1 click) on the plan canvas
4. Parameters — set units, heights, and language
5. **Views** — save section + view point presets in the sidebar; switch between saved views
6. Generate Section — preview appears in the right panel; auto-updates when section/view changes

### Project files (`.kesit`)

Use **Save Project** to write a `.kesit` file containing everything you configured:

- Linked DXF path
- Per-layer role assignments
- Units and drawing parameters
- Section line, view point, and saved views
- UI locale (`en` or `tr`)

**Open Project** (or `python -m kesit.ui.app --project myfile.kesit`) restores the full workspace and regenerates the section preview.

Legacy YAML/JSON project files remain supported.

## CLI usage

### Synthetic proof of concept

```bash
python -m kesit.cli.run_poc --config config/defaults.yaml
```

Writes `output/section.svg` and `output/diagnostics.json`.

### Inspect DXF inventory

```bash
python -m kesit.cli.inspect_dxf sample-files/dxf/dxf-parser/floorplan.dxf
```

### Generate section from floorplan DXF

```bash
python -m kesit.cli.run_section --config config/floorplan.yaml
```

Writes `output/floorplan-section.svg` and `output/floorplan-diagnostics.json`.

## Tests

```bash
pytest -q
```

## Configuration

- `config/defaults.yaml` — global drawing parameters and unit settings
- `config/floorplan.yaml` — project preset for `floorplan.dxf` (section line, layer mapping, unit override)

Units are configured per project via the `units` block (`source`, `parameters`, `output`). All geometry is computed internally in millimeters.

## Packaging (standalone executable)

Install build dependencies:

```bash
pip install -e ".[desktop,build]"
```

**Linux:**

```bash
chmod +x scripts/build_linux.sh scripts/kesit.sh
./scripts/build_linux.sh
./scripts/kesit.sh
```

Output: `dist/Kotline/Kotline` binary.

**Windows (PowerShell):**

```powershell
.\scripts\build_windows.ps1
# Output: dist\Kotline\Kotline.exe
```

The PyInstaller spec is in [`packaging/kesit.spec`](packaging/kesit.spec). Default config files from `config/` and branding assets are bundled into the distribution.
