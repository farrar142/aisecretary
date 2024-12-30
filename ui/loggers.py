import logging
from PyQt6.QtWidgets import QPlainTextEdit


class LogHandler(logging.Handler):
    def __init__(self, widget: QPlainTextEdit):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        self.widget.appendPlainText(log_entry)


class QtLogger:
    def setup_logger(self, log_output: QPlainTextEdit):
        self.logger = logging.getLogger("Secretary")
        self.logger.setLevel(logging.DEBUG)

        log_handler = LogHandler(log_output)
        log_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(log_handler)
