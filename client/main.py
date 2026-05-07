import sys
import traceback
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox

from application.team_app import team_app
from repositories.local_api_cache_repository import LocalApiCacheRepository
from ui.dialogs.login_dialog import LoginDialog
from ui.styling.style_loader import load_style
from ui.windows.main_window import MainWindow


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
    LocalApiCacheRepository.ensure_ready()

    load_style(app, team_app.load_theme_mode())

    login_dialog = LoginDialog()
    existing_token = team_app.load_auth_token().strip()

    if existing_token:
        try:
            login_dialog.current_user = team_app.get_current_user()
        except Exception:
            team_app.clear_auth_token()
            team_app.save_auth_username("")
            login_dialog.show_session_notice(
                "로그인 세션이 만료되었습니다. 다시 로그인해주세요."
            )
            QMessageBox.information(
                login_dialog,
                "세션 만료",
                "로그인 세션이 만료되었습니다. 다시 로그인해주세요.",
            )
            if login_dialog.exec_() != LoginDialog.Accepted:
                sys.exit(0)
    else:
        if login_dialog.exec_() != LoginDialog.Accepted:
            sys.exit(0)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())
