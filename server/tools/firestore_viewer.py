from __future__ import annotations

import json
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.backend.firestore_store import get_client


class FirestoreViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firestore Viewer")
        self.setGeometry(100, 100, 1100, 720)
        self._build_ui()
        self.load_collections()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.collection_selector = QComboBox()
        self.collection_selector.currentTextChanged.connect(self.load_collection_docs)
        self.limit_input = QSpinBox()
        self.limit_input.setRange(1, 500)
        self.limit_input.setValue(50)

        self.refresh_collections_btn = QPushButton("Collections Refresh")
        self.refresh_collections_btn.clicked.connect(self.load_collections)
        self.refresh_docs_btn = QPushButton("Docs Refresh")
        self.refresh_docs_btn.clicked.connect(self.load_collection_docs)

        top_row.addWidget(QLabel("Collection"))
        top_row.addWidget(self.collection_selector, 1)
        top_row.addWidget(QLabel("Limit"))
        top_row.addWidget(self.limit_input)
        top_row.addWidget(self.refresh_collections_btn)
        top_row.addWidget(self.refresh_docs_btn)
        root.addLayout(top_row)

        content_row = QHBoxLayout()
        self.doc_list = QListWidget()
        self.doc_list.itemClicked.connect(self.show_selected_doc)
        self.doc_detail = QTextEdit()
        self.doc_detail.setReadOnly(True)

        content_row.addWidget(self.doc_list, 1)
        content_row.addWidget(self.doc_detail, 2)
        root.addLayout(content_row)

    def load_collections(self) -> None:
        try:
            current = self.collection_selector.currentText()
            collections = sorted(collection.id for collection in get_client().collections())
            self.collection_selector.blockSignals(True)
            self.collection_selector.clear()
            self.collection_selector.addItems(collections)
            self.collection_selector.blockSignals(False)

            if current and current in collections:
                self.collection_selector.setCurrentText(current)
            elif collections:
                self.collection_selector.setCurrentIndex(0)
            else:
                self.doc_list.clear()
                self.doc_detail.setPlainText("No collections found.")
                return

            self.load_collection_docs()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to load collections: {exc}")

    def load_collection_docs(self) -> None:
        collection_name = self.collection_selector.currentText().strip()
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
        payload = item.data(Qt.UserRole) or {}
        self.doc_detail.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = FirestoreViewer()
    viewer.show()
    sys.exit(app.exec_())
