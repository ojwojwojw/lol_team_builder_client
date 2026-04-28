from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QMessageBox
)
from util.constants import TIER_LIST, DEFAULT_TIER_SCORE
from service.dataset_service import load_config, save_config


class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("티어 가중치 설정")
        self.resize(400, 250)

        layout = QVBoxLayout()
        self.inputs = {}

        # 🔥 저장된 값 로드
        config = load_config()

        for tier in TIER_LIST:
            h = QHBoxLayout()

            label = QLabel(tier)
            spin = QSpinBox()
            ## 가중치 범위 설정 
            spin.setRange(1, 1000) 
            spin.setValue(config.get(tier, DEFAULT_TIER_SCORE[tier]))

            h.addWidget(label)
            h.addWidget(spin)

            layout.addLayout(h)
            self.inputs[tier] = spin

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
        QMessageBox.information(self, "완료", "가중치 저장됨")
        self.accept()