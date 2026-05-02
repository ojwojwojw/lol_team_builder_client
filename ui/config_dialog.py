from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from service.dataset_service import (
    load_config,
    load_server_base_url,
    save_config,
    save_server_base_url,
)
from util.constants import DEFAULT_TIER_SCORE, TIER_LIST


class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("설정")
        self.resize(500, 320)

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
        QMessageBox.information(self, "완료", "설정이 저장되었습니다.")
        self.accept()
