import sys
import traceback
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox

from application.team_app import team_app
from ui.login_dialog import LoginDialog
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
                "저장된 로그인 세션이 만료되었거나 현재 서버/Firestore에 해당 사용자가 없습니다. "
                "로컬 토큰을 초기화했으니 다시 로그인해주세요."
            )
            QMessageBox.information(
                login_dialog,
                "세션 다시 확인 필요",
                "저장된 로그인 세션이 서버 상태와 맞지 않아 로컬 토큰을 초기화했습니다.\n"
                "에뮬레이터를 비웠다면 관리자 계정을 다시 만든 뒤 로그인해주세요.",
            )
            if login_dialog.exec_() != LoginDialog.Accepted:
                sys.exit(0)
    else:
        if login_dialog.exec_() != LoginDialog.Accepted:
            sys.exit(0)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())
