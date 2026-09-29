"""Save / open projects as JSON (.uttam)."""

import json
from tkinter import filedialog, messagebox

from config import APP_NAME, APP_VERSION


def save_project(app):
    path = filedialog.asksaveasfilename(
        title="Save Board", defaultextension=".uttam",
        filetypes=[("Uttam Board", "*.uttam"), ("JSON", "*.json"), ("All files", "*.*")])
    if not path:
        return
    data = {"app": APP_NAME, "version": APP_VERSION, "theme": app.theme,
            "show_grid": app.show_grid, "objects": app.cm.objects}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except (OSError, PermissionError) as ex:
        messagebox.showerror("Save Failed", f"Could not save file:\n{ex}")
        return
    app.current_file = path
    app.dirty = False
    app.update_title()
    messagebox.showinfo("Saved", "Board saved successfully!")


def open_project(app):
    if not app.confirm_discard():
        return
    path = filedialog.askopenfilename(
        title="Open Board",
        filetypes=[("Uttam Board", "*.uttam"), ("JSON", "*.json"), ("All files", "*.*")])
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as ex:
        messagebox.showerror("Open Failed", f"Could not open file:\n{ex}")
        return
    if not isinstance(data, dict) or "objects" not in data \
            or not isinstance(data["objects"], list):
        messagebox.showerror("Invalid File", "This is not a valid Uttam's Board file.")
        return
    app.cm.objects = data["objects"]
    app.cm.selected = None
    app.cm.reset_zoom()
    if "show_grid" in data:
        app.show_grid = bool(data["show_grid"])
        app.grid_var.set(app.show_grid)
    app.history.reset()
    app.history.push(app.cm.objects)
    app.current_file = path
    app.dirty = False
    app.update_title()
    app.cm.redraw()
