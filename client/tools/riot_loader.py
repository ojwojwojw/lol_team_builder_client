import sys
from pathlib import Path
from pprint import pformat
from urllib.parse import urlencode

import requests
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
from domain.constants import ACCOUNT_SEARCH_LIMIT
from repositories.dataset_repository import load_server_base_url
from ui.login_dialog import LoginDialog
from ui.style_loader import load_style


class RiotLoaderWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user or {}
        self.current_puuid = ""
        self.current_match_ids = []
        self.api_base_url = ""
        self.setWindowTitle("Riot 적재 도구")
        self.setMinimumSize(980, 780)
        self._create_ui()
        self.refresh_api_urls()
        self._update_session_badge()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        root.addWidget(self._build_header_card())

        content_grid = QGridLayout()
        content_grid.setHorizontalSpacing(14)
        content_grid.setVerticalSpacing(14)
        content_grid.addWidget(self._build_manual_group(), 0, 0)
        content_grid.addWidget(self._build_account_group(), 0, 1)
        content_grid.setColumnStretch(0, 1)
        content_grid.setColumnStretch(1, 1)
        root.addLayout(content_grid)

        root.addWidget(self._build_result_group(), 1)

    def _build_header_card(self):
        box = QGroupBox("관리자 세션")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        title = QLabel("Riot 전적 적재 콘솔")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "JWT 로그인이 필요하며, 관리자 계정만 Riot 적재 및 갱신 API를 호출할 수 있습니다."
        )
        subtitle.setWordWrap(True)

        info_row = QHBoxLayout()
        self.server_url_label = QLabel()
        self.session_label = QLabel()
        self.session_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_row.addWidget(self.server_url_label, 1)
        info_row.addWidget(self.session_label, 1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.relogin_btn = QPushButton("관리자 다시 로그인")
        self.relogin_btn.clicked.connect(self.reauthenticate)
        button_row.addWidget(self.relogin_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(info_row)
        layout.addLayout(button_row)
        return box

    def _build_manual_group(self):
        box = QGroupBox("수동 적재")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        helper = QLabel(
            "하나의 Riot ID를 조회하고 최근 경기 데이터를 확인한 뒤 DB에 적재합니다."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)

        form = QFormLayout()
        self.game_name_input = QLineEdit()
        self.game_name_input.setPlaceholderText("예: Hide on bush")
        self.tag_line_input = QLineEdit()
        self.tag_line_input.setPlaceholderText("예: KR1")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Riot API Key 입력")
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(500)
        self.count_input.setValue(5)
        self.count_input.setSuffix(" 경기")

        form.addRow("게임 닉네임", self.game_name_input)
        form.addRow("태그", self.tag_line_input)
        form.addRow("Riot API Key", self.api_key_input)
        form.addRow("최근 경기 수", self.count_input)
        layout.addLayout(form)

        button_grid = QGridLayout()
        self.load_btn = QPushButton("1. PUUID 조회")
        self.load_btn.clicked.connect(self.fetch_puuid)
        self.match_btn = QPushButton("2. 매치 ID 조회")
        self.match_btn.clicked.connect(self.fetch_match_ids)
        self.detail_btn = QPushButton("3. 첫 경기 상세 조회")
        self.detail_btn.clicked.connect(self.fetch_match_detail)
        self.store_btn = QPushButton("4. 최근 경기 DB 적재")
        self.store_btn.clicked.connect(self.store_recent_matches)

        button_grid.addWidget(self.load_btn, 0, 0)
        button_grid.addWidget(self.match_btn, 0, 1)
        button_grid.addWidget(self.detail_btn, 1, 0)
        button_grid.addWidget(self.store_btn, 1, 1)
        layout.addLayout(button_grid)
        layout.addStretch(1)
        return box

    def _build_account_group(self):
        box = QGroupBox("저장된 계정 일괄 적재")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        helper = QLabel(
            "저장된 Riot ID를 검색하고 여러 계정을 선택해 최근 경기 적재 또는 티어 갱신을 실행합니다."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)

        search_row = QHBoxLayout()
        self.account_keyword_input = QLineEdit()
        self.account_keyword_input.setPlaceholderText("저장된 게임 닉네임으로 검색")
        self.account_keyword_input.returnPressed.connect(self.search_stored_accounts)
        self.account_list_all_btn = QPushButton("전체 불러오기")
        self.account_list_all_btn.clicked.connect(self.load_all_stored_accounts)
        self.account_search_btn = QPushButton("검색")
        self.account_search_btn.clicked.connect(self.search_stored_accounts)
        search_row.addWidget(self.account_keyword_input, 1)
        search_row.addWidget(self.account_list_all_btn)
        search_row.addWidget(self.account_search_btn)
        layout.addLayout(search_row)

        selection_row = QHBoxLayout()
        self.select_all_btn = QPushButton("전체 선택")
        self.select_all_btn.clicked.connect(self.check_all_accounts)
        self.clear_selection_btn = QPushButton("선택 해제")
        self.clear_selection_btn.clicked.connect(self.uncheck_all_accounts)
        selection_row.addWidget(self.select_all_btn)
        selection_row.addWidget(self.clear_selection_btn)
        selection_row.addStretch(1)
        layout.addLayout(selection_row)

        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.fill_manual_fields_from_item)
        layout.addWidget(self.account_list, 1)

        action_row = QGridLayout()
        self.store_selected_btn = QPushButton("선택 계정 적재")
        self.store_selected_btn.clicked.connect(self.store_selected_accounts)
        self.refresh_tier_selected_btn = QPushButton("선택 계정 티어 갱신")
        self.refresh_tier_selected_btn.clicked.connect(self.refresh_selected_account_tiers)
        action_row.addWidget(self.store_selected_btn, 0, 0)
        action_row.addWidget(self.refresh_tier_selected_btn, 0, 1)
        layout.addLayout(action_row)
        return box

    def _build_result_group(self):
        box = QGroupBox("응답 결과")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        self.status_label = QLabel("준비 완료")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box, 1)
        return box

    def refresh_api_urls(self):
        self.api_base_url = load_server_base_url().rstrip("/")
        self.server_url_label.setText(f"서버 주소: {self.api_base_url}")
        self.puuid_url = f"{self.api_base_url}/get_puuid"
        self.match_ids_url = f"{self.api_base_url}/get_match_ids"
        self.match_detail_url = f"{self.api_base_url}/get_match_detail"
        self.store_matches_url = f"{self.api_base_url}/store_recent_matches"
        self.list_accounts_url = f"{self.api_base_url}/accounts"
        self.search_accounts_url = f"{self.api_base_url}/accounts/search"
        self.store_selected_accounts_url = (
            f"{self.api_base_url}/store_recent_matches/by-stored-accounts"
        )
        self.refresh_selected_tiers_url = (
            f"{self.api_base_url}/refresh_account_tier/by-stored-accounts"
        )

    def _update_session_badge(self):
        username = self.current_user.get("username") or "unknown"
        role = "관리자" if self.current_user.get("is_admin") else "일반 사용자"
        self.session_label.setText(f"로그인 사용자: {username} ({role})")

    def _auth_headers(self):
        token = team_app.load_auth_token().strip()
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _request(self, method, url, *, payload=None, timeout=30):
        response = requests.request(
            method,
            url,
            json=payload,
            headers=self._auth_headers(),
            timeout=timeout,
        )
        data = self._show_response(response)
        if response.status_code == 401:
            team_app.clear_auth_token()
            self.status_label.setText("인증이 만료되었습니다. 다시 로그인해주세요.")
        elif response.status_code == 403:
            self.status_label.setText("이 작업은 관리자 권한이 필요합니다.")
        elif response.ok:
            self.status_label.setText(f"요청 완료: HTTP {response.status_code}")
        else:
            self.status_label.setText(f"요청 실패: HTTP {response.status_code}")
        return response, data

    def _show_response(self, response):
        try:
            data = response.json()
        except Exception:
            self.result_box.setText(f"HTTP {response.status_code}\n\n{response.text}")
            return None

        self.result_box.setText(
            f"HTTP {response.status_code}\n\n{pformat(data, sort_dicts=False)}"
        )
        return data

    def _set_result_data(self, data):
        self.result_box.setText(pformat(data, sort_dicts=False))

    def _set_validation_message(self, message):
        self.status_label.setText(message)
        self.result_box.setText(message)

    def fetch_puuid(self):
        self.refresh_api_urls()

        game_name = self.game_name_input.text().strip()
        tag_line = self.tag_line_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not game_name:
            self._set_validation_message("게임 닉네임을 먼저 입력해주세요.")
            return
        if not tag_line:
            self._set_validation_message("태그를 먼저 입력해주세요.")
            return
        if not api_key:
            self._set_validation_message("Riot API Key를 먼저 입력해주세요.")
            return

        payload = {
            "api_key": api_key,
            "game_name": game_name,
            "tag_line": tag_line,
        }

        try:
            response, data = self._request("POST", self.puuid_url, payload=payload, timeout=30)
            if response.status_code == 200 and data and "puuid" in data:
                self.current_puuid = data["puuid"]
                self.current_match_ids = []
            else:
                self.current_puuid = ""
                self.current_match_ids = []
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def fetch_match_ids(self):
        self.refresh_api_urls()

        api_key = self.api_key_input.text().strip()
        count = self.count_input.value()

        if not api_key:
            self._set_validation_message("Riot API Key를 먼저 입력해주세요.")
            return
        if not self.current_puuid:
            self._set_validation_message("먼저 PUUID를 조회해주세요.")
            return

        payload = {
            "api_key": api_key,
            "puuid": self.current_puuid,
            "count": count,
        }

        try:
            response, data = self._request("POST", self.match_ids_url, payload=payload, timeout=30)
            if response.status_code == 200 and data and "match_ids" in data:
                self.current_match_ids = data["match_ids"]
            else:
                self.current_match_ids = []
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def fetch_match_detail(self):
        self.refresh_api_urls()

        api_key = self.api_key_input.text().strip()

        if not api_key:
            self._set_validation_message("Riot API Key를 먼저 입력해주세요.")
            return
        if not self.current_match_ids:
            self._set_validation_message("먼저 매치 ID를 조회해주세요.")
            return

        payload = {
            "api_key": api_key,
            "match_id": self.current_match_ids[0],
        }

        try:
            self._request("POST", self.match_detail_url, payload=payload, timeout=30)
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def store_recent_matches(self):
        self.refresh_api_urls()

        game_name = self.game_name_input.text().strip()
        tag_line = self.tag_line_input.text().strip()
        api_key = self.api_key_input.text().strip()
        count = self.count_input.value()

        if not game_name:
            self._set_validation_message("게임 닉네임을 먼저 입력해주세요.")
            return
        if not tag_line:
            self._set_validation_message("태그를 먼저 입력해주세요.")
            return
        if not api_key:
            self._set_validation_message("Riot API Key를 먼저 입력해주세요.")
            return

        payload = {
            "api_key": api_key,
            "game_name": game_name,
            "tag_line": tag_line,
            "count": count,
        }

        try:
            self._request("POST", self.store_matches_url, payload=payload, timeout=60)
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def search_stored_accounts(self):
        self.refresh_api_urls()
        keyword = self.account_keyword_input.text().strip()

        if not keyword:
            self._set_validation_message("저장된 계정을 검색할 키워드를 입력해주세요.")
            return

        url = f"{self.search_accounts_url}?{urlencode({'keyword': keyword, 'limit': ACCOUNT_SEARCH_LIMIT})}"

        try:
            response, data = self._request("GET", url, timeout=30)
            self._populate_account_list(response, data, "검색된 저장 계정이 없습니다.")
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def load_all_stored_accounts(self):
        self.refresh_api_urls()
        url = f"{self.list_accounts_url}?{urlencode({'limit': ACCOUNT_SEARCH_LIMIT})}"

        try:
            response, data = self._request("GET", url, timeout=30)
            self._populate_account_list(response, data, "저장된 계정이 없습니다.")
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def _populate_account_list(self, response, data, empty_message):
        self.account_list.clear()

        if response.status_code != 200 or not data:
            return

        for account in data.get("accounts", []):
            label = (
                f"{account.get('game_name', '')}#{account.get('tag_line', '')}"
                f"  |  조회 시각: {account.get('fetched_at', '-')}"
            )
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, account)
            self.account_list.addItem(item)

        if self.account_list.count() == 0:
            self.result_box.setText(empty_message)
            self.status_label.setText(empty_message)
        else:
            self.status_label.setText(
                f"저장된 계정 {self.account_list.count()}개를 불러왔습니다."
            )

    def fill_manual_fields_from_item(self, item):
        account = item.data(Qt.UserRole) or {}
        self.game_name_input.setText(account.get("game_name", ""))
        self.tag_line_input.setText(account.get("tag_line", ""))
        self.status_label.setText("선택한 Riot ID를 수동 적재 입력칸에 채웠습니다.")

    def check_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Checked)
        self.status_label.setText("목록의 모든 계정을 선택했습니다.")

    def uncheck_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Unchecked)
        self.status_label.setText("계정 선택을 모두 해제했습니다.")

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
        self.refresh_api_urls()
        api_key = self.api_key_input.text().strip()
        count = self.count_input.value()
        accounts = self._get_checked_accounts()

        if not api_key:
            self._set_validation_message("Riot API Key를 먼저 입력해주세요.")
            return
        if not accounts:
            self._set_validation_message("적재할 저장 계정을 하나 이상 선택해주세요.")
            return

        payload = {
            "api_key": api_key,
            "count": count,
            "accounts": accounts,
        }

        try:
            response, data = self._request(
                "POST",
                self.store_selected_accounts_url,
                payload=payload,
                timeout=300,
            )
            if response.status_code == 200 and data:
                self._set_result_data(data)
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def refresh_selected_account_tiers(self):
        self.refresh_api_urls()
        api_key = self.api_key_input.text().strip()
        accounts = self._get_checked_accounts()

        if not api_key:
            self._set_validation_message("Riot API Key를 먼저 입력해주세요.")
            return
        if not accounts:
            self._set_validation_message("티어를 갱신할 저장 계정을 하나 이상 선택해주세요.")
            return

        payload = {
            "api_key": api_key,
            "accounts": accounts,
        }

        try:
            response, data = self._request(
                "POST",
                self.refresh_selected_tiers_url,
                payload=payload,
                timeout=300,
            )
            if response.status_code == 200 and data:
                self._set_result_data(data)
                self.load_all_stored_accounts()
        except Exception as exc:
            self._set_validation_message(f"요청 오류: {exc}")

    def reauthenticate(self):
        current_user = ensure_admin_session(self)
        if current_user:
            self.current_user = current_user
            self.refresh_api_urls()
            self._update_session_badge()
            self.status_label.setText("관리자 세션을 새로고침했습니다.")


def ensure_admin_session(parent=None):
    existing_token = team_app.load_auth_token().strip()

    if existing_token:
        try:
            current_user = team_app.get_current_user()
            if current_user.get("is_admin"):
                return current_user
            team_app.clear_auth_token()
            QMessageBox.warning(
                parent,
                "관리자 권한 필요",
                "이 도구는 관리자 계정만 사용할 수 있습니다.",
            )
        except Exception:
            team_app.clear_auth_token()

    login_dialog = LoginDialog(parent)
    while True:
        if login_dialog.exec_() != LoginDialog.Accepted:
            return None

        current_user = login_dialog.current_user or {}
        if current_user.get("is_admin"):
            return current_user

        team_app.clear_auth_token()
        QMessageBox.warning(
            parent,
            "관리자 권한 필요",
            "이 도구는 관리자 계정만 사용할 수 있습니다. 관리자 계정으로 로그인해주세요.",
        )
        login_dialog.password_input.clear()


def main():
    app = QApplication(sys.argv)
    load_style(app, team_app.load_theme_mode())

    current_user = ensure_admin_session()
    if not current_user:
        sys.exit(0)

    window = RiotLoaderWidget(current_user)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
