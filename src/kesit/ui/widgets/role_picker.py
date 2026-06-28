"""Role picker with section-preview swatch beside each option."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from kesit.app.project_state import LAYER_ROLES
from kesit.ui import i18n, theme
from kesit.ui.widgets.role_swatch import RoleSwatch


class RolePicker(ctk.CTkFrame):
    """Compact role selector: swatch + label on the button; same in the popup list."""

    def __init__(
        self,
        master,
        role: str = "skip",
        width: int = 200,
        command: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._role = role
        self._command = command
        self._popup: ctk.CTkToplevel | None = None
        self._picker_width = width
        self._outside_bind_id: str | None = None

        self._button = ctk.CTkFrame(
            self, fg_color=theme.BG_CANVAS, corner_radius=6, border_width=1, border_color=theme.GRID,
        )
        self._button.pack(fill="x")
        self._button.bind("<Button-1>", lambda e: self._toggle_popup())
        self._button.configure(cursor="hand2")

        inner = ctk.CTkFrame(self._button, fg_color="transparent")
        inner.pack(fill="x", padx=4, pady=2)
        inner.bind("<Button-1>", lambda e: self._toggle_popup())

        self._swatch = RoleSwatch(inner, role=role, width=24, height=16)
        self._swatch.pack(side="left", padx=(0, 6))
        self._swatch.bind("<Button-1>", lambda e: self._toggle_popup())

        self._label = ctk.CTkLabel(
            inner, text=i18n.role_label(role), font=theme.FONT_UI, anchor="w",
            text_color=theme.TEXT_PRIMARY,
        )
        self._label.pack(side="left", fill="x", expand=True)
        self._label.bind("<Button-1>", lambda e: self._toggle_popup())

        self._arrow = ctk.CTkLabel(inner, text="▾", font=theme.FONT_UI, text_color=theme.TEXT_MUTED, width=12)
        self._arrow.pack(side="right")
        self._arrow.bind("<Button-1>", lambda e: self._toggle_popup())

    def get_role(self) -> str:
        return self._role

    def set_role(self, role: str) -> None:
        self._role = role
        self._swatch.set_role(role)
        self._label.configure(text=i18n.role_label(role))

    def refresh_locale(self) -> None:
        self._label.configure(text=i18n.role_label(self._role))

    def _toggle_popup(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self) -> None:
        self._popup = ctk.CTkToplevel(self)
        self._popup.overrideredirect(True)
        self._popup.configure(fg_color=theme.BG_PANEL)
        self._popup.attributes("-topmost", True)

        self.update_idletasks()
        x = self._button.winfo_rootx()
        y = self._button.winfo_rooty() + self._button.winfo_height() + 2
        self._popup.geometry(f"{self._picker_width}x{min(320, 36 * len(LAYER_ROLES) + 8)}+{x}+{y}")

        list_frame = ctk.CTkScrollableFrame(self._popup, fg_color=theme.BG_PANEL, width=self._picker_width - 4)
        list_frame.pack(fill="both", expand=True, padx=2, pady=2)

        from kesit.ui.widgets.role_swatch import _bind_role_tooltip

        for role in LAYER_ROLES:
            row = ctk.CTkFrame(list_frame, fg_color="transparent", corner_radius=4)
            row.pack(fill="x", padx=2, pady=1)
            swatch = RoleSwatch(row, role=role, width=24, height=16)
            swatch.pack(side="left", padx=(4, 6), pady=2)

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True, pady=2)
            lbl = ctk.CTkLabel(
                text_col, text=i18n.role_label(role), font=theme.FONT_UI, anchor="w",
                text_color=theme.TEXT_PRIMARY,
            )
            lbl.pack(anchor="w")
            hint = ctk.CTkLabel(
                text_col, text=i18n.role_hint(role), font=theme.FONT_MONO, anchor="w",
                text_color=theme.TEXT_MUTED, wraplength=self._picker_width - 48, justify="left",
            )
            hint.pack(anchor="w")
            _bind_role_tooltip(row, role)

            hover_bg = theme.LAYER_ROW_HOVER

            def on_enter(_e, r=row) -> None:
                r.configure(fg_color=hover_bg)

            def on_leave(_e, r=row) -> None:
                r.configure(fg_color="transparent")

            def on_pick(_e, picked=role) -> None:
                self._select(picked)

            for widget in (row, swatch, text_col, lbl, hint):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_pick)
                widget.configure(cursor="hand2")

        # Close on a click anywhere outside the popup/button. Install the
        # handler deferred so the click that *opened* the popup doesn't
        # immediately close it. (Focus-based closing is unreliable for
        # overrideredirect toplevels on Linux and closed the popup instantly.)
        self.after(50, self._install_outside_close)

    def _install_outside_close(self) -> None:
        if not self._popup or not self._popup.winfo_exists():
            return
        root = self.winfo_toplevel()
        self._outside_bind_id = root.bind("<Button-1>", self._check_outside_click, add="+")

    def _check_outside_click(self, event) -> None:
        if not self._popup or not self._popup.winfo_exists():
            return
        widget_path = str(event.widget)
        popup_path = str(self._popup)
        button_path = str(self._button)
        for base in (popup_path, button_path):
            if widget_path == base or widget_path.startswith(base + "."):
                return
        self._close_popup()

    def _close_popup(self) -> None:
        if self._outside_bind_id is not None:
            try:
                self.winfo_toplevel().unbind("<Button-1>", self._outside_bind_id)
            except Exception:  # noqa: BLE001
                pass
            self._outside_bind_id = None
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None

    def _select(self, role: str) -> None:
        self.set_role(role)
        self._close_popup()
        if self._command:
            self._command(role)
