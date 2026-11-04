"""DocuForge desktop application entry point.

The first UI milestone provides persistent workspace preferences, navigation,
and local registration of source/template files. Document generation is added
in a later milestone.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont
from docuforge.ui.template_designer import TemplateDesigner

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


APP_ORGANIZATION = "DocuForge"
APP_NAME = "DocuForge"
ACCENTS = {
    "Blue": "#3978F6",
    "Violet": "#8B5CF6",
    "Teal": "#0D9488",
    "Green": "#16A34A",
    "Orange": "#EA580C",
    "Rose": "#E11D48",
}


class Preferences:
    """Small persistent preferences store backed by Qt's platform settings."""

    def __init__(self) -> None:
        self.store = QSettings(APP_ORGANIZATION, APP_NAME)

    def get(self, key: str, default: object) -> object:
        return self.store.value(key, default)

    def set(self, key: str, value: object) -> None:
        self.store.setValue(key, value)

    def string_list(self, key: str) -> list[str]:
        value = self.store.value(key, [])
        if isinstance(value, str):
            return [value] if value else []
        return [str(item) for item in value]


def make_card(title: str, description: str) -> QFrame:
    card = QFrame()
    card.setObjectName("InfoCard")
    layout = QVBoxLayout(card)
    heading = QLabel(title)
    heading.setObjectName("CardHeading")
    body = QLabel(description)
    body.setObjectName("Muted")
    body.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(body)
    return card


