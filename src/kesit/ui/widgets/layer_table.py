"""Layer role assignment table."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from kesit.app.project_state import ProjectState
from kesit.ui import i18n, theme
from kesit.ui.widgets.role_picker import RolePicker
from kesit.ui.widgets.role_swatch import RoleLegendStrip


class LayerTable(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        state: ProjectState,
        on_layer_hover: Callable[[str | None], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=theme.BG_PANEL, **kwargs)
        self.state = state
        self.on_layer_hover = on_layer_hover
        self._pickers: dict[str, RolePicker] = {}
        self._row_frames: dict[str, ctk.CTkFrame] = {}
        self._hover_layer: str | None = None
        self._clear_hover_after_id: str | None = None
        self._legend = RoleLegendStrip(self)
        self.refresh()

    def refresh(self) -> None:
        self._cancel_clear_hover()
        self._hover_layer = None
        if self.on_layer_hover:
            self.on_layer_hover(None)

        for widget in self.winfo_children():
            widget.destroy()
        self._pickers.clear()
        self._row_frames.clear()

        legend_hdr = ctk.CTkLabel(
            self, text=i18n.t("layers.legend_title"), font=theme.FONT_UI_BOLD,
            text_color=theme.TEXT_MUTED, anchor="w",
        )
        legend_hdr.pack(anchor="w", padx=8, pady=(4, 0))
        self._legend = RoleLegendStrip(self)
        self._legend.pack(fill="x", padx=4, pady=(0, 4))
        self._legend.refresh()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=4, pady=(2, 2))
        ctk.CTkLabel(
            header, text=i18n.t("layers.layer"), font=theme.FONT_UI_BOLD, width=180, anchor="w",
        ).pack(side="left", padx=4)
        ctk.CTkLabel(
            header, text=i18n.t("layers.role"), font=theme.FONT_UI_BOLD, width=200, anchor="w",
        ).pack(side="left", padx=4)

        for layer in sorted(self.state.detected_layers):
            row = ctk.CTkFrame(self, fg_color="transparent", corner_radius=4)
            row.pack(fill="x", padx=2, pady=1)
            self._row_frames[layer] = row

            label = ctk.CTkLabel(row, text=layer, font=theme.FONT_MONO, width=180, anchor="w")
            label.pack(side="left", padx=4, pady=2)

            current = self.state.layer_roles.get(layer, "skip")
            picker = RolePicker(
                row,
                role=current,
                width=200,
                command=lambda role, l=layer: self._on_change(l, role),
            )
            picker.pack(side="left", padx=4, pady=2)
            self._pickers[layer] = picker

            self._bind_row_hover(row, layer, label, picker)

    def refresh_locale(self) -> None:
        self._legend.refresh_locale()
        for picker in self._pickers.values():
            picker.refresh_locale()

    def _bind_row_hover(self, row: ctk.CTkFrame, layer: str, *widgets) -> None:
        for widget in (row, *widgets):
            widget.bind("<Enter>", lambda e, l=layer: self._on_row_enter(l))
            widget.bind("<Leave>", lambda e: self._schedule_clear_hover())

    def _cancel_clear_hover(self) -> None:
        if self._clear_hover_after_id is not None:
            self.after_cancel(self._clear_hover_after_id)
            self._clear_hover_after_id = None

    def _schedule_clear_hover(self) -> None:
        self._cancel_clear_hover()
        self._clear_hover_after_id = self.after(40, self._clear_hover)

    def _clear_hover(self) -> None:
        self._clear_hover_after_id = None
        if self._hover_layer is None:
            return
        self._hover_layer = None
        for row in self._row_frames.values():
            row.configure(fg_color="transparent")
        if self.on_layer_hover:
            self.on_layer_hover(None)

    def _on_row_enter(self, layer: str) -> None:
        self._cancel_clear_hover()
        if self._hover_layer == layer:
            return
        if self._hover_layer and self._hover_layer in self._row_frames:
            self._row_frames[self._hover_layer].configure(fg_color="transparent")
        self._hover_layer = layer
        self._row_frames[layer].configure(fg_color=theme.LAYER_ROW_HOVER)
        if self.on_layer_hover:
            self.on_layer_hover(layer)

    def _on_change(self, layer: str, role: str) -> None:
        self.state.layer_roles[layer] = role
        self.state.rebuild_layer_mapping_from_roles()
