"""Main application window."""

from __future__ import annotations

import queue
import threading
import tkinter.filedialog as filedialog
from pathlib import Path

import customtkinter as ctk

from kesit.app.config_io import KESIT_EXTENSION, load_project, save_project
from kesit.paths import resource_root
from kesit.app.demo import is_demo_available, load_demo_project
from kesit.app.pipeline import load_inventory, run_pipeline
from kesit.app.project_state import ProjectState, SavedView
from kesit.generation.section_generator import write_diagnostics
from kesit.generation.svg_exporter import export_svg
from kesit.ui import branding, i18n, theme
from kesit.ui.widgets.diagnostics_view import DiagnosticsView
from kesit.ui.widgets.language_selector import LanguageSelector
from kesit.ui.widgets.layer_table import LayerTable
from kesit.ui.widgets.params_form import ParametersForm
from kesit.ui.widgets.plan_canvas import PlanCanvas
from kesit.ui.widgets.section_canvas import SectionCanvas
from kesit.ui.widgets.views_panel import ViewsPanel
from kesit.ui.widgets.workflow_dialog import WorkflowDialog

_REGEN_DEBOUNCE_MS = 300


class MainWindow(ctk.CTk):
    def __init__(self, root_dir: Path | None = None, auto_demo: bool = False):
        super().__init__()
        self.root_dir = root_dir or resource_root()
        self.auto_demo = auto_demo
        self.project = ProjectState()
        self._result_queue: queue.Queue = queue.Queue()
        self._generating = False
        self._regen_after_id: str | None = None
        self._regen_pending = False
        self._header_buttons: dict[str, ctk.CTkButton] = {}
        self._logo_label: ctk.CTkLabel | None = None
        self._title_label: ctk.CTkLabel | None = None
        self._tagline_label: ctk.CTkLabel | None = None
        self._context_file_label: ctk.CTkLabel | None = None
        self._context_view_label: ctk.CTkLabel | None = None
        self._language_selector: LanguageSelector | None = None
        self._panels: ctk.CTkTabview | None = None
        self._panels_parent: ctk.CTkFrame | None = None

        i18n.set_locale(self.project.locale)
        self.title(branding.window_title())
        branding.apply_window_icon(self)
        self.geometry("1280x800")
        self.minsize(960, 640)
        self.configure(fg_color=theme.BG_DARK)

        self._build_header()
        self._build_body()
        self._build_status()
        self._bind_shortcuts()
        self.after(100, self._poll_queue)
        if self.auto_demo and is_demo_available(self.root_dir):
            self.after(300, lambda: self.load_demo(auto_generate=True))

    def _project_filetypes(self) -> list[tuple[str, str]]:
        return [
            (branding.project_file_label(), f"*{KESIT_EXTENSION}"),
            (i18n.t("filetype.yaml"), "*.yaml *.yml"),
            (i18n.t("filetype.json"), "*.json"),
            (i18n.t("filetype.all"), "*.*"),
        ]

    def set_project_context(self) -> None:
        """Update the header's live project/view context labels."""
        if self.project.project_path:
            name = Path(self.project.project_path).name
        elif self.project.dxf_path:
            name = Path(self.project.dxf_path).name
        else:
            name = i18n.t("header.untitled")
        if self._context_file_label:
            self._context_file_label.configure(text=name)
        if self._context_view_label:
            view = self.project.active_view_name
            text = i18n.t("header.view_label", name=view) if view else i18n.t("header.no_view")
            self._context_view_label.configure(text=text)

    def refresh_locale(self) -> None:
        self.title(branding.window_title())
        if self._title_label:
            self._title_label.configure(text=branding.APP_NAME)
        if self._tagline_label:
            self._tagline_label.configure(text=i18n.t("app.tagline"))
        self.set_project_context()
        for key, btn in self._header_buttons.items():
            btn.configure(text=i18n.t(key))
        if self._language_selector:
            self._language_selector.refresh_locale()
        self.generate_btn.configure(text=i18n.t("sidebar.generate"))
        self.status_label.configure(text=i18n.t("status.ready"))
        self.views_panel.refresh_locale()
        self.plan_canvas.refresh_locale()
        self.section_canvas.refresh_locale()
        self.diagnostics.refresh_locale()
        self._rebuild_tabs()

    def _rebuild_tabs(self) -> None:
        if not self._panels or not self._panels_parent:
            return
        try:
            current_idx = self._panels._current_name_index
        except Exception:  # noqa: BLE001
            current_idx = 0

        self.layer_table.destroy()
        self.params_form.destroy()
        self._panels.destroy()

        self._panels = ctk.CTkTabview(self._panels_parent, fg_color=theme.BG_PANEL)
        self._panels.pack(fill="x", pady=(8, 0))
        layers_name = i18n.t("tab.layers")
        params_name = i18n.t("tab.parameters")
        self._panels.add(layers_name)
        self._panels.add(params_name)

        self.layer_table = LayerTable(
            self._panels.tab(layers_name),
            self.project,
            height=160,
            on_layer_hover=self.plan_canvas.set_highlight_layer,
        )
        self.layer_table.pack(fill="both", expand=True)

        self.params_form = ParametersForm(
            self._panels.tab(params_name),
            self.project,
            height=160,
        )
        self.params_form.pack(fill="both", expand=True)
        self.params_form.refresh_from_state()

        try:
            self._panels._segmented_button.set(current_idx)
        except Exception:  # noqa: BLE001
            pass

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-o>", lambda e: self.open_dxf())
        self.bind("<Control-s>", lambda e: self.save_project_dialog())
        self.bind("<Control-q>", lambda e: self.quit())

    def _apply_project_to_ui(self) -> None:
        if self.project.locale:
            i18n.set_locale(self.project.locale)
        if self._language_selector:
            self._language_selector.set_locale(self.project.locale or "en")
        self.plan_canvas.project = self.project
        self.layer_table.state = self.project
        self.layer_table.refresh()
        self.params_form.state = self.project
        self.params_form.refresh_from_state()
        self.views_panel.state = self.project
        self.views_panel.refresh()
        self.refresh_locale()

    def show_workflow(self) -> None:
        WorkflowDialog(self)

    def apply_saved_view(self, view: SavedView) -> None:
        self.project.apply_saved_view(view)
        self.plan_canvas.redraw()
        self.set_project_context()
        self.set_status(i18n.t("status.applied_view_regen", name=view.name))
        self._schedule_section_regenerate()

    def load_demo(self, auto_generate: bool = False) -> None:
        try:
            self.project = load_demo_project(self.root_dir)
            i18n.set_locale(self.project.locale or "en")
            inventory = load_inventory(self.project, convert_geometry=True)
            self.plan_canvas.load_inventory(inventory, self.project)
            self._apply_project_to_ui()
            self.plan_canvas.redraw()
            if self.project.is_ready_to_save_view() and not self.project.find_view("Demo"):
                self.project.save_current_view("Demo")
                self.views_panel.refresh()
            msg = i18n.t("status.demo_loaded")
            if auto_generate:
                msg += i18n.t("status.demo_generating")
            else:
                msg += i18n.t("status.demo_click_generate")
            self.set_status(msg)
            self.diagnostics.show_message(
                i18n.t("diag.demo_loaded_title") + "\n"
                + i18n.t("diag.dxf_label", path=self.project.dxf_path) + "\n"
                + i18n.t(
                    "diag.section_p0",
                    p0=self.project.section.p0,
                    p1=self.project.section.p1,
                ) + "\n"
                + i18n.t("diag.view_point", point=self.project.section.view_point) + "\n"
                + i18n.t("diag.demo_units")
            )
            if auto_generate:
                self.generate_section()
        except Exception as exc:  # noqa: BLE001
            self.set_status(i18n.t("status.demo_failed", exc=i18n.translate_error(str(exc))))
            self.diagnostics.show_message(i18n.translate_error(str(exc)))

    def _on_locale_changed(self, code: str) -> None:
        if code == (self.project.locale or "en"):
            return
        self.project.locale = code
        i18n.set_locale(code)
        self.refresh_locale()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=theme.BG_PANEL, height=56)
        header.pack(fill="x", padx=8, pady=(8, 4))
        header.pack_propagate(False)

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", padx=10, pady=6)
        logo = branding.load_header_logo(36)
        if logo:
            self._logo_label = ctk.CTkLabel(brand, text="", image=logo)
            self._logo_label.pack(side="left", padx=(2, 8))
        wordmark = ctk.CTkFrame(brand, fg_color="transparent")
        wordmark.pack(side="left")
        self._title_label = ctk.CTkLabel(
            wordmark, text=branding.APP_NAME, font=theme.FONT_TITLE,
            text_color=theme.TEXT_PRIMARY, anchor="w",
        )
        self._title_label.pack(anchor="w")
        self._tagline_label = ctk.CTkLabel(
            wordmark, text=i18n.t("app.tagline"), font=theme.FONT_MONO,
            text_color=theme.TEXT_MUTED, anchor="w",
        )
        self._tagline_label.pack(anchor="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=4, pady=6)

        context = ctk.CTkFrame(header, fg_color="transparent")
        context.pack(side="left", fill="x", expand=True, padx=12)
        self._context_file_label = ctk.CTkLabel(
            context, text=i18n.t("header.untitled"), font=theme.FONT_UI_BOLD,
            text_color=theme.TEXT_PRIMARY, anchor="center",
        )
        self._context_file_label.pack(anchor="center")
        self._context_view_label = ctk.CTkLabel(
            context, text=i18n.t("header.no_view"), font=theme.FONT_MONO,
            text_color=theme.TEXT_MUTED, anchor="center",
        )
        self._context_view_label.pack(anchor="center")

        self._language_selector = LanguageSelector(
            actions,
            locale=self.project.locale or "en",
            on_change=self._on_locale_changed,
        )
        self._language_selector.pack(side="right", padx=(8, 0))

        self._header_buttons["header.workflow"] = ctk.CTkButton(
            actions, text=i18n.t("header.workflow"), command=self.show_workflow, width=90,
        )
        self._header_buttons["header.workflow"].pack(side="right", padx=4)

        sep = ctk.CTkFrame(actions, width=1, fg_color=theme.GRID)
        sep.pack(side="right", fill="y", padx=6, pady=4)

        for key, width in (
            ("header.export_json", 100),
            ("header.export_svg", 100),
        ):
            btn = ctk.CTkButton(
                actions,
                text=i18n.t(key),
                command={
                    "header.export_svg": self.export_svg_dialog,
                    "header.export_json": self.export_json_dialog,
                }[key],
                width=width,
            )
            btn.pack(side="right", padx=2)
            self._header_buttons[key] = btn

        sep2 = ctk.CTkFrame(actions, width=1, fg_color=theme.GRID)
        sep2.pack(side="right", fill="y", padx=6, pady=4)

        for key, width in (
            ("header.save_project", 110),
            ("header.open_project", 110),
            ("header.open_dxf", 100),
            ("header.load_demo", 100),
        ):
            btn = ctk.CTkButton(
                actions,
                text=i18n.t(key),
                command={
                    "header.load_demo": lambda: self.load_demo(auto_generate=True),
                    "header.open_dxf": self.open_dxf,
                    "header.open_project": self.open_project,
                    "header.save_project": self.save_project_dialog,
                }[key],
                width=width,
                fg_color=theme.ACCENT if key == "header.load_demo" else None,
            )
            btn.pack(side="right", padx=2)
            self._header_buttons[key] = btn

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color=theme.BG_DARK)
        body.pack(fill="both", expand=True, padx=8, pady=4)

        sidebar = ctk.CTkFrame(body, fg_color=theme.BG_PANEL, width=theme.SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y", padx=(0, 4))
        sidebar.pack_propagate(False)

        self.views_panel = ViewsPanel(
            sidebar,
            self.project,
            on_apply_view=self.apply_saved_view,
            on_status=self.set_status,
        )
        self.views_panel.pack(fill="both", expand=True, padx=0, pady=0)

        self.generate_btn = ctk.CTkButton(
            sidebar, text=i18n.t("sidebar.generate"), command=self.generate_section, fg_color=theme.ACCENT,
        )
        self.generate_btn.pack(side="bottom", fill="x", padx=12, pady=12)

        center = ctk.CTkFrame(body, fg_color=theme.BG_DARK)
        center.pack(side="left", fill="both", expand=True, padx=4)

        top = ctk.CTkFrame(center, fg_color=theme.BG_DARK)
        top.pack(fill="both", expand=True)
        self.plan_canvas = PlanCanvas(top, on_section_changed=self._on_section_changed)
        self.plan_canvas.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.section_canvas = SectionCanvas(top)
        self.section_canvas.pack(side="right", fill="both", expand=True, padx=(4, 0))

        self._panels_parent = center
        self._panels = ctk.CTkTabview(center, fg_color=theme.BG_PANEL)
        self._panels.pack(fill="x", pady=(8, 0))
        self._panels.add(i18n.t("tab.layers"))
        self._panels.add(i18n.t("tab.parameters"))
        self.layer_table = LayerTable(
            self._panels.tab(i18n.t("tab.layers")),
            self.project,
            height=160,
            on_layer_hover=self.plan_canvas.set_highlight_layer,
        )
        self.layer_table.pack(fill="both", expand=True)
        self.params_form = ParametersForm(
            self._panels.tab(i18n.t("tab.parameters")),
            self.project,
            height=160,
        )
        self.params_form.pack(fill="both", expand=True)

    def _build_status(self) -> None:
        status_frame = ctk.CTkFrame(self, fg_color=theme.BG_PANEL)
        status_frame.pack(fill="x", padx=8, pady=(4, 8))
        self.status_label = ctk.CTkLabel(
            status_frame, text=i18n.t("status.ready"), text_color=theme.TEXT_MUTED, anchor="w",
        )
        self.status_label.pack(fill="x", padx=12, pady=4)
        self.diagnostics = DiagnosticsView(status_frame)
        self.diagnostics.pack(fill="x", padx=8, pady=(0, 8))

    def set_status(self, message: str) -> None:
        self.status_label.configure(text=message)

    def _cancel_scheduled_regen(self) -> None:
        if self._regen_after_id is not None:
            self.after_cancel(self._regen_after_id)
            self._regen_after_id = None

    def _schedule_section_regenerate(self) -> None:
        self._cancel_scheduled_regen()
        if self._generating:
            self._regen_pending = True
            return

        def run_regen() -> None:
            self._regen_after_id = None
            if self.project.is_ready_to_generate():
                self.generate_section()

        self._regen_after_id = self.after(_REGEN_DEBOUNCE_MS, run_regen)

    def _invalidate_preview(self) -> None:
        self._cancel_scheduled_regen()
        self.project.last_pipeline_result = None
        self.section_canvas.clear_preview()
        self.diagnostics.show_message(i18n.t("diag.section_changed"))

    def _on_section_changed(self) -> None:
        self.project.active_view_name = None
        self.views_panel.refresh()
        self.set_project_context()
        sec = self.project.section
        if not (sec.p0 and sec.p1 and sec.view_point):
            self._invalidate_preview()
            if sec.p0 and sec.p1 and not sec.view_point:
                self.set_status(i18n.t("status.section_line_set"))
            return

        self.set_status(i18n.t("status.section_updated"))
        self._schedule_section_regenerate()

    def open_dxf(self) -> None:
        path = filedialog.askopenfilename(
            title=i18n.t("dialog.open_dxf"),
            filetypes=[
                (i18n.t("filetype.dxf"), "*.dxf"),
                (i18n.t("filetype.all"), "*.*"),
            ],
        )
        if not path:
            return
        self.project.dxf_path = path
        self._invalidate_preview()
        self.set_project_context()
        self.set_status(i18n.t("status.loading", filename=Path(path).name))
        try:
            raw = load_inventory(self.project)
            self.project.dxf_insunits = raw.insunits
            if self.project.units.get("source") == "auto" and raw.insunits == 4:
                if not self.project.units.get("source_override"):
                    self.project.units["source_override"] = "cm"
                    self.set_status(
                        i18n.t("status.loaded_mm_override", filename=Path(path).name),
                    )
            default_map = ProjectState.load_default_mapping(self.root_dir)
            self.project.apply_defaults_from_inventory(raw.layers, default_map)
            inventory = load_inventory(self.project, convert_geometry=True)
            self.plan_canvas.load_inventory(inventory, self.project)
            self.layer_table.refresh()
            unit_note = i18n.t("status.unit_note_cm") if self.project.units.get("source_override") == "cm" else ""
            self.set_status(
                i18n.t(
                    "status.loaded_dxf",
                    filename=Path(path).name,
                    entities=raw.total_entities,
                    layers=len(raw.layers),
                    unit_note=unit_note,
                ),
            )
            self.diagnostics.show_message(
                i18n.t(
                    "diag.loaded_dxf",
                    path=path,
                    insunits=raw.insunits,
                    layers=len(raw.layers),
                ),
            )
        except Exception as exc:  # noqa: BLE001
            err = i18n.translate_error(str(exc))
            self.set_status(i18n.t("status.error", exc=err))
            self.diagnostics.show_message(err)

    def load_project_into_ui(self, path: str | Path, auto_generate: bool = True) -> None:
        try:
            self.project = load_project(path, root_dir=self.root_dir)
            i18n.set_locale(self.project.locale or "en")
            self._invalidate_preview()
            if self.project.dxf_path:
                inventory = load_inventory(self.project, convert_geometry=True)
                self.plan_canvas.load_inventory(inventory, self.project)
            self._apply_project_to_ui()
            self.plan_canvas.redraw()
            name = Path(path).name
            if self.project.is_ready_to_generate() and auto_generate:
                self.set_status(i18n.t("status.project_loaded_regen", name=name))
                self.diagnostics.show_message(
                    i18n.t(
                        "diag.loaded_project",
                        path=path,
                        dxf=self.project.dxf_path,
                        layers=len(self.project.layer_roles),
                        views=len(self.project.views),
                    ),
                )
                self.generate_section()
            else:
                self.set_status(i18n.t("status.project_loaded", name=name))
                self.diagnostics.show_message(i18n.t("diag.loaded_project_short", path=path))
        except Exception as exc:  # noqa: BLE001
            err = i18n.translate_error(str(exc))
            self.set_status(i18n.t("status.project_load_error", exc=err))
            self.diagnostics.show_message(err)

    def open_project(self) -> None:
        path = filedialog.askopenfilename(
            title=i18n.t("dialog.open_project"),
            filetypes=self._project_filetypes(),
        )
        if not path:
            return
        self.load_project_into_ui(path)

    def save_project_dialog(self) -> None:
        self.params_form.apply_to_state()
        self.project.rebuild_layer_mapping_from_roles()
        initial = Path(self.project.project_path).name if self.project.project_path else "project.kesit"
        path = filedialog.asksaveasfilename(
            title=i18n.t("dialog.save_project"),
            defaultextension=KESIT_EXTENSION,
            initialfile=initial,
            filetypes=self._project_filetypes(),
        )
        if not path:
            return
        save_project(path, self.project)
        self.project.project_path = str(path)
        self.set_project_context()
        self.set_status(i18n.t("status.project_saved", filename=Path(path).name))

    def generate_section(self) -> None:
        if self._generating:
            self._regen_pending = True
            return
        self._cancel_scheduled_regen()
        self.params_form.apply_to_state()
        self.project.rebuild_layer_mapping_from_roles()
        if not self.project.is_ready_to_generate():
            self.set_status(i18n.t("status.complete_steps"))
            return
        self._generating = True
        self._regen_pending = False
        self.generate_btn.configure(state="disabled", text=i18n.t("sidebar.generating"))
        self.set_status(i18n.t("status.generating_section"))

        project_snapshot = self.project

        def worker():
            try:
                result = run_pipeline(project_snapshot)
                self._result_queue.put(("ok", result))
            except Exception as exc:  # noqa: BLE001
                self._result_queue.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._result_queue.get_nowait()
                if kind == "ok":
                    result = payload
                    self.project.last_pipeline_result = result
                    cfg = result.config
                    levels = [
                        (i18n.t("section.level.window_sill"), cfg.window_sill_height_mm),
                        (i18n.t("section.level.door_head"), cfg.door_height_mm),
                        (i18n.t("section.level.window_head"), cfg.window_head_height_mm),
                        (i18n.t("section.level.wall_top"), cfg.wall_height_mm),
                        (i18n.t("section.level.storey"), cfg.storey_height_mm),
                    ]
                    self.section_canvas.show_shapes(
                        result.section_result.shapes,
                        section_depth_mm=cfg.section_depth_mm,
                        levels=levels,
                        output_scale=cfg.output_scale,
                    )
                    self.diagnostics.show_report(result.section_result.diagnostics)
                    counts = result.section_result.diagnostics.counts
                    self.set_status(
                        i18n.t(
                            "status.generated",
                            cut=counts.get("cut", 0),
                            projected=counts.get("projected", 0),
                        ),
                    )
                else:
                    err = i18n.translate_error(str(payload))
                    self.set_status(i18n.t("status.error", exc=err))
                    self.diagnostics.show_message(err)
                self._generating = False
                self.generate_btn.configure(state="normal", text=i18n.t("sidebar.generate"))
                if self._regen_pending:
                    self._regen_pending = False
                    self._schedule_section_regenerate()
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def export_svg_dialog(self) -> None:
        if not self.project.last_pipeline_result:
            self.set_status(i18n.t("status.generate_first"))
            return
        path = filedialog.asksaveasfilename(
            title=i18n.t("dialog.export_svg"),
            defaultextension=".svg",
            filetypes=[(i18n.t("filetype.svg"), "*.svg")],
        )
        if not path:
            return
        result = self.project.last_pipeline_result
        export_svg(result.section_result.shapes, path, result.config, title=i18n.t("export.section_title"))
        self.set_status(i18n.t("status.svg_exported", path=path))

    def export_json_dialog(self) -> None:
        if not self.project.last_pipeline_result:
            self.set_status(i18n.t("status.generate_first"))
            return
        path = filedialog.asksaveasfilename(
            title=i18n.t("dialog.export_json"),
            defaultextension=".json",
            filetypes=[(i18n.t("filetype.json"), "*.json")],
        )
        if not path:
            return
        result = self.project.last_pipeline_result
        write_diagnostics(result.section_result.diagnostics, path)
        self.set_status(i18n.t("status.diagnostics_exported", path=path))
