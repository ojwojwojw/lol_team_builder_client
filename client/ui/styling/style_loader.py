from pathlib import Path
import sys

from domain.constants import normalize_theme_mode


CLIENT_ROOT = Path(__file__).resolve().parents[2]


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return CLIENT_ROOT / relative_path


def load_style(app, theme_mode="dark"):
    normalized = normalize_theme_mode(theme_mode)
    path = resource_path(f"styles/{normalized}.qss")
    with open(path, "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())
