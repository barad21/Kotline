"""Sidebar panel for saved section/view presets."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from kesit.app.project_state import ProjectState, SavedView
from kesit.ui import i18n, theme


class ViewsPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        state: ProjectState,
        on_apply_view: Callable[[SavedView], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=theme.BG_PANEL, **kwargs)
        self.state = state
        self.on_apply_view = on_apply_view
        self.on_status = on_status

        self._title = ctk.CTkLabel(
            self, text=i18n.t("views.title"), font=theme.FONT_UI_BOLD, text_color=theme.TEXT_PRIMARY,
        )
        self._title.pack(anchor="w", padx=12, pady=(12, 4))

        self._help = ctk.CTkLabel(
            self,
            text=i18n.t("views.help"),
            font=theme.FONT_MONO,
            text_color=theme.TEXT_MUTED,
            anchor="w",
            wraplength=theme.SIDEBAR_WIDTH - 24,
            justify="left",
        )
        self._help.pack(anchor="w", padx=12, pady=(0, 8))

        name_row = ctk.CTkFrame(self, fg_color=theme.BG_PANEL)
        name_row.pack(fill="x", padx=8, pady=4)
        self.name_entry = ctk.CTkEntry(name_row, placeholder_text=i18n.t("views.name_placeholder"), width=120)
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._save_btn = ctk.CTkButton(
            name_row, text=i18n.t("views.save"), width=52, command=self._save_current, fg_color=theme.ACCENT,
        )
        self._save_btn.pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=theme.BG_PANEL, height=200)
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.refresh()

    def refresh_locale(self) -> None:
        self._title.configure(text=i18n.t("views.title"))
        self._help.configure(text=i18n.t("views.help"))
        self.name_entry.configure(placeholder_text=i18n.t("views.name_placeholder"))
        self._save_btn.configure(text=i18n.t("views.save"))
        self.refresh()

    def refresh(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        if not self.state.views:
            ctk.CTkLabel(
                self.list_frame,
                text=i18n.t("views.empty"),
                font=theme.FONT_MONO,
                text_color=theme.TEXT_MUTED,
                justify="left",
            ).pack(anchor="w", padx=4, pady=8)
            return

        for view in self.state.views:
            self._add_view_row(view)

    def _add_view_row(self, view: SavedView) -> None:
        row = ctk.CTkFrame(self.list_frame, fg_color=theme.BG_CANVAS)
        row.pack(fill="x", pady=2)

        is_active = self.state.active_view_name == view.name
        label = view.name + (i18n.t("views.active_marker") if is_active else "")
        btn = ctk.CTkButton(
            row,
            text=label,
            anchor="w",
            fg_color=theme.ACCENT if is_active else theme.BG_PANEL,
            hover_color=theme.ACCENT_HOVER,
            command=lambda v=view: self._apply(v),
        )
        btn.pack(side="left", fill="x", expand=True, padx=(4, 2), pady=4)

        ctk.CTkButton(
            row,
            text="×",
            width=28,
            fg_color=theme.ERROR,
            hover_color="#c9302c",
            command=lambda n=view.name: self._delete(n),
        ).pack(side="right", padx=4, pady=4)

    def _save_current(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            if self.on_status:
                self.on_status(i18n.t("views.enter_name"))
            return
        if not self.state.is_ready_to_save_view():
            if self.on_status:
                self.on_status(i18n.t("views.set_before_save"))
            return
        self.state.save_current_view(name)
        self.name_entry.delete(0, "end")
        self.refresh()
        if self.on_status:
            self.on_status(i18n.t("views.saved", name=name))

    def _apply(self, view: SavedView) -> None:
        self.state.apply_saved_view(view)
        self.refresh()
        if self.on_apply_view:
            self.on_apply_view(view)
        if self.on_status:
            self.on_status(i18n.t("views.applied", name=view.name))

    def _delete(self, name: str) -> None:
        if not self.state.delete_saved_view(name):
            return
        self.refresh()
        if self.on_status:
            self.on_status(i18n.t("views.deleted", name=name))
