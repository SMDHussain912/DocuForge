"""Desktop application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    """Initial application window; feature screens will be added in later phases."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DocuForge")
        self.resize(1100, 720)

        welcome = QLabel(
            "DocuForge\n\n"
            "Document generation workspace\n"
            "Foundation initialized. Feature modules are coming next."
        )
        welcome.setWordWrap(True)
        welcome.setMargin(32)
        self.setCentralWidget(welcome)


def main() -> int:
    """Create and run the Qt application."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