class MainWindow(QMainWindow):
    """Main DocuForge workspace."""

    def __init__(self) -> None:
        super().__init__()
        self.preferences = Preferences()
        self.setWindowTitle("DocuForge")
        self.resize(1180, 780)
        self.setMinimumSize(900, 620)
        self._build_shell()
        self._build_pages()
        self._load_registered_files()
        self._apply_preferences()
        self.navigate("Dashboard")

    def _build_shell(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(218)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(16, 22, 16, 18)
        side_layout.setSpacing(8)

        brand = QLabel("DocuForge")
        brand.setObjectName("Brand")
        side_layout.addWidget(brand)
        tagline = QLabel("DOCUMENT WORKSPACE")
        tagline.setObjectName("SidebarCaption")
        side_layout.addWidget(tagline)
        side_layout.addSpacing(24)

        self.nav_buttons: dict[str, QPushButton] = {}
        for name in ("Dashboard", "Data Sources", "Templates", "Template Designer", "Generate", "History", "Settings"):
            button = QPushButton(name)
            button.setObjectName("NavButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, page=name: self.navigate(page))
            side_layout.addWidget(button)
            self.nav_buttons[name] = button

        side_layout.addStretch()
        version = QLabel("DocuForge 0.1.0 · Foundation")
        version.setObjectName("SidebarCaption")
        side_layout.addWidget(version)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 22, 28, 24)
        content_layout.setSpacing(18)

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel("Your document generation workspace.")
        self.page_subtitle.setObjectName("Muted")
        content_layout.addWidget(self.page_title)
        content_layout.addWidget(self.page_subtitle)

        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages, 1)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

    def _build_pages(self) -> None:
        self.page_index: dict[str, int] = {}
        self.pages.addWidget(self._dashboard_page())
        self.page_index["Dashboard"] = 0
        self.pages.addWidget(self._sources_page())
        self.page_index["Data Sources"] = 1
        self.pages.addWidget(self._templates_page())
        self.page_index["Templates"] = 2
        self.template_designer = TemplateDesigner(
            self.preferences.string_list("registry/sources")
        )
        self.pages.addWidget(self.template_designer)
        self.page_index["Template Designer"] = 3
        self.pages.addWidget(self._generate_page())
        self.page_index["Generate"] = 4
        self.pages.addWidget(self._history_page())
        self.page_index["History"] = 5
        self.pages.addWidget(self._settings_page())
        self.page_index["Settings"] = 6

    def _section_heading(self, title: str, detail: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QLabel(title)
        heading.setObjectName("SectionHeading")
        description = QLabel(detail)
        description.setObjectName("Muted")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)
        return widget

    def _dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._section_heading(
            "Welcome to DocuForge",
            "Prepare data, choose a template, and create consistent documents in batches.",
        ))

        cards = QHBoxLayout()
        cards.addWidget(make_card("Data sources", "Register spreadsheet files and manage the inputs used by your projects."))
        cards.addWidget(make_card("Templates", "Keep reusable document templates in one place."))
        cards.addWidget(make_card("Generation", "Configure output options and review batches before exporting."))
        layout.addLayout(cards)

        next_steps = QFrame()
        next_steps.setObjectName("InfoCard")
        steps_layout = QVBoxLayout(next_steps)
        steps_title = QLabel("Getting started")
        steps_title.setObjectName("CardHeading")
        steps_layout.addWidget(steps_title)
        for step in (
            "1. Add an XLSX, ODS, or CSV data source.",
            "2. Register a document template.",
            "3. Configure field mappings and output naming.",
            "4. Preview and generate your documents.",
        ):
            label = QLabel(step)
            label.setObjectName("StepText")
            steps_layout.addWidget(label)
        layout.addWidget(next_steps)
        layout.addStretch()
        return page

    def _sources_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._section_heading(
            "Data sources",
            "Register local spreadsheet and delimited-text files. Registration stores file paths; it does not modify source files.",
        ))
        self.source_list = QListWidget()
        self.source_list.setObjectName("FileList")
        layout.addWidget(self.source_list, 1)
        actions = QHBoxLayout()
        add_button = QPushButton("Add data file")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self._add_source)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(lambda: self._remove_selected(self.source_list, "sources"))
        actions.addWidget(add_button)
        actions.addWidget(remove_button)
        actions.addStretch()
        layout.addLayout(actions)
        return page

    def _templates_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._section_heading(
            "Templates",
            "Register reusable ODT and DOCX template files. Template parsing and placeholder mapping will be implemented in the template-engine milestone.",
        ))
        self.template_list = QListWidget()
        self.template_list.setObjectName("FileList")
        layout.addWidget(self.template_list, 1)
        actions = QHBoxLayout()
        add_button = QPushButton("Add template")
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self._add_template)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(lambda: self._remove_selected(self.template_list, "templates"))
        actions.addWidget(add_button)
        actions.addWidget(remove_button)
        actions.addStretch()
        layout.addLayout(actions)
        return page

    def _generate_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._section_heading(
            "Document generation",
            "The generation workflow will connect selected data, templates, field mappings, and export settings.",
        ))
        notice = make_card(
            "Generation engine is under development",
            "The current milestone provides the workspace and file registration. We will add data inspection, template mapping, batch preview, collision checks, and export as separate tested components.",
        )
        layout.addWidget(notice)
        layout.addStretch()
        return page

    def _history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._section_heading(
            "Generation history",
            "Completed and failed batch records will appear here once the generation engine is implemented.",
        ))
        layout.addWidget(make_card("No generation runs yet", "There are no generation records to display."))
        layout.addStretch()
        return page

    def _settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._section_heading(
            "Workspace preferences",
            "Customize the appearance and default behavior of this DocuForge installation. Preferences are saved locally.",
        ))

        form = QVBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(list(ACCENTS))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(9, 18)
        self.font_spin.setSuffix(" pt")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "ODT", "DOCX"])
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Choose a default output folder")
        browse_button = QPushButton("Browse…")
        browse_button.clicked.connect(self._browse_output)

        self._add_setting_row(form, "Appearance", self.theme_combo)
        self._add_setting_row(form, "Accent color", self.accent_combo)
        self._add_setting_row(form, "Interface font size", self.font_spin)
        self._add_setting_row(form, "Default export format", self.format_combo)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(browse_button)
        self._add_setting_row(form, "Default output folder", output_row)

        layout.addLayout(form)
        buttons = QHBoxLayout()
        save_button = QPushButton("Save preferences")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self._save_preferences)
        reset_button = QPushButton("Reset defaults")
        reset_button.clicked.connect(self._reset_preferences)
        buttons.addWidget(save_button)
        buttons.addWidget(reset_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        layout.addStretch()
        return page

    def _add_setting_row(self, parent: QVBoxLayout, label_text: str, control: QWidget | QHBoxLayout) -> None:
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(180)
        row.addWidget(label)
        if isinstance(control, QHBoxLayout):
            row.addLayout(control, 1)
        else:
            row.addWidget(control, 1)
        parent.addLayout(row)

    def navigate(self, page_name: str) -> None:
        index = self.page_index[page_name]
        self.pages.setCurrentIndex(index)
        self.page_title.setText(page_name)
        subtitles = {
            "Dashboard": "Your document generation workspace.",
            "Data Sources": "Manage the files that provide your document data.",
            "Templates": "Manage reusable document layouts.",
            "Template Designer": "Design document layouts and insert spreadsheet fields.",
            "Generate": "Prepare and run document-generation batches.",
            "History": "Review previous generation activity.",
            "Settings": "Personalize your DocuForge workspace.",
        }
        self.page_subtitle.setText(subtitles[page_name])
        for name, button in self.nav_buttons.items():
            button.setProperty("active", name == page_name)
            button.style().unpolish(button)
            button.style().polish(button)

    def _apply_preferences(self) -> None:
        self.theme_combo.setCurrentText(str(self.preferences.get("appearance/theme", "System")))
        self.accent_combo.setCurrentText(str(self.preferences.get("appearance/accent", "Blue")))
        self.font_spin.setValue(int(self.preferences.get("appearance/font_size", 10)))
        self.format_combo.setCurrentText(str(self.preferences.get("output/format", "PDF")))
        self.output_edit.setText(str(self.preferences.get("output/directory", str(Path.home() / "Documents"))))
        self._apply_theme()

    def _apply_theme(self) -> None:
        theme = self.theme_combo.currentText()
        accent = ACCENTS.get(self.accent_combo.currentText(), ACCENTS["Blue"])
        app = QApplication.instance()
        if app is None:
            return
        if theme == "System":
            dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        else:
            dark = theme == "Dark"

        if dark:
            background, surface, text, muted, border = "#1E2025", "#292C33", "#F2F3F5", "#A7ADB8", "#3B404A"
            sidebar = "#191B20"
        else:
            background, surface, text, muted, border = "#F4F6FA", "#FFFFFF", "#202633", "#667085", "#E0E5ED"
            sidebar = "#FFFFFF"

        app.setFont(QFont(app.font().family(), self.font_spin.value()))
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {background}; color: {text}; }}
            #Sidebar {{ background: {sidebar}; border-right: 1px solid {border}; }}
            #Brand {{ font-size: 22px; font-weight: 700; color: {accent}; }}
            #SidebarCaption {{ color: {muted}; font-size: 10px; letter-spacing: 1px; }}
            #PageTitle {{ font-size: 25px; font-weight: 700; }}
            #SectionHeading {{ font-size: 19px; font-weight: 650; }}
            #Muted {{ color: {muted}; }}
            #CardHeading {{ font-size: 15px; font-weight: 650; }}
            #StepText {{ padding: 5px 0; }}
            #InfoCard, #FileList {{ background: {surface}; border: 1px solid {border}; border-radius: 10px; padding: 14px; }}
            #NavButton {{ text-align: left; padding: 11px 12px; border: 0; border-radius: 7px; background: transparent; }}
            #NavButton:hover {{ background: {surface}; }}
            #NavButton[active="true"] {{ background: {accent}; color: white; font-weight: 650; }}
            QPushButton {{ padding: 8px 13px; border: 1px solid {border}; border-radius: 7px; background: {surface}; }}
            QPushButton:hover {{ border-color: {accent}; }}
            #PrimaryButton {{ background: {accent}; color: white; border: 0; font-weight: 650; }}
            #PrimaryButton:hover {{ opacity: 0.9; }}
            QLineEdit, QComboBox, QSpinBox {{ background: {surface}; border: 1px solid {border}; border-radius: 6px; padding: 8px; min-height: 20px; }}
            QListWidget {{ outline: 0; }}
            QListWidget::item {{ padding: 9px; border-bottom: 1px solid {border}; }}
        """)

    def _save_preferences(self) -> None:
        self.preferences.set("appearance/theme", self.theme_combo.currentText())
        self.preferences.set("appearance/accent", self.accent_combo.currentText())
        self.preferences.set("appearance/font_size", self.font_spin.value())
        self.preferences.set("output/format", self.format_combo.currentText())
        self.preferences.set("output/directory", self.output_edit.text().strip())
        self._apply_theme()
        QMessageBox.information(self, "Preferences saved", "Your workspace preferences have been saved.")

    def _reset_preferences(self) -> None:
        self.theme_combo.setCurrentText("System")
        self.accent_combo.setCurrentText("Blue")
        self.font_spin.setValue(10)
        self.format_combo.setCurrentText("PDF")
        self.output_edit.setText(str(Path.home() / "Documents"))
        self._save_preferences()

    def _browse_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self, "Choose default output folder", self.output_edit.text()
        )
        if selected:
            self.output_edit.setText(selected)

    def _add_source(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add data source",
            str(Path.home()),
            "Supported data files (*.xlsx *.xlsm *.ods *.csv);;All files (*)",
        )
        self._register_files(paths, self.source_list, "sources")

    def _add_template(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add document template",
            str(Path.home()),
            "Document templates (*.odt *.docx);;All files (*)",
        )
        self._register_files(paths, self.template_list, "templates")

    def _register_files(self, paths: list[str], widget: QListWidget, key: str) -> None:
        current = self.preferences.string_list(f"registry/{key}")
        for raw_path in paths:
            path = str(Path(raw_path).expanduser().resolve())
            if path not in current:
                current.append(path)
        self.preferences.set(f"registry/{key}", current)
        self._refresh_file_list(widget, current)
        if key == "sources" and hasattr(self, "template_designer"):
            self.template_designer.update_registered_sources(current)

    def _remove_selected(self, widget: QListWidget, key: str) -> None:
        selected = widget.currentItem()
        if selected is None:
            return
        current = self.preferences.string_list(f"registry/{key}")
        path = selected.data(Qt.ItemDataRole.UserRole)
        if path in current:
            current.remove(path)
        self.preferences.set(f"registry/{key}", current)
        self._refresh_file_list(widget, current)

    def _refresh_file_list(self, widget: QListWidget, paths: list[str]) -> None:
        widget.clear()
        for path in paths:
            label = QListWidgetItemLabel(path)
            widget.addItem(label)

    def _load_registered_files(self) -> None:
        self._refresh_file_list(self.source_list, self.preferences.string_list("registry/sources"))
        self._refresh_file_list(self.template_list, self.preferences.string_list("registry/templates"))


class QListWidgetItemLabel:
    """Small helper that stores the full path while showing a readable filename."""

    def __new__(cls, path: str):
        from PySide6.QtWidgets import QListWidgetItem

        item = QListWidgetItem(Path(path).name)
        item.setToolTip(path)
        item.setData(Qt.ItemDataRole.UserRole, path)
        return item


def main() -> int:
    """Create and run the Qt application."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
