import os
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_style(app):
    path = resource_path("styles/dark.qss")
    with open(path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())