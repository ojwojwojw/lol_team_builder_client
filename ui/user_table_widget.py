from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QComboBox, QCheckBox, QLineEdit
)
from PyQt5.QtCore import pyqtSignal

from util.constants import TIER_LIST, ANY_POSITION, POSITION_OPTIONS, TIER_COLOR


class UserTableWidget(QWidget):
    toggle_clicked = pyqtSignal()
    add_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    save_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._create_ui()
        self._connect_signals()

    def _create_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["선택", "Name", "Tier", "lv", "Pos1", "Pos2", "Pos3"]
        )

        btns = QHBoxLayout()

        self.toggle_btn = QPushButton("전체 선택/해제")
        self.add_btn = QPushButton("행 추가")
        self.delete_btn = QPushButton("삭제")
        self.save_btn = QPushButton("저장")

        btns.addWidget(self.toggle_btn)
        btns.addWidget(self.add_btn)
        btns.addWidget(self.delete_btn)
        btns.addWidget(self.save_btn)

        layout.addWidget(self.table)
        layout.addLayout(btns)

        self.setLayout(layout)

    def _connect_signals(self):
        self.toggle_btn.clicked.connect(self.toggle_clicked.emit)
        self.add_btn.clicked.connect(self.add_clicked.emit)
        self.delete_btn.clicked.connect(self.delete_clicked.emit)
        self.save_btn.clicked.connect(self.save_clicked.emit)

    def populate(self, users):
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            self._set_row_widgets(row, user)

    def _set_row_widgets(self, row, user=None):
        user = user or {}

        chk = QCheckBox()
        chk.setChecked(user.get("selected", False))
        self.table.setCellWidget(row, 0, chk)

        name_edit = QLineEdit()
        name_edit.setText(user.get("name", ""))
        self.table.setCellWidget(row, 1, name_edit)

        tier = QComboBox()
        tier.addItems(TIER_LIST)
        tier.setCurrentText(user.get("tier", ""))
        self.apply_tier_style(tier)
        self.bind_tier_change(tier)
        self.table.setCellWidget(row, 2, tier)

        detail = QComboBox()
        detail.addItems(["1", "2", "3", "4"])
        detail.setCurrentText(str(user.get("tier_detail", 1)))
        self.table.setCellWidget(row, 3, detail)

        positions = user.get("positions", [ANY_POSITION, ANY_POSITION, ANY_POSITION])
        position_combos = []

        for i in range(3):
            combo = QComboBox()
            combo.addItems(POSITION_OPTIONS)

            if i < len(positions):
                combo.setCurrentText(positions[i])

            self.table.setCellWidget(row, 4 + i, combo)
            position_combos.append(combo)

        self._bind_position_filters(position_combos)

    def _bind_position_filters(self, combos):
        def refresh():
            selected_before = []

            for index, combo in enumerate(combos):
                current = combo.currentText()
                blocked = set(selected_before)
                options = [
                    option for option in POSITION_OPTIONS
                    if option == ANY_POSITION or option not in blocked
                ]

                combo.blockSignals(True)
                combo.clear()
                combo.addItems(options)

                if current in options:
                    combo.setCurrentText(current)
                else:
                    combo.setCurrentText(ANY_POSITION)

                combo.blockSignals(False)

                selected = combo.currentText()
                if selected != ANY_POSITION:
                    selected_before.append(selected)

        for combo in combos:
            combo.currentIndexChanged.connect(refresh)

        refresh()

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._set_row_widgets(row)

    def delete_row(self):
        row = self.table.currentRow()

        if row >= 0:
            self.table.removeRow(row)

    def toggle_all(self):
        new_state = not any(
            self.table.cellWidget(row, 0).isChecked()
            for row in range(self.table.rowCount())
            if self.table.cellWidget(row, 0)
        )

        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, 0)

            if chk:
                chk.setChecked(new_state)

    def get_tier_color(self, tier):
        return TIER_COLOR.get(tier, "#ffffff")

    def apply_tier_style(self, combo):
        tier = combo.currentText()
        color = self.get_tier_color(tier)

        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {color};
                color: black;
                font-weight: bold;
                border-radius: 4px;
                padding: 2px;
            }}
        """)

    def bind_tier_change(self, combo):
        def update():
            self.apply_tier_style(combo)

        combo.currentIndexChanged.connect(update)
        update()
