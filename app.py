import logging
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal

from layout_colorwidget import Color
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QStackedLayout,
    QLayout,
    QPlainTextEdit,
)


import sys

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
    QTabWidget,
)

from layout_colorwidget import Color
from ui.component import Component
from ui.loggers import QtLogger
from ui.tabs.setting_tabs.setting_tab import SettingTab


class AIThread(QThread):
    update_signal = pyqtSignal(str)

    def run(self) -> None:
        from main import main

        main()


class MainTab(QWidget):

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout()
        label = QLabel("Main")
        layout.addWidget(label)
        self.setLayout(layout)
        self.worker_thread = AIThread()
        self.worker_thread.update_signal.connect(self.update_log)
        self.worker_thread.start()

    def update_log(self, message: str):
        main_window = Component.inject("main_window")
        main_window.info(message)


@Component("main_window")
@Component("logger")
class MainWindow(QMainWindow, QtLogger):
    main_tab = Component.inject("main_tab")

    def __init__(self):
        super().__init__()

        tabs = QTabWidget()
        main_tab = MainTab()
        setting_tab = SettingTab()
        tabs.addTab(main_tab, "Main")
        tabs.addTab(setting_tab, "Setting")

        log_output = QPlainTextEdit(self)
        log_output.setReadOnly(True)

        hbox = QHBoxLayout()
        close_button = QPushButton("Exit")
        log_button = QPushButton("Generate Log", self)
        hbox.addWidget(close_button)
        hbox.addWidget(log_button)

        vbox = QVBoxLayout()
        vbox.addWidget(tabs)
        vbox.addWidget(log_output)
        vbox.addLayout(hbox)

        widget = QWidget()
        widget.setLayout(vbox)

        self.setCentralWidget(widget)

        self.setWindowTitle("Secretary")
        self.setMinimumSize(400, 300)
        self.setup_logger(log_output)

    def info(self, message: str):
        self.logger.info(message)


app = Component.initialize_app()
window = MainWindow()
window.show()
print(Component.inject("main_window"))
print(Component.inject("logger"))
app.exec()
