from PyQt6.QtWidgets import *

from settings import Setting
from ui.component import Component


class SettingTab(QWidget):
    logger = Component.inject("logger")

    def __init__(self) -> None:
        super().__init__()
        self.initUi()

    def initUi(self):  # Main widget and layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # OPEN_AI_KEY
        self.open_ai_key_input = self.create_input_row(
            "OPEN_AI_KEY:", main_layout, Setting.OPEN_AI_KEY
        )

        # SECRETARY_NAMES
        self.secretary_names_input = self.create_input_row(
            "SECRETARY_NAMES (comma-separated):",
            main_layout,
            default=",".join(Setting.SECRETARY_NAMES),
        )

        # DISCORD_WEBHOOK_URL
        self.discord_webhook_url_input = self.create_input_row(
            "DISCORD_WEBHOOK_URL:", main_layout, Setting.DISCORD_WEBHOOK_URL
        )

        # RECORD_DEVICE
        self.record_device_spinbox = self.create_spinbox_row(
            "RECORD_DEVICE:", 0, 10, Setting.RECORD_DEVICE, main_layout
        )

        # CHAT_LIMIT_PER_SESSION
        self.chat_limit_spinbox = self.create_spinbox_row(
            "CHAT_LIMIT_PER_SESSION:",
            1,
            10,
            Setting.CHAT_LIMIT_PER_SESSION,
            main_layout,
        )

        # CHAT_GPT_MODEL_NAME
        self.chat_gpt_model_input = self.create_input_row(
            "CHAT_GPT_MODEL_NAME:", main_layout, Setting.CHAT_GPT_MODEL_NAME
        )

        # WHISPER_DEVICE
        self.whisper_device_combobox = self.create_combobox_row(
            "WHISPER_DEVICE:",
            ["cuda"] + [f"cuda:{i}" for i in range(10)],
            Setting.WHISPER_DEVICE or "cuda",
            main_layout,
        )

        # STT
        self.stt_combobox = self.create_combobox_row(
            "STT:", ["local", "remote"], Setting.STT, main_layout
        )

        # TTS
        self.tts_combobox = self.create_combobox_row(
            "TTS:", ["gtts", "xtts"], Setting.TTS, main_layout
        )

        # Buttons (Save / Cancel)
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.save_settings)
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def create_input_row(
        self, label_text: str, layout: QVBoxLayout, default: str | None = None
    ):
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        input_field = QLineEdit()
        if default:
            input_field.setText(default)
        row_layout.addWidget(label)
        row_layout.addWidget(input_field)
        layout.addLayout(row_layout)
        return input_field

    def create_spinbox_row(
        self,
        label_text: str,
        min_val: int,
        max_val: int,
        default_val: int,
        layout: QVBoxLayout,
    ):
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        row_layout.addWidget(label)
        row_layout.addWidget(spinbox)
        layout.addLayout(row_layout)
        return spinbox

    def create_combobox_row(
        self, label_text: str, options: list[str], default: str, layout: QVBoxLayout
    ):
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        combobox = QComboBox()
        combobox.addItems(options)
        combobox.setCurrentText(default)
        row_layout.addWidget(label)
        row_layout.addWidget(combobox)
        layout.addLayout(row_layout)
        return combobox

    def save_settings(self):
        settings = {
            "OPEN_AI_KEY": self.open_ai_key_input.text(),
            "SECRETARY_NAMES": [
                name.strip() for name in self.secretary_names_input.text().split(",")
            ],
            "DISCORD_WEBHOOK_URL": self.discord_webhook_url_input.text(),
            "RECORD_DEVICE": self.record_device_spinbox.value(),
            "CHAT_LIMIT_PER_SESSION": self.chat_limit_spinbox.value(),
            "CHAT_GPT_MODEL_NAME": self.chat_gpt_model_input.text(),
            "WHISPER_DEVICE": self.whisper_device_combobox.currentText(),
            "STT": self.stt_combobox.currentText(),
            "TTS": self.tts_combobox.currentText(),
        }
        Setting.save(lambda: settings, Setting.json_writer)
        self.logger.info("Settings Saved")
