"""
Screen Pen - Epic-Pen-style overlay that lets you draw on top of the
whole desktop. A fullscreen transparent, always-on-top window captures
your ink, with a small floating control panel.
"""

import sys
import tkinter as tk

_TRANSPARENT_KEY = "#fe01fe"

PEN_COLORS = ["#ff2d2d", "#ffd400", "#00c853", "#2979ff",
              "#ffffff", "#000000", "#ff9100", "#d500f9"]
PEN_WIDTHS = [2, 3, 5, 8, 12]


class ScreenPen:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.overlay = None
        self.canvas = None
        self.panel = None
        self.color = "#ff2d2d"
        self.width = 5
        self.mode = "pen"
        self.strokes = []
        self.cur_points = None
        self.cur_ids = None
        self._transparent = False

    def toggle(self):
        if self.overlay:
            self.close()
        else:
            self.open()

    def open(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-topmost", True)
        try:
            self.overlay.attributes("-fullscreen", True)
        except tk.TclError:
            sw = self.overlay.winfo_screenwidth()
            sh = self.overlay.winfo_screenheight()
            self.overlay.geometry(f"{sw}x{sh}+0+0")
        self.overlay.overrideredirect(True)

        self._transparent = False
        bg = "#101014"
        if sys.platform.startswith("win"):
            try:
                self.overlay.config(bg=_TRANSPARENT_KEY)
                self.overlay.attributes("-transparentcolor", _TRANSPARENT_KEY)
                bg = _TRANSPARENT_KEY
                self._transparent = True
            except tk.TclError:
                self._transparent = False
        if not self._transparent:
            try:
                self.overlay.attributes("-alpha", 0.30)
            except tk.TclError:
                pass

        self.canvas = tk.Canvas(self.overlay, bg=bg, highlightthickness=0, bd=0,
                                cursor="pencil")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.overlay.bind("<Escape>", lambda e: self.close())

        self.strokes = []
        self._build_panel()

    def close(self):
        if self.panel:
            self.panel.destroy()
            self.panel = None
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        self.canvas = None

    def _press(self, e):
        if self.mode == "eraser":
            self._erase_at(e.x, e.y)
            return
        self.cur_points = [(e.x, e.y)]
        self.cur_ids = []

    def _drag(self, e):
        if self.mode == "eraser":
            self._erase_at(e.x, e.y)
            return
        if self.cur_points is None:
            return
        x0, y0 = self.cur_points[-1]
        line = self.canvas.create_line(x0, y0, e.x, e.y, fill=self.color,
                                       width=self.width, capstyle="round",
                                       joinstyle="round", smooth=True)
        self.cur_points.append((e.x, e.y))
        self.cur_ids.append(line)

    def _release(self, e):
        if self.mode == "eraser":
            return
        if self.cur_ids:
            self.strokes.append({"ids": self.cur_ids, "points": self.cur_points})
        self.cur_points = None
        self.cur_ids = None

    def _erase_at(self, x, y):
        r = 18
        for i in range(len(self.strokes) - 1, -1, -1):
            for (px, py) in self.strokes[i]["points"]:
                if abs(px - x) <= r and abs(py - y) <= r:
                    for cid in self.strokes[i]["ids"]:
                        self.canvas.delete(cid)
                    del self.strokes[i]
                    break

    def undo(self):
        if self.strokes:
            stroke = self.strokes.pop()
            for cid in stroke["ids"]:
                self.canvas.delete(cid)

    def clear(self):
        self.canvas.delete("all")
        self.strokes = []

    def _build_panel(self):
        self.panel = tk.Toplevel(self.root)
        self.panel.attributes("-topmost", True)
        self.panel.overrideredirect(True)
        sw = self.panel.winfo_screenwidth()
        self.panel.geometry(f"+{sw // 2 - 240}+18")

        wrap = tk.Frame(self.panel, bg="#26262a", bd=0,
                        highlightbackground="#3a3a40", highlightthickness=1)
        wrap.pack()

        title = tk.Label(wrap, text="\u2712 Screen Pen", bg="#26262a", fg="#a29bfe",
                         font=("Segoe UI Semibold", 10), padx=8)
        title.grid(row=0, column=0, rowspan=2, padx=(8, 6), pady=6)
        self._make_draggable(title)

        cframe = tk.Frame(wrap, bg="#26262a")
        cframe.grid(row=0, column=1, columnspan=8, padx=4, pady=(6, 0), sticky="w")
        self._swatches = {}
        for i, col in enumerate(PEN_COLORS):
            b = tk.Button(cframe, bg=col, activebackground=col, width=2, height=1,
                          relief="flat", bd=2, cursor="hand2",
                          command=lambda c=col: self._set_color(c))
            b.grid(row=0, column=i, padx=2)
            self._swatches[col] = b
        self._highlight_color()

        self.width_var = tk.StringVar(value=str(self.width))
        wmenu = tk.OptionMenu(wrap, self.width_var, *[str(w) for w in PEN_WIDTHS],
                              command=lambda v: setattr(self, "width", int(v)))
        wmenu.config(bg="#2f2f35", fg="#e9e9ec", relief="flat", bd=0,
                     highlightthickness=0, activebackground="#3d3d45", width=3)
        wmenu.grid(row=1, column=1, padx=4, pady=(2, 6), sticky="w")

        def tool_btn(text, cmd, col):
            b = tk.Button(wrap, text=text, command=cmd, bg="#2f2f35", fg="#e9e9ec",
                          relief="flat", bd=0, highlightthickness=0, cursor="hand2",
                          activebackground="#3d3d45", font=("Segoe UI", 11),
                          padx=8, pady=3)
            b.grid(row=1, column=col, padx=2, pady=(2, 6))
            return b

        self.pen_btn = tool_btn("\u270E Pen", lambda: self._set_mode("pen"), 2)
        self.eraser_btn = tool_btn("\u232B Eraser", lambda: self._set_mode("eraser"), 3)
        tool_btn("\u21B6 Undo", self.undo, 4)
        tool_btn("\U0001F5D1 Clear", self.clear, 5)
        tool_btn("\u2715 Exit", self.close, 6)
        self._highlight_mode()

    def _make_draggable(self, widget):
        def start(e):
            self._dx, self._dy = e.x, e.y

        def move(e):
            x = self.panel.winfo_x() + e.x - self._dx
            y = self.panel.winfo_y() + e.y - self._dy
            self.panel.geometry(f"+{x}+{y}")
        widget.bind("<ButtonPress-1>", start)
        widget.bind("<B1-Motion>", move)

    def _set_color(self, c):
        self.color = c
        self.mode = "pen"
        self._highlight_color()
        self._highlight_mode()

    def _set_mode(self, m):
        self.mode = m
        self.canvas.config(cursor="dotbox" if m == "eraser" else "pencil")
        self._highlight_mode()

    def _highlight_color(self):
        for col, btn in self._swatches.items():
            btn.config(relief="solid" if col == self.color else "flat",
                       highlightbackground="#ffffff")

    def _highlight_mode(self):
        if not self.panel:
            return
        act, ina = "#a29bfe", "#2f2f35"
        self.pen_btn.config(bg=act if self.mode == "pen" else ina)
        self.eraser_btn.config(bg=act if self.mode == "eraser" else ina)
