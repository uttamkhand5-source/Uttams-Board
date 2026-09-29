"""Global constants and configuration for Uttam's Board."""

APP_NAME = "Uttam's Board"
APP_VERSION = "1.0"

DEFAULT_WIDTH = 1400
DEFAULT_HEIGHT = 850

GRID_SIZE = 25
MIN_ZOOM = 0.25
MAX_ZOOM = 4.0
HISTORY_LIMIT = 60

PALETTE = [
    ("Black", "#000000"), ("Red", "#e03131"), ("Blue", "#1971c2"),
    ("Green", "#2f9e44"), ("Yellow", "#f2c037"), ("Purple", "#7048e8"),
    ("Orange", "#e8590c"), ("White", "#ffffff"),
]
COLOR_MAP = {name: hexv for name, hexv in PALETTE}

STROKE_WIDTHS = [1, 2, 4, 6, 8, 12, 20]
FONT_SIZES = [12, 16, 20, 24, 32, 48]
ERASER_SIZES = {"Small": 14, "Medium": 26, "Large": 44}

TOOLS = [
    ("select", "\U0001F5B1", "Select", "V"),
    ("pen", "\u270E", "Pen", "P"),
    ("line", "\u2571", "Line", "L"),
    ("rect", "\u25AD", "Rectangle", "R"),
    ("oval", "\u25EF", "Circle", "C"),
    ("arrow", "\u279C", "Arrow", "A"),
    ("text", "T", "Text", "T"),
    ("eraser", "\u232B", "Eraser", "E"),
]
TOOL_LABELS = {tid: label for tid, _, label, _ in TOOLS}
