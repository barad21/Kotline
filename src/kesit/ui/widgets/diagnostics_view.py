"""Diagnostics text panel."""

from __future__ import annotations

import json

import customtkinter as ctk

from kesit.models import DiagnosticReport
from kesit.ui import i18n, theme


class DiagnosticsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG_PANEL, **kwargs)
        self._title = ctk.CTkLabel(
            self, text=i18n.t("diagnostics.title"), font=theme.FONT_UI_BOLD, text_color=theme.TEXT_PRIMARY,
        )
        self._title.pack(anchor="w", padx=8, pady=4)
        self.text = ctk.CTkTextbox(self, font=theme.FONT_MONO, height=theme.STATUS_HEIGHT, fg_color=theme.BG_DARK)
        self.text.pack(fill="both", expand=True, padx=8, pady=4)
        self.text.configure(state="disabled")

    def refresh_locale(self) -> None:
        self._title.configure(text=i18n.t("diagnostics.title"))

    def show_report(self, report: DiagnosticReport | None) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        if report is None:
            self.text.insert("end", i18n.t("diagnostics.empty"))
        else:
            self.text.insert("end", json.dumps(report.to_dict(), indent=2))
        self.text.configure(state="disabled")

    def show_message(self, message: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", message)
        self.text.configure(state="disabled")
