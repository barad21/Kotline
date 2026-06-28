"""Drawing parameters form."""

from __future__ import annotations

import customtkinter as ctk

from kesit.app.project_state import ProjectState
from kesit.ui import i18n, theme

SOURCE_UNIT_OPTIONS = ["auto", "mm", "cm", "m", "in", "ft"]
UNIT_OPTIONS = ["mm", "cm", "m", "in", "ft"]


class ParametersForm(ctk.CTkScrollableFrame):
    PARAM_FIELDS = [
        "wall_height",
        "storey_height",
        "door_height",
        "window_sill_height",
        "window_head_height",
        "section_depth",
        "snap_tolerance",
    ]

    UNIT_FIELDS = [
        ("source", SOURCE_UNIT_OPTIONS),
        ("source_override", None),
        ("parameters", UNIT_OPTIONS),
        ("output", UNIT_OPTIONS),
    ]

    def __init__(self, master, state: ProjectState, **kwargs):
        super().__init__(master, fg_color=theme.BG_PANEL, **kwargs)
        self.state = state
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._unit_menus: dict[str, ctk.CTkOptionMenu] = {}
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._section_labels: list[ctk.CTkLabel] = []
        self._insunits_label: ctk.CTkLabel | None = None
        self._build()

    def _override_options(self) -> list[str]:
        return [i18n.t("params.override_none"), *UNIT_OPTIONS]

    def _unit_field_options(self, key: str) -> list[str]:
        if key == "source":
            return SOURCE_UNIT_OPTIONS
        if key == "source_override":
            return self._override_options()
        return UNIT_OPTIONS

    def _unit_display(self, key: str) -> str:
        val = self.state.units.get(key)
        if key == "source_override":
            if val is None or str(val).lower() in ("", "null", "none"):
                return i18n.t("params.override_none")
            return str(val)
        if val is None:
            return "auto" if key == "source" else "cm"
        return str(val)

    def _param_label_key(self, key: str) -> str:
        return {
            "wall_height": "params.wall_height",
            "storey_height": "params.storey_height",
            "door_height": "params.door_height",
            "window_sill_height": "params.window_sill",
            "window_head_height": "params.window_head",
            "section_depth": "params.section_depth",
            "snap_tolerance": "params.snap_tolerance",
        }[key]

    def _unit_label_key(self, key: str) -> str:
        return {
            "source": "params.plan_source",
            "source_override": "params.source_override",
            "parameters": "params.parameter_unit",
            "output": "params.output_unit",
        }[key]

    def _build(self) -> None:
        units_hdr = ctk.CTkLabel(
            self, text=i18n.t("params.units"), font=theme.FONT_UI_BOLD, text_color=theme.TEXT_PRIMARY,
        )
        units_hdr.pack(anchor="w", padx=8, pady=(8, 4))
        self._section_labels.append(units_hdr)

        for key, _ in self.UNIT_FIELDS:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            lbl = ctk.CTkLabel(row, text=i18n.t(self._unit_label_key(key)), width=140, anchor="w")
            lbl.pack(side="left")
            self._labels[f"unit_{key}"] = lbl
            options = self._unit_field_options(key)
            display = self._unit_display(key)
            if display not in options:
                display = options[0]
            menu = ctk.CTkOptionMenu(
                row,
                values=options,
                width=120,
                command=lambda v, k=key: self._save_unit(k, v),
            )
            menu.set(display)
            menu.pack(side="left", padx=4)
            self._unit_menus[key] = menu

        heights_hdr = ctk.CTkLabel(
            self, text=i18n.t("params.heights"), font=theme.FONT_UI_BOLD, text_color=theme.TEXT_PRIMARY,
        )
        heights_hdr.pack(anchor="w", padx=8, pady=(12, 4))
        self._section_labels.append(heights_hdr)

        for key in self.PARAM_FIELDS:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            lbl = ctk.CTkLabel(row, text=i18n.t(self._param_label_key(key)), width=140, anchor="w")
            lbl.pack(side="left")
            self._labels[key] = lbl
            entry = ctk.CTkEntry(row, width=120)
            entry.insert(0, str(getattr(self.state, key)))
            entry.pack(side="left", padx=4)
            entry.bind("<FocusOut>", lambda e, k=key: self._save_param(k))
            self._entries[key] = entry

        if self.state.dxf_insunits is not None:
            self._insunits_label = ctk.CTkLabel(
                self,
                text=i18n.t("params.insunits", value=self.state.dxf_insunits),
                text_color=theme.TEXT_MUTED,
                font=theme.FONT_MONO,
            )
            self._insunits_label.pack(anchor="w", padx=8, pady=8)

    def _save_param(self, key: str) -> None:
        try:
            setattr(self.state, key, float(self._entries[key].get()))
        except ValueError:
            pass

    def _save_unit(self, key: str, value: str | None = None) -> None:
        if value is None:
            value = self._unit_menus[key].get()
        if key == "source_override":
            none_label = i18n.t("params.override_none")
            self.state.units[key] = None if value == none_label else value
        else:
            self.state.units[key] = value

    def apply_to_state(self) -> None:
        for key in self._entries:
            self._save_param(key)
        for key in self._unit_menus:
            self._save_unit(key)

    def refresh_from_state(self) -> None:
        for key, menu in self._unit_menus.items():
            options = self._unit_field_options(key)
            menu.configure(values=options)
            display = self._unit_display(key)
            if display not in options:
                display = options[0]
            menu.set(display)
            self._labels[f"unit_{key}"].configure(text=i18n.t(self._unit_label_key(key)))
        for key, entry in self._entries.items():
            entry.delete(0, "end")
            entry.insert(0, str(getattr(self.state, key)))
            self._labels[key].configure(text=i18n.t(self._param_label_key(key)))
        for idx, key in enumerate(["params.units", "params.heights"]):
            if idx < len(self._section_labels):
                self._section_labels[idx].configure(text=i18n.t(key))
        if self._insunits_label and self.state.dxf_insunits is not None:
            self._insunits_label.configure(
                text=i18n.t("params.insunits", value=self.state.dxf_insunits),
            )
