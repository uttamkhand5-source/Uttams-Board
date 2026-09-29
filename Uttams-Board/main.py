"""Uttam's Board - a clean, Excalidraw-inspired Tkinter whiteboard."""

import tkinter as tk
from tkinter import colorchooser, messagebox

from config import (APP_NAME, DEFAULT_WIDTH, DEFAULT_HEIGHT, HISTORY_LIMIT,
                    ERASER_SIZES, COLOR_MAP, TOOL_LABELS)
from theme import THEMES, apply_theme, register
from history import History
from canvas_manager import CanvasManager
from toolbar import build_toolbar
from sidebar import build_sidebar
from file_manager import save_project, open_project
from screenshot import take_screenshot, export_png
from screen_pen import ScreenPen


class App:
    def __init__(self, root):
        self.root = root
        self.themed = []
        self.theme = "light"
        self.tool = "pen"
        self.color = "#000000"
        self.fill = None
        self.width = 2
        self.font_size = 20
        self.bold = False
        self.eraser_size = ERASER_SIZES["Medium"]
        self.show_grid = True
        self.dirty = False
        self.current_file = None

        root.title(APP_NAME)
        root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        root.minsize(900, 560)
        root.configure(bg=THEMES[self.theme]["bg"])
        register(self, root, "bg")

        # Build the main drawing area before the toolbar because the toolbar
        # needs access to CanvasManager for zoom controls.
        middle = tk.Frame(root, bg=THEMES[self.theme]["bg"])
        middle.pack(side="top", fill="both", expand=True)
        register(self, middle, "bg")

        canvas_wrap = tk.Frame(middle, bg=THEMES[self.theme]["border"])
        canvas_wrap.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        register(self, canvas_wrap, "sep")

        self.canvas = tk.Canvas(canvas_wrap, bg=THEMES[self.theme]["canvas"],
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        # CanvasManager must exist before build_toolbar(), because the toolbar
        # creates the zoom/reset commands from app.cm.
        self.cm = CanvasManager(self, self.canvas)
        self.screen_pen = ScreenPen(self)

        build_toolbar(self, root)
        build_sidebar(self, middle)
        self._build_status(root)

        self.history = History(HISTORY_LIMIT)
        self.history.push(self.cm.objects)

        apply_theme(self)
        self._bind_shortcuts()
        self.set_tool("pen")
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_title()

        self.root.after(100, lambda: self.canvas.create_text(
            self.canvas.winfo_width() / 2, 40, text="Start drawing\u2026  \u270E",
            fill=self.theme_colors()["muted"], font=("Segoe UI", 12), tags="hint"))

    def theme_colors(self):
        return THEMES[self.theme]

    def _build_status(self, root):
        bar = tk.Frame(root, bg=self.theme_colors()["status"], height=26)
        bar.pack(side="bottom", fill="x")
        register(self, bar, "status")
        self.status_tool = tk.Label(bar, text="Tool: Pen", anchor="w",
                                    bg=self.theme_colors()["status"],
                                    fg=self.theme_colors()["text"], font=("Segoe UI", 9))
        self.status_tool.pack(side="left", padx=12)
        register(self, self.status_tool, "status")
        self.status_zoom = tk.Label(bar, text="Zoom: 100%", anchor="w",
                                    bg=self.theme_colors()["status"],
                                    fg=self.theme_colors()["text"], font=("Segoe UI", 9))
        self.status_zoom.pack(side="left", padx=12)
        register(self, self.status_zoom, "status")
        self.status_obj = tk.Label(bar, text="Objects: 0", anchor="w",
                                   bg=self.theme_colors()["status"],
                                   fg=self.theme_colors()["text"], font=("Segoe UI", 9))
        self.status_obj.pack(side="left", padx=12)
        register(self, self.status_obj, "status")
        hint = tk.Label(bar, text="Middle-drag to pan \u2022 Ctrl+Wheel to zoom \u2022 F8 Screen Pen",
                        anchor="e", bg=self.theme_colors()["status"],
                        fg=self.theme_colors()["muted"], font=("Segoe UI", 9))
        hint.pack(side="right", padx=12)
        register(self, hint, "status")

    def update_status(self):
        self.status_tool.config(text=f"Tool: {TOOL_LABELS.get(self.tool, self.tool)}")
        self.status_zoom.config(text=f"Zoom: {int(round(self.cm.scale * 100))}%")
        self.status_obj.config(text=f"Objects: {len(self.cm.objects)}")

    def update_title(self):
        name = self.current_file.split("/")[-1] if self.current_file else "Untitled"
        star = "*" if self.dirty else ""
        self.root.title(f"{APP_NAME} - {name}{star}")

    def mark_dirty(self):
        self.dirty = True
        self.update_title()

    def push_history(self):
        self.history.push(self.cm.objects)

    def set_tool(self, tool):
        self.cm.commit_text_if_any()
        self.tool = tool
        cursors = {"select": "arrow", "text": "xterm", "eraser": "dotbox"}
        self.canvas.config(cursor=cursors.get(tool, "crosshair"))
        self.update_tool_buttons()
        self.update_status()

    def update_tool_buttons(self):
        if not hasattr(self, "tool_buttons"):
            return
        t = self.theme_colors()
        for tid, btn in self.tool_buttons.items():
            if tid == self.tool:
                btn.config(bg=t["accent"], fg="#ffffff", activebackground=t["accent"])
            else:
                btn.config(bg=t["button"], fg=t["text"],
                           activebackground=t["button_active"])

    def set_color(self, c):
        self.color = c
        if hasattr(self, "color_display"):
            self.color_display.config(bg=c)

    def pick_custom_color(self):
        result = colorchooser.askcolor(color=self.color, title="Choose Color")
        if result and result[1]:
            self.set_color(result[1])

    def set_width(self, w):
        self.width = int(w)

    def set_fill(self, name):
        self.fill = None if name == "No Fill" else COLOR_MAP.get(name)

    def set_font_size(self, s):
        self.font_size = int(s)

    def set_bold(self, b):
        self.bold = bool(b)

    def set_eraser(self, name):
        self.eraser_size = ERASER_SIZES.get(name, 26)

    def toggle_grid(self):
        self.show_grid = self.grid_var.get()
        self.cm.redraw()

    def toggle_screen_pen(self):
        self.screen_pen.toggle()

    def set_theme(self, theme):
        if theme not in THEMES:
            return
        self.theme = theme
        apply_theme(self)

    def undo(self):
        state = self.history.undo()
        if state is not None:
            self.cm.objects = state
            self.cm.selected = None
            self.mark_dirty()
            self.cm.redraw()

    def redo(self):
        state = self.history.redo()
        if state is not None:
            self.cm.objects = state
            self.cm.selected = None
            self.mark_dirty()
            self.cm.redraw()

    def save_board(self):
        save_project(self)

    def open_board(self):
        open_project(self)

    def new_board(self):
        if not self.confirm_discard():
            return
        self.cm.objects = []
        self.cm.selected = None
        self.cm.reset_zoom()
        self.history.reset()
        self.history.push(self.cm.objects)
        self.current_file = None
        self.dirty = False
        self.update_title()
        self.cm.redraw()

    def clear_board(self):
        if not self.cm.objects:
            return
        if messagebox.askyesno("Clear Board",
                               "Are you sure you want to clear the board?"):
            self.cm.objects = []
            self.cm.selected = None
            self.push_history()
            self.mark_dirty()
            self.cm.redraw()

    def confirm_discard(self):
        if not self.dirty:
            return True
        r = messagebox.askyesnocancel("Unsaved Changes",
                                      "You have unsaved changes.\n\nSave them before continuing?")
        if r is None:
            return False
        if r:
            save_project(self)
            return not self.dirty
        return True

    def export_png(self):
        export_png(self)

    def screenshot(self):
        take_screenshot(self)

    def _is_typing(self):
        w = self.root.focus_get()
        return isinstance(w, (tk.Entry, tk.Text))

    def _bind_shortcuts(self):
        r = self.root
        r.bind("<Control-z>", lambda e: self.undo())
        r.bind("<Control-y>", lambda e: self.redo())
        r.bind("<Control-s>", lambda e: self.save_board())
        r.bind("<Control-o>", lambda e: self.open_board())
        r.bind("<Control-n>", lambda e: self.new_board())
        r.bind("<Control-Shift-S>", lambda e: self.screenshot())
        r.bind("<Delete>", lambda e: self.cm.delete_selected())
        r.bind("<F8>", lambda e: self.toggle_screen_pen())
        for key, tool in [("v", "select"), ("p", "pen"), ("l", "line"),
                          ("r", "rect"), ("c", "oval"), ("a", "arrow"),
                          ("t", "text"), ("e", "eraser")]:
            r.bind(f"<KeyPress-{key}>",
                   lambda e, tl=tool: (None if self._is_typing() else self.set_tool(tl)))

    def on_close(self):
        if self.confirm_discard():
            self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
