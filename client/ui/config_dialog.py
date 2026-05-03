from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from domain.constants import (
    DEFAULT_BUILD_WEIGHTS,
    DEFAULT_TIER_SCORE,
    THEME_LABELS,
    TIER_LIST,
)
from repositories.dataset_repository import (
    load_build_weights,
    load_config,
    load_server_base_url,
    load_theme_mode,
    save_build_weights,
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
        self.weight_inputs = {}

        config = load_config()
        build_weights = load_build_weights()

        tier_group = QGroupBox("티어 점수 가중치")
        tier_layout = QVBoxLayout()

        for tier in TIER_LIST:
            if tier not in DEFAULT_TIER_SCORE:
                continue
            row = QHBoxLayout()

            label = QLabel(tier)
            spin = QSpinBox()
            spin.setRange(1, 1000)
            spin.setValue(config.get(tier, DEFAULT_TIER_SCORE[tier]))

            row.addWidget(label)
            row.addWidget(spin)
            tier_layout.addLayout(row)
            self.inputs[tier] = spin

        tier_group.setLayout(tier_layout)
        layout.addWidget(tier_group)

        weight_group = QGroupBox("팀 빌딩 계산 가중치")
        weight_layout = QVBoxLayout()
        weight_labels = {
            "team_diff": "팀 총점 차이",
            "line_diff_total": "라인 점수 차이 합",
            "position_penalty": "선호 포지션 페널티",
            "bottom_penalty": "봇 듀오 밸런스 페널티",
            "team_form_diff": "팀 최근 폼 차이",
            "couple_group_penalty": "커플매칭 중요도",
        }

        for key, label_text in weight_labels.items():
            row = QHBoxLayout()
            label = QLabel(label_text)
            spin = QSpinBox()
            spin.setRange(0, 1000)
            spin.setValue(build_weights.get(key, DEFAULT_BUILD_WEIGHTS[key]))
            row.addWidget(label)
            row.addWidget(spin)
            weight_layout.addLayout(row)
            self.weight_inputs[key] = spin

        weight_group.setLayout(weight_layout)
        layout.addWidget(weight_group)

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
        weight_map = {
            key: spin.value()
            for key, spin in self.weight_inputs.items()
        }

        save_config(score_map)
        save_build_weights(weight_map)
        save_server_base_url(self.server_url_input.text().strip())
        save_theme_mode(self.theme_mode_combo.currentData())
        QMessageBox.information(self, "완료", "설정이 저장되었습니다.")
        self.accept()
