from PyQt5.QtWidgets import (
    QDialog,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from application.recent_match_views import MATCH_DETAIL_COLUMNS

MATCH_DETAIL_ROW_KEYS = [
    "summoner_name",
    "champion_name",
    "position",
    "result",
    "kda",
    "cs",
    "damage",
    "vision",
]


class MatchDetailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("경기 상세 보기")
        self.resize(980, 520)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(len(MATCH_DETAIL_COLUMNS))
        self.table.setHorizontalHeaderLabels(MATCH_DETAIL_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def set_rows(self, rows):
        self.table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            for col_index, data_key in enumerate(MATCH_DETAIL_ROW_KEYS):
                self.table.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(str(row_data.get(data_key, ""))),
                )
