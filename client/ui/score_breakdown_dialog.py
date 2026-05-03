from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


SCORE_BREAKDOWN_COLUMNS = ["항목", "원본값", "가중치", "반영값"]


class ScoreBreakdownDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("조합 선택 근거")
        self.resize(760, 420)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(len(SCORE_BREAKDOWN_COLUMNS))
        self.table.setHorizontalHeaderLabels(SCORE_BREAKDOWN_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def set_rows(self, rows):
        self.table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            for col_index, column_name in enumerate(SCORE_BREAKDOWN_COLUMNS):
                value = row_data.get(column_name, "")
                self.table.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(str(value)),
                )
