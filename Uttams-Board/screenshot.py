"""Export/Screenshot: render the data model to a PNG using Pillow."""

import math
from tkinter import filedialog, messagebox


def _pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except ImportError:
        return None


_FONT_CACHE = {}


def _get_font(ImageFont, size, bold):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    names = (["DejaVuSans-Bold.ttf", "arialbd.ttf"] if bold
             else ["DejaVuSans.ttf", "arial.ttf"])
    font = None
    for n in names:
        try:
            font = ImageFont.truetype(n, size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _draw_objects(ImageFont, draw, objects, tx, scale):
    for obj in objects:
        t = obj["type"]
        color = obj.get("color", "#000000")
        w = max(1, int(round(obj.get("width", 2) * scale)))
        if t == "pen":
            pts = [tx(p[0], p[1]) for p in obj["points"]]
            if len(pts) >= 2:
                draw.line(pts, fill=color, width=w, joint="curve")
        elif t == "line":
            draw.line([tx(obj["x1"], obj["y1"]), tx(obj["x2"], obj["y2"])],
                      fill=color, width=w)
        elif t == "arrow":
            p1 = tx(obj["x1"], obj["y1"]); p2 = tx(obj["x2"], obj["y2"])
            draw.line([p1, p2], fill=color, width=w)
            ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            size = 10 + w * 2
            a1 = (p2[0] - size * math.cos(ang - 0.4), p2[1] - size * math.sin(ang - 0.4))
            a2 = (p2[0] - size * math.cos(ang + 0.4), p2[1] - size * math.sin(ang + 0.4))
            draw.polygon([p2, a1, a2], fill=color)
        elif t in ("rect", "oval"):
            p1 = tx(obj["x1"], obj["y1"]); p2 = tx(obj["x2"], obj["y2"])
            box = [min(p1[0], p2[0]), min(p1[1], p2[1]),
                   max(p1[0], p2[0]), max(p1[1], p2[1])]
            fill = obj.get("fill") or None
            if t == "rect":
                draw.rectangle(box, outline=color, width=w, fill=fill)
            else:
                draw.ellipse(box, outline=color, width=w, fill=fill)
        elif t == "text":
            font = _get_font(ImageFont, max(6, int(obj.get("font_size", 20) * scale)),
                             obj.get("bold", False))
            draw.text(tx(obj["x"], obj["y"]), obj["text"], fill=color, font=font)


def render_view(app):
    libs = _pillow()
    if not libs:
        return None
    Image, ImageDraw, ImageFont = libs
    cm = app.cm
    w = max(1, app.canvas.winfo_width())
    h = max(1, app.canvas.winfo_height())
    img = Image.new("RGB", (w, h), app.theme_colors()["canvas"])
    draw = ImageDraw.Draw(img)
    _draw_objects(ImageFont, draw, cm.objects, cm.w2s, cm.scale)
    return img


def render_all(app):
    libs = _pillow()
    if not libs:
        return None
    Image, ImageDraw, ImageFont = libs
    cm = app.cm
    if not cm.objects:
        return render_view(app)
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    for obj in cm.objects:
        x1, y1, x2, y2 = cm.object_bounds(obj)
        minx, miny = min(minx, x1), min(miny, y1)
        maxx, maxy = max(maxx, x2), max(maxy, y2)
    pad = 40
    w = max(1, int(maxx - minx + 2 * pad))
    h = max(1, int(maxy - miny + 2 * pad))
    img = Image.new("RGB", (w, h), app.theme_colors()["canvas"])
    draw = ImageDraw.Draw(img)

    def tx(x, y):
        return (x - minx + pad, y - miny + pad)

    _draw_objects(ImageFont, draw, cm.objects, tx, 1.0)
    return img


def _save_image(img, title):
    path = filedialog.asksaveasfilename(
        title=title, defaultextension=".png",
        filetypes=[("PNG Image", "*.png"), ("All files", "*.*")])
    if not path:
        return False
    try:
        img.save(path, "PNG")
    except (OSError, PermissionError) as ex:
        messagebox.showerror("Save Failed", f"Could not save image:\n{ex}")
        return False
    return True


def take_screenshot(app):
    app.cm.commit_text_if_any()
    img = render_view(app)
    if img is None:
        messagebox.showerror("Pillow Required",
                             "Screenshot needs Pillow.\n\nInstall:\n    pip install pillow")
        return
    if _save_image(img, "Save Screenshot"):
        messagebox.showinfo("Screenshot", "Screenshot saved successfully!")


def export_png(app):
    app.cm.commit_text_if_any()
    img = render_all(app)
    if img is None:
        messagebox.showerror("Pillow Required",
                             "PNG export needs Pillow.\n\nInstall:\n    pip install pillow")
        return
    if _save_image(img, "Export as PNG"):
        messagebox.showinfo("Export", "Board exported successfully!")
