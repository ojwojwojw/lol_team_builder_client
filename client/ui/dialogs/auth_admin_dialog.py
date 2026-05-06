from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from application.team_app import team_app


USER_COLUMNS = ["ID", "아이디", "권한", "활성", "생성일"]


class AuthAdminDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("계정 관리")
        self.resize(720, 460)
        self._create_ui()
        self.refresh_users()

    def _create_ui(self):
        layout = QVBoxLayout()

        guide = QLabel(
            "서버에 저장된 앱 계정을 관리합니다.\n"
            "이 목록은 server SQLite 의 app_user 테이블 기준으로 보여줍니다."
        )
        guide.setWordWrap(True)

        self.user_table = QTableWidget()
        self.user_table.setColumnCount(len(USER_COLUMNS))
        self.user_table.setHorizontalHeaderLabels(USER_COLUMNS)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.user_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        form = QFormLayout()
        self.new_username_input = QLineEdit()
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        form.addRow("새 아이디", self.new_username_input)
        form.addRow("새 비밀번호", self.new_password_input)

        button_row = QHBoxLayout()
        self.refresh_btn = QPushButton("새로고침")
        self.create_btn = QPushButton("계정 생성")
        button_row.addWidget(self.refresh_btn)
        button_row.addWidget(self.create_btn)

        layout.addWidget(guide)
        layout.addWidget(self.user_table)
        layout.addLayout(form)
        layout.addLayout(button_row)
        self.setLayout(layout)

        self.refresh_btn.clicked.connect(self.refresh_users)
        self.create_btn.clicked.connect(self.create_user)

    def refresh_users(self):
        try:
            result = team_app.list_users()
        except Exception as exc:
            QMessageBox.critical(self, "계정 조회 실패", str(exc))
            return

        users = result.get("users", [])
        self.user_table.setRowCount(len(users))
        for row, user in enumerate(users):
            values = [
                user.get("id", ""),
                user.get("username", ""),
                "관리자" if user.get("is_admin") else "일반",
                "활성" if user.get("is_active") else "비활성",
                user.get("created_at", ""),
            ]
            for col, value in enumerate(values):
                self.user_table.setItem(row, col, QTableWidgetItem(str(value)))

    def create_user(self):
        username = self.new_username_input.text().strip()
        password = self.new_password_input.text()

        if not username:
            QMessageBox.warning(self, "입력 오류", "새 아이디를 입력해주세요.")
            return
        if not password:
            QMessageBox.warning(self, "입력 오류", "새 비밀번호를 입력해주세요.")
            return

        try:
            result = team_app.create_user(username, password)
        except Exception as exc:
            QMessageBox.critical(self, "계정 생성 실패", str(exc))
            return

        QMessageBox.information(self, "완료", result.get("message", "계정이 생성되었습니다."))
        self.new_password_input.clear()
        self.refresh_users()
