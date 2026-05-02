import sqlite3
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

try:
    from .common import DB_PATH
except ImportError:
    from common import DB_PATH


class DBViewer(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("SQLite DB Viewer")
        self.setGeometry(100, 100, 800, 700)

        layout = QVBoxLayout()

        self.table_selector = QComboBox()
        self.table_selector.addItems(
            ["riot_account", "match_summary", "team_summary", "participant_detail"]
        )
        self.table_selector.currentTextChanged.connect(self.load_table)
        layout.addWidget(QLabel("Table"))
        layout.addWidget(self.table_selector)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_table)
        layout.addWidget(self.refresh_btn)

        layout.addWidget(QLabel("SQL Query"))
        self.sql_input = QTextEdit()
        self.sql_input.setPlaceholderText("Enter SQL query")
        layout.addWidget(self.sql_input)

        self.sql_btn = QPushButton("Run SQL")
        self.sql_btn.clicked.connect(self.run_sql_query)
        layout.addWidget(self.sql_btn)

        self.setLayout(layout)
        self.load_table()

    def run_sql_query(self):
        sql = self.sql_input.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Warning", "Enter a SQL query first.")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)

            if sql.lower().startswith("select"):
                rows = cursor.fetchall()
                headers = [column[0] for column in cursor.description]
                self._render_rows(headers, rows)
            else:
                conn.commit()
                QMessageBox.information(self, "Success", "Query executed.")
                self.load_table()

            conn.close()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to run query: {exc}")

    def load_table(self):
        table_name = self.table_selector.currentText()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        headers = [column[0] for column in cursor.description]
        conn.close()
        self._render_rows(headers, rows)

    def _render_rows(self, headers, rows):
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(headers)
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = DBViewer(str(DB_PATH))
    viewer.show()
    sys.exit(app.exec_())
