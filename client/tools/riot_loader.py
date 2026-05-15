import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from application.team_app import team_app
from core.auth_session import clear_saved_session
from repositories.local_api_cache_repository import LocalApiCacheRepository
from tools.riot_loader_api import RiotLoaderApi
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.riot_loader_scheduler_dialog import RiotLoaderSchedulerDialog
from ui.styling.style_loader import load_style


class RiotLoaderWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user or {}
        self.current_puuid = ""
        self.current_match_ids = []
        self.api = RiotLoaderApi()
        self.scheduler_dialog = None

        self.setWindowTitle("Riot Loader")
        self.setMinimumSize(980, 760)
        self._create_ui()
        self._update_session_badge()
        self._update_server_label()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        root.addWidget(self._build_header_group())

        content_grid = QGridLayout()
        content_grid.setHorizontalSpacing(14)
        content_grid.setVerticalSpacing(14)
        content_grid.addWidget(self._build_manual_group(), 0, 0)
        content_grid.addWidget(self._build_account_group(), 0, 1)
        content_grid.setColumnStretch(0, 1)
        content_grid.setColumnStretch(1, 1)
        root.addLayout(content_grid)

        root.addWidget(self._build_result_group(), 1)

    def _build_header_group(self):
        box = QGroupBox("Admin Session")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        title = QLabel("Riot Data Loader Console")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "Run manual loads, batch sync jobs, and cache checks from one place."
        )
        subtitle.setWordWrap(True)

        info_row = QHBoxLayout()
        self.server_url_label = QLabel()
        self.session_label = QLabel()
        self.session_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_row.addWidget(self.server_url_label, 1)
        info_row.addWidget(self.session_label, 1)

        button_row = QHBoxLayout()
        self.scheduler_btn = QPushButton("Batch Scheduler")
        self.scheduler_btn.clicked.connect(self.open_scheduler_dialog)
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout)
        button_row.addWidget(self.scheduler_btn)
        button_row.addStretch(1)
        button_row.addWidget(self.logout_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(info_row)
        layout.addLayout(button_row)
        return box

    def _build_manual_group(self):
        box = QGroupBox("Manual Load")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        helper = QLabel(
            "Look up a Riot ID, inspect recent match data, and store the latest matches "
            "into Firestore."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)

        form = QFormLayout()
        self.game_name_input = QLineEdit()
        self.game_name_input.setPlaceholderText("Hide on bush")
        self.tag_line_input = QLineEdit()
        self.tag_line_input.setPlaceholderText("KR1")
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(500)
        self.count_input.setValue(5)
        self.count_input.setSuffix(" matches")

        form.addRow("Game Name", self.game_name_input)
        form.addRow("Tag Line", self.tag_line_input)
        form.addRow("Recent Matches", self.count_input)
        layout.addLayout(form)

        button_grid = QGridLayout()
        self.load_btn = QPushButton("1. Fetch PUUID")
        self.load_btn.clicked.connect(self.fetch_puuid)
        self.match_btn = QPushButton("2. Fetch Match IDs")
        self.match_btn.clicked.connect(self.fetch_match_ids)
        self.detail_btn = QPushButton("3. Fetch First Match Detail")
        self.detail_btn.clicked.connect(self.fetch_match_detail)
        self.store_btn = QPushButton("4. Store Recent Matches")
        self.store_btn.clicked.connect(self.store_recent_matches)

        button_grid.addWidget(self.load_btn, 0, 0)
        button_grid.addWidget(self.match_btn, 0, 1)
        button_grid.addWidget(self.detail_btn, 1, 0)
        button_grid.addWidget(self.store_btn, 1, 1)
        layout.addLayout(button_grid)
        layout.addStretch(1)
        return box

    def _build_account_group(self):
        box = QGroupBox("Stored Accounts")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        helper = QLabel(
            "Search stored Riot IDs and bulk refresh tiers or store recent matches for "
            "selected accounts."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)

        search_row = QHBoxLayout()
        self.account_keyword_input = QLineEdit()
        self.account_keyword_input.setPlaceholderText("Search by stored game name")
        self.account_keyword_input.returnPressed.connect(self.search_stored_accounts)
        self.account_list_all_btn = QPushButton("Load All")
        self.account_list_all_btn.clicked.connect(self.load_all_stored_accounts)
        self.account_search_btn = QPushButton("Search")
        self.account_search_btn.clicked.connect(self.search_stored_accounts)
        search_row.addWidget(self.account_keyword_input, 1)
        search_row.addWidget(self.account_list_all_btn)
        search_row.addWidget(self.account_search_btn)
        layout.addLayout(search_row)

        selection_row = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.check_all_accounts)
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.uncheck_all_accounts)
        selection_row.addWidget(self.select_all_btn)
        selection_row.addWidget(self.clear_selection_btn)
        selection_row.addStretch(1)
        layout.addLayout(selection_row)

        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.fill_manual_fields_from_item)
        layout.addWidget(self.account_list, 1)

        action_row = QGridLayout()
        self.store_selected_btn = QPushButton("Store Selected Matches")
        self.store_selected_btn.clicked.connect(self.store_selected_accounts)
        self.refresh_tier_btn = QPushButton("Refresh Selected Tiers")
        self.refresh_tier_btn.clicked.connect(self.refresh_selected_account_tiers)
        action_row.addWidget(self.store_selected_btn, 0, 0)
        action_row.addWidget(self.refresh_tier_btn, 0, 1)
        layout.addLayout(action_row)
        return box

    def _build_result_group(self):
        box = QGroupBox("Response")
        layout = QVBoxLayout(box)

        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box, 1)
        return box

    def _update_session_badge(self):
        username = self.current_user.get("username") or "unknown"
        role = "admin" if self.current_user.get("is_admin") else "user"
        self.session_label.setText(f"Signed in: {username} ({role})")

    def _update_server_label(self):
        self.api.refresh_urls()
        self.server_url_label.setText(f"Server: {self.api.api_base_url}")

    def _show_response(self, response, data):
        text = self.api.format_response_text(response, data)
        self.result_box.setText(text)
        if response.status_code == 401:
            self.status_label.setText("로그인 세션이 만료되었습니다. 다시 로그인해주세요.")
        elif response.status_code == 403:
            self.status_label.setText("Admin permission is required for this action.")
        elif response.ok:
            self.status_label.setText(f"Request completed: HTTP {response.status_code}")
        else:
            self.status_label.setText(f"Request failed: HTTP {response.status_code}")

    def _set_message(self, message):
        self.status_label.setText(message)
        self.result_box.setText(message)

    def fetch_puuid(self):
        self._update_server_label()
        game_name = self.game_name_input.text().strip()
        tag_line = self.tag_line_input.text().strip()

        if not game_name:
            self._set_message("Enter a game name first.")
            return
        if not tag_line:
            self._set_message("Enter a tag line first.")
            return

        try:
            response, data = self.api.fetch_puuid(game_name, tag_line)
            self._show_response(response, data)
            if response.status_code == 200 and data and "puuid" in data:
                self.current_puuid = data["puuid"]
                self.current_match_ids = []
            else:
                self.current_puuid = ""
                self.current_match_ids = []
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def fetch_match_ids(self):
        self._update_server_label()
        count = self.count_input.value()

        if not self.current_puuid:
            self._set_message("Fetch a PUUID first.")
            return

        try:
            response, data = self.api.fetch_match_ids(self.current_puuid, count)
            self._show_response(response, data)
            if response.status_code == 200 and data and "match_ids" in data:
                self.current_match_ids = data["match_ids"]
            else:
                self.current_match_ids = []
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def fetch_match_detail(self):
        self._update_server_label()
        if not self.current_match_ids:
            self._set_message("Fetch match IDs first.")
            return

        try:
            response, data = self.api.fetch_match_detail(self.current_match_ids[0])
            self._show_response(response, data)
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def store_recent_matches(self):
        self._update_server_label()
        game_name = self.game_name_input.text().strip()
        tag_line = self.tag_line_input.text().strip()
        count = self.count_input.value()

        if not game_name:
            self._set_message("Enter a game name first.")
            return
        if not tag_line:
            self._set_message("Enter a tag line first.")
            return

        try:
            response, data = self.api.store_recent_matches(game_name, tag_line, count)
            if response.ok:
                LocalApiCacheRepository.invalidate_after_loader_sync()
            self._show_response(response, data)
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def search_stored_accounts(self):
        self._update_server_label()
        keyword = self.account_keyword_input.text().strip()
        if not keyword:
            self._set_message("Enter a keyword to search stored accounts.")
            return

        try:
            response, data = self.api.search_accounts(keyword)
            self._show_response(response, data)
            self._populate_account_list(response, data, "No stored accounts matched.")
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def load_all_stored_accounts(self):
        self._update_server_label()
        try:
            response, data = self.api.list_accounts()
            self._show_response(response, data)
            self._populate_account_list(response, data, "No stored accounts found.")
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def _populate_account_list(self, response, data, empty_message):
        self.account_list.clear()
        if response.status_code != 200 or not data:
            return

        for account in data.get("accounts", []):
            label = (
                f"{account.get('game_name', '')}#{account.get('tag_line', '')}"
                f" | fetched at: {account.get('fetched_at', '-')}"
            )
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, account)
            self.account_list.addItem(item)

        if self.account_list.count() == 0:
            self._set_message(empty_message)

    def fill_manual_fields_from_item(self, item):
        account = item.data(Qt.UserRole) or {}
        self.game_name_input.setText(account.get("game_name", ""))
        self.tag_line_input.setText(account.get("tag_line", ""))
        self.status_label.setText("Selected Riot ID copied into the manual load fields.")

    def check_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Checked)
        self.status_label.setText("All listed accounts selected.")

    def uncheck_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Unchecked)
        self.status_label.setText("Selection cleared.")

    def _get_checked_accounts(self):
        accounts = []
        seen = set()

        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            if item.checkState() != Qt.Checked:
                continue
            account = item.data(Qt.UserRole) or {}
            game_name = (account.get("game_name") or "").strip()
            tag_line = (account.get("tag_line") or "").strip()
            if not game_name or not tag_line:
                continue
            key = (game_name.lower(), tag_line.lower())
            if key in seen:
                continue
            seen.add(key)
            accounts.append({"game_name": game_name, "tag_line": tag_line})

        return accounts

    def store_selected_accounts(self):
        self._update_server_label()
        count = self.count_input.value()
        accounts = self._get_checked_accounts()

        if not accounts:
            self._set_message("Select at least one account to store matches.")
            return

        try:
            response, data = self.api.store_selected_accounts(count, accounts)
            if response.ok:
                LocalApiCacheRepository.invalidate_after_loader_sync()
            self._show_response(response, data)
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def refresh_selected_account_tiers(self):
        self._update_server_label()
        accounts = self._get_checked_accounts()

        if not accounts:
            self._set_message("Select at least one account to refresh tiers.")
            return

        try:
            response, data = self.api.refresh_selected_tiers(accounts)
            if response.ok:
                LocalApiCacheRepository.invalidate_after_loader_sync()
            self._show_response(response, data)
            if response.status_code == 200:
                self.load_all_stored_accounts()
        except Exception as exc:
            self._set_message(f"Request error: {exc}")

    def open_scheduler_dialog(self):
        if self.scheduler_dialog is None:
            self.scheduler_dialog = RiotLoaderSchedulerDialog(self)
        self.scheduler_dialog.count_input.setValue(self.count_input.value())
        self.scheduler_dialog.show()
        self.scheduler_dialog.raise_()
        self.scheduler_dialog.activateWindow()

    def _close_aux_dialogs(self):
        if self.scheduler_dialog is not None:
            self.scheduler_dialog.close()
            self.scheduler_dialog = None

    def logout(self):
        answer = QMessageBox.question(
            self,
            "Confirm Logout",
            "End the current admin session and sign in again?",
        )
        if answer != QMessageBox.Yes:
            return

        self._close_aux_dialogs()
        clear_saved_session()
        self.current_user = {}
        self.current_puuid = ""
        self.current_match_ids = []
        self._update_session_badge()
        self._set_message("Signed out of the admin session.")

        current_user = ensure_admin_session(self)
        if not current_user:
            self.close()
            return

        self.current_user = current_user
        self._update_server_label()
        self._update_session_badge()
        self._set_message("Signed in again with a new admin session.")


