import sys
import traceback
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.style_loader import load_style  


def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    log_path = Path(__file__).resolve().parent / "team_builder_client_error.log"
    message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    try:
        with open(log_path, "a", encoding="utf-8") as file:
            file.write(message + "\n")
    except Exception:
        pass

    sys.__excepthook__(exc_type, exc_value, exc_traceback)

if __name__ == "__main__":
    sys.excepthook = log_unhandled_exception
    app = QApplication(sys.argv)

    load_style(app)   # ✔ 먼저 적용

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())   
