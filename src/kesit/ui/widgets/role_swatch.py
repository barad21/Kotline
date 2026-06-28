"""Mini preview swatches for layer roles (section preview appearance)."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from kesit.app.project_state import LAYER_ROLES
from kesit.ui import i18n, theme


def _y_band(y0: float, y1: float, top_frac: float, bottom_frac: float) -> tuple[float, float]:
    """Map normalized height fractions (0=top, 1=floor) to canvas y coordinates."""
    h = y1 - y0
    return y0 + h * top_frac, y0 + h * bottom_frac


def _draw_hatch(canvas: tk.Canvas, x0: float, y0: float, x1: float, y1: float, color: str) -> None:
    step = max(3, int((x1 - x0) / 5))
    for i in range(int(x0), int(x1), step):
        canvas.create_line(i, y1, i + (y1 - y0) * 0.6, y0, fill=color, width=1)


def _draw_wall_outline(canvas: tk.Canvas, x0: float, y0: float, x1: float, y1: float) -> None:
    canvas.create_rectangle(x0, y0, x1, y1, outline=theme.LINE_PLAN, width=1)


def _draw_opening_band(
    canvas: tk.Canvas,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    top_frac: float,
    bottom_frac: float,
    *,
    dashed: bool = True,
    color: str | None = None,
) -> None:
    by0, by1 = _y_band(y0, y1, top_frac, bottom_frac)
    inset = max(2, (x1 - x0) * 0.15)
    stroke = color or theme.LINE_CUT
    dash = (3, 2) if dashed else ()
    canvas.create_rectangle(
        x0 + inset, by0, x1 - inset, by1,
        outline=stroke, width=1, dash=dash,
    )


def draw_role_swatch(canvas: tk.Canvas, role: str, width: int = 28, height: int = 18) -> None:
    """Draw a miniature section-elevation symbol for each architectural role."""
    canvas.delete("all")
    canvas.configure(width=width, height=height, bg=theme.BG_PANEL, highlightthickness=0)
    pad = max(1, width // 14)
    x0, y0 = pad, pad
    x1, y1 = width - pad, height - pad

    if role == "walls":
        # Cut wall: poché fill + diagonal hatch (standard section convention).
        canvas.create_rectangle(x0, y0, x1, y1, fill=theme.CUT_FILL, outline=theme.LINE_CUT, width=1)
        _draw_hatch(canvas, x0, y0, x1, y1, theme.GRID)
        floor_y = y1 - 1
        canvas.create_line(x0, floor_y, x1, floor_y, fill=theme.LINE_CUT, width=1)

    elif role == "doors":
        # Door opening: dashed void in lower portion of wall height.
        _draw_wall_outline(canvas, x0, y0, x1, y1)
        _draw_opening_band(canvas, x0, y0, x1, y1, 0.38, 1.0, dashed=True)

    elif role == "windows":
        # Window: dashed opening band at sill–head height; distinct from door position.
        _draw_wall_outline(canvas, x0, y0, x1, y1)
        _draw_opening_band(canvas, x0, y0, x1, y1, 0.22, 0.62, dashed=True)
        # Faint projection edge (solid gray) on one side — beyond-cut appearance.
        by0, by1 = _y_band(y0, y1, 0.22, 0.62)
        canvas.create_line(x1 - 3, by0, x1 - 3, by1, fill=theme.LINE_PROJ, width=1)

    elif role == "openings":
        # Generic opening: full-height dashed void (non-standard height).
        _draw_wall_outline(canvas, x0, y0, x1, y1)
        _draw_opening_band(canvas, x0, y0, x1, y1, 0.15, 0.85, dashed=True)

    elif role == "slab":
        # Floor slab / baseline at grade.
        floor = y1 - 2
        canvas.create_line(x0, floor, x1, floor, fill=theme.LINE_CUT, width=2)
        canvas.create_line(x0, floor - 2, x1, floor - 2, fill=theme.LINE_PROJ, width=1)

    elif role == "columns":
        # Column cut: solid poché profile (rules exist; pipeline wiring pending).
        cx = (x0 + x1) / 2
        half = max(2, (x1 - x0) * 0.22)
        canvas.create_rectangle(
            cx - half, y0 + 1, cx + half, y1 - 1,
            fill=theme.CUT_FILL, outline=theme.LINE_CUT, width=1,
        )
        _draw_hatch(canvas, cx - half, y0 + 1, cx + half, y1 - 1, theme.GRID)

    elif role in ("structure", "fixtures", "footprint"):
        # Assigned in UI but not emitted in section preview yet.
        canvas.create_rectangle(
            x0 + 1, y0 + 1, x1 - 1, y1 - 1,
            outline=theme.LINE_PROJ, width=1, dash=(2, 2),
        )
        canvas.create_line(x0 + 2, y1 - 2, x1 - 2, y0 + 2, fill=theme.TEXT_MUTED, width=1)
        canvas.create_text(
            (x0 + x1) / 2, (y0 + y1) / 2, text="—",
            fill=theme.TEXT_MUTED, font=("DejaVu Sans", max(6, height - 6)),
        )

    else:
        # annotations / skip — excluded from section output.
        canvas.create_line(x0 + 2, y0 + 2, x1 - 2, y1 - 2, fill=theme.TEXT_MUTED, width=1)
        canvas.create_line(x1 - 2, y0 + 2, x0 + 2, y1 - 2, fill=theme.TEXT_MUTED, width=1)


class RoleSwatch(ctk.CTkFrame):
    def __init__(self, master, role: str = "skip", width: int = 28, height: int = 18, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._role = role
        self.canvas = tk.Canvas(
            self, width=width, height=height, bg=theme.BG_PANEL, highlightthickness=0,
        )
        self.canvas.pack()
        self.set_role(role)

    def set_role(self, role: str) -> None:
        self._role = role
        w = int(self.canvas.cget("width"))
        h = int(self.canvas.cget("height"))
        draw_role_swatch(self.canvas, role, width=w, height=h)


def _bind_role_tooltip(widget, role: str) -> None:
    state: dict[str, ctk.CTkToplevel | None] = {"tip": None}

    def on_enter(_event) -> None:
        if state["tip"] is not None:
            return
        tip = ctk.CTkToplevel(widget)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(fg_color=theme.BG_CANVAS)
        ctk.CTkLabel(
            tip,
            text=i18n.role_hint(role),
            font=theme.FONT_MONO,
            text_color=theme.TEXT_PRIMARY,
            fg_color=theme.BG_CANVAS,
            wraplength=280,
            justify="left",
        ).pack(padx=8, pady=6)
        widget.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        tip.geometry(f"+{x}+{y}")
        state["tip"] = tip

    def on_leave(_event) -> None:
        if state["tip"] is not None:
            state["tip"].destroy()
            state["tip"] = None

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


class RoleLegendStrip(ctk.CTkFrame):
    """Single horizontal row of role swatches + short labels."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG_PANEL, **kwargs)
        self._items: list[tuple[RoleSwatch, ctk.CTkLabel, ctk.CTkFrame]] = []

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._items.clear()

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=2)

        for role in LAYER_ROLES:
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.pack(side="left", padx=(0, 8))
            swatch = RoleSwatch(cell, role=role, width=24, height=16)
            swatch.pack(side="left", padx=(0, 4))
            label = ctk.CTkLabel(
                cell, text=i18n.role_label(role), font=theme.FONT_MONO,
                text_color=theme.TEXT_MUTED,
            )
            label.pack(side="left")
            _bind_role_tooltip(cell, role)
            _bind_role_tooltip(swatch, role)
            _bind_role_tooltip(label, role)
            self._items.append((swatch, label, cell))

    def refresh_locale(self) -> None:
        for _swatch, label, _cell in self._items:
            role = _swatch._role
            label.configure(text=i18n.role_label(role))


RoleLegend = RoleLegendStrip
