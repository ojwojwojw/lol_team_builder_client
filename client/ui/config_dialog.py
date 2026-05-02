from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from domain.constants import DEFAULT_TIER_SCORE, THEME_LABELS, TIER_LIST
from repositories.dataset_repository import (
    load_config,
    load_server_base_url,
    load_theme_mode,
    save_config,
    save_server_base_url,
    save_theme_mode,
)


class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("설정")
        self.resize(520, 380)

        layout = QVBoxLayout()
        self.inputs = {}

        config = load_config()

        for tier in TIER_LIST:
            row = QHBoxLayout()

            label = QLabel(tier)
            spin = QSpinBox()
            spin.setRange(1, 1000)
            spin.setValue(config.get(tier, DEFAULT_TIER_SCORE[tier]))

            row.addWidget(label)
            row.addWidget(spin)
            layout.addLayout(row)
            self.inputs[tier] = spin

        server_row = QHBoxLayout()
        server_row.addWidget(QLabel("서버 주소"))
        self.server_url_input = QLineEdit()
        self.server_url_input.setText(load_server_base_url())
        server_row.addWidget(self.server_url_input)
        layout.addLayout(server_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("테마 모드"))
        self.theme_mode_combo = QComboBox()
        self.theme_mode_combo.addItem(THEME_LABELS["dark"], "dark")
        self.theme_mode_combo.addItem(THEME_LABELS["light"], "light")
        current_theme = load_theme_mode()
        current_index = self.theme_mode_combo.findData(current_theme)
        if current_index >= 0:
            self.theme_mode_combo.setCurrentIndex(current_index)
        theme_row.addWidget(self.theme_mode_combo)
        layout.addLayout(theme_row)

        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save(self):
        score_map = {
            tier: spin.value()
            for tier, spin in self.inputs.items()
        }

        save_config(score_map)
        save_server_base_url(self.server_url_input.text().strip())
        save_theme_mode(self.theme_mode_combo.currentData())
        QMessageBox.information(self, "완료", "설정이 저장되었습니다.")
        self.accept()
