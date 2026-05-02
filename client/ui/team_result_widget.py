from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from domain.constants import DEFAULT_THEME_MODE, POSITIONS
from domain.team_builder import calc_position_fit_bonus, calc_recent_form_bonus
from ui.theme import TIER_COLOR, get_theme_tokens


class TeamResultWidget(QWidget):
    generate_clicked = pyqtSignal()
    copy_clicked = pyqtSignal()
    account_clicked = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.result_text = ""
        self.theme_mode = DEFAULT_THEME_MODE
        self._create_ui()
        self._connect_signals()
        self.apply_theme(self.theme_mode)

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
        self.team1_score_label = QLabel("팀 1 점수: -")
        self.team1_table = self._create_team_table()
        team1_container.addWidget(self.team1_score_label)
        team1_container.addWidget(self.team1_table)

        team2_container = QVBoxLayout()
        self.team2_score_label = QLabel("팀 2 점수: -")
        self.team2_table = self._create_team_table()
        team2_container.addWidget(self.team2_score_label)
        team2_container.addWidget(self.team2_table)

        teams_layout.addLayout(team1_container, 1)
        teams_layout.addLayout(team2_container, 1)
        layout.addLayout(teams_layout)

        self.diff_label = QLabel("점수 차이: -")
        layout.addWidget(self.diff_label)

        self.setLayout(layout)

    def _connect_signals(self):
        self.generate_btn.clicked.connect(self.generate_clicked.emit)
        self.copy_btn.clicked.connect(self.copy_clicked.emit)
        self.team1_table.cellClicked.connect(
            lambda row, _col: self._emit_account_click(self.team1_table, row)
        )
        self.team2_table.cellClicked.connect(
            lambda row, _col: self._emit_account_click(self.team2_table, row)
        )

    def apply_theme(self, theme_mode):
        self.theme_mode = theme_mode
        tokens = get_theme_tokens(theme_mode)
        self.team1_score_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {tokens['team1_score']};"
        )
        self.team2_score_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {tokens['team2_score']};"
        )
        self.diff_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {tokens['diff_text']};"
        )

    def _create_team_table(self):
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["포지션", "이름", "티어", "세부", "최근 폼", "포지션 적합"]
        )
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        return table

    def _emit_account_click(self, table, row):
        name_item = table.item(row, 1)
        if not name_item:
            return

        user = name_item.data(Qt.UserRole)
        if not isinstance(user, dict):
            return

        if not user.get("account_tag_line"):
            return

        self.account_clicked.emit(user)

    def render(self, result):
        self.fill(self.team1_table, result["a1"])
        self.fill(self.team2_table, result["a2"])

        self.team1_score_label.setText(f"팀 1 점수: {round(result['t1_score'], 2)}")
        self.team2_score_label.setText(f"팀 2 점수: {round(result['t2_score'], 2)}")
        self.diff_label.setText(f"점수 차이: {round(result['diff'], 2)}")

    def fill(self, table, assign):
        tokens = get_theme_tokens(self.theme_mode)
        table.setRowCount(5)

        for index, position in enumerate(POSITIONS):
            pos_item = QTableWidgetItem(position)
            pos_item.setForeground(QBrush(QColor(tokens["muted_text"])))
            table.setItem(index, 0, pos_item)

            if position not in assign:
                for col in range(1, 6):
                    table.setItem(index, col, QTableWidgetItem(""))
                continue

            user = assign[position]
            name = user["name"]
            tier = user["tier"]
            detail = user.get("tier_detail", 2)

            name_item = QTableWidgetItem(name)
            name_item.setBackground(QColor(tokens["result_name_bg"]))
            name_item.setForeground(QBrush(QColor(tokens["result_name_fg"])))
            name_item.setData(Qt.UserRole, user)
            table.setItem(index, 1, name_item)

            tier_color = QColor(TIER_COLOR.get(tier, "#ffffff"))

            tier_item = QTableWidgetItem(tier)
            tier_item.setBackground(tier_color)
            tier_item.setForeground(QBrush(QColor("#000000")))
            table.setItem(index, 2, tier_item)

            detail_item = QTableWidgetItem(str(detail))
            detail_item.setBackground(tier_color)
            detail_item.setForeground(QBrush(QColor("#000000")))
            table.setItem(index, 3, detail_item)

            form_bonus = calc_recent_form_bonus(user)
            form_text = f"{form_bonus * 100:+.1f}%" if user.get("recent_match_count", 0) else "-"

            form_item = QTableWidgetItem(form_text)
            form_item.setForeground(QBrush(QColor(tokens["muted_text"])))
            table.setItem(index, 4, form_item)

            fit_bonus = calc_position_fit_bonus(user, position)
            fit_text = f"{fit_bonus * 100:+.1f}%" if user.get("recent_match_count", 0) else "-"

            fit_item = QTableWidgetItem(fit_text)
            fit_item.setForeground(QBrush(QColor(tokens["muted_text"])))
            table.setItem(index, 5, fit_item)
