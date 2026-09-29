"""Core drawing engine: data model, transforms, events and rendering."""

import math
import tkinter as tk

from config import GRID_SIZE, MIN_ZOOM, MAX_ZOOM


def _pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


class CanvasManager:
    def __init__(self, app, canvas):
        self.app = app
        self.canvas = canvas
        self.objects = []
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.selected = None
        self.start = None
        self.temp_points = None
        self.moving = False
        self.moved = False
        self.move_last = None
        self.eraser_changed = False
        self.pan_start = None
        self.text_entry = None
        self.text_win = None
        self.text_world = None
        self._bind()

    def w2s(self, x, y):
        return x * self.scale + self.offset_x, y * self.scale + self.offset_y

    def s2w(self, x, y):
        return (x - self.offset_x) / self.scale, (y - self.offset_y) / self.scale

    def _bind(self):
        c = self.canvas
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<Motion>", self.on_hover)
        c.bind("<ButtonPress-2>", self.on_pan_start)
        c.bind("<B2-Motion>", self.on_pan_move)
        c.bind("<Control-MouseWheel>",
               lambda e: self.zoom_at(1.1 if e.delta > 0 else 0.9, e.x, e.y))
        c.bind("<Control-Button-4>", lambda e: self.zoom_at(1.1, e.x, e.y))
        c.bind("<Control-Button-5>", lambda e: self.zoom_at(0.9, e.x, e.y))
        c.bind("<MouseWheel>", lambda e: self.scroll(0, 40 if e.delta > 0 else -40))
        c.bind("<Button-4>", lambda e: self.scroll(0, 40))
        c.bind("<Button-5>", lambda e: self.scroll(0, -40))
        c.bind("<Shift-MouseWheel>", lambda e: self.scroll(40 if e.delta > 0 else -40, 0))
        c.bind("<Configure>", lambda e: self.redraw())

    def object_bounds(self, obj):
        t = obj["type"]
        if t == "pen":
            xs = [p[0] for p in obj["points"]]
            ys = [p[1] for p in obj["points"]]
            return min(xs), min(ys), max(xs), max(ys)
        if t in ("line", "rect", "oval", "arrow"):
            return (min(obj["x1"], obj["x2"]), min(obj["y1"], obj["y2"]),
                    max(obj["x1"], obj["x2"]), max(obj["y1"], obj["y2"]))
        if t == "text":
            fs = obj.get("font_size", 20)
            w = max(10, len(obj["text"]) * fs * 0.6)
            h = fs * 1.3
            return obj["x"], obj["y"], obj["x"] + w, obj["y"] + h
        return 0, 0, 0, 0

    def obj_hit(self, obj, wx, wy, tol):
        t = obj["type"]
        half = obj.get("width", 2) / 2
        if t == "pen":
            pts = obj["points"]
            for i in range(len(pts) - 1):
                if _pt_seg(wx, wy, pts[i][0], pts[i][1],
                           pts[i + 1][0], pts[i + 1][1]) <= tol + half:
                    return True
            return False
        if t in ("line", "arrow"):
            return _pt_seg(wx, wy, obj["x1"], obj["y1"],
                           obj["x2"], obj["y2"]) <= tol + half
        if t in ("rect", "oval", "text"):
            minx, miny, maxx, maxy = self.object_bounds(obj)
            return minx - tol <= wx <= maxx + tol and miny - tol <= wy <= maxy + tol
        return False

    def hit_test(self, sx, sy):
        wx, wy = self.s2w(sx, sy)
        tol = 8 / self.scale
        for i in range(len(self.objects) - 1, -1, -1):
            if self.obj_hit(self.objects[i], wx, wy, tol):
                return i
        return None

    def translate_object(self, obj, dx, dy):
        t = obj["type"]
        if t == "pen":
            obj["points"] = [(p[0] + dx, p[1] + dy) for p in obj["points"]]
        elif t in ("line", "rect", "oval", "arrow"):
            obj["x1"] += dx; obj["y1"] += dy
            obj["x2"] += dx; obj["y2"] += dy
        elif t == "text":
            obj["x"] += dx; obj["y"] += dy

    def on_press(self, e):
        self.commit_text_if_any()
        tool = self.app.tool
        wx, wy = self.s2w(e.x, e.y)
        if tool == "select":
            idx = self.hit_test(e.x, e.y)
            self.selected = idx
            if idx is not None:
                self.moving = True
                self.moved = False
                self.move_last = (wx, wy)
            self.redraw()
        elif tool == "text":
            self.start_text(e.x, e.y)
        elif tool == "eraser":
            self.eraser_changed = False
            self.erase_at(wx, wy)
        else:
            self.start = (wx, wy)
            if tool == "pen":
                self.temp_points = [(wx, wy)]

    def on_drag(self, e):
        tool = self.app.tool
        wx, wy = self.s2w(e.x, e.y)
        if tool == "select" and self.moving and self.selected is not None:
            dx = wx - self.move_last[0]
            dy = wy - self.move_last[1]
            self.translate_object(self.objects[self.selected], dx, dy)
            self.move_last = (wx, wy)
            self.moved = True
            self.redraw()
        elif tool == "eraser":
            self.erase_at(wx, wy)
        elif tool == "pen" and self.temp_points is not None:
            self.temp_points.append((wx, wy))
            x1, y1 = self.w2s(*self.temp_points[-2])
            x2, y2 = self.w2s(wx, wy)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.app.color,
                                    width=max(1, self.app.width * self.scale),
                                    capstyle="round", smooth=True, tags="temp")
        elif tool in ("line", "rect", "oval", "arrow") and self.start:
            self.draw_preview(tool, self.start, (wx, wy))

    def draw_preview(self, tool, p1, p2):
        self.canvas.delete("preview")
        x1, y1 = self.w2s(*p1)
        x2, y2 = self.w2s(*p2)
        col = self.app.color
        w = max(1, self.app.width * self.scale)
        if tool == "line":
            self.canvas.create_line(x1, y1, x2, y2, fill=col, width=w, tags="preview")
        elif tool == "arrow":
            self.canvas.create_line(x1, y1, x2, y2, fill=col, width=w,
                                    arrow="last", tags="preview")
        elif tool == "rect":
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=col, width=w,
                                         fill=self.app.fill or "", tags="preview")
        elif tool == "oval":
            self.canvas.create_oval(x1, y1, x2, y2, outline=col, width=w,
                                    fill=self.app.fill or "", tags="preview")

    def on_release(self, e):
        tool = self.app.tool
        wx, wy = self.s2w(e.x, e.y)
        if tool == "select":
            if self.moving and self.moved:
                self.app.push_history()
                self.app.mark_dirty()
            self.moving = False
        elif tool == "eraser":
            if self.eraser_changed:
                self.app.push_history()
                self.app.mark_dirty()
                self.eraser_changed = False
        elif tool == "pen" and self.temp_points is not None:
            if len(self.temp_points) >= 2:
                self.objects.append({"type": "pen", "points": self.temp_points,
                                     "color": self.app.color, "width": self.app.width})
                self.app.push_history()
                self.app.mark_dirty()
            self.temp_points = None
            self.redraw()
        elif tool in ("line", "rect", "oval", "arrow") and self.start:
            x1, y1 = self.start
            x2, y2 = wx, wy
            if abs(x2 - x1) > 2 or abs(y2 - y1) > 2:
                obj = {"type": tool, "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                       "color": self.app.color, "width": self.app.width}
                if tool in ("rect", "oval"):
                    obj["fill"] = self.app.fill or ""
                self.objects.append(obj)
                self.app.push_history()
                self.app.mark_dirty()
            self.start = None
            self.redraw()

    def on_hover(self, e):
        self.canvas.delete("ecursor")
        if self.app.tool == "eraser":
            r = self.app.eraser_size / 2
            t = self.app.theme_colors()
            self.canvas.create_oval(e.x - r, e.y - r, e.x + r, e.y + r,
                                    outline=t["accent"], dash=(3, 2), tags="ecursor")

    def on_pan_start(self, e):
        self.pan_start = (e.x, e.y, self.offset_x, self.offset_y)
        self.canvas.config(cursor="fleur")

    def on_pan_move(self, e):
        if not self.pan_start:
            return
        sx, sy, ox, oy = self.pan_start
        self.offset_x = ox + (e.x - sx)
        self.offset_y = oy + (e.y - sy)
        self.redraw()

    def scroll(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy
        self.redraw()

    def zoom_at(self, factor, cx, cy):
        new = max(MIN_ZOOM, min(MAX_ZOOM, self.scale * factor))
        if abs(new - self.scale) < 1e-6:
            return
        wx, wy = self.s2w(cx, cy)
        self.scale = new
        self.offset_x = cx - wx * self.scale
        self.offset_y = cy - wy * self.scale
        self.redraw()
        self.app.update_status()

    def zoom_buttons(self, factor):
        self.zoom_at(factor, self.canvas.winfo_width() / 2,
                     self.canvas.winfo_height() / 2)

    def reset_zoom(self):
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.redraw()
        self.app.update_status()

    def erase_at(self, wx, wy):
        radius = (self.app.eraser_size / 2) / self.scale
        removed = False
        for i in range(len(self.objects) - 1, -1, -1):
            if self.obj_hit(self.objects[i], wx, wy, radius):
                del self.objects[i]
                removed = True
        if removed:
            self.eraser_changed = True
            self.selected = None
            self.redraw()

    def start_text(self, sx, sy):
        self.commit_text_if_any()
        self.text_world = self.s2w(sx, sy)
        t = self.app.theme_colors()
        weight = "bold" if self.app.bold else "normal"
        e = tk.Entry(self.canvas, bd=1, relief="solid",
                     font=("Segoe UI", max(8, int(self.app.font_size * self.scale)), weight),
                     bg=t["canvas"], fg=self.app.color, insertbackground=self.app.color)
        self.text_entry = e
        self.text_win = self.canvas.create_window(sx, sy, window=e, anchor="nw")
        e.focus_set()
        e.bind("<Return>", lambda ev: self.commit_text())
        e.bind("<Escape>", lambda ev: self.cancel_text())

    def commit_text(self):
        if not self.text_entry:
            return
        txt = self.text_entry.get().strip()
        wx, wy = self.text_world
        self.canvas.delete(self.text_win)
        self.text_entry.destroy()
        self.text_entry = None
        if txt:
            self.objects.append({"type": "text", "x": wx, "y": wy, "text": txt,
                                 "color": self.app.color,
                                 "font_size": self.app.font_size, "bold": self.app.bold})
            self.app.push_history()
            self.app.mark_dirty()
        self.redraw()

    def cancel_text(self):
        if self.text_entry:
            self.canvas.delete(self.text_win)
            self.text_entry.destroy()
            self.text_entry = None

    def commit_text_if_any(self):
        if self.text_entry:
            self.commit_text()

    def draw_grid(self):
        if not self.app.show_grid:
            return
        t = self.app.theme_colors()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        step = GRID_SIZE * self.scale
        if step < 8:
            return
        x = self.offset_x % step
        while x < w:
            self.canvas.create_line(x, 0, x, h, fill=t["grid"], tags="grid")
            x += step
        y = self.offset_y % step
        while y < h:
            self.canvas.create_line(0, y, w, y, fill=t["grid"], tags="grid")
            y += step

    def draw_object(self, obj):
        t = obj["type"]
        color = obj.get("color", "#000000")
        w = max(1, obj.get("width", 2) * self.scale)
        ids = []
        if t == "pen":
            pts = []
            for p in obj["points"]:
                sx, sy = self.w2s(p[0], p[1])
                pts += [sx, sy]
            if len(pts) >= 4:
                ids.append(self.canvas.create_line(*pts, fill=color, width=w,
                           capstyle="round", joinstyle="round", smooth=True))
        elif t == "line":
            x1, y1 = self.w2s(obj["x1"], obj["y1"])
            x2, y2 = self.w2s(obj["x2"], obj["y2"])
            ids.append(self.canvas.create_line(x1, y1, x2, y2, fill=color,
                       width=w, capstyle="round"))
        elif t == "arrow":
            x1, y1 = self.w2s(obj["x1"], obj["y1"])
            x2, y2 = self.w2s(obj["x2"], obj["y2"])
            ash = tuple(max(4, int(v * self.scale)) for v in (16, 20, 6))
            ids.append(self.canvas.create_line(x1, y1, x2, y2, fill=color, width=w,
                       arrow="last", arrowshape=ash, capstyle="round"))
        elif t == "rect":
            x1, y1 = self.w2s(obj["x1"], obj["y1"])
            x2, y2 = self.w2s(obj["x2"], obj["y2"])
            ids.append(self.canvas.create_rectangle(x1, y1, x2, y2, outline=color,
                       width=w, fill=obj.get("fill") or ""))
        elif t == "oval":
            x1, y1 = self.w2s(obj["x1"], obj["y1"])
            x2, y2 = self.w2s(obj["x2"], obj["y2"])
            ids.append(self.canvas.create_oval(x1, y1, x2, y2, outline=color,
                       width=w, fill=obj.get("fill") or ""))
        elif t == "text":
            x, y = self.w2s(obj["x"], obj["y"])
            size = max(1, int(obj.get("font_size", 20) * self.scale))
            weight = "bold" if obj.get("bold") else "normal"
            ids.append(self.canvas.create_text(x, y, text=obj["text"], fill=color,
                       anchor="nw", font=("Segoe UI", size, weight)))
        return ids

    def redraw(self):
        c = self.canvas
        c.delete("all")
        self.draw_grid()
        sel_ids = None
        for i, obj in enumerate(self.objects):
            ids = self.draw_object(obj)
            if i == self.selected:
                sel_ids = ids
        if (self.selected is not None and 0 <= self.selected < len(self.objects)
                and sel_ids):
            bbox = c.bbox(*sel_ids)
            if bbox:
                t = self.app.theme_colors()
                pad = 4
                x1, y1, x2, y2 = bbox
                c.create_rectangle(x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                                   outline=t["accent"], dash=(4, 3), width=1)
                for hx, hy in ((x1 - pad, y1 - pad), (x2 + pad, y1 - pad),
                               (x1 - pad, y2 + pad), (x2 + pad, y2 + pad)):
                    c.create_rectangle(hx - 3, hy - 3, hx + 3, hy + 3,
                                       outline=t["accent"], fill=t["accent"])
        self.app.update_status()

    def delete_selected(self):
        if self.selected is not None and 0 <= self.selected < len(self.objects):
            del self.objects[self.selected]
            self.selected = None
            self.app.push_history()
            self.app.mark_dirty()
            self.redraw()
