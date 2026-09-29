"""Top toolbar: history, file, view, appearance and screen pen."""

import tkinter as tk

from config import APP_NAME
from theme import make_button, register


def _sep(app, parent):
    f = tk.Frame(parent, width=1, bg=app.theme_colors()["border"])
    f.pack(side="left", fill="y", padx=8, pady=6)
    register(app, f, "sep")


def build_toolbar(app, parent):
    bar = tk.Frame(parent, bg=app.theme_colors()["panel"], height=52)
    bar.pack(side="top", fill="x")
    register(app, bar, "panel")

    brand = tk.Label(bar, text="\u2726 " + APP_NAME, font=("Segoe UI Semibold", 15),
                     bg=app.theme_colors()["panel"], fg=app.theme_colors()["accent"])
    brand.pack(side="left", padx=(14, 10), pady=8)
    register(app, brand, "title")

    _sep(app, bar)

    def add(text, cmd, tip):
        b = make_button(app, bar, text, cmd, tooltip=tip)
        b.pack(side="left", padx=2, pady=8)
        return b

    add("\u21B6", app.undo, "Undo (Ctrl+Z)")
    add("\u21B7", app.redo, "Redo (Ctrl+Y)")
    _sep(app, bar)
    add("\U0001F5CE", app.new_board, "New Board (Ctrl+N)")
    add("\U0001F4C2", app.open_board, "Open (Ctrl+O)")
    add("\U0001F4BE", app.save_board, "Save (Ctrl+S)")
    add("\U0001F5BC", app.export_png, "Export as PNG")
    add("\U0001F4F8", app.screenshot, "Screenshot (Ctrl+Shift+S)")
    _sep(app, bar)
    add("\uFF0B", lambda: app.cm.zoom_buttons(1.25), "Zoom In")
    add("\uFF0D", lambda: app.cm.zoom_buttons(0.8), "Zoom Out")
    add("\u2302", app.cm.reset_zoom, "Reset Zoom (100%)")
    _sep(app, bar)
    add("\u2600", lambda: app.set_theme("light"), "Light Mode")
    add("\U0001F319", lambda: app.set_theme("dark"), "Dark Mode")
    _sep(app, bar)
    add("\u2712", app.toggle_screen_pen,
        "Screen Pen - draw over your desktop (F8)")
    return bar