def ensure_admin_session(parent=None):
    existing_token = team_app.load_auth_token().strip()
    login_dialog = LoginDialog(parent)
    session_notice = ""

    if existing_token:
        try:
            current_user = team_app.get_current_user()
            if current_user.get("is_admin"):
                return current_user
            clear_saved_session()
            session_notice = (
                "The saved session is still present but the current server no longer "
                "accepts it as an admin session. Please sign in again."
            )
            QMessageBox.warning(
                parent,
                "Admin Permission Required",
                "This tool can only be used with an admin account.",
            )
        except Exception:
            clear_saved_session()
            session_notice = (
                "로그인 세션이 만료되었습니다. 다시 로그인해주세요."
            )

    if session_notice:
        login_dialog.show_session_notice(session_notice)

    while True:
        if login_dialog.exec_() != LoginDialog.Accepted:
            return None

        current_user = login_dialog.current_user or {}
        if current_user.get("is_admin"):
            return current_user

        clear_saved_session()
        QMessageBox.warning(
            parent,
            "Admin Permission Required",
            "This tool can only be used with an admin account. Please sign in again.",
        )
        login_dialog.password_input.clear()


def main():
    app = QApplication(sys.argv)
    LocalApiCacheRepository.ensure_ready()
    load_style(app, team_app.load_theme_mode())

    current_user = ensure_admin_session()
    if not current_user:
        sys.exit(0)

    window = RiotLoaderWidget(current_user)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
