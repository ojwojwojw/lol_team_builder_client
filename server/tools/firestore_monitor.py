from __future__ import annotations

import json
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.backend.stores.firestore_client import get_client


def format_bytes(num_bytes: int) -> str:
    """바이트 수를 사람이 읽기 쉬운 단위 문자열로 변환한다."""
    value = float(num_bytes)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


class FirestoreMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firestore Monitor")
        self.setGeometry(100, 100, 1400, 820)
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        header_row = QHBoxLayout()
        self.limit_input = QSpinBox()
        self.limit_input.setRange(1, 500)
        self.limit_input.setValue(50)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_all)

        self.summary_label = QLabel("Ready")
        header_row.addWidget(QLabel("문서 목록 제한"))
        header_row.addWidget(self.limit_input)
        header_row.addWidget(self.refresh_btn)
        header_row.addStretch(1)
        header_row.addWidget(self.summary_label)
        root.addLayout(header_row)

        body_row = QHBoxLayout()

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("컬렉션 통계"))
        self.collection_table = QTableWidget()
        self.collection_table.setColumnCount(3)
        self.collection_table.setHorizontalHeaderLabels(["Collection", "Docs", "Approx JSON Size"])
        self.collection_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.collection_table.setSelectionMode(QTableWidget.SingleSelection)
        self.collection_table.itemSelectionChanged.connect(self.load_selected_collection_docs)
        left_panel.addWidget(self.collection_table)

        middle_panel = QVBoxLayout()
        middle_panel.addWidget(QLabel("문서 목록"))
        self.doc_list = QListWidget()
        self.doc_list.itemClicked.connect(self.show_selected_doc)
        middle_panel.addWidget(self.doc_list)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("문서 상세"))
        self.doc_detail = QTextEdit()
        self.doc_detail.setReadOnly(True)
        right_panel.addWidget(self.doc_detail)

        body_row.addLayout(left_panel, 2)
        body_row.addLayout(middle_panel, 1)
        body_row.addLayout(right_panel, 2)
        root.addLayout(body_row)

    def refresh_all(self) -> None:
        """컬렉션 통계, 문서 목록, 상세 패널을 한 번에 새로고침한다."""
        try:
            rows = self._load_collection_stats()
            self._render_collection_stats(rows)
            if rows:
                self.collection_table.selectRow(0)
                self.load_selected_collection_docs()
            else:
                self.doc_list.clear()
                self.doc_detail.setPlainText("No collections found.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to refresh Firestore monitor: {exc}")

    def _load_collection_stats(self) -> list[dict]:
        """컬렉션별 문서 수와 대략적인 JSON 크기를 집계한다."""
        client = get_client()
        rows = []
        for collection in sorted(client.collections(), key=lambda item: item.id):
            doc_count = 0
            approx_bytes = 0
            for snapshot in collection.stream():
                payload = snapshot.to_dict() or {}
                encoded = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
                approx_bytes += len(encoded)
                doc_count += 1

            rows.append({
                "collection": collection.id,
                "documents": doc_count,
                "approx_json_bytes": approx_bytes,
            })
        return rows

    def _render_collection_stats(self, rows: list[dict]) -> None:
        """집계 결과를 좌측 컬렉션 통계 테이블에 그린다."""
        self.collection_table.setRowCount(len(rows))
        total_docs = 0
        total_bytes = 0

        for row_index, row in enumerate(rows):
            total_docs += row["documents"]
            total_bytes += row["approx_json_bytes"]
            self.collection_table.setItem(row_index, 0, QTableWidgetItem(row["collection"]))
            self.collection_table.setItem(row_index, 1, QTableWidgetItem(str(row["documents"])))
            self.collection_table.setItem(
                row_index,
                2,
                QTableWidgetItem(format_bytes(row["approx_json_bytes"])),
            )

        self.summary_label.setText(
            f"컬렉션 {len(rows)}개 | 문서 {total_docs}개 | 대략 {format_bytes(total_bytes)}"
        )
        self.collection_table.resizeColumnsToContents()

    def load_selected_collection_docs(self) -> None:
        """선택된 컬렉션의 문서 목록을 가운데 패널에 채운다."""
        selected_items = self.collection_table.selectedItems()
        if not selected_items:
            return

        collection_name = selected_items[0].text().strip()
        if not collection_name:
            return

        try:
            self.doc_list.clear()
            self.doc_detail.clear()
            limit = self.limit_input.value()
            docs = get_client().collection(collection_name).limit(limit).stream()
            count = 0
            for snapshot in docs:
                item = QListWidgetItem(snapshot.id)
                item.setData(Qt.UserRole, snapshot.to_dict() or {})
                self.doc_list.addItem(item)
                count += 1

            if count == 0:
                self.doc_detail.setPlainText("No documents found.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to load documents: {exc}")

    def show_selected_doc(self, item: QListWidgetItem) -> None:
        """선택된 문서의 JSON 내용을 우측 패널에 표시한다."""
        payload = item.data(Qt.UserRole) or {}
        self.doc_detail.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = FirestoreMonitor()
    viewer.show()
    sys.exit(app.exec_())
