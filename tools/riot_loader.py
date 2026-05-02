import sys
from pprint import pformat
from pathlib import Path

import requests
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from service.dataset_service import load_server_base_url


class RiotLoaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Riot 전적 적재 도구")
        self.setGeometry(200, 200, 620, 700)
        self.current_puuid = ""
        self.current_match_ids = []

        layout = QVBoxLayout()

        self.server_url_label = QLabel()
        layout.addWidget(self.server_url_label)

        layout.addWidget(QLabel("게임 닉네임"))
        self.game_name_input = QLineEdit()
        layout.addWidget(self.game_name_input)

        layout.addWidget(QLabel("태그"))
        self.tag_line_input = QLineEdit()
        layout.addWidget(self.tag_line_input)

        layout.addWidget(QLabel("Riot API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.api_key_input)

        layout.addWidget(QLabel("최근 경기 수"))
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(500)
        self.count_input.setValue(5)
        layout.addWidget(self.count_input)

        self.load_btn = QPushButton("puuid 조회")
        self.load_btn.clicked.connect(self.fetch_puuid)
        layout.addWidget(self.load_btn)

        self.match_btn = QPushButton("매치 ID 조회")
        self.match_btn.clicked.connect(self.fetch_match_ids)
        layout.addWidget(self.match_btn)

        self.detail_btn = QPushButton("첫 경기 상세 조회")
        self.detail_btn.clicked.connect(self.fetch_match_detail)
        layout.addWidget(self.detail_btn)

        self.store_btn = QPushButton("최근 경기 DB 적재")
        self.store_btn.clicked.connect(self.store_recent_matches)
        layout.addWidget(self.store_btn)

        layout.addWidget(QLabel("응답 결과"))
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)

        self.setLayout(layout)
        self.refresh_api_urls()

    def refresh_api_urls(self):
        self.api_base_url = load_server_base_url().rstrip("/")
        self.server_url_label.setText(f"서버 주소: {self.api_base_url}")
        self.puuid_url = f"{self.api_base_url}/get_puuid"
        self.match_ids_url = f"{self.api_base_url}/get_match_ids"
        self.match_detail_url = f"{self.api_base_url}/get_match_detail"
        self.store_matches_url = f"{self.api_base_url}/store_recent_matches"

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


def main():
    app = QApplication(sys.argv)
    window = RiotLoaderWidget()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
