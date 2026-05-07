from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
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
    BUILD_WEIGHT_LABELS,
    CANDIDATE_PRIORITY_LABELS,
    DEFAULT_BUILD_PREFERENCES,
    DEFAULT_BUILD_WEIGHTS,
    DEFAULT_TIER_SCORE,
    THEME_LABELS,
    TIER_LIST,
)
from repositories.dataset_repository import (
    load_build_preferences,
    load_build_weights,
    load_config,
    load_server_base_url,
    load_theme_mode,
    save_build_preferences,
    save_build_weights,
    save_config,
    save_server_base_url,
    save_theme_mode,
)


class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("설정")
        self.resize(620, 720)

        layout = QVBoxLayout()
        self.inputs = {}
        self.weight_inputs = {}
        self.priority_inputs = []

        config = load_config()
        build_weights = load_build_weights()
        build_preferences = load_build_preferences()

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

        for key, label_text in BUILD_WEIGHT_LABELS.items():
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

        preference_group = QGroupBox("팀 빌딩 선택 우선순위")
        preference_layout = QVBoxLayout()

        any_position_row = QHBoxLayout()
        any_position_row.addWidget(QLabel("상관없음 포지션 페널티"))
        self.any_position_penalty_input = QSpinBox()
        self.any_position_penalty_input.setRange(0, 1000)
        self.any_position_penalty_input.setValue(
            build_preferences.get(
                "any_position_penalty",
                DEFAULT_BUILD_PREFERENCES["any_position_penalty"],
            )
        )
        any_position_row.addWidget(self.any_position_penalty_input)
        preference_layout.addLayout(any_position_row)

        priority_penalty_form = QFormLayout()
        self.priority_penalty_first_input = QSpinBox()
        self.priority_penalty_first_input.setRange(0, 1000)
        self.priority_penalty_first_input.setValue(
            build_preferences.get(
                "priority_penalty_first",
                DEFAULT_BUILD_PREFERENCES["priority_penalty_first"],
            )
        )
        self.priority_penalty_second_input = QSpinBox()
        self.priority_penalty_second_input.setRange(0, 1000)
        self.priority_penalty_second_input.setValue(
            build_preferences.get(
                "priority_penalty_second",
                DEFAULT_BUILD_PREFERENCES["priority_penalty_second"],
            )
        )
        self.priority_penalty_third_input = QSpinBox()
        self.priority_penalty_third_input.setRange(0, 1000)
        self.priority_penalty_third_input.setValue(
            build_preferences.get(
                "priority_penalty_third",
                DEFAULT_BUILD_PREFERENCES["priority_penalty_third"],
            )
        )
        priority_penalty_form.addRow("1지망 페널티", self.priority_penalty_first_input)
        priority_penalty_form.addRow("2지망 페널티", self.priority_penalty_second_input)
        priority_penalty_form.addRow("3지망 페널티", self.priority_penalty_third_input)
        preference_layout.addLayout(priority_penalty_form)

        max_maps_row = QHBoxLayout()
        max_maps_row.addWidget(QLabel("팀별 배치 검사 개수"))
        self.max_position_maps_input = QSpinBox()
        self.max_position_maps_input.setRange(1, 2000)
        self.max_position_maps_input.setValue(
            build_preferences.get(
                "max_position_maps_per_team",
                DEFAULT_BUILD_PREFERENCES["max_position_maps_per_team"],
            )
        )
        max_maps_row.addWidget(self.max_position_maps_input)
        preference_layout.addLayout(max_maps_row)

        priority_form = QFormLayout()
        selected_priority = build_preferences.get(
            "candidate_priority",
            DEFAULT_BUILD_PREFERENCES["candidate_priority"],
        )
        for index, selected_key in enumerate(selected_priority, start=1):
            combo = QComboBox()
            for key, label_text in CANDIDATE_PRIORITY_LABELS.items():
                combo.addItem(label_text, key)
            selected_index = combo.findData(selected_key)
            if selected_index >= 0:
                combo.setCurrentIndex(selected_index)
            priority_form.addRow(f"{index}순위", combo)
            self.priority_inputs.append(combo)

        preference_layout.addLayout(priority_form)
        preference_group.setLayout(preference_layout)
        layout.addWidget(preference_group)

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
        priority_order = [combo.currentData() for combo in self.priority_inputs]

        if len(set(priority_order)) != len(priority_order):
            QMessageBox.warning(
                self,
                "설정 오류",
                "후보 우선순위는 같은 항목을 중복해서 선택할 수 없습니다.",
            )
            return

        build_preferences = {
            "any_position_penalty": self.any_position_penalty_input.value(),
            "priority_penalty_first": self.priority_penalty_first_input.value(),
            "priority_penalty_second": self.priority_penalty_second_input.value(),
            "priority_penalty_third": self.priority_penalty_third_input.value(),
            "max_position_maps_per_team": self.max_position_maps_input.value(),
            "candidate_priority": priority_order,
        }

        save_config(score_map)
        save_build_weights(weight_map)
        save_build_preferences(build_preferences)
        save_server_base_url(self.server_url_input.text().strip())
        save_theme_mode(self.theme_mode_combo.currentData())
        QMessageBox.information(self, "완료", "설정이 저장되었습니다.")
        self.accept()
