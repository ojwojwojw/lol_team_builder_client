from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QBrush

from util.constants import POSITIONS, TIER_COLOR


class TeamResultWidget(QWidget):
    generate_clicked = pyqtSignal()
    copy_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.result_text = ""
        self._create_ui()
        self._connect_signals()

    def _create_ui(self):
        layout = QVBoxLayout()

        top_btns = QHBoxLayout()

        self.generate_btn = QPushButton("팀 생성")
        self.copy_btn = QPushButton("복사")

        top_btns.addWidget(self.generate_btn)
        top_btns.addWidget(self.copy_btn)

        layout.addLayout(top_btns)

        teams_layout = QHBoxLayout()

        team1_container = QVBoxLayout()
        self.team1_score_label = QLabel("TEAM 1: -")
        self.team1_score_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #E74C3C;"
        )

        self.team1_table = self._create_team_table()

        team1_container.addWidget(self.team1_score_label)
        team1_container.addWidget(self.team1_table)

        team2_container = QVBoxLayout()
        self.team2_score_label = QLabel("TEAM 2: -")
        self.team2_score_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #3498DB;"
        )

        self.team2_table = self._create_team_table()

        team2_container.addWidget(self.team2_score_label)
        team2_container.addWidget(self.team2_table)

        teams_layout.addLayout(team1_container, 1)
        teams_layout.addLayout(team2_container, 1)

        layout.addLayout(teams_layout)

        self.diff_label = QLabel("DIFF: -")
        self.diff_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1E90FF;"
        )

        layout.addWidget(self.diff_label)

        self.setLayout(layout)

    def _connect_signals(self):
        self.generate_btn.clicked.connect(self.generate_clicked.emit)
        self.copy_btn.clicked.connect(self.copy_clicked.emit)

    def _create_team_table(self):
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Pos", "Name", "Tier", "Detail"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        return table

    def render(self, result):
        self.fill(self.team1_table, result["a1"])
        self.fill(self.team2_table, result["a2"])

        self.team1_score_label.setText(f"TEAM 1: {round(result['t1_score'], 2)}")
        self.team2_score_label.setText(f"TEAM 2: {round(result['t2_score'], 2)}")
        self.diff_label.setText(f"DIFF: {round(result['diff'], 2)}")

    def fill(self, table, assign):
        table.setRowCount(5)

        for i, position in enumerate(POSITIONS):
            pos_item = QTableWidgetItem(position)
            pos_item.setForeground(QBrush(QColor("#E0E0E0")))
            table.setItem(i, 0, pos_item)

            if position not in assign:
                continue

            user = assign[position]

            name = user["name"]
            tier = user["tier"]
            detail = user.get("tier_detail", 2)

            name_item = QTableWidgetItem(name)
            name_item.setBackground(QColor("#FFFFFF"))
            name_item.setForeground(QBrush(QColor("#000000")))
            table.setItem(i, 1, name_item)

            tier_color = QColor(TIER_COLOR.get(tier, "#ffffff"))

            tier_item = QTableWidgetItem(tier)
            tier_item.setBackground(tier_color)
            tier_item.setForeground(QBrush(QColor("#000000")))
            table.setItem(i, 2, tier_item)

            detail_item = QTableWidgetItem(str(detail))
            detail_item.setBackground(tier_color)
            detail_item.setForeground(QBrush(QColor("#000000")))
            table.setItem(i, 3, detail_item)
