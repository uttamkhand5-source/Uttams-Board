"""Theme colors, tooltip system and themed button helper."""

import tkinter as tk

THEMES = {
    "light": {
        "bg": "#f4f5f7", "panel": "#ffffff", "canvas": "#ffffff",
        "text": "#1e1e21", "muted": "#6b7280", "button": "#ffffff",
        "button_active": "#e9ebf0", "accent": "#6965db", "border": "#d8dbe0",
        "grid": "#e9ebef", "status": "#eef0f3",
    },
    "dark": {
        "bg": "#1c1c1f", "panel": "#26262a", "canvas": "#232326",
        "text": "#e9e9ec", "muted": "#9a9aa2", "button": "#2f2f35",
        "button_active": "#3d3d45", "accent": "#a29bfe", "border": "#3a3a40",
        "grid": "#2b2b31", "status": "#26262a",
    },
}


class Tooltip:
    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _=None):
        self._cancel()
        self.after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def _show(self):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg="#111318", fg="#ffffff",
                 font=("Segoe UI", 9), padx=8, pady=4, bd=0).pack()

    def _hide(self, _=None):
        self._cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


def register(app, widget, role):
    app.themed.append((widget, role))


def make_button(app, parent, text, command, tooltip=None, role="button",
                font=("Segoe UI", 12), width=None, padx=9, pady=5):
    t = THEMES[app.theme]
    btn = tk.Button(parent, text=text, command=command, relief="flat", bd=0,
                    highlightthickness=0, cursor="hand2", font=font,
                    bg=t["button"], fg=t["text"], activebackground=t["button_active"],
                    activeforeground=t["text"], padx=padx, pady=pady)
    if width:
        btn.config(width=width)
    register(app, btn, role)
    btn.bind("<Enter>", lambda _: btn.config(bg=app.theme_colors()["button_active"]))
    btn.bind("<Leave>", lambda _: btn.config(bg=app.theme_colors()["button"]))
    if tooltip:
        Tooltip(btn, tooltip)
    return btn


def apply_theme(app):
    t = THEMES[app.theme]
    for widget, role in app.themed:
        try:
            if role == "bg":
                widget.config(bg=t["bg"])
            elif role == "panel":
                widget.config(bg=t["panel"])
            elif role == "status":
                widget.config(bg=t["status"], fg=t["text"])
            elif role == "button":
                widget.config(bg=t["button"], fg=t["text"],
                              activebackground=t["button_active"],
                              activeforeground=t["text"])
            elif role == "title":
                widget.config(bg=t["panel"], fg=t["accent"])
            elif role == "plabel":
                widget.config(bg=t["panel"], fg=t["text"])
            elif role == "pmuted":
                widget.config(bg=t["panel"], fg=t["muted"])
            elif role == "sep":
                widget.config(bg=t["border"])
            elif role == "option":
                widget.config(bg=t["button"], fg=t["text"],
                              activebackground=t["button_active"], highlightthickness=0)
            elif role == "check":
                widget.config(bg=t["panel"], fg=t["text"], selectcolor=t["button"],
                              activebackground=t["panel"], activeforeground=t["text"])
        except tk.TclError:
            pass
    app.canvas.config(bg=t["canvas"])
    app.cm.redraw()
    app.update_tool_buttons()
