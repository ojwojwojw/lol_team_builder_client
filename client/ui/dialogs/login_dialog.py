from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from application.team_app import team_app
from core.auth_session import clear_saved_session, save_login_session


class LoginDialog(QDialog):
    DEFAULT_BOOTSTRAP_USERNAME = "admin"
    USERNAME_PLACEHOLDER = "아이디를 입력해주세요"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("서버 로그인")
        self.resize(420, 220)
        self.current_user = None
        self.needs_bootstrap = False
        self._create_ui()
        self.refresh_setup_status()

    def _create_ui(self):
        layout = QVBoxLayout()

        guide = QLabel(
            "FastAPI 서버에 로그인한 뒤 클라이언트를 사용할 수 있습니다.\n"
            "서버에 계정이 없을 때만 최초 관리자 생성 버튼을 사용할 수 있습니다."
        )
        self.guide_label = guide
        guide.setWordWrap(True)

        self.session_notice_label = QLabel("")
        self.session_notice_label.setWordWrap(True)
        self.session_notice_label.hide()

        form = QFormLayout()
        self.server_url_input = QLineEdit()
        self.server_url_input.setText(team_app.load_server_base_url())

        self.username_input = QLineEdit()
        self.username_input.setText(team_app.load_auth_username())
        self.username_input.setPlaceholderText(self.USERNAME_PLACEHOLDER)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("8자 이상 비밀번호")

        form.addRow("서버 주소", self.server_url_input)
        form.addRow("아이디", self.username_input)
        form.addRow("비밀번호", self.password_input)

        button_row = QHBoxLayout()
        self.bootstrap_btn = QPushButton("최초 관리자 생성")
        self.reset_session_btn = QPushButton("저장 세션 초기화")
        self.login_btn = QPushButton("로그인")
        self.cancel_btn = QPushButton("종료")
        button_row.addWidget(self.bootstrap_btn)
        button_row.addWidget(self.reset_session_btn)
        button_row.addWidget(self.login_btn)
        button_row.addWidget(self.cancel_btn)

        layout.addWidget(guide)
        layout.addWidget(self.session_notice_label)
        layout.addLayout(form)
        layout.addLayout(button_row)
        self.setLayout(layout)

        self.bootstrap_btn.clicked.connect(self.bootstrap_admin)
        self.reset_session_btn.clicked.connect(self.reset_saved_session)
        self.login_btn.clicked.connect(self.login)
        self.cancel_btn.clicked.connect(self.reject)
        self.password_input.returnPressed.connect(self.login)

    def refresh_setup_status(self):
        team_app.save_server_base_url(self.server_url_input.text().strip())
        try:
            result = team_app.get_auth_setup_status()
            self.needs_bootstrap = bool(result.get("needs_bootstrap"))
        except Exception:
            self.needs_bootstrap = False

        self.bootstrap_btn.setVisible(self.needs_bootstrap)
        if self.needs_bootstrap:
            self.guide_label.setText(
                "현재 서버에는 계정이 없어 최초 관리자 계정을 먼저 만들어야 합니다.\n"
                "아이디를 비워두면 기본값 admin을 사용합니다."
            )
        else:
            self.guide_label.setText(
                "FastAPI 서버에 로그인한 뒤 클라이언트를 사용할 수 있습니다."
            )

    def show_session_notice(self, message: str):
        """저장된 토큰이 초기화되었거나 다시 로그인해야 하는 이유를 안내한다."""
        self.session_notice_label.setText(message)
        self.session_notice_label.show()

    def reset_saved_session(self):
        """로컬에 저장된 로그인 토큰과 사용자명을 명시적으로 초기화한다."""
        clear_saved_session()
        self.username_input.clear()
        self.password_input.clear()
        self.show_session_notice(
            "로컬에 저장된 로그인 세션을 초기화했습니다. "
            "에뮬레이터를 비웠거나 서버 상태가 바뀐 경우 다시 로그인해주세요."
        )
        QMessageBox.information(self, "세션 초기화", "저장된 로그인 세션을 초기화했습니다.")

    def login(self):
        username, password = self._read_credentials()
        if not username or not password:
            return

        team_app.save_server_base_url(self.server_url_input.text().strip())

        try:
            result = team_app.login(username, password)
        except Exception as exc:
            QMessageBox.critical(self, "로그인 실패", str(exc))
            return

        self._accept_auth_result(result, username)

    def bootstrap_admin(self):
        username, password = self._read_credentials(allow_default_bootstrap_username=True)
        if not username or not password:
            return

        team_app.save_server_base_url(self.server_url_input.text().strip())

        try:
            result = team_app.bootstrap_admin(username, password)
        except Exception as exc:
            QMessageBox.critical(self, "최초 관리자 생성 실패", str(exc))
            return

        self._accept_auth_result(result, username)
        QMessageBox.information(self, "완료", "최초 관리자 계정 생성과 로그인이 완료되었습니다.")

    def _read_credentials(self, allow_default_bootstrap_username=False):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if allow_default_bootstrap_username and not username:
            username = self.DEFAULT_BOOTSTRAP_USERNAME
            self.username_input.setText(username)

        if not self.server_url_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "서버 주소를 입력해주세요.")
            return None, None
        if not username:
            QMessageBox.warning(self, "입력 오류", "아이디를 입력해주세요.")
            return None, None
        if not password:
            QMessageBox.warning(self, "입력 오류", "비밀번호를 입력해주세요.")
            return None, None
        return username, password

    def _accept_auth_result(self, result, username):
        token = (result or {}).get("access_token", "")
        if not token:
            raise RuntimeError("로그인 응답에 access_token 이 없습니다.")

        save_login_session(token, username)
        self.current_user = result.get("user")
        self.accept()
