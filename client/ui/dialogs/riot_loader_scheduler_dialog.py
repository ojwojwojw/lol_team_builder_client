from __future__ import annotations

from datetime import datetime, timedelta
from pprint import pformat

from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
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
)

from tools.riot_loader_api import RiotLoaderApi


class BatchStoreWorker(QThread):
    finished_with_result = pyqtSignal(dict)
    failed_with_error = pyqtSignal(str)

    def __init__(self, api: RiotLoaderApi, count: int, accounts: list[dict]):
        super().__init__()
        self.api = api
        self.count = count
        self.accounts = list(accounts)

    def run(self):
        try:
            response, data = self.api.store_selected_accounts(
                self.count,
                self.accounts,
            )
            self.finished_with_result.emit(
                {
                    "status_code": response.status_code,
                    "ok": response.ok,
                    "data": data,
                    "text": self.api.format_response_text(response, data),
                }
            )
        except Exception as exc:
            self.failed_with_error.emit(str(exc))


class RiotLoaderSchedulerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = RiotLoaderApi()
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.setSingleShot(True)
        self.scheduler_timer.timeout.connect(self._run_scheduled_batch)
        self.scheduler_worker = None
        self.scheduler_enabled = False
        self.scheduler_accounts = []
        self.scheduler_index = 0
        self.scheduler_run_count = 0
        self.scheduler_next_run_at = None
        self.scheduler_current_batch = []

        self.setWindowTitle("배치 스케줄러")
        self.resize(960, 760)
        self._create_ui()
        self._update_status("스케줄러 대기 중")
        self._update_target_summary()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        root.addWidget(self._build_intro_group())

        content_grid = QGridLayout()
        content_grid.setHorizontalSpacing(14)
        content_grid.addWidget(self._build_account_group(), 0, 0)
        content_grid.addWidget(self._build_scheduler_group(), 0, 1)
        content_grid.setColumnStretch(0, 1)
        content_grid.setColumnStretch(1, 1)
        root.addLayout(content_grid)

        root.addWidget(self._build_result_group(), 1)

    def _build_intro_group(self):
        box = QGroupBox("배치 스케줄러")
        layout = QVBoxLayout(box)

        guide = QLabel(
            "저장된 계정을 이 화면에서 직접 선택하고, 작은 배치로 나누어 일정 간격마다 순환 적재합니다. "
            "Riot API 키는 서버 환경변수에서 관리됩니다."
        )
        guide.setWordWrap(True)
        layout.addWidget(guide)
        return box

    def _build_account_group(self):
        box = QGroupBox("대상 계정 선택")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        search_row = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("저장된 게임 닉네임으로 검색")
        self.keyword_input.returnPressed.connect(self.search_accounts)
        self.load_all_btn = QPushButton("전체 불러오기")
        self.load_all_btn.clicked.connect(self.load_all_accounts)
        self.search_btn = QPushButton("검색")
        self.search_btn.clicked.connect(self.search_accounts)
        search_row.addWidget(self.keyword_input, 1)
        search_row.addWidget(self.load_all_btn)
        search_row.addWidget(self.search_btn)
        layout.addLayout(search_row)

        selection_row = QHBoxLayout()
        self.select_all_btn = QPushButton("전체 선택")
        self.select_all_btn.clicked.connect(self.check_all_accounts)
        self.clear_btn = QPushButton("선택 해제")
        self.clear_btn.clicked.connect(self.uncheck_all_accounts)
        selection_row.addWidget(self.select_all_btn)
        selection_row.addWidget(self.clear_btn)
        selection_row.addStretch(1)
        layout.addLayout(selection_row)

        self.account_list = QListWidget()
        self.account_list.itemChanged.connect(self._update_target_summary)
        layout.addWidget(self.account_list, 1)
        return box

    def _build_scheduler_group(self):
        box = QGroupBox("실행 설정 및 상태")
        layout = QVBoxLayout(box)
        layout.setSpacing(12)

        form = QFormLayout()
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(500)
        self.count_input.setValue(5)
        self.count_input.setSuffix(" 경기")

        self.batch_size_input = QSpinBox()
        self.batch_size_input.setMinimum(1)
        self.batch_size_input.setMaximum(20)
        self.batch_size_input.setValue(2)
        self.batch_size_input.setSuffix(" 계정")

        self.interval_input = QSpinBox()
        self.interval_input.setMinimum(5)
        self.interval_input.setMaximum(1440)
        self.interval_input.setValue(10)
        self.interval_input.setSuffix(" 분")

        form.addRow("최근 경기 수", self.count_input)
        form.addRow("배치 크기", self.batch_size_input)
        form.addRow("실행 간격", self.interval_input)
        layout.addLayout(form)

        button_row = QHBoxLayout()
        self.start_btn = QPushButton("스케줄러 시작")
        self.start_btn.clicked.connect(self.start_scheduler)
        self.stop_btn = QPushButton("스케줄러 중지")
        self.stop_btn.clicked.connect(self.stop_scheduler)
        self.stop_btn.setEnabled(False)
        button_row.addWidget(self.start_btn)
        button_row.addWidget(self.stop_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.target_label = QLabel("선택된 계정 0개")
        self.target_label.setWordWrap(True)
        self.progress_label = QLabel("진행 정보 없음")
        self.progress_label.setWordWrap(True)
        self.next_run_label = QLabel("다음 실행 예정 없음")
        self.next_run_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addWidget(self.target_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.next_run_label)
        layout.addStretch(1)
        return box

    def _build_result_group(self):
        box = QGroupBox("응답 결과")
        layout = QVBoxLayout(box)
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)
        return box

    def _update_status(self, message: str):
        self.status_label.setText(message)

    def _update_controls(self):
        self.start_btn.setEnabled(not self.scheduler_enabled)
        self.stop_btn.setEnabled(self.scheduler_enabled)

    def _update_target_summary(self):
        self.target_label.setText(f"선택된 계정 {len(self._get_checked_accounts())}개")

    def _format_next_run(self):
        if not self.scheduler_next_run_at:
            return "다음 실행 예정 없음"
        return self.scheduler_next_run_at.strftime("%Y-%m-%d %H:%M:%S")

    def _show_result(self, text: str):
        self.result_box.setText(text)

    def search_accounts(self):
        keyword = self.keyword_input.text().strip()
        if not keyword:
            self._show_result("검색어를 입력해주세요.")
            return

        try:
            response, data = self.api.search_accounts(keyword)
            self._show_result(self.api.format_response_text(response, data))
            self._populate_account_list(response, data, "검색된 저장 계정이 없습니다.")
        except Exception as exc:
            self._show_result(f"요청 오류: {exc}")

    def load_all_accounts(self):
        try:
            response, data = self.api.list_accounts()
            self._show_result(self.api.format_response_text(response, data))
            self._populate_account_list(response, data, "저장된 계정이 없습니다.")
        except Exception as exc:
            self._show_result(f"요청 오류: {exc}")

    def _populate_account_list(self, response, data, empty_message):
        self.account_list.blockSignals(True)
        self.account_list.clear()

        if response.status_code == 200 and data:
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

        self.account_list.blockSignals(False)

        if self.account_list.count() == 0:
            self._show_result(empty_message)
        self._update_target_summary()

    def check_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Checked)
        self._update_target_summary()

    def uncheck_all_accounts(self):
        for index in range(self.account_list.count()):
            self.account_list.item(index).setCheckState(Qt.Unchecked)
        self._update_target_summary()

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

    def _build_scheduler_batch(self):
        total_accounts = len(self.scheduler_accounts)
        if total_accounts == 0:
            return []

        batch_size = min(self.batch_size_input.value(), total_accounts)
        batch = []

        for _ in range(batch_size):
            batch.append(self.scheduler_accounts[self.scheduler_index])
            self.scheduler_index = (self.scheduler_index + 1) % total_accounts

        return batch

    def start_scheduler(self):
        if self.scheduler_enabled:
            self._update_status("스케줄러가 이미 실행 중입니다.")
            return

        accounts = self._get_checked_accounts()
        if not accounts:
            QMessageBox.warning(self, "입력 오류", "대상 계정을 하나 이상 선택해주세요.")
            return

        self.scheduler_accounts = list(accounts)
        self.scheduler_index = 0
        self.scheduler_run_count = 0
        self.scheduler_enabled = True
        self.scheduler_current_batch = []
        self.scheduler_next_run_at = None
        self._update_controls()
        self._update_target_summary()
        self._update_status("스케줄러를 시작했습니다. 첫 배치를 바로 실행합니다.")
        self.progress_label.setText(
            f"대상 계정 {len(accounts)}개, 배치 크기 {self.batch_size_input.value()}개, 실행 간격 {self.interval_input.value()}분"
        )
        self.next_run_label.setText("첫 배치 즉시 실행")
        self._run_scheduled_batch()

    def stop_scheduler(self):
        self.scheduler_enabled = False
        self.scheduler_timer.stop()
        self.scheduler_next_run_at = None
        self._update_controls()

        if self.scheduler_worker and self.scheduler_worker.isRunning():
            self._update_status("현재 배치가 끝나면 스케줄러를 중지합니다.")
        else:
            self._update_status("스케줄러를 중지했습니다.")
            self.progress_label.setText("진행 정보 없음")
            self.next_run_label.setText("다음 실행 예정 없음")

    def _run_scheduled_batch(self):
        if not self.scheduler_enabled:
            return
        if self.scheduler_worker and self.scheduler_worker.isRunning():
            return

        self.scheduler_current_batch = self._build_scheduler_batch()
        if not self.scheduler_current_batch:
            self.stop_scheduler()
            self._show_result("스케줄러 대상 계정을 찾지 못했습니다.")
            return

        self.scheduler_run_count += 1
        batch_names = ", ".join(
            f"{account['game_name']}#{account['tag_line']}"
            for account in self.scheduler_current_batch
        )
        self._update_status(f"{self.scheduler_run_count}회차 배치를 실행 중입니다.")
        self.progress_label.setText(
            f"이번 배치 {len(self.scheduler_current_batch)}개 계정: {batch_names}"
        )

        self.scheduler_worker = BatchStoreWorker(
            self.api,
            self.count_input.value(),
            self.scheduler_current_batch,
        )
        self.scheduler_worker.finished_with_result.connect(self._handle_scheduler_result)
        self.scheduler_worker.failed_with_error.connect(self._handle_scheduler_error)
        self.scheduler_worker.start()

    def _schedule_next_batch(self):
        if not self.scheduler_enabled:
            return

        interval_minutes = self.interval_input.value()
        self.scheduler_next_run_at = datetime.now() + timedelta(minutes=interval_minutes)
        self.scheduler_timer.start(interval_minutes * 60 * 1000)
        self._update_status(f"다음 배치는 {self._format_next_run()}에 실행됩니다.")
        self.next_run_label.setText(f"다음 실행 예정: {self._format_next_run()}")

    def _handle_scheduler_result(self, result: dict):
        self.scheduler_worker = None
        self._show_result(result.get("text", pformat(result)))

        status_code = int(result.get("status_code", 0) or 0)
        payload = result.get("data") or {}
        if status_code == 401:
            self.stop_scheduler()
            self._update_status("인증 만료로 스케줄러를 중지했습니다.")
            return
        if status_code == 403:
            self.stop_scheduler()
            self._update_status("권한 오류로 스케줄러를 중지했습니다.")
            return
        if status_code >= 400:
            self.stop_scheduler()
            self._update_status(f"요청 실패로 스케줄러를 중지했습니다. HTTP {status_code}")
            return

        stored_total = int(payload.get("stored_match_total", 0) or 0)
        self.progress_label.setText(
            f"{self.scheduler_run_count}회차 완료, 신규 경기 {stored_total}건"
        )
        self._schedule_next_batch()

    def _handle_scheduler_error(self, error_message: str):
        self.scheduler_worker = None
        self.stop_scheduler()
        self._show_result(f"스케줄러 오류: {error_message}")

    def closeEvent(self, event):
        self.scheduler_enabled = False
        self.scheduler_timer.stop()
        super().closeEvent(event)
