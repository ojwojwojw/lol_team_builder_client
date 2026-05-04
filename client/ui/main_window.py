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

from application.recent_match_views import (
    CHAMPION_SUMMARY_COLUMNS,
    MATCH_DETAIL_COLUMNS,
    MATCH_TABLE_COLUMNS,
    POSITION_SUMMARY_COLUMNS,
    build_champion_summary_rows,
    build_empty_recent_summary_text,
    build_loading_recent_summary_text,
    build_position_summary_rows,
    build_recent_match_error_text,
    build_recent_match_rows,
    build_recent_summary_text,
)
from application.team_app import team_app
from domain.constants import ACCOUNT_SEARCH_LIMIT, ANY_POSITION
from ui.config_dialog import ConfigDialog
from ui.auth_admin_dialog import AuthAdminDialog
from ui.couple_group_dialog import CoupleGroupDialog
from ui.login_dialog import LoginDialog
from ui.match_detail_dialog import MatchDetailDialog
from ui.style_loader import load_style
from ui.team_result_widget import TeamResultWidget
from ui.theme import get_recent_summary_style
from ui.user_table_widget import UserTableWidget


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
        self.current_user = None
        self.theme_mode = team_app.load_theme_mode()
        self.match_detail_dialog = MatchDetailDialog(self)
        self.couple_group_dialog = CoupleGroupDialog(self)
        self.auth_admin_dialog = None

        self._create_ui()
        self._connect_signals()
        self.refresh_auth_status()
        self.apply_theme()
        self.load_dataset_list()

    def _log_exception(self, title, exc):
        log_path = Path(__file__).resolve().parent.parent / "team_builder_client_error.log"
        message = f"{title}\n{traceback.format_exc()}\n"
        try:
            with open(log_path, "a", encoding="utf-8") as file:
                file.write(message)
        except Exception:
            pass

        QMessageBox.critical(self, title, f"{exc}\n\n상세 로그: {log_path}")

    def _format_account_tier_text(self, account):
        tier = (account.get("tier") or "").strip()
        rank = (account.get("rank") or "").strip()
        league_points = account.get("league_points")
        queue_type = (account.get("queue_type") or "").strip()

        if not tier:
            return "언랭크"

        parts = [tier]
        if rank:
            parts.append(rank)
        if league_points is not None:
            parts.append(f"{league_points}LP")

        queue_label = ""
        if queue_type == "RANKED_SOLO_5x5":
            queue_label = "솔랭"
        elif queue_type == "RANKED_FLEX_SR":
            queue_label = "자랭"

        tier_text = " ".join(parts)
        if queue_label:
            return f"{tier_text} ({queue_label})"
        return tier_text

    def _format_account_list_label(self, account):
        return (
            f"{account.get('game_name', '')}#{account.get('tag_line', '')}"
            f" | {self._format_account_tier_text(account)}"
        )

    def _format_selected_account_label(self, account):
        return (
            f"선택 계정: {account.get('game_name', '')}#{account.get('tag_line', '')}"
            f" | {self._format_account_tier_text(account)}"
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
        container.setLayout(self._create_left_panel())
        return container

    def _build_right_panel_widget(self):
        container = QWidget()
        container.setLayout(self._create_right_panel())
        return container

    def _create_left_panel(self):
        left = QVBoxLayout()

        self.dataset_list = QListWidget()
        self.new_btn = QPushButton("데이터셋 생성")
        self.copy_dataset_btn = QPushButton("데이터셋 복사")
        self.delete_dataset_btn = QPushButton("데이터셋 삭제")
        self.user_table = UserTableWidget()
        self.auth_status_label = QLabel("로그인: -")
        self.config_btn = QPushButton("설정")
        self.auth_manage_btn = QPushButton("계정 관리")
        self.logout_btn = QPushButton("로그아웃")

        dataset_btn_row = QHBoxLayout()
        dataset_btn_row.addWidget(self.new_btn)
        dataset_btn_row.addWidget(self.copy_dataset_btn)
        dataset_btn_row.addWidget(self.delete_dataset_btn)

        left.addWidget(QLabel("데이터셋"))
        left.addWidget(self.dataset_list, 2)
        left.addLayout(dataset_btn_row)
        left.addWidget(QLabel("유저 목록"))
        left.addWidget(self.user_table, 7)
        left.addWidget(self.auth_status_label)
        left.addWidget(self.auth_manage_btn)
        left.addWidget(self.logout_btn)
        left.addWidget(self.config_btn)

        return left

    def _create_right_panel(self):
        right = QVBoxLayout()
        self.team_result = TeamResultWidget()
        right.addWidget(self.team_result, 4)
        right.addWidget(self._create_api_panel(), 6)
        return right

    def _create_api_panel(self):
        group = QGroupBox("최근 전적 분석")
        layout = QVBoxLayout()

        search_row = QHBoxLayout()
        self.account_keyword_input = QLineEdit()
        self.account_keyword_input.setPlaceholderText("게임 닉네임을 검색하세요")
        search_row.addWidget(QLabel("검색어"))
        search_row.addWidget(self.account_keyword_input, 1)

        action_row = QHBoxLayout()
        self.recent_match_limit = QSpinBox()
        self.recent_match_limit.setRange(1, 100)
        self.recent_match_limit.setValue(10)
        self.account_search_btn = QPushButton("계정 검색")
        self.account_list_all_btn = QPushButton("전체 유저 검색")
        self.apply_user_btn = QPushButton("선택 유저 추가")
        self.match_detail_btn = QPushButton("경기 상세 보기")
        action_row.addWidget(QLabel("최근 경기 수"))
        action_row.addWidget(self.recent_match_limit)
        action_row.addWidget(self.account_search_btn)
        action_row.addWidget(self.account_list_all_btn)
        action_row.addWidget(self.apply_user_btn)
        action_row.addWidget(self.match_detail_btn)

        self.selected_account_label = QLabel("선택 계정: -")
        self.selected_match_label = QLabel("선택 경기: -")
        self.selected_account_label.setWordWrap(True)
        self.selected_match_label.setWordWrap(True)

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.selected_account_label)
        info_layout.addWidget(self.selected_match_label)

        self.recent_summary_label = QLabel(build_empty_recent_summary_text())
        self.recent_summary_label.setWordWrap(True)

        account_panel = QWidget()
        account_box = QVBoxLayout()
        account_box.setContentsMargins(0, 0, 0, 0)
        account_box.addWidget(QLabel("검색된 계정"))
        self.account_list = QListWidget()
        self.account_list.setMinimumWidth(220)
        self.account_list.setMaximumWidth(280)
        account_box.addWidget(self.account_list)
        account_panel.setLayout(account_box)

        recent_panel = QWidget()
        center_box = QVBoxLayout()
        center_box.setContentsMargins(0, 0, 0, 0)
        center_box.addWidget(QLabel("최근 경기"))
        self.match_table = self._create_table(MATCH_TABLE_COLUMNS)
        self._configure_match_table()
        center_box.addWidget(self.match_table)
        recent_panel.setLayout(center_box)

        position_panel = QWidget()
        position_box = QVBoxLayout()
        position_box.setContentsMargins(0, 0, 0, 0)
        position_box.addWidget(QLabel("포지션 통계"))
        self.position_summary_table = self._create_table(POSITION_SUMMARY_COLUMNS)
        self._configure_summary_table(self.position_summary_table)
        position_box.addWidget(self.position_summary_table)
        position_panel.setLayout(position_box)

        champion_panel = QWidget()
        champion_box = QVBoxLayout()
        champion_box.setContentsMargins(0, 0, 0, 0)
        champion_box.addWidget(QLabel("챔피언 통계"))
        self.champion_summary_table = self._create_table(CHAMPION_SUMMARY_COLUMNS)
        self._configure_summary_table(self.champion_summary_table)
        champion_box.addWidget(self.champion_summary_table)
        champion_panel.setLayout(champion_box)

        summary_splitter = QSplitter(Qt.Horizontal)
        summary_splitter.addWidget(position_panel)
        summary_splitter.addWidget(champion_panel)
        summary_splitter.setChildrenCollapsible(False)
        summary_splitter.setSizes([420, 420])

        analysis_panel = QWidget()
        analysis_layout = QVBoxLayout()
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.addWidget(recent_panel, 5)
        analysis_layout.addWidget(summary_splitter, 3)
        analysis_panel.setLayout(analysis_layout)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.addWidget(account_panel)
        content_splitter.addWidget(analysis_panel)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setSizes([240, 1160])

        layout.addLayout(search_row)
        layout.addLayout(action_row)
        layout.addLayout(info_layout)
        layout.addWidget(self.recent_summary_label)
        layout.addWidget(content_splitter, 1)

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
        table.setWordWrap(False)
        return table

    def _configure_match_table(self):
        header = self.match_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.match_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.match_table.setColumnWidth(1, 160)

    def _configure_summary_table(self, table):
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for index in range(1, table.columnCount()):
            header.setSectionResizeMode(index, QHeaderView.ResizeToContents)

    def _connect_signals(self):
        self.dataset_list.itemClicked.connect(self.load_dataset)
        self.new_btn.clicked.connect(self.create_dataset)
        self.copy_dataset_btn.clicked.connect(self.copy_dataset)
        self.delete_dataset_btn.clicked.connect(self.delete_dataset)

        self.user_table.toggle_clicked.connect(self.user_table.toggle_all)
        self.user_table.add_clicked.connect(self.user_table.add_row)
        self.user_table.delete_clicked.connect(self.user_table.delete_row)
        self.user_table.couple_group_clicked.connect(self.open_couple_group_dialog)
        self.user_table.save_clicked.connect(self.save)

        self.team_result.generate_clicked.connect(self.make_team)
        self.team_result.copy_clicked.connect(self.copy)
        self.team_result.account_clicked.connect(self.open_account_from_team_result)

        self.auth_manage_btn.clicked.connect(self.open_auth_admin_dialog)
        self.logout_btn.clicked.connect(self.logout)
        self.config_btn.clicked.connect(self.open_config_dialog)
        self.account_search_btn.clicked.connect(self.search_accounts)
        self.account_list_all_btn.clicked.connect(self.load_all_accounts)
        self.account_keyword_input.returnPressed.connect(self.search_accounts)
        self.apply_user_btn.clicked.connect(self.apply_selected_user_to_table)
        self.match_detail_btn.clicked.connect(self.load_match_detail)
        self.account_list.itemClicked.connect(self.select_account)
        self.match_table.itemSelectionChanged.connect(self.select_match_from_table)

    def apply_theme(self):
        self.theme_mode = team_app.load_theme_mode()
        app = QApplication.instance()
        if app is not None:
            load_style(app, self.theme_mode)

        self.recent_summary_label.setStyleSheet(get_recent_summary_style(self.theme_mode))
        self.user_table.apply_theme(self.theme_mode)
        self.team_result.apply_theme(self.theme_mode)

    def refresh_auth_status(self):
        try:
            self.current_user = team_app.get_current_user()
        except Exception:
            self.current_user = None

        if not self.current_user:
            self.auth_status_label.setText("로그인: -")
            self.auth_manage_btn.setVisible(False)
            return

        is_admin = bool(self.current_user.get("is_admin"))
        role_text = "관리자" if is_admin else "일반"
        self.auth_status_label.setText(
            f"로그인: {self.current_user.get('username', '-')} ({role_text})"
        )
        self.auth_manage_btn.setVisible(is_admin)

    def open_auth_admin_dialog(self):
        if not self.current_user or not self.current_user.get("is_admin"):
            QMessageBox.warning(self, "권한 없음", "관리자 계정으로 로그인해야 합니다.")
            return

        self.auth_admin_dialog = AuthAdminDialog(self)
        self.auth_admin_dialog.exec_()

    def logout(self):
        answer = QMessageBox.question(
            self,
            "로그아웃",
            "현재 계정에서 로그아웃하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        team_app.clear_auth_token()
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() != LoginDialog.Accepted:
            self.close()
            return

        self.refresh_auth_status()

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
        self.selected_match = None
        self.recent_matches = []
        self.selected_match_label.setText("선택 경기: -")
        self.recent_summary_label.setText(build_empty_recent_summary_text())

    def _fill_table(self, table, rows, columns):
        table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            for col_index, column_name in enumerate(columns):
                table.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(str(row_data.get(column_name, ""))),
                )

    def _render_recent_summary(self, summary):
        self.recent_summary_label.setText(build_recent_summary_text(summary))

    def _render_recent_matches(self, matches):
        self._fill_table(
            self.match_table,
            build_recent_match_rows(matches),
            MATCH_TABLE_COLUMNS,
        )

    def _render_position_summary(self, stats):
        self._fill_table(
            self.position_summary_table,
            build_position_summary_rows(stats),
            POSITION_SUMMARY_COLUMNS,
        )

    def _render_champion_summary(self, stats):
        self._fill_table(
            self.champion_summary_table,
            build_champion_summary_rows(stats),
            CHAMPION_SUMMARY_COLUMNS,
        )

    def load_dataset_list(self):
        self.dataset_list.clear()
        self.dataset_list.addItems(team_app.get_dataset_list())

    def load_dataset(self, item):
        self.current_file = item.text()
        users = team_app.load_dataset(self.current_file)
        self.user_table.populate(users)

    def create_dataset(self):
        name, ok = QInputDialog.getText(self, "데이터셋 생성", "파일명을 입력하세요.")
        if not ok or not name.strip():
            return

        try:
            file_name = team_app.create_dataset(name.strip())
            self.load_dataset_list()
            self.current_file = file_name
            users = team_app.load_dataset(file_name)
            self.user_table.populate(users)
            QMessageBox.information(self, "완료", f"{file_name} 생성 완료")
        except FileExistsError:
            QMessageBox.warning(self, "오류", "이미 존재하는 파일입니다.")

    def copy_dataset(self):
        if not self.current_file:
            QMessageBox.warning(self, "오류", "복사할 데이터셋을 먼저 선택해주세요.")
            return

        name, ok = QInputDialog.getText(
            self,
            "데이터셋 복사",
            "새 데이터셋 이름을 입력하세요.",
            text=f"{Path(self.current_file).stem}_copy",
        )
        if not ok or not name.strip():
            return

        try:
            source_users = team_app.load_dataset(self.current_file)
            new_file_name = team_app.create_dataset(name.strip())
            team_app.save_dataset(new_file_name, source_users)
            self.load_dataset_list()
            self.current_file = new_file_name
            self.user_table.populate(source_users)
            QMessageBox.information(self, "완료", f"{new_file_name} 복사 완료")
        except FileExistsError:
            QMessageBox.warning(self, "오류", "이미 존재하는 파일입니다.")

    def delete_dataset(self):
        if not self.current_file:
            QMessageBox.warning(self, "오류", "삭제할 데이터셋을 먼저 선택해주세요.")
            return

        answer = QMessageBox.question(
            self,
            "데이터셋 삭제",
            f"{self.current_file} 파일을 정말 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            deleted_file = self.current_file
            team_app.delete_dataset(deleted_file)
            self.current_file = None
            self.user_table.populate([])
            self.load_dataset_list()
            QMessageBox.information(self, "완료", f"{deleted_file} 삭제 완료")
        except FileNotFoundError:
            QMessageBox.warning(self, "오류", "삭제할 데이터셋 파일을 찾지 못했습니다.")

    def save(self):
        if not self.current_file:
            QMessageBox.warning(self, "오류", "데이터셋을 먼저 선택해주세요.")
            return

        users, error = team_app.extract_table_data(self.user_table.table)
        if error:
            QMessageBox.warning(self, "입력 오류", error)
            return

        users = self._normalize_positions(users)
        team_app.save_dataset(self.current_file, users)
        QMessageBox.information(self, "저장 완료", "데이터가 저장되었습니다.")

    def open_couple_group_dialog(self):
        users = self.user_table.get_users_snapshot()
        if not users:
            QMessageBox.information(self, "커플 그룹", "먼저 유저를 표에 추가해주세요.")
            return

        self.couple_group_dialog.set_users(users)
        if self.couple_group_dialog.exec_():
            self.user_table.apply_couple_groups(
                self.couple_group_dialog.get_group_map()
            )

    def make_team(self):
        try:
            selected = team_app.extract_selected_users(self.user_table.table)
            if not selected:
                QMessageBox.warning(self, "오류", "선택된 유저가 없습니다.")
                return

            selected = self._normalize_positions(selected)
            result, error = team_app.build_teams(selected)
            if error:
                QMessageBox.warning(self, "오류", error)
                return

            self.team_result.render(result)
            self.result_text = team_app.format_team_result(result["a1"], result["a2"])

            if result.get("alerts"):
                alert_msg = team_app.format_alerts(result["alerts"])
                if alert_msg:
                    QMessageBox.information(self, "밸런스 주의", alert_msg)

            if result.get("warnings"):
                warning_msg = team_app.format_warnings(result["warnings"])
                if warning_msg:
                    QMessageBox.warning(self, "라인 밸런스 경고", warning_msg)
        except Exception as exc:
            QMessageBox.critical(self, "팀 생성 실패", str(exc))

    def copy(self):
        if not self.result_text:
            QMessageBox.warning(self, "오류", "복사할 팀 결과가 없습니다.")
            return

        QApplication.clipboard().setText(self.result_text)
        QMessageBox.information(self, "완료", "클립보드에 복사되었습니다.")

    def open_config_dialog(self):
        dialog = ConfigDialog()
        if dialog.exec_():
            self.apply_theme()

    def search_accounts(self):
        keyword = self.account_keyword_input.text().strip()

        if not keyword:
            QMessageBox.warning(self, "오류", "검색어를 입력해주세요.")
            return

        try:
            result = team_app.search_accounts(keyword, ACCOUNT_SEARCH_LIMIT)
        except Exception as exc:
            QMessageBox.critical(self, "API 오류", str(exc))
            return

        self._render_account_results(result, empty_message="검색된 계정이 없습니다.")

    def load_all_accounts(self):
        """검색어 없이 저장된 전체 유저 목록을 불러온다."""
        try:
            result = team_app.list_accounts(ACCOUNT_SEARCH_LIMIT)
        except Exception as exc:
            QMessageBox.critical(self, "API 오류", str(exc))
            return

        self._render_account_results(result, empty_message="저장된 계정이 없습니다.")

    def _render_account_results(self, result, empty_message: str):
        """검색/전체조회 응답을 공통 방식으로 리스트에 그린다."""
        self.account_list.clear()
        self.selected_account = None
        self.selected_account_label.setText("선택 계정: -")
        self._clear_match_views()

        accounts = result.get("accounts", [])
        for account in accounts:
            label = self._format_account_list_label(account)
            item = QListWidgetItem(label)
            item.setToolTip(label)
            item.setData(Qt.UserRole, account)
            self.account_list.addItem(item)

        if not accounts:
            QMessageBox.information(self, "검색 결과", empty_message)
            return

        self.account_list.setCurrentRow(0)
        self.select_account(self.account_list.item(0))

    def select_account(self, item):
        self.selected_account = item.data(Qt.UserRole)
        self._clear_match_views()
        self.selected_account_label.setText(
            self._format_selected_account_label(self.selected_account)
        )
        self._fetch_recent_matches(show_feedback=False)

    def open_account_from_team_result(self, user):
        game_name = (user.get("name") or user.get("account_game_name") or "").strip()
        tag_line = (user.get("account_tag_line") or "").strip()
        if not game_name or not tag_line:
            return

        self.account_keyword_input.setText(game_name)
        try:
            result = team_app.search_accounts(game_name, ACCOUNT_SEARCH_LIMIT)
        except Exception:
            return

        self.account_list.clear()
        self.selected_account = None
        self.selected_account_label.setText("선택 계정: -")
        self._clear_match_views()

        matched_item = None
        for account in result.get("accounts", []):
            label = self._format_account_list_label(account)
            item = QListWidgetItem(label)
            item.setToolTip(label)
            item.setData(Qt.UserRole, account)
            self.account_list.addItem(item)

            if (
                (account.get("game_name", "").strip().lower() == game_name.lower())
                and (account.get("tag_line", "").strip().lower() == tag_line.lower())
            ):
                matched_item = item

        if matched_item is not None:
            self.account_list.setCurrentItem(matched_item)
            self.select_account(matched_item)

    def _fetch_recent_matches(self, show_feedback):
        self.recent_summary_label.setText(build_loading_recent_summary_text())

        try:
            result = team_app.get_recent_matches_by_riot_id(
                self.selected_account.get("game_name", ""),
                self.selected_account.get("tag_line", ""),
                self.recent_match_limit.value(),
            )
        except Exception as exc:
            self._clear_match_views()
            self.recent_summary_label.setText(build_recent_match_error_text())
            if show_feedback:
                QMessageBox.critical(self, "API 오류", str(exc))
            return False

        self.recent_matches = result.get("matches", [])
        summary = team_app.summarize_recent_matches(self.recent_matches)
        self._render_recent_summary(summary)
        self._render_recent_matches(self.recent_matches)
        self._render_position_summary(summary["position_stats"])
        self._render_champion_summary(summary["champion_stats"])
        self.selected_match = None
        self.selected_match_label.setText("선택 경기: -")

        if not self.recent_matches:
            if show_feedback:
                QMessageBox.information(self, "조회 결과", "불러온 최근 경기가 없습니다.")
            return True

        self.match_table.selectRow(0)
        self.select_match_from_table()
        return True

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
            result = team_app.get_match_detail(self.selected_match.get("match_id", ""))
        except Exception as exc:
            QMessageBox.critical(self, "API 오류", str(exc))
            return

        if result.get("error"):
            QMessageBox.warning(self, "조회 실패", result["error"])
            return

        participants = team_app.normalize_match_detail(result)
        self.match_detail_dialog.set_rows(participants)
        self.match_detail_dialog.exec_()

    def apply_selected_user_to_table(self):
        try:
            if not self.current_file:
                QMessageBox.warning(self, "오류", "데이터셋을 먼저 불러와주세요.")
                return

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

            user_profile = team_app.build_user_profile(
                self.selected_account,
                self.recent_matches,
            )
            added = self.user_table.add_user(user_profile)

            if not added:
                QMessageBox.information(self, "중복 유저", "이미 표에 추가된 유저입니다.")
                return

            if user_profile.get("tier") == "언랭크":
                message = (
                    "선택한 유저가 언랭크 상태로 추가되었습니다.\n"
                    "팀빌딩 전에 표에서 티어와 랭크를 직접 입력해주세요."
                )
            elif self.recent_matches:
                message = (
                    "선택한 유저를 표에 추가했습니다.\n"
                    "최근 승률과 KDA, 포지션 통계가 함께 저장됩니다.\n"
                    "불러온 티어 정보도 함께 반영됐는지 확인해주세요."
                )
            else:
                message = (
                    "선택한 유저를 표에 추가했습니다.\n"
                    "최근 전적은 아직 없지만, 저장된 티어 정보가 있으면 함께 반영됩니다.\n"
                    "필요하면 전적 적재 후 다시 확인해주세요."
                )

            QMessageBox.information(self, "추가 완료", message)
        except Exception as exc:
            self._log_exception("유저 추가 실패", exc)
