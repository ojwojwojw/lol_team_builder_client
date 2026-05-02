import traceback
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.config_dialog import ConfigDialog
from ui.presenter import team_presenter
from ui.team_result_widget import TeamResultWidget
from ui.user_table_widget import UserTableWidget
from util.constants import ANY_POSITION


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("팀 빌더")
        self.resize(1960, 980)

        self.current_file = None
        self.result_text = ""
        self.selected_account = None
        self.selected_match = None
        self.recent_matches = []

        self._create_ui()
        self._connect_signals()
        self.load_dataset_list()

    def _log_exception(self, title, exc):
        log_path = Path(__file__).resolve().parent.parent / "team_builder_client_error.log"
        message = f"{title}\n{traceback.format_exc()}\n"
        try:
            with open(log_path, "a", encoding="utf-8") as file:
                file.write(message)
        except Exception:
            pass

        QMessageBox.critical(
            self,
            title,
            f"{exc}\n\n상세 로그: {log_path}",
        )

    def _create_ui(self):
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_left_panel_widget())
        splitter.addWidget(self._build_right_panel_widget())
        splitter.setSizes([980, 1180])
        layout.addWidget(splitter)
        self.setLayout(layout)

    def _build_left_panel_widget(self):
        container = QWidget()
        layout = self._create_left_panel()
        container.setLayout(layout)
        return container

    def _build_right_panel_widget(self):
        container = QWidget()
        layout = self._create_right_panel()
        container.setLayout(layout)
        return container

    def _create_left_panel(self):
        left = QVBoxLayout()

        self.dataset_list = QListWidget()
        self.new_btn = QPushButton("데이터셋 생성")
        self.user_table = UserTableWidget()
        self.config_btn = QPushButton("설정")

        left.addWidget(QLabel("데이터셋"))
        left.addWidget(self.dataset_list, 2)
        left.addWidget(self.new_btn)
        left.addWidget(QLabel("유저 목록"))
        left.addWidget(self.user_table, 7)
        left.addWidget(self.config_btn)

        return left

    def _create_right_panel(self):
        right = QVBoxLayout()
        self.team_result = TeamResultWidget()
        right.addWidget(self.team_result, 4)
        right.addWidget(self._create_api_panel(), 6)
        return right

    def _create_api_panel(self):
        group = QGroupBox("실제 전적 분석")
        layout = QVBoxLayout()

        search_row = QHBoxLayout()
        self.account_keyword_input = QLineEdit()
        self.account_keyword_input.setPlaceholderText("게임 닉네임을 검색하세요")
        self.account_search_limit = QSpinBox()
        self.account_search_limit.setRange(1, 100)
        self.account_search_limit.setValue(20)
        self.account_search_btn = QPushButton("계정 검색")
        search_row.addWidget(QLabel("검색어"))
        search_row.addWidget(self.account_keyword_input, 1)
        search_row.addWidget(QLabel("개수"))
        search_row.addWidget(self.account_search_limit)
        search_row.addWidget(self.account_search_btn)

        action_row = QHBoxLayout()
        self.recent_match_limit = QSpinBox()
        self.recent_match_limit.setRange(1, 100)
        self.recent_match_limit.setValue(10)
        self.recent_match_btn = QPushButton("최근 전적 불러오기")
        self.apply_user_btn = QPushButton("선택 유저 추가")
        self.match_detail_btn = QPushButton("경기 상세 보기")
        action_row.addWidget(QLabel("최근 경기 수"))
        action_row.addWidget(self.recent_match_limit)
        action_row.addWidget(self.recent_match_btn)
        action_row.addWidget(self.apply_user_btn)
        action_row.addWidget(self.match_detail_btn)

        info_row = QHBoxLayout()
        self.selected_account_label = QLabel("선택 계정: -")
        self.selected_match_label = QLabel("선택 경기: -")
        info_row.addWidget(self.selected_account_label, 1)
        info_row.addWidget(self.selected_match_label, 1)

        self.recent_summary_label = QLabel(
            "최근 요약: 계정을 선택하면 승률, KDA, 주 포지션 통계를 볼 수 있습니다."
        )
        self.recent_summary_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #d9e6ff; "
            "background-color: #1f2c3a; border-radius: 6px; padding: 8px;"
        )

        content_row = QHBoxLayout()

        account_box = QVBoxLayout()
        account_box.addWidget(QLabel("검색 계정"))
        self.account_list = QListWidget()
        account_box.addWidget(self.account_list)

        center_box = QVBoxLayout()
        center_box.addWidget(QLabel("최근 경기"))
        self.match_table = self._create_table(
            ["일시", "챔피언", "포지션", "결과", "K/D/A", "CS", "시야", "딜량", "골드"]
        )
        center_box.addWidget(self.match_table)

        summary_box = QVBoxLayout()
        summary_box.addWidget(QLabel("포지션 통계"))
        self.position_summary_table = self._create_table(
            ["포지션", "경기 수", "승", "패", "승률"]
        )
        summary_box.addWidget(self.position_summary_table)
        summary_box.addWidget(QLabel("챔피언 통계"))
        self.champion_summary_table = self._create_table(
            ["챔피언", "경기 수", "승", "패", "승률"]
        )
        summary_box.addWidget(self.champion_summary_table)

        content_row.addLayout(account_box, 2)
        content_row.addLayout(center_box, 5)
        content_row.addLayout(summary_box, 3)

        detail_box = QVBoxLayout()
        detail_box.addWidget(QLabel("선택 경기 참가자"))
        self.match_detail_table = self._create_table(
            ["소환사", "챔피언", "포지션", "결과", "K/D/A", "CS", "딜량", "시야"]
        )
        detail_box.addWidget(self.match_detail_table)

        layout.addLayout(search_row)
        layout.addLayout(action_row)
        layout.addLayout(info_row)
        layout.addWidget(self.recent_summary_label)
        layout.addLayout(content_row, 4)
        layout.addLayout(detail_box, 3)

        group.setLayout(layout)
        return group

    def _create_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        return table

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
        self.account_search_btn.clicked.connect(self.search_accounts)
        self.recent_match_btn.clicked.connect(self.load_recent_matches)
        self.apply_user_btn.clicked.connect(self.apply_selected_user_to_table)
        self.match_detail_btn.clicked.connect(self.load_match_detail)
        self.account_list.itemClicked.connect(self.select_account)
        self.match_table.itemSelectionChanged.connect(self.select_match_from_table)

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

    def _clear_match_views(self):
        self.match_table.setRowCount(0)
        self.position_summary_table.setRowCount(0)
        self.champion_summary_table.setRowCount(0)
        self.match_detail_table.setRowCount(0)
        self.selected_match = None
        self.recent_matches = []
        self.selected_match_label.setText("선택 경기: -")
        self.recent_summary_label.setText(
            "최근 요약: 계정을 선택하면 승률, KDA, 주 포지션 통계를 볼 수 있습니다."
        )

    def _fill_table(self, table, rows, columns):
        table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            for col_index, column_name in enumerate(columns):
                value = row_data.get(column_name, "")
                table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

    def _render_recent_summary(self, summary):
        if not summary.get("match_count"):
            self.recent_summary_label.setText(
                "최근 요약: 아직 불러온 경기가 없습니다. 계정은 지금 바로 표에 추가할 수 있습니다."
            )
            return

        self.recent_summary_label.setText(
            "최근 요약: "
            f"{summary['match_count']}경기 {summary['wins']}승 {summary['losses']}패"
            f" / 승률 {summary['recent_win_rate']}%"
            f" / 평균 KDA {summary['recent_kda']}"
            f" / 평균 CS {summary['avg_cs']}"
            f" / 주 챔피언 {summary['main_champion']}"
        )

    def load_dataset_list(self):
        self.dataset_list.clear()
        self.dataset_list.addItems(team_presenter.get_dataset_list())

    def load_dataset(self, item):
        self.current_file = item.text()
        users = team_presenter.load_dataset(self.current_file)
        self.user_table.populate(users)

    def create_dataset(self):
        name, ok = QInputDialog.getText(self, "데이터셋 생성", "파일명을 입력하세요")
        if not ok or not name.strip():
            return

        try:
            file_name = team_presenter.create_dataset(name.strip())
            self.load_dataset_list()
            self.current_file = file_name
            users = team_presenter.load_dataset(file_name)
            self.user_table.populate(users)
            QMessageBox.information(self, "완료", f"{file_name} 생성 완료")
        except FileExistsError:
            QMessageBox.warning(self, "오류", "이미 존재하는 파일입니다.")

    def save(self):
        if not self.current_file:
            QMessageBox.warning(self, "오류", "데이터셋을 먼저 선택해주세요.")
            return

        users, error = team_presenter.extract_table_data(self.user_table.table)
        if error:
            QMessageBox.warning(self, "입력 오류", error)
            return

        users = self._normalize_positions(users)
        team_presenter.save_dataset(self.current_file, users)
        QMessageBox.information(self, "저장 완료", "데이터가 저장되었습니다.")

    def make_team(self):
        try:
            selected = team_presenter.extract_selected_users(self.user_table.table)
            if not selected:
                QMessageBox.warning(self, "오류", "선택된 유저가 없습니다.")
                return

            selected = self._normalize_positions(selected)
            result, error = team_presenter.build_teams(selected)
            if error:
                QMessageBox.warning(self, "오류", error)
                return

            self.team_result.render(result)
            self.result_text = team_presenter.format_team_result(
                result["a1"],
                result["a2"],
            )

            if result.get("alerts"):
                alert_msg = team_presenter.format_alerts(result["alerts"])
                if alert_msg:
                    QMessageBox.information(self, "밸런스 주의", alert_msg)

            if result.get("warnings"):
                warning_msg = team_presenter.format_warnings(result["warnings"])
                if warning_msg:
                    QMessageBox.warning(self, "라인 밸런스 경고", warning_msg)

        except Exception as exc:
            QMessageBox.critical(self, "팀 생성 실패", str(exc))

    def copy(self):
        if not self.result_text:
            QMessageBox.warning(self, "오류", "복사할 팀 결과가 없습니다.")
            return

        QApplication.clipboard().setText(self.result_text)
        QMessageBox.information(self, "완료", "클립보드에 복사했습니다.")

    def open_config_dialog(self):
        dialog = ConfigDialog()
        dialog.exec_()

    def search_accounts(self):
        keyword = self.account_keyword_input.text().strip()
        limit = self.account_search_limit.value()

        if not keyword:
            QMessageBox.warning(self, "오류", "검색어를 입력해주세요.")
            return

        try:
            result = team_presenter.search_accounts(keyword, limit)
        except Exception as exc:
            QMessageBox.critical(self, "API 오류", str(exc))
            return

        self.account_list.clear()
        self.selected_account = None
        self.selected_account_label.setText("선택 계정: -")
        self._clear_match_views()

        accounts = result.get("accounts", [])
        for account in accounts:
            label = f"{account.get('game_name', '')}#{account.get('tag_line', '')}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, account)
            self.account_list.addItem(item)

        if not accounts:
            QMessageBox.information(self, "검색 결과", "검색된 계정이 없습니다.")
            return

        self.account_list.setCurrentRow(0)
        self.select_account(self.account_list.item(0))

    def select_account(self, item):
        self.selected_account = item.data(Qt.UserRole)
        self._clear_match_views()

        game_name = self.selected_account.get("game_name", "")
        tag_line = self.selected_account.get("tag_line", "")
        self.selected_account_label.setText(f"선택 계정: {game_name}#{tag_line}")
        self._fetch_recent_matches(show_feedback=False)

    def load_recent_matches(self):
        if not self.selected_account:
            QMessageBox.warning(self, "오류", "계정을 먼저 선택해주세요.")
            return

        self._fetch_recent_matches(show_feedback=True)

    def _fetch_recent_matches(self, show_feedback):
        self.recent_summary_label.setText("최근 요약: 최근 전적을 불러오는 중입니다...")

        try:
            result = team_presenter.get_recent_matches_by_riot_id(
                self.selected_account.get("game_name", ""),
                self.selected_account.get("tag_line", ""),
                self.recent_match_limit.value(),
            )
        except Exception as exc:
            self._clear_match_views()
            self.recent_summary_label.setText(
                "최근 요약: 최근 전적을 불러오지 못했습니다. 계정 정보만으로 추가할 수 있습니다."
            )
            if show_feedback:
                QMessageBox.critical(self, "API 오류", str(exc))
            return False

        self.recent_matches = result.get("matches", [])
        summary = team_presenter.summarize_recent_matches(self.recent_matches)
        self._render_recent_summary(summary)
        self._render_recent_matches(self.recent_matches)
        self._render_position_summary(summary["position_stats"])
        self._render_champion_summary(summary["champion_stats"])
        self.match_detail_table.setRowCount(0)
        self.selected_match = None
        self.selected_match_label.setText("선택 경기: -")

        if not self.recent_matches:
            if show_feedback:
                QMessageBox.information(self, "조회 결과", "불러온 최근 경기가 없습니다.")
            return True

        self.match_table.selectRow(0)
        self.select_match_from_table()
        return True

    def _render_recent_matches(self, matches):
        rows = []
        for match in matches:
            rows.append({
                "일시": team_presenter.format_match_datetime(
                    match.get("game_start_timestamp")
                ),
                "챔피언": match.get("champion_name", "-"),
                "포지션": team_presenter.get_match_position(match),
                "결과": team_presenter.get_match_result_text(match),
                "K/D/A": team_presenter.format_kda(match),
                "CS": team_presenter.get_match_cs(match),
                "시야": match.get("vision_score", 0) or 0,
                "딜량": match.get("total_damage_dealt_to_champions", 0) or 0,
                "골드": match.get("gold_earned", 0) or 0,
            })

        self._fill_table(
            self.match_table,
            rows,
            ["일시", "챔피언", "포지션", "결과", "K/D/A", "CS", "시야", "딜량", "골드"],
        )

    def _render_position_summary(self, stats):
        rows = []
        for item in stats:
            rows.append({
                "포지션": item["position"],
                "경기 수": item["count"],
                "승": item["wins"],
                "패": item["losses"],
                "승률": f"{item['win_rate']}%",
            })

        self._fill_table(
            self.position_summary_table,
            rows,
            ["포지션", "경기 수", "승", "패", "승률"],
        )

    def _render_champion_summary(self, stats):
        rows = []
        for item in stats:
            rows.append({
                "챔피언": item["champion_name"],
                "경기 수": item["count"],
                "승": item["wins"],
                "패": item["losses"],
                "승률": f"{item['win_rate']}%",
            })

        self._fill_table(
            self.champion_summary_table,
            rows,
            ["챔피언", "경기 수", "승", "패", "승률"],
        )

    def select_match_from_table(self):
        row = self.match_table.currentRow()
        if row < 0 or row >= len(self.recent_matches):
            return

        self.selected_match = self.recent_matches[row]
        self.selected_match_label.setText(
            f"선택 경기: {self.selected_match.get('match_id', '-')}"
        )

    def load_match_detail(self):
        if not self.selected_match:
            QMessageBox.warning(self, "오류", "최근 경기에서 경기를 먼저 선택해주세요.")
            return

        try:
            result = team_presenter.get_match_detail(
                self.selected_match.get("match_id", "")
            )
        except Exception as exc:
            QMessageBox.critical(self, "API 오류", str(exc))
            return

        if result.get("error"):
            QMessageBox.warning(self, "조회 실패", result["error"])
            return

        participants = team_presenter.normalize_match_detail(result)
        self._fill_table(
            self.match_detail_table,
            participants,
            ["summoner_name", "champion_name", "position", "result", "kda", "cs", "damage", "vision"],
        )
        self.match_detail_table.setHorizontalHeaderLabels(
            ["소환사", "챔피언", "포지션", "결과", "K/D/A", "CS", "딜량", "시야"]
        )

    def apply_selected_user_to_table(self):
        try:
            if not self.selected_account:
                QMessageBox.warning(self, "오류", "계정을 먼저 선택해주세요.")
                return

            game_name = self.selected_account.get("game_name", "").strip()
            if self.user_table.has_user(game_name):
                row = self.user_table.find_row_by_name(game_name)
                if row >= 0:
                    self.user_table.set_selected_row(row)
                QMessageBox.information(self, "중복 유저", "이미 표에 추가된 유저입니다.")
                return

            user_profile = team_presenter.build_user_profile(
                self.selected_account,
                self.recent_matches,
            )
            added = self.user_table.add_user(user_profile)

            if not added:
                QMessageBox.information(self, "중복 유저", "이미 표에 추가된 유저입니다.")
                return

            if self.recent_matches:
                message = (
                    "선택한 유저를 표에 추가했습니다.\n"
                    "최근 승률과 KDA, 포지션 통계가 숨은 데이터로 함께 저장됩니다.\n"
                    "티어는 직접 확인 후 조정해주세요."
                )
            else:
                message = (
                    "선택한 유저를 표에 추가했습니다.\n"
                    "최근 전적을 아직 불러오지 않았으므로 포지션은 기본값으로 들어갑니다.\n"
                    "나중에 전적을 불러온 뒤 다시 추가하지 않고도 티어만 수정해서 사용할 수 있습니다."
                )

            QMessageBox.information(self, "추가 완료", message)
        except Exception as exc:
            self._log_exception("유저 추가 실패", exc)
