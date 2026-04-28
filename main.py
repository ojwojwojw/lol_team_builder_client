import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.style_loader import load_style  

if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_style(app)   # ✔ 먼저 적용

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())   