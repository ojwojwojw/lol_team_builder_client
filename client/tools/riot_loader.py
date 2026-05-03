import sys
from pathlib import Path
from pprint import pformat
from urllib.parse import urlencode

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domain.constants import ACCOUNT_SEARCH_LIMIT
from repositories.dataset_repository import load_server_base_url


class RiotLoaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Riot 전적 적재 도구")
        self.setGeometry(180, 120, 760, 880)
        self.current_puuid = ""
        self.current_match_ids = []
        self.api_base_url = ""

        layout = QVBoxLayout()

        self.server_url_label = QLabel()
        layout.addWidget(self.server_url_label)

        layout.addWidget(QLabel("수동 적재"))
        manual_row = QHBoxLayout()

        left_form = QVBoxLayout()
        left_form.addWidget(QLabel("게임 닉네임"))
        self.game_name_input = QLineEdit()
        left_form.addWidget(self.game_name_input)

        left_form.addWidget(QLabel("태그"))
        self.tag_line_input = QLineEdit()
        left_form.addWidget(self.tag_line_input)

        left_form.addWidget(QLabel("Riot API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        left_form.addWidget(self.api_key_input)

        left_form.addWidget(QLabel("최근 경기 수"))
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(500)
        self.count_input.setValue(5)
        left_form.addWidget(self.count_input)

        button_col = QVBoxLayout()
        self.load_btn = QPushButton("puuid 조회")
        self.load_btn.clicked.connect(self.fetch_puuid)
        button_col.addWidget(self.load_btn)

        self.match_btn = QPushButton("매치 ID 조회")
        self.match_btn.clicked.connect(self.fetch_match_ids)
        button_col.addWidget(self.match_btn)

        self.detail_btn = QPushButton("첫 경기 상세 조회")
        self.detail_btn.clicked.connect(self.fetch_match_detail)
        button_col.addWidget(self.detail_btn)

        self.store_btn = QPushButton("최근 경기 DB 적재")
        self.store_btn.clicked.connect(self.store_recent_matches)
        button_col.addWidget(self.store_btn)
        button_col.addStretch(1)

        manual_row.addLayout(left_form, 3)
        manual_row.addLayout(button_col, 2)
        layout.addLayout(manual_row)

        layout.addWidget(QLabel("저장된 계정 선택 적재"))
        search_row = QHBoxLayout()
        self.account_keyword_input = QLineEdit()
        self.account_keyword_input.setPlaceholderText("riot_account에서 닉네임 검색")
        self.account_list_all_btn = QPushButton("전체 불러오기")
        self.account_list_all_btn.clicked.connect(self.load_all_stored_accounts)
        self.account_search_btn = QPushButton("저장 계정 검색")
        self.account_search_btn.clicked.connect(self.search_stored_accounts)
        search_row.addWidget(self.account_keyword_input, 1)
        search_row.addWidget(self.account_list_all_btn)
        search_row.addWidget(self.account_search_btn)
        layout.addLayout(search_row)

        selection_row = QHBoxLayout()
        self.select_all_btn = QPushButton("전체 선택")
        self.select_all_btn.clicked.connect(self.check_all_accounts)
        selection_row.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("선택 해제")
        self.clear_selection_btn.clicked.connect(self.uncheck_all_accounts)
        selection_row.addWidget(self.clear_selection_btn)

        self.store_selected_btn = QPushButton("선택 계정만 적재")
        self.store_selected_btn.clicked.connect(self.store_selected_accounts)
        selection_row.addWidget(self.store_selected_btn)

        self.refresh_tier_selected_btn = QPushButton("선택 계정 티어만 갱신")
        self.refresh_tier_selected_btn.clicked.connect(self.refresh_selected_account_tiers)
        selection_row.addWidget(self.refresh_tier_selected_btn)

        selection_row.addStretch(1)
        layout.addLayout(selection_row)

        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.fill_manual_fields_from_item)
        layout.addWidget(self.account_list, 3)

        layout.addWidget(QLabel("응답 결과"))
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box, 4)

        self.setLayout(layout)
        self.refresh_api_urls()

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

    def fetch_puuid(self):
        self.refresh_api_urls()

        game_name = self.game_name_input.text().strip()
        tag_line = self.tag_line_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not game_name:
            self.result_box.setText("게임 닉네임을 입력해주세요.")
            return
        if not tag_line:
            self.result_box.setText("태그를 입력해주세요.")
            return
        if not api_key:
            self.result_box.setText("Riot API Key를 입력해주세요.")
            return

        payload = {
            "api_key": api_key,
            "game_name": game_name,
            "tag_line": tag_line,
        }

        try:
            response = requests.post(self.puuid_url, json=payload, timeout=30)
            data = self._show_response(response)
            if response.status_code == 200 and data and "puuid" in data:
                self.current_puuid = data["puuid"]
                self.current_match_ids = []
            else:
                self.current_puuid = ""
                self.current_match_ids = []
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")

    def fetch_match_ids(self):
        self.refresh_api_urls()

        api_key = self.api_key_input.text().strip()
        count = self.count_input.value()

        if not api_key:
            self.result_box.setText("Riot API Key를 입력해주세요.")
            return
        if not self.current_puuid:
            self.result_box.setText("먼저 puuid를 조회해주세요.")
            return

        payload = {
            "api_key": api_key,
            "puuid": self.current_puuid,
            "count": count,
        }

        try:
            response = requests.post(self.match_ids_url, json=payload, timeout=30)
            data = self._show_response(response)
            if response.status_code == 200 and data and "match_ids" in data:
                self.current_match_ids = data["match_ids"]
            else:
                self.current_match_ids = []
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")

    def fetch_match_detail(self):
        self.refresh_api_urls()

        api_key = self.api_key_input.text().strip()

        if not api_key:
            self.result_box.setText("Riot API Key를 입력해주세요.")
            return
        if not self.current_match_ids:
            self.result_box.setText("먼저 매치 ID를 조회해주세요.")
            return

        payload = {
            "api_key": api_key,
            "match_id": self.current_match_ids[0],
        }

        try:
            response = requests.post(self.match_detail_url, json=payload, timeout=30)
            self._show_response(response)
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")

    def store_recent_matches(self):
        self.refresh_api_urls()

        game_name = self.game_name_input.text().strip()
        tag_line = self.tag_line_input.text().strip()
        api_key = self.api_key_input.text().strip()
        count = self.count_input.value()

        if not game_name:
            self.result_box.setText("게임 닉네임을 입력해주세요.")
            return
        if not tag_line:
            self.result_box.setText("태그를 입력해주세요.")
            return
        if not api_key:
            self.result_box.setText("Riot API Key를 입력해주세요.")
            return

        payload = {
            "api_key": api_key,
            "game_name": game_name,
            "tag_line": tag_line,
            "count": count,
        }

        try:
            response = requests.post(self.store_matches_url, json=payload, timeout=60)
            self._show_response(response)
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")

    def search_stored_accounts(self):
        self.refresh_api_urls()
        keyword = self.account_keyword_input.text().strip()

        if not keyword:
            self.result_box.setText("저장된 계정을 찾을 검색어를 입력해주세요.")
            return

        url = f"{self.search_accounts_url}?{urlencode({'keyword': keyword, 'limit': ACCOUNT_SEARCH_LIMIT})}"

        try:
            response = requests.get(url, timeout=30)
            data = self._show_response(response)
            self._populate_account_list(response, data, "검색된 저장 계정이 없습니다.")
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")

    def load_all_stored_accounts(self):
        self.refresh_api_urls()
        url = f"{self.list_accounts_url}?{urlencode({'limit': ACCOUNT_SEARCH_LIMIT})}"

        try:
            response = requests.get(url, timeout=30)
            data = self._show_response(response)
            self._populate_account_list(response, data, "불러온 저장 계정이 없습니다.")
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")

    def _populate_account_list(self, response, data, empty_message):
        self.account_list.clear()

        if response.status_code != 200 or not data:
            return

        for account in data.get("accounts", []):
            label = (
                f"{account.get('game_name', '')}#{account.get('tag_line', '')}"
                f"  |  조회시각: {account.get('fetched_at', '-')}"
            )
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, account)
            self.account_list.addItem(item)

        if self.account_list.count() == 0:
            self.result_box.setText(empty_message)

    def fill_manual_fields_from_item(self, item):
        account = item.data(Qt.UserRole) or {}
        self.game_name_input.setText(account.get("game_name", ""))
        self.tag_line_input.setText(account.get("tag_line", ""))

    def check_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Checked)

    def uncheck_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Unchecked)

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
            accounts.append({
                "game_name": game_name,
                "tag_line": tag_line,
            })

        return accounts

    def store_selected_accounts(self):
        self.refresh_api_urls()
        api_key = self.api_key_input.text().strip()
        count = self.count_input.value()
        accounts = self._get_checked_accounts()

        if not api_key:
            self.result_box.setText("Riot API Key를 입력해주세요.")
            return
        if not accounts:
            self.result_box.setText("적재할 저장 계정을 하나 이상 체크해주세요.")
            return

        payload = {
            "api_key": api_key,
            "count": count,
            "accounts": accounts,
        }

        try:
            response = requests.post(
                self.store_selected_accounts_url,
                json=payload,
                timeout=300,
            )
            data = self._show_response(response)
            if response.status_code == 200 and data:
                self._set_result_data(data)
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")

    def refresh_selected_account_tiers(self):
        self.refresh_api_urls()
        api_key = self.api_key_input.text().strip()
        accounts = self._get_checked_accounts()

        if not api_key:
            self.result_box.setText("Riot API Key를 입력해주세요.")
            return
        if not accounts:
            self.result_box.setText("티어를 갱신할 저장 계정을 하나 이상 체크해주세요.")
            return

        payload = {
            "api_key": api_key,
            "accounts": accounts,
        }

        try:
            response = requests.post(
                self.refresh_selected_tiers_url,
                json=payload,
                timeout=300,
            )
            data = self._show_response(response)
            if response.status_code == 200 and data:
                self._set_result_data(data)
                self.load_all_stored_accounts()
        except Exception as exc:
            self.result_box.setText(f"오류: {exc}")


def main():
    app = QApplication(sys.argv)
    window = RiotLoaderWidget()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
