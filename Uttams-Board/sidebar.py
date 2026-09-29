"""Left tool panel: tools, colors, stroke width, fill, text and options."""

import tkinter as tk

from config import (TOOLS, PALETTE, STROKE_WIDTHS, FONT_SIZES, ERASER_SIZES)
from theme import register, make_button, Tooltip


def _heading(app, parent, text):
    lbl = tk.Label(parent, text=text, font=("Segoe UI Semibold", 9),
                   bg=app.theme_colors()["panel"], fg=app.theme_colors()["muted"],
                   anchor="w")
    lbl.pack(fill="x", padx=12, pady=(12, 4))
    register(app, lbl, "pmuted")


def build_sidebar(app, parent):
    panel = tk.Frame(parent, width=200, bg=app.theme_colors()["panel"])
    panel.pack(side="left", fill="y")
    panel.pack_propagate(False)
    register(app, panel, "panel")

    _heading(app, panel, "TOOLS")
    grid = tk.Frame(panel, bg=app.theme_colors()["panel"])
    grid.pack(fill="x", padx=8)
    register(app, grid, "panel")

    app.tool_buttons = {}
    for i, (tid, icon, label, sc) in enumerate(TOOLS):
        b = tk.Button(grid, text=icon, font=("Segoe UI", 14), relief="flat", bd=0,
                      highlightthickness=0, cursor="hand2",
                      bg=app.theme_colors()["button"], fg=app.theme_colors()["text"],
                      width=3, height=1, command=lambda t=tid: app.set_tool(t))
        b.grid(row=i // 2, column=i % 2, padx=3, pady=3, sticky="nsew")
        Tooltip(b, f"{label}  ({sc})")
        app.tool_buttons[tid] = b
        b.bind("<Enter>", lambda _e, t=tid, btn=b:
               btn.config(bg=app.theme_colors()["button_active"]) if app.tool != t else None)
        b.bind("<Leave>", lambda _e, t=tid, btn=b:
               btn.config(bg=app.theme_colors()["button"]) if app.tool != t else None)
    grid.columnconfigure(0, weight=1)
    grid.columnconfigure(1, weight=1)

    _heading(app, panel, "COLOR")
    cframe = tk.Frame(panel, bg=app.theme_colors()["panel"])
    cframe.pack(fill="x", padx=8)
    register(app, cframe, "panel")
    for i, (name, hexv) in enumerate(PALETTE):
        border = "#999999" if hexv.lower() == "#ffffff" else hexv
        sw = tk.Button(cframe, bg=hexv, activebackground=hexv, relief="solid", bd=1,
                       width=2, height=1, cursor="hand2", highlightbackground=border,
                       command=lambda c=hexv: app.set_color(c))
        sw.grid(row=i // 4, column=i % 4, padx=3, pady=3, sticky="nsew")
        Tooltip(sw, name)
    for col in range(4):
        cframe.columnconfigure(col, weight=1)

    crow = tk.Frame(panel, bg=app.theme_colors()["panel"])
    crow.pack(fill="x", padx=12, pady=(8, 2))
    register(app, crow, "panel")
    app.color_display = tk.Label(crow, bg=app.color, width=3, relief="solid", bd=1)
    app.color_display.pack(side="left")
    custom = make_button(app, crow, "Custom\u2026", app.pick_custom_color,
                         tooltip="Choose a custom color", padx=6, pady=3,
                         font=("Segoe UI", 10))
    custom.pack(side="left", padx=6)

    _heading(app, panel, "STROKE WIDTH")
    app.width_var = tk.StringVar(value=str(app.width))
    wmenu = tk.OptionMenu(panel, app.width_var, *[str(w) for w in STROKE_WIDTHS],
                          command=lambda v: app.set_width(int(v)))
    wmenu.config(relief="flat", bd=0, highlightthickness=0,
                 bg=app.theme_colors()["button"], fg=app.theme_colors()["text"],
                 activebackground=app.theme_colors()["button_active"])
    wmenu.pack(fill="x", padx=12, pady=2)
    register(app, wmenu, "option")

    _heading(app, panel, "FILL (Rect / Circle)")
    app.fill_var = tk.StringVar(value="No Fill")
    fill_opts = ["No Fill"] + [n for n, _ in PALETTE]
    fmenu = tk.OptionMenu(panel, app.fill_var, *fill_opts, command=lambda v: app.set_fill(v))
    fmenu.config(relief="flat", bd=0, highlightthickness=0,
                 bg=app.theme_colors()["button"], fg=app.theme_colors()["text"],
                 activebackground=app.theme_colors()["button_active"])
    fmenu.pack(fill="x", padx=12, pady=2)
    register(app, fmenu, "option")

    _heading(app, panel, "TEXT")
    app.font_var = tk.StringVar(value=str(app.font_size))
    tmenu = tk.OptionMenu(panel, app.font_var, *[str(s) for s in FONT_SIZES],
                          command=lambda v: app.set_font_size(int(v)))
    tmenu.config(relief="flat", bd=0, highlightthickness=0,
                 bg=app.theme_colors()["button"], fg=app.theme_colors()["text"],
                 activebackground=app.theme_colors()["button_active"])
    tmenu.pack(fill="x", padx=12, pady=2)
    register(app, tmenu, "option")

    app.bold_var = tk.BooleanVar(value=False)
    bchk = tk.Checkbutton(panel, text="Bold", variable=app.bold_var,
                          command=lambda: app.set_bold(app.bold_var.get()),
                          bg=app.theme_colors()["panel"], fg=app.theme_colors()["text"],
                          selectcolor=app.theme_colors()["button"],
                          activebackground=app.theme_colors()["panel"],
                          activeforeground=app.theme_colors()["text"])
    bchk.pack(anchor="w", padx=12, pady=(2, 4))
    register(app, bchk, "check")

    _heading(app, panel, "ERASER SIZE")
    app.eraser_var = tk.StringVar(value="Medium")
    emenu = tk.OptionMenu(panel, app.eraser_var, *ERASER_SIZES.keys(),
                          command=lambda v: app.set_eraser(v))
    emenu.config(relief="flat", bd=0, highlightthickness=0,
                 bg=app.theme_colors()["button"], fg=app.theme_colors()["text"],
                 activebackground=app.theme_colors()["button_active"])
    emenu.pack(fill="x", padx=12, pady=2)
    register(app, emenu, "option")

    _heading(app, panel, "OPTIONS")
    app.grid_var = tk.BooleanVar(value=app.show_grid)
    gchk = tk.Checkbutton(panel, text="Show Grid", variable=app.grid_var,
                          command=app.toggle_grid,
                          bg=app.theme_colors()["panel"], fg=app.theme_colors()["text"],
                          selectcolor=app.theme_colors()["button"],
                          activebackground=app.theme_colors()["panel"],
                          activeforeground=app.theme_colors()["text"])
    gchk.pack(anchor="w", padx=12, pady=2)
    register(app, gchk, "check")

    spen = make_button(app, panel, "\u2712  Screen Pen", app.toggle_screen_pen,
                       tooltip="Draw over your whole desktop (F8)",
                       font=("Segoe UI", 10))
    spen.pack(fill="x", padx=12, pady=(10, 2))

    clear_btn = make_button(app, panel, "\U0001F5D1  Clear Board", app.clear_board,
                            tooltip="Clear everything", font=("Segoe UI", 10))
    clear_btn.pack(fill="x", padx=12, pady=(6, 12))
    return panel
