"""Plan view canvas with pan/zoom and section line tools."""

from __future__ import annotations

import math
import tkinter as tk
from typing import Callable

import customtkinter as ctk

from kesit.app.project_state import ProjectState
from kesit.cad_io.dxf_reader import DxfInventory
from kesit.geometry.section_line import SectionLine
from kesit.rendering.coords import fit_bounds, screen_to_world, world_to_screen
from kesit.rendering.plan_renderer import collect_plan_bounds, draw_inventory
from kesit.ui import i18n, theme
from kesit.units import Unit, UnitContext, convert_length

_MIN_SECTION_LENGTH_PLAN = 1.0


class PlanCanvas(ctk.CTkFrame):
    def __init__(self, master, on_section_changed: Callable[[], None] | None = None, **kwargs):
        super().__init__(master, fg_color=theme.BG_CANVAS, **kwargs)
        self.on_section_changed = on_section_changed
        self.inventory: DxfInventory | None = None
        self.project: ProjectState | None = None
        self.tool = "pan"
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._pan_start: tuple[float, float] | None = None
        self._section_drag_start: tuple[float, float] | None = None
        self._section_drag_current: tuple[float, float] | None = None
        self._world_bounds = (0, 0, 100, 100)
        self._needs_fit = True
        self._highlight_layer: str | None = None

        toolbar = ctk.CTkFrame(self, fg_color=theme.BG_PANEL, height=36)
        toolbar.pack(fill="x", padx=4, pady=4)
        self._btn_move = ctk.CTkButton(
            toolbar, text=i18n.t("plan.tool.move"), width=60, command=lambda: self.set_tool("pan"),
        )
        self._btn_move.pack(side="left", padx=2)
        self._btn_section = ctk.CTkButton(
            toolbar, text=i18n.t("plan.tool.section"), width=100, command=lambda: self.set_tool("section"),
        )
        self._btn_section.pack(side="left", padx=2)
        self._btn_view = ctk.CTkButton(
            toolbar, text=i18n.t("plan.tool.view"), width=90, command=lambda: self.set_tool("view"),
        )
        self._btn_view.pack(side="left", padx=2)
        self._btn_fit = ctk.CTkButton(
            toolbar, text=i18n.t("plan.tool.fit"), width=50, command=self.fit_view,
        )
        self._btn_fit.pack(side="left", padx=2)
        self.status_label = ctk.CTkLabel(
            toolbar, text=i18n.t("plan.load_dxf"), text_color=theme.TEXT_MUTED,
        )
        self.status_label.pack(side="left", padx=8)

        self.canvas = tk.Canvas(self, bg=theme.BG_CANVAS, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom(1.1, e.x, e.y))
        self.canvas.bind("<Button-5>", lambda e: self._zoom(0.9, e.x, e.y))

    def refresh_locale(self) -> None:
        self._btn_move.configure(text=i18n.t("plan.tool.move"))
        self._btn_section.configure(text=i18n.t("plan.tool.section"))
        self._btn_view.configure(text=i18n.t("plan.tool.view"))
        self._btn_fit.configure(text=i18n.t("plan.tool.fit"))
        if not self.inventory:
            self.status_label.configure(text=i18n.t("plan.load_dxf"))
        else:
            self.set_tool(self.tool)

    def _unit_context(self) -> UnitContext | None:
        if not self.project:
            return None
        return UnitContext.from_config(self.project.units, self.project.dxf_insunits)

    def _internal_to_plan(self, x: float, y: float) -> tuple[float, float]:
        ctx = self._unit_context()
        if ctx is None:
            return x, y
        return convert_length(x, Unit.MM, ctx.source), convert_length(y, Unit.MM, ctx.source)

    def _plan_to_internal(self, x: float, y: float) -> tuple[float, float]:
        ctx = self._unit_context()
        if ctx is None:
            return x, y
        return ctx.plan_to_internal(x), ctx.plan_to_internal(y)

    def set_tool(self, tool: str) -> None:
        self.tool = tool
        self._section_drag_start = None
        self._section_drag_current = None
        hints = {
            "pan": i18n.t("plan.hint.pan"),
            "section": i18n.t("plan.hint.section"),
            "view": i18n.t("plan.hint.view"),
        }
        self.status_label.configure(text=hints.get(tool, tool))
        self.canvas.configure(cursor="fleur" if tool == "pan" else "crosshair")

    @staticmethod
    def _angle_from_p0_deg(p0: tuple[float, float], p1: tuple[float, float]) -> float:
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        return math.degrees(math.atan2(dy, dx)) % 360.0

    def _event_to_plan(self, event) -> tuple[float, float]:
        h = self.canvas.winfo_height()
        wx, wy = screen_to_world(
            event.x, event.y, self._scale, self._offset_x, self._offset_y,
            flip_y=True, canvas_height=h,
        )
        return self._internal_to_plan(wx, wy)

    def set_highlight_layer(self, layer: str | None) -> None:
        if self._highlight_layer == layer:
            return
        self._highlight_layer = layer
        self.redraw()

    def load_inventory(self, inventory: DxfInventory, project: ProjectState) -> None:
        self.inventory = inventory
        self.project = project
        self._world_bounds = collect_plan_bounds(inventory)
        self._needs_fit = True
        self.fit_view()
        self.redraw()

    def fit_view(self) -> None:
        w = max(self.canvas.winfo_width(), 400)
        h = max(self.canvas.winfo_height(), 300)
        minx, miny, maxx, maxy = self._world_bounds
        self._scale, self._offset_x, self._offset_y = fit_bounds(minx, miny, maxx, maxy, w, h)
        self._needs_fit = False

    def redraw(self) -> None:
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 2 or h < 2:
            return
        if self.inventory:
            draw_inventory(
                self.canvas,
                self.inventory,
                self._scale,
                self._offset_x,
                self._offset_y,
                h,
                highlight_layer=self._highlight_layer,
            )
        self._draw_section_overlay(h)

    def _draw_section_overlay(self, canvas_height: int) -> None:
        if not self.project or not self.project.section:
            return
        sec = self.project.section

        def pt_plan(p):
            if p is None:
                return None
            ix, iy = self._plan_to_internal(p[0], p[1])
            return world_to_screen(
                ix, iy, self._scale, self._offset_x, self._offset_y,
                flip_y=True, canvas_height=canvas_height,
            )

        if sec.p0 and sec.p1:
            a = pt_plan(sec.p0)
            b = pt_plan(sec.p1)
            if a and b:
                self.canvas.create_line(*a, *b, fill=theme.ACCENT, width=2, tags="overlay")
                if sec.view_point:
                    self._draw_view_arrow(sec, pt_plan, canvas_height)
        if sec.view_point:
            v = pt_plan(sec.view_point)
            if v:
                self.canvas.create_oval(
                    v[0] - 6, v[1] - 6, v[0] + 6, v[1] + 6,
                    fill=theme.SUCCESS, outline=theme.LINE_CUT, width=2, tags="overlay",
                )
        self._draw_section_drag_preview(pt_plan, canvas_height)

    def _draw_section_drag_preview(self, pt_plan, canvas_height: int) -> None:
        if not self._section_drag_start or not self._section_drag_current:
            return
        a = pt_plan(self._section_drag_start)
        b = pt_plan(self._section_drag_current)
        if not a or not b:
            return
        self.canvas.create_line(
            *a, *b, fill=theme.WARNING, width=2, dash=(6, 4), tags="overlay",
        )
        self.canvas.create_oval(
            a[0] - 5, a[1] - 5, a[0] + 5, a[1] + 5,
            fill=theme.WARNING, outline=theme.LINE_CUT, width=2, tags="overlay",
        )
        angle = self._angle_from_p0_deg(self._section_drag_start, self._section_drag_current)
        mid_x = (a[0] + b[0]) / 2
        mid_y = (a[1] + b[1]) / 2
        self.canvas.create_text(
            mid_x, mid_y - 14,
            text=f"{angle:.1f}°",
            fill=theme.WARNING,
            font=theme.FONT_UI_BOLD,
            tags="overlay",
        )

    def _draw_view_arrow(self, sec, pt_plan, canvas_height: int) -> None:
        try:
            ix0, iy0 = self._plan_to_internal(sec.p0[0], sec.p0[1])
            ix1, iy1 = self._plan_to_internal(sec.p1[0], sec.p1[1])
            ivx, ivy = self._plan_to_internal(sec.view_point[0], sec.view_point[1])
            section = SectionLine.from_tuples((ix0, iy0), (ix1, iy1), (ivx, ivy))
        except ValueError:
            return

        mid_x = (ix0 + ix1) / 2
        mid_y = (iy0 + iy1) / 2
        v = section.direction_v()
        arrow_len = 80.0
        tip_x = mid_x + v.x * arrow_len
        tip_y = mid_y + v.y * arrow_len
        tail_x = mid_x + v.x * 20.0
        tail_y = mid_y + v.y * 20.0

        tail = world_to_screen(
            tail_x, tail_y, self._scale, self._offset_x, self._offset_y,
            flip_y=True, canvas_height=canvas_height,
        )
        tip = world_to_screen(
            tip_x, tip_y, self._scale, self._offset_x, self._offset_y,
            flip_y=True, canvas_height=canvas_height,
        )
        self.canvas.create_line(
            *tail, *tip, fill=theme.SUCCESS, width=2, arrow=tk.LAST, tags="overlay",
        )

    def _on_resize(self, event) -> None:
        if self._needs_fit and self.inventory:
            self.fit_view()
            self.redraw()

    def _on_press(self, event) -> None:
        if self.tool == "pan":
            self._pan_start = (event.x, event.y)
            self.canvas.configure(cursor="fleur")
        elif self.tool == "section" and self.project:
            self._section_drag_start = self._event_to_plan(event)
            self._section_drag_current = self._section_drag_start
            self.redraw()

    def _on_drag(self, event) -> None:
        if self.tool == "pan" and self._pan_start:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self._offset_x += dx
            self._offset_y -= dy
            self._pan_start = (event.x, event.y)
            self.redraw()
        elif self.tool == "section" and self._section_drag_start is not None:
            self._section_drag_current = self._event_to_plan(event)
            angle = self._angle_from_p0_deg(self._section_drag_start, self._section_drag_current)
            p0 = self._section_drag_start
            self.status_label.configure(
                text=i18n.t("plan.section_angle", angle=f"{angle:.1f}", x=f"{p0[0]:.1f}", y=f"{p0[1]:.1f}"),
            )
            self.redraw()

    def _on_release(self, event) -> None:
        if self.tool == "pan":
            self._pan_start = None
            return
        if not self.project:
            return

        if self.tool == "section":
            if self._section_drag_start is None:
                return
            p1 = self._event_to_plan(event)
            p0 = self._section_drag_start
            self._section_drag_start = None
            self._section_drag_current = None
            dx = p1[0] - p0[0]
            dy = p1[1] - p0[1]
            length = math.hypot(dx, dy)
            if length < _MIN_SECTION_LENGTH_PLAN:
                self.status_label.configure(text=i18n.t("plan.section_too_short"))
                self.redraw()
                return
            angle = self._angle_from_p0_deg(p0, p1)
            self.project.section.p0 = p0
            self.project.section.p1 = p1
            self.status_label.configure(
                text=i18n.t("plan.section_set", angle=f"{angle:.1f}"),
            )
            if self.on_section_changed:
                self.on_section_changed()
            self.redraw()
            return

        h = self.canvas.winfo_height()
        wx, wy = screen_to_world(
            event.x, event.y, self._scale, self._offset_x, self._offset_y,
            flip_y=True, canvas_height=h,
        )
        px, py = self._internal_to_plan(wx, wy)

        if self.tool == "view":
            self.project.section.view_point = (px, py)
            self.status_label.configure(
                text=i18n.t("plan.view_point", x=f"{px:.1f}", y=f"{py:.1f}"),
            )
            if self.on_section_changed:
                self.on_section_changed()
            self.redraw()

    def _on_wheel(self, event) -> None:
        factor = 1.1 if event.delta > 0 else 0.9
        self._zoom(factor, event.x, event.y)

    def _zoom(self, factor: float, sx: float, sy: float) -> None:
        h = self.canvas.winfo_height()
        wx, wy = screen_to_world(sx, sy, self._scale, self._offset_x, self._offset_y, flip_y=True, canvas_height=h)
        self._scale *= factor
        new_sx, new_sy = world_to_screen(wx, wy, self._scale, self._offset_x, self._offset_y, flip_y=True, canvas_height=h)
        self._offset_x += sx - new_sx
        self._offset_y += sy - new_sy
        self.redraw()
