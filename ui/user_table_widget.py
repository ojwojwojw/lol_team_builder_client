import traceback
from pathlib import Path

from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from util.constants import (
    ANY_POSITION,
    POSITION_OPTIONS,
    TIER_COLOR,
    TIER_LIST,
    normalize_position_name,
    normalize_tier_name,
)


VISIBLE_USER_KEYS = {"selected", "name", "tier", "tier_detail", "positions"}


class UserTableWidget(QWidget):
    toggle_clicked = pyqtSignal()
    add_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    save_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._row_widget_map = {}
        self._is_building_row = False
        self._selected_row = -1
        self._create_ui()
        self._connect_signals()

    def _log_debug(self, message):
        log_path = Path(__file__).resolve().parent.parent / "team_builder_client_error.log"
        try:
            with open(log_path, "a", encoding="utf-8") as file:
                file.write(f"[UserTableWidget] {message}\n")
        except Exception:
            pass

    def _log_exception(self, title, exc):
        log_path = Path(__file__).resolve().parent.parent / "team_builder_client_error.log"
        try:
            with open(log_path, "a", encoding="utf-8") as file:
                file.write(f"[UserTableWidget] {title}: {exc}\n")
                file.write(traceback.format_exc())
                file.write("\n")
        except Exception:
            pass

    def _create_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["선택", "이름", "티어", "세부", "1지망", "2지망", "3지망"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #404040;
                alternate-background-color: #20242b;
                background-color: #171a20;
            }
            QTableWidget::item:selected {
                background-color: #35516b;
            }
            """
        )
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(0, 78)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 130)
        self.table.setColumnWidth(6, 130)
        self.table.setMinimumWidth(930)

        btns = QHBoxLayout()
        self.toggle_btn = QPushButton("전체 선택/해제")
        self.add_btn = QPushButton("행 추가")
        self.delete_btn = QPushButton("행 삭제")
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
        try:
            self._log_debug(f"populate start rows={len(users)}")
            self._is_building_row = True
            self.table.setRowCount(len(users))
            self._row_widget_map.clear()
            for row, user in enumerate(users):
                self._set_row_widgets(row, user)
            self._is_building_row = False
            if users:
                self._selected_row = 0
            else:
                self._selected_row = -1
            self.refresh_row_highlight()
            self._log_debug("populate done")
        except Exception as exc:
            self._is_building_row = False
            self._log_exception("populate failed", exc)
            raise

    def find_row_by_name(self, name):
        normalized_name = (name or "").strip().lower()
        for row in range(self.table.rowCount()):
            name_edit = self.table.cellWidget(row, 1)
            if not name_edit:
                continue
            if name_edit.text().strip().lower() == normalized_name:
                return row
        return -1

    def has_user(self, name):
        return self.find_row_by_name(name) >= 0

    def get_current_row_data(self):
        row = self._selected_row
        if row < 0:
            return None

        name_edit = self.table.cellWidget(row, 1)
        tier_cb = self.table.cellWidget(row, 2)
        detail_cb = self.table.cellWidget(row, 3)
        p1 = self.table.cellWidget(row, 4)
        p2 = self.table.cellWidget(row, 5)
        p3 = self.table.cellWidget(row, 6)
        chk = self.table.cellWidget(row, 0)

        if not all([name_edit, tier_cb, detail_cb, p1, p2, p3, chk]):
            return None

        user = self._get_row_meta(row)
        user.update({
            "selected": chk.isChecked(),
            "name": name_edit.text().strip(),
            "tier": tier_cb.currentText(),
            "tier_detail": int(detail_cb.currentText()),
            "positions": [
                p1.currentText(),
                p2.currentText(),
                p3.currentText(),
            ],
        })
        return user

    def add_user(self, user):
        try:
            self._log_debug(
                f"add_user start name={user.get('name', '')!r} rows={self.table.rowCount()}"
            )
            if self.has_user(user.get("name", "")):
                self._log_debug("add_user duplicate")
                return False

            row = self.table.rowCount()
            self._is_building_row = True
            self.table.insertRow(row)
            self._log_debug(f"add_user inserted row={row}")
            self._set_row_widgets(row, user)
            self._is_building_row = False
            self._selected_row = row
            self.refresh_row_highlight()
            self._log_debug("add_user after refresh")
            self._log_debug("add_user done")
            return True
        except Exception as exc:
            self._is_building_row = False
            self._log_exception("add_user failed", exc)
            raise

    def _set_row_widgets(self, row, user=None):
        try:
            user = user or {}
            self._log_debug(f"_set_row_widgets start row={row} name={user.get('name', '')!r}")

            chk = QCheckBox()
            chk.setChecked(user.get("selected", False))
            self.table.setCellWidget(row, 0, chk)

            name_edit = QLineEdit()
            name_edit.setText(user.get("name", ""))
            self.table.setCellWidget(row, 1, name_edit)

            tier = QComboBox()
            tier.addItems(TIER_LIST)
            tier.setCurrentText(normalize_tier_name(user.get("tier", "실버")))
            self.table.setCellWidget(row, 2, tier)

            detail = QComboBox()
            detail.addItems(["1", "2", "3", "4"])
            detail.setCurrentText(str(user.get("tier_detail", 2)))
            self.table.setCellWidget(row, 3, detail)

            positions = [
                normalize_position_name(position)
                for position in user.get("positions", [ANY_POSITION, ANY_POSITION, ANY_POSITION])
            ]
            position_combos = []

            for index in range(3):
                combo = QComboBox()
                combo.addItems(POSITION_OPTIONS)
                if index < len(positions):
                    combo.setCurrentText(positions[index])
                self.table.setCellWidget(row, 4 + index, combo)
                position_combos.append(combo)

            self._set_row_meta(row, user)
            row_widgets = [chk, name_edit, tier, detail, *position_combos]
            for widget in row_widgets:
                self._bind_row_selection(widget, row)

            self._bind_position_filters(position_combos)
            self.apply_tier_style(tier, row == self._selected_row)
            self.bind_tier_change(tier)
            if not self._is_building_row:
                self.refresh_row_highlight()
            self._log_debug(f"_set_row_widgets done row={row}")
        except Exception as exc:
            self._log_exception(f"_set_row_widgets failed row={row}", exc)
            raise

    def _bind_row_selection(self, widget, row):
        self._row_widget_map[widget] = row
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if self._is_building_row:
            return super().eventFilter(watched, event)

        if event.type() in (QEvent.MouseButtonPress, QEvent.FocusIn):
            row = self._row_widget_map.get(watched)
            if row is not None:
                self._selected_row = row
                self.refresh_row_highlight()
        return super().eventFilter(watched, event)

    def set_selected_row(self, row):
        if 0 <= row < self.table.rowCount():
            self._selected_row = row
            self.refresh_row_highlight()

    def _set_row_meta(self, row, user):
        chk = self.table.cellWidget(row, 0)
        if not chk:
            return

        extra = {
            key: value
            for key, value in user.items()
            if key not in VISIBLE_USER_KEYS
        }
        chk.setProperty("user_meta", extra)

    def _get_row_meta(self, row):
        chk = self.table.cellWidget(row, 0)
        if not chk:
            return {}
        return dict(chk.property("user_meta") or {})

    def _bind_position_filters(self, combos):
        def refresh():
            selected_before = []

            for combo in combos:
                current = combo.currentText()
                blocked = set(selected_before)
                options = [
                    option
                    for option in POSITION_OPTIONS
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
        try:
            row = self.table.rowCount()
            self._log_debug(f"add_row start row={row}")
            self._is_building_row = True
            self.table.insertRow(row)
            self._log_debug(f"add_row inserted row={row}")
            self._set_row_widgets(row)
            self._is_building_row = False
            self._selected_row = row
            self.refresh_row_highlight()
            self._log_debug("add_row after refresh")
            self._log_debug(f"add_row done row={row}")
        except Exception as exc:
            self._is_building_row = False
            self._log_exception("add_row failed", exc)
            raise

    def delete_row(self):
        try:
            row = self._selected_row
            self._log_debug(f"delete_row start current_row={row}")
            if row >= 0:
                self.table.removeRow(row)
                self._row_widget_map = {
                    widget: (mapped_row - 1 if mapped_row > row else mapped_row)
                    for widget, mapped_row in self._row_widget_map.items()
                    if mapped_row != row
                }
                if self.table.rowCount():
                    self._selected_row = min(row, self.table.rowCount() - 1)
                else:
                    self._selected_row = -1
                self.refresh_row_highlight()
            self._log_debug("delete_row done")
        except Exception as exc:
            self._log_exception("delete_row failed", exc)
            raise

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

    def apply_tier_style(self, combo, is_selected=False):
        tier = combo.currentText()
        color = self.get_tier_color(tier)
        border_color = "#ffd966" if is_selected else "#3a3a3a"

        combo.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {color};
                color: black;
                font-weight: bold;
                border-radius: 4px;
                border: 2px solid {border_color};
                padding: 2px;
            }}
            """
        )

    def bind_tier_change(self, combo):
        def update():
            if self._is_building_row:
                return
            current_row = self._selected_row
            if current_row < 0:
                self.apply_tier_style(combo, False)
                return
            selected_combo = self.table.cellWidget(current_row, 2)
            self.apply_tier_style(combo, combo is selected_combo)

        combo.currentIndexChanged.connect(update)
        update()

    def refresh_row_highlight(self):
        if self._is_building_row:
            return

        current_row = self._selected_row

        for row in range(self.table.rowCount()):
            selected = row == current_row
            row_border = "#ffd966" if selected else "#4a4a4a"
            row_bg = "#253546" if selected else "#1f1f1f"

            name_edit = self.table.cellWidget(row, 1)
            if name_edit:
                name_edit.setStyleSheet(
                    f"""
                    QLineEdit {{
                        background-color: {row_bg};
                        color: white;
                        border: 2px solid {row_border};
                        padding: 2px;
                        font-weight: {'bold' if selected else 'normal'};
                    }}
                    """
                )

            chk = self.table.cellWidget(row, 0)
            if chk:
                chk.setStyleSheet(
                    f"""
                    QCheckBox {{
                        background-color: {row_bg};
                        border: 2px solid {row_border};
                        padding: 2px;
                    }}
                    """
                )

            detail = self.table.cellWidget(row, 3)
            if detail:
                detail.setStyleSheet(
                    f"""
                    QComboBox {{
                        background-color: {row_bg};
                        color: white;
                        border: 2px solid {row_border};
                        padding: 2px;
                    }}
                    """
                )

            tier = self.table.cellWidget(row, 2)
            if tier:
                self.apply_tier_style(tier, selected)

            for col in (4, 5, 6):
                combo = self.table.cellWidget(row, col)
                if combo:
                    combo.setStyleSheet(
                        f"""
                        QComboBox {{
                            background-color: {row_bg};
                            color: white;
                            border: 2px solid {row_border};
                            padding: 2px;
                        }}
                        """
                    )
