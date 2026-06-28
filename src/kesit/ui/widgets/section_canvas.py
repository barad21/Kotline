"""Section preview canvas."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from kesit.models import SectionShape
from kesit.rendering.coords import fit_bounds, screen_to_world, world_to_screen
from kesit.rendering.depth_colors import gradient_at
from kesit.rendering.section_renderer import (
    draw_scale_bar,
    draw_section_chrome,
    draw_section_shapes,
    section_bounds,
)
from kesit.ui import i18n, theme

# Horizontal room reserved on the right edge for level-name labels.
_LABEL_MARGIN_PX = 120


class SectionCanvas(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG_CANVAS, **kwargs)
        self.depth_gradient = False
        self.section_depth_mm = 5000.0

        header = ctk.CTkFrame(self, fg_color=theme.BG_CANVAS)
        header.pack(fill="x", padx=8, pady=(4, 0))
        self._header_label = ctk.CTkLabel(
            header, text=i18n.t("section.preview"), font=theme.FONT_UI_BOLD, text_color=theme.TEXT_PRIMARY,
        )
        self._header_label.pack(side="left")

        toolbar = ctk.CTkFrame(self, fg_color=theme.BG_PANEL, height=36)
        toolbar.pack(fill="x", padx=4, pady=4)

        self.depth_switch = ctk.CTkSwitch(
            toolbar,
            text=i18n.t("section.depth_gradient"),
            command=self._on_depth_toggle,
            font=theme.FONT_UI,
        )
        self.depth_switch.pack(side="left", padx=8, pady=6)

        self._btn_fit = ctk.CTkButton(
            toolbar, text=i18n.t("plan.tool.fit"), width=50, command=self.fit_view,
        )
        self._btn_fit.pack(side="left", padx=4, pady=4)

        legend = ctk.CTkFrame(toolbar, fg_color=theme.BG_PANEL)
        legend.pack(side="right", padx=8, pady=4)
        self._near_label = ctk.CTkLabel(
            legend, text=i18n.t("section.near_red"), font=theme.FONT_MONO, text_color=theme.TEXT_MUTED,
        )
        self._near_label.pack(side="left", padx=(0, 4))
        self.legend_canvas = tk.Canvas(
            legend, width=80, height=12, bg=theme.BG_PANEL, highlightthickness=0,
        )
        self.legend_canvas.pack(side="left", padx=2)
        self._far_label = ctk.CTkLabel(
            legend, text=i18n.t("section.far_blue"), font=theme.FONT_MONO, text_color=theme.TEXT_MUTED,
        )
        self._far_label.pack(side="left", padx=(4, 0))
        self._draw_legend()

        self.canvas = tk.Canvas(self, bg=theme.BG_CANVAS, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)
        self.shapes: list[SectionShape] = []
        self._levels: list[tuple[str, float]] = []
        self._output_scale = "1:50"
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._z_min = 0.0
        self._z_max = 3000.0
        self._needs_fit = True
        self._pan_start: tuple[float, float] | None = None
        self._message_key = "section.generate_to_preview"
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom(1.1, e.x, e.y))
        self.canvas.bind("<Button-5>", lambda e: self._zoom(0.9, e.x, e.y))

    def refresh_locale(self) -> None:
        self._header_label.configure(text=i18n.t("section.preview"))
        self.depth_switch.configure(text=i18n.t("section.depth_gradient"))
        self._btn_fit.configure(text=i18n.t("plan.tool.fit"))
        self._near_label.configure(text=i18n.t("section.near_red"))
        self._far_label.configure(text=i18n.t("section.far_blue"))
        if self._message_key:
            self.redraw()

    def _draw_legend(self) -> None:
        self.legend_canvas.delete("all")
        steps = 20
        w = 80
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = gradient_at(t)
            x0 = int(i * w / steps)
            x1 = int((i + 1) * w / steps)
            self.legend_canvas.create_rectangle(x0, 0, x1, 12, fill=color, outline=color)

    def set_depth_gradient(self, enabled: bool) -> None:
        self.depth_gradient = enabled
        if enabled:
            self.depth_switch.select()
        else:
            self.depth_switch.deselect()
        self.redraw()

    def _on_depth_toggle(self) -> None:
        self.depth_gradient = bool(self.depth_switch.get())
        self.redraw()

    def show_shapes(
        self,
        shapes: list[SectionShape],
        section_depth_mm: float = 5000.0,
        levels: list[tuple[str, float]] | None = None,
        output_scale: str = "1:50",
    ) -> None:
        self.shapes = shapes
        self.section_depth_mm = section_depth_mm
        self._levels = levels or []
        self._output_scale = output_scale
        self._message_key = None
        self._needs_fit = True
        self.redraw()

    def clear_preview(self, message_key: str | None = None) -> None:
        self.shapes = []
        self._message_key = message_key or "section.changed_regenerate"
        self.redraw()

    def _content_bounds(self) -> tuple[float, float, float, float]:
        """Section bounds, always including the ground datum (z = 0)."""
        minx, miny, maxx, maxy = section_bounds(self.shapes)
        miny = min(miny, 0.0)
        return minx, miny, maxx, maxy

    def fit_view(self) -> None:
        if not self.shapes:
            return
        w = max(self.canvas.winfo_width(), 200)
        h = max(self.canvas.winfo_height(), 200)
        minx, miny, maxx, maxy = self._content_bounds()
        self._z_min = miny
        self._z_max = maxy
        # Reserve space on the right for the level-name labels so the whole
        # section stays visible instead of being pushed off the canvas.
        content_w = max(w - _LABEL_MARGIN_PX, 200)
        self._scale, self._offset_x, self._offset_y = fit_bounds(minx, miny, maxx, maxy, content_w, h)
        self._needs_fit = False
        self.redraw()

    def _on_resize(self, event) -> None:
        # Always refit on resize so the preview adapts to window changes.
        if self.shapes:
            self.fit_view()
        else:
            self.redraw()

    def _on_press(self, event) -> None:
        self._pan_start = (event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def _on_drag(self, event) -> None:
        if self._pan_start is None:
            return
        dx = event.x - self._pan_start[0]
        dy = event.y - self._pan_start[1]
        self._offset_x += dx
        self._offset_y += dy
        self._pan_start = (event.x, event.y)
        self.redraw()

    def _on_release(self, event) -> None:
        self._pan_start = None
        self.canvas.configure(cursor="")

    def _on_wheel(self, event) -> None:
        factor = 1.1 if event.delta > 0 else 0.9
        self._zoom(factor, event.x, event.y)

    def _zoom(self, factor: float, sx: float, sy: float) -> None:
        if not self.shapes:
            return
        wx, wy = screen_to_world(sx, sy, self._scale, self._offset_x, self._offset_y)
        self._scale *= factor
        new_sx, new_sy = world_to_screen(wx, wy, self._scale, self._offset_x, self._offset_y)
        self._offset_x += sx - new_sx
        self._offset_y += sy - new_sy
        self.redraw()

    def redraw(self) -> None:
        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 200)
        h = max(self.canvas.winfo_height(), 200)
        if not self.shapes:
            message = i18n.t(self._message_key) if self._message_key else ""
            self.canvas.create_text(
                w / 2, h / 2, text=message,
                fill=theme.TEXT_MUTED, font=theme.FONT_UI,
            )
            return
        if self._needs_fit:
            self.fit_view()
            return
        minx, _, maxx, _ = self._content_bounds()
        draw_section_chrome(
            self.canvas,
            self._scale,
            self._offset_x,
            self._offset_y,
            h,
            self._z_min,
            self._z_max,
            minx,
            maxx,
            self._levels,
            i18n.t("section.ground"),
        )
        draw_section_shapes(
            self.canvas,
            self.shapes,
            self._scale,
            self._offset_x,
            self._offset_y,
            h,
            self._z_min,
            self._z_max,
            depth_gradient=self.depth_gradient,
            section_depth_mm=self.section_depth_mm,
        )
        draw_scale_bar(
            self.canvas,
            self._scale,
            w,
            h,
            i18n.t("section.scale_label", scale=self._output_scale),
        )
