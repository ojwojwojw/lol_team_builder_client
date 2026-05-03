from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialogButtonBox,
    QDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


COUPLE_GROUP_COLUMNS = ["이름", "커플 그룹"]


class CoupleGroupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("커플 그룹 설정")
        self.resize(520, 420)

        layout = QVBoxLayout()
        guide_label = QLabel(
            "같은 팀으로 묶고 싶은 유저들에게 동일한 커플 그룹명을 입력하세요.\n"
            "비워두면 커플 그룹 고려 없이 팀을 생성합니다."
        )
        guide_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COUPLE_GROUP_COLUMNS))
        self.table.setHorizontalHeaderLabels(COUPLE_GROUP_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setCornerButtonEnabled(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionsMovable(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 180)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(guide_label)
        layout.addWidget(self.table)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def set_users(self, users):
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            name = (user.get("name") or "").strip()
            group_name = (user.get("couple_group") or "").strip()

            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            group_input = QLineEdit()
            group_input.setPlaceholderText("예: 친구1조, 커플A")
            group_input.setText(group_name)
            self.table.setCellWidget(row, 1, group_input)

    def get_group_map(self):
        group_map = {}
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            group_input = self.table.cellWidget(row, 1)
            if not name_item or group_input is None:
                continue

            name = name_item.text().strip()
            group_name = group_input.text().strip()
            if name:
                group_map[name] = group_name
        return group_map
