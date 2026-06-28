"""Modal dialog showing the full Kotline workflow."""

from __future__ import annotations

import customtkinter as ctk

from kesit.ui import i18n, theme

WORKFLOW_STEP_KEYS = [
    ("workflow.step1.title", "workflow.step1.desc"),
    ("workflow.step2.title", "workflow.step2.desc"),
    ("workflow.step3.title", "workflow.step3.desc"),
    ("workflow.step4.title", "workflow.step4.desc"),
    ("workflow.step5.title", "workflow.step5.desc"),
    ("workflow.step6.title", "workflow.step6.desc"),
    ("workflow.step7.title", "workflow.step7.desc"),
]


class WorkflowDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(i18n.t("workflow.title"))
        self.geometry("480x420")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_DARK)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text=i18n.t("workflow.header"),
            font=theme.FONT_TITLE,
            text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(16, 8))

        body = ctk.CTkScrollableFrame(self, fg_color=theme.BG_PANEL)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        for title_key, desc_key in WORKFLOW_STEP_KEYS:
            ctk.CTkLabel(
                body, text=i18n.t(title_key), font=theme.FONT_UI_BOLD, text_color=theme.ACCENT, anchor="w",
            ).pack(anchor="w", padx=8, pady=(10, 2))
            ctk.CTkLabel(
                body, text=i18n.t(desc_key), font=theme.FONT_UI, text_color=theme.TEXT_MUTED,
                anchor="w", justify="left", wraplength=420,
            ).pack(anchor="w", padx=8, pady=(0, 4))

        ctk.CTkButton(
            self, text=i18n.t("workflow.close"), command=self.destroy, width=100, fg_color=theme.ACCENT,
        ).pack(pady=12)

        self.after(50, self.focus_force)
