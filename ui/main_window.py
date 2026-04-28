from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QMessageBox, QInputDialog,
    QApplication
)

from ui.presenter import team_presenter
from ui.config_dialog import ConfigDialog
from ui.user_table_widget import UserTableWidget
from ui.team_result_widget import TeamResultWidget
from util.constants import ANY_POSITION


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Team Builder")
        self.resize(1500, 850)

        self.current_file = None
        self.result_text = ""

        self._create_ui()
        self._connect_signals()
        self.load_dataset_list()

    def _create_ui(self):
        layout = QHBoxLayout()

        left = self._create_left_panel()

        self.team_result = TeamResultWidget()

        layout.addLayout(left, 5)
        layout.addWidget(self.team_result, 5)

        self.setLayout(layout)

    def _create_left_panel(self):
        left = QVBoxLayout()

        self.dataset_list = QListWidget()
        self.new_btn = QPushButton("새 데이터셋")

        self.user_table = UserTableWidget()

        self.config_btn = QPushButton("가중치 설정")

        left.addWidget(QLabel("데이터셋"))
        left.addWidget(self.dataset_list)
        left.addWidget(self.new_btn)
        left.addWidget(QLabel("유저"))
        left.addWidget(self.user_table)
        left.addWidget(self.config_btn)

        return left

    def _connect_signals(self):
        self.dataset_list.itemClicked.connect(self.load_dataset)
        self.new_btn.clicked.connect(self.create_dataset)

        self.user_table.toggle_clicked.connect(self.user_table.toggle_all)
        self.user_table.add_clicked.connect(self.user_table.add_row)
        self.user_table.delete_clicked.connect(self.user_table.delete_row)
        self.user_table.save_clicked.connect(self.save)

        self.team_result.generate_clicked.connect(self.make_team)
        self.team_result.copy_clicked.connect(self.copy)

        self.config_btn.clicked.connect(self.open_config_dialog)

    def _normalize_positions(self, users):
        normalized = []

        for user in users:
            copied = dict(user)
            raw_positions = copied.get("positions", [])
            positions = []

            for pos in raw_positions:
                if not pos:
                    continue
                if pos not in positions:
                    positions.append(pos)

            if not positions:
                positions = [ANY_POSITION]

            copied["positions"] = positions
            normalized.append(copied)

        return normalized

    def load_dataset_list(self):
        self.dataset_list.clear()
        self.dataset_list.addItems(team_presenter.get_dataset_list())

    def load_dataset(self, item):
        self.current_file = item.text()

        users = team_presenter.load_dataset(self.current_file)
        self.user_table.populate(users)

    def create_dataset(self):
        name, ok = QInputDialog.getText(
            self,
            "데이터셋 생성",
            "파일명 입력"
        )

        if not ok or not name.strip():
            return

        try:
            file_name = team_presenter.create_dataset(name.strip())

            self.load_dataset_list()

            self.current_file = file_name
            users = team_presenter.load_dataset(file_name)
            self.user_table.populate(users)

            QMessageBox.information(self, "완료", f"{file_name} 생성됨")

        except FileExistsError:
            QMessageBox.warning(self, "오류", "이미 존재하는 파일입니다")

    def save(self):
        if not self.current_file:
            QMessageBox.warning(self, "오류", "데이터셋 선택 필요")
            return

        users, error = team_presenter.extract_table_data(self.user_table.table)

        if error:
            QMessageBox.warning(self, "입력 오류", error)
            return

        users = self._normalize_positions(users)

        team_presenter.save_dataset(self.current_file, users)
        QMessageBox.information(self, "저장 완료", "저장되었습니다")

    def make_team(self):
        try:
            selected = team_presenter.extract_selected_users(
                self.user_table.table
            )

            if not selected:
                QMessageBox.warning(self, "오류", "선택된 유저가 없습니다")
                return

            selected = self._normalize_positions(selected)

            result, error = team_presenter.build_teams(selected)

            if error:
                QMessageBox.warning(self, "오류", error)
                return

            self.team_result.render(result)

            self.result_text = team_presenter.format_team_result(
                result["a1"],
                result["a2"]
            )

            if result.get("alerts"):
                alert_msg = team_presenter.format_alerts(result["alerts"])
                if alert_msg:
                    QMessageBox.information(self, "밸런스 주의", alert_msg)

            if result.get("warnings"):
                warning_msg = team_presenter.format_warnings(result["warnings"])
                if warning_msg:
                    QMessageBox.warning(self, "라인 밸런스 경고", warning_msg)

        except Exception as e:
            QMessageBox.critical(self, "크래시 방지", str(e))

    def copy(self):
        if not self.result_text:
            QMessageBox.warning(
                self,
                "오류",
                "복사할 팀 결과가 없습니다. 먼저 팀 생성하세요."
            )
            return

        QApplication.clipboard().setText(self.result_text)
        QMessageBox.information(self, "완료", "클립보드에 복사되었습니다.")

    def open_config_dialog(self):
        dialog = ConfigDialog()
        dialog.exec_()
