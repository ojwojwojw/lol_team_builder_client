from __future__ import annotations

import json

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from tools.riot_loader_api import RiotLoaderApi


def format_bytes(num_bytes: int) -> str:
    """바이트 수를 사람이 읽기 쉬운 단위 문자열로 변환한다."""
    value = float(num_bytes)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


class FirestoreAdminDialog(QDialog):
    DELETABLE_BY_AGE = {"matches", "match_participants"}
    DELETE_SELECTED_CONFIRM_TEXT = "진짜 선택문서 삭제를 수행합니다"
    CLEAR_COLLECTION_CONFIRM_TEXT = "진짜 현재 컬렉션 삭제를 수행합니다"
    DELETE_OLDER_CONFIRM_TEXT = "진짜 기간기준 문서 삭제를 수행합니다"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = RiotLoaderApi()
        self.current_collection = ""
        self.setWindowTitle("Firestore 관리")
        self.resize(1380, 860)
        self.setSizeGripEnabled(True)
        self._create_ui()
        self.refresh_all()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        root.addWidget(self._build_header_group())

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.addWidget(self._build_stats_group(), 0, 0)
        grid.addWidget(self._build_docs_group(), 0, 1)
        grid.addWidget(self._build_detail_group(), 0, 2)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 3)
        root.addLayout(grid, 1)

        root.addWidget(self._build_delete_group())

    def _build_header_group(self):
        box = QGroupBox("Firestore 모니터링")
        layout = QVBoxLayout(box)

        info_row = QHBoxLayout()
        self.summary_label = QLabel("준비 중")
        self.limit_input = QSpinBox()
        self.limit_input.setRange(1, 500)
        self.limit_input.setValue(50)
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.refresh_all)
        info_row.addWidget(QLabel("문서 목록 제한"))
        info_row.addWidget(self.limit_input)
        info_row.addWidget(self.refresh_btn)
        info_row.addStretch(1)
        info_row.addWidget(self.summary_label)
        layout.addLayout(info_row)
        return box

    def _build_stats_group(self):
        box = QGroupBox("컬렉션 통계")
        layout = QVBoxLayout(box)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["Collection", "Docs", "Approx JSON Size"])
        self.stats_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.stats_table.setSelectionMode(QTableWidget.SingleSelection)
        self.stats_table.itemSelectionChanged.connect(self.load_selected_collection_documents)
        layout.addWidget(self.stats_table)
        return box

    def _build_docs_group(self):
        box = QGroupBox("문서 목록")
        layout = QVBoxLayout(box)

        action_row = QHBoxLayout()
        self.check_all_btn = QPushButton("전체 선택")
        self.check_all_btn.clicked.connect(self.check_all_documents)
        self.clear_check_btn = QPushButton("선택 해제")
        self.clear_check_btn.clicked.connect(self.uncheck_all_documents)
        action_row.addWidget(self.check_all_btn)
        action_row.addWidget(self.clear_check_btn)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.doc_list = QListWidget()
        self.doc_list.itemClicked.connect(self.show_selected_document)
        layout.addWidget(self.doc_list)
        return box

    def _build_detail_group(self):
        box = QGroupBox("문서 상세")
        layout = QVBoxLayout(box)
        self.doc_detail = QTextEdit()
        self.doc_detail.setReadOnly(True)
        layout.addWidget(self.doc_detail)
        return box

    def _build_delete_group(self):
        box = QGroupBox("삭제 도구")
        layout = QVBoxLayout(box)

        top_row = QHBoxLayout()
        self.delete_selected_btn = QPushButton("선택 문서 삭제")
        self.delete_selected_btn.clicked.connect(self.delete_selected_documents)
        self.clear_collection_btn = QPushButton("현재 컬렉션 전체 삭제")
        self.clear_collection_btn.clicked.connect(self.clear_current_collection)
        top_row.addWidget(self.delete_selected_btn)
        top_row.addWidget(self.clear_collection_btn)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        older_group = QGroupBox("오래된 데이터 삭제")
        older_layout = QFormLayout(older_group)
        self.delete_days_input = QSpinBox()
        self.delete_days_input.setRange(1, 3650)
        self.delete_days_input.setValue(30)
        self.delete_older_btn = QPushButton("기준 일수보다 오래된 문서 삭제")
        self.delete_older_btn.clicked.connect(self.delete_older_than)
        older_layout.addRow("기준 일수", self.delete_days_input)
        older_layout.addRow("", self.delete_older_btn)
        layout.addWidget(older_group)

        self.delete_status_label = QLabel("삭제 준비 완료")
        layout.addWidget(self.delete_status_label)

        self.delete_result_output = QTextEdit()
        self.delete_result_output.setReadOnly(True)
        self.delete_result_output.setMinimumHeight(110)
        self.delete_result_output.setMaximumHeight(140)
        self.delete_result_output.setPlaceholderText("삭제/관리 응답 상세 내용이 여기에 표시됩니다.")
        layout.addWidget(self.delete_result_output)
        return box

    def _set_action_result(self, status_text: str, detail_text: str = ""):
        """삭제 결과를 짧은 상태 문구와 스크롤 가능한 상세 로그로 나눠 보여준다."""
        self.delete_status_label.setText(status_text)
        self.delete_result_output.setPlainText(detail_text)

    def refresh_all(self):
        """컬렉션 통계와 현재 선택 컬렉션 문서 목록을 새로고침한다."""
        self.api.refresh_urls()
        try:
            response, data = self.api.get_firestore_stats()
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"Firestore 통계를 불러오지 못했습니다: {exc}")
            return

        if response.status_code != 200 or not data:
            self.doc_detail.setPlainText(self.api.format_response_text(response, data))
            return

        rows = data.get("collections", [])
        self._render_stats(rows, data)
        if rows:
            self.stats_table.selectRow(0)
            self.load_selected_collection_documents()

    def _render_stats(self, rows: list[dict], data: dict):
        """컬렉션별 집계 결과를 통계 테이블에 그린다."""
        self.stats_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.stats_table.setItem(row_index, 0, QTableWidgetItem(row.get("collection", "")))
            self.stats_table.setItem(row_index, 1, QTableWidgetItem(str(row.get("documents", 0))))
            self.stats_table.setItem(
                row_index,
                2,
                QTableWidgetItem(format_bytes(int(row.get("approx_json_bytes", 0) or 0))),
            )

        self.stats_table.resizeColumnsToContents()
        self.summary_label.setText(
            f"컬렉션 {data.get('collection_count', 0)}개 | 문서 {data.get('document_count', 0)}개 | 대략 {format_bytes(int(data.get('approx_json_bytes', 0) or 0))}"
        )

    def load_selected_collection_documents(self):
        """선택한 컬렉션의 문서 목록을 불러와 가운데 패널에 표시한다."""
        selected_items = self.stats_table.selectedItems()
        if not selected_items:
            return

        self.current_collection = selected_items[0].text().strip()
        if not self.current_collection:
            return

        try:
            response, data = self.api.list_firestore_documents(
                self.current_collection,
                self.limit_input.value(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"문서 목록을 불러오지 못했습니다: {exc}")
            return

        self.doc_list.clear()
        self.doc_detail.clear()

        if response.status_code != 200 or not data:
            self.doc_detail.setPlainText(self.api.format_response_text(response, data))
            return

        for document in data.get("documents", []):
            label = f"{document.get('id', '')} | {format_bytes(int(document.get('approx_json_bytes', 0) or 0))}"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, document)
            self.doc_list.addItem(item)

        self.delete_older_btn.setEnabled(self.current_collection in self.DELETABLE_BY_AGE)

    def show_selected_document(self, item: QListWidgetItem):
        """선택한 문서의 상세 JSON을 우측 패널에 출력한다."""
        document = item.data(Qt.UserRole) or {}
        payload = {
            "id": document.get("id"),
            "data": document.get("data", {}),
        }
        self.doc_detail.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    def check_all_documents(self):
        """현재 목록의 모든 문서를 삭제 대상으로 체크한다."""
        for index in range(self.doc_list.count()):
            self.doc_list.item(index).setCheckState(Qt.Checked)

    def uncheck_all_documents(self):
        """현재 목록의 모든 문서 선택을 해제한다."""
        for index in range(self.doc_list.count()):
            self.doc_list.item(index).setCheckState(Qt.Unchecked)

    def _get_checked_document_ids(self) -> list[str]:
        """문서 목록에서 체크된 문서 ID만 추려 반환한다."""
        document_ids = []
        for index in range(self.doc_list.count()):
            item = self.doc_list.item(index)
            if item.checkState() != Qt.Checked:
                continue
            document = item.data(Qt.UserRole) or {}
            document_id = (document.get("id") or "").strip()
            if document_id:
                document_ids.append(document_id)
        return document_ids

    def delete_selected_documents(self):
        """체크한 문서들만 현재 컬렉션에서 삭제한다."""
        if not self.current_collection:
            QMessageBox.warning(self, "선택 오류", "먼저 컬렉션을 선택해주세요.")
            return

        document_ids = self._get_checked_document_ids()
        if not document_ids:
            QMessageBox.warning(self, "선택 오류", "삭제할 문서를 하나 이상 체크해주세요.")
            return

        if not self._require_delete_phrase(
            title="선택 문서 삭제 확인",
            prompt=(
                f"{self.current_collection} 컬렉션에서 {len(document_ids)}개 문서를 삭제하려면\n"
                f"아래 문구를 정확히 입력해주세요.\n\n{self.DELETE_SELECTED_CONFIRM_TEXT}"
            ),
            expected_text=self.DELETE_SELECTED_CONFIRM_TEXT,
        ):
            self._set_action_result("선택 문서 삭제가 취소되었습니다.")
            return

        try:
            response, data = self.api.delete_firestore_documents(self.current_collection, document_ids)
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"문서 삭제 요청에 실패했습니다: {exc}")
            return

        self._set_action_result(
            f"선택 문서 삭제 결과: HTTP {response.status_code}",
            self.api.format_response_text(response, data),
        )
        if response.status_code == 200:
            self.refresh_all()

    def clear_current_collection(self):
        """현재 선택 컬렉션 전체를 삭제한다."""
        if not self.current_collection:
            QMessageBox.warning(self, "선택 오류", "먼저 컬렉션을 선택해주세요.")
            return

        if not self._require_delete_phrase(
            title="현재 컬렉션 전체 삭제 확인",
            prompt=(
                f"{self.current_collection} 컬렉션 전체를 삭제하려면\n"
                f"아래 문구를 정확히 입력해주세요.\n\n{self.CLEAR_COLLECTION_CONFIRM_TEXT}"
            ),
            expected_text=self.CLEAR_COLLECTION_CONFIRM_TEXT,
        ):
            self._set_action_result("현재 컬렉션 삭제가 취소되었습니다.")
            return

        try:
            response, data = self.api.clear_firestore_collection(self.current_collection)
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"컬렉션 삭제 요청에 실패했습니다: {exc}")
            return

        self._set_action_result(
            f"현재 컬렉션 삭제 결과: HTTP {response.status_code}",
            self.api.format_response_text(response, data),
        )
        if response.status_code == 200:
            self.refresh_all()

    def _require_delete_phrase(self, title: str, prompt: str, expected_text: str) -> bool:
        """삭제 전 지정된 확인 문구를 정확히 입력했는지 검사한다."""
        typed_text, ok = QInputDialog.getText(self, title, prompt)
        if not ok:
            return False
        if typed_text.strip() != expected_text:
            QMessageBox.warning(self, "입력 불일치", "확인 문구가 정확히 일치하지 않아 삭제를 중단했습니다.")
            return False
        return True

    def delete_older_than(self):
        """기준 일수보다 오래된 경기 문서를 삭제한다."""
        if self.current_collection not in self.DELETABLE_BY_AGE:
            QMessageBox.warning(self, "지원되지 않음", "현재 컬렉션은 기간 삭제를 지원하지 않습니다.")
            return

        days = self.delete_days_input.value()
        if not self._require_delete_phrase(
            title="기간 삭제 확인",
            prompt=(
                f"{self.current_collection} 컬렉션에서 {days}일보다 오래된 문서를 삭제하려면\n"
                f"아래 문구를 정확히 입력해주세요.\n\n{self.DELETE_OLDER_CONFIRM_TEXT}"
            ),
            expected_text=self.DELETE_OLDER_CONFIRM_TEXT,
        ):
            self._set_action_result("기간 삭제가 취소되었습니다.")
            return

        try:
            response, data = self.api.delete_firestore_older_than(self.current_collection, days)
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"기간 삭제 요청에 실패했습니다: {exc}")
            return

        self._set_action_result(
            f"기간 삭제 결과: HTTP {response.status_code}",
            self.api.format_response_text(response, data),
        )
        if response.status_code == 200:
            self.refresh_all()
