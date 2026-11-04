"""Rich-text template designer with spreadsheet field insertion and preview."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from docuforge.templates.spreadsheet import list_sheets, read_columns_and_sample
from docuforge.templates.template_file import load_template, save_template


_FIELD_PATTERN = re.compile(r"{{\s*([^{}]+?)\s*}}")


class TemplateDesigner(QWidget):
    """Editable rich-text document with data fields and live sample preview."""

    status_message = Signal(str)

    def __init__(self, registered_sources: list[str]) -> None:
        super().__init__()
        self.registered_sources = registered_sources
        self.current_template_path: Path | None = None
        self.current_source_path: Path | None = None
        self.sample_record: dict[str, Any] = {}
        self.columns: list[str] = []
        self._build_ui()
        self._populate_sources()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.template_title = QLabel("Untitled template")
        self.template_title.setObjectName("SectionHeading")
        self.source_combo = QComboBox()
        self.source_combo.setMinimumWidth(240)
        self.sheet_combo = QComboBox()
        self.sheet_combo.setMinimumWidth(150)
        self.refresh_button = QPushButton("Load columns")
        self.refresh_button.clicked.connect(self._load_selected_source)
        top.addWidget(self.template_title, 1)
        top.addWidget(QLabel("Data source"))
        top.addWidget(self.source_combo)
        top.addWidget(QLabel("Sheet"))
        top.addWidget(self.sheet_combo)
        top.addWidget(self.refresh_button)
        root.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Available spreadsheet columns"))
        self.field_list = QListWidget()
        self.field_list.itemDoubleClicked.connect(self._insert_selected_field)
        left_layout.addWidget(self.field_list, 1)
        insert_button = QPushButton("Insert selected field →")
        insert_button.clicked.connect(self._insert_selected_field)
        left_layout.addWidget(insert_button)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(QLabel("Document editor"))
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self._build_toolbar()
        center_layout.addWidget(self.toolbar)
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText(
            "Start writing your document here…\n\n"
            "Choose a spreadsheet source, load its columns, then insert fields "
            "where their values should appear."
        )
        center_layout.addWidget(self.editor, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("Sample preview"))
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(False)
        right_layout.addWidget(self.preview, 1)
        preview_button = QPushButton("Refresh preview")
        preview_button.clicked.connect(self._refresh_preview)
        right_layout.addWidget(preview_button)

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setSizes([210, 570, 330])
        root.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        new_button = QPushButton("New")
        new_button.clicked.connect(self.new_template)
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_template)
        save_button = QPushButton("Save")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_template)
        save_as_button = QPushButton("Save as…")
        save_as_button.clicked.connect(self.save_template_as)
        bottom.addWidget(new_button)
        bottom.addWidget(open_button)
        bottom.addStretch()
        bottom.addWidget(save_as_button)
        bottom.addWidget(save_button)
        root.addLayout(bottom)

        self.editor.textChanged.connect(self._refresh_preview)

    def _build_toolbar(self) -> None:
        bold = QAction("B", self)
        bold.setToolTip("Bold")
        bold.setCheckable(True)
        bold.triggered.connect(lambda checked: self._toggle_format("bold", checked))
        italic = QAction("I", self)
        italic.setToolTip("Italic")
        italic.setCheckable(True)
        italic.triggered.connect(lambda checked: self._toggle_format("italic", checked))
        underline = QAction("U", self)
        underline.setToolTip("Underline")
        underline.setCheckable(True)
        underline.triggered.connect(lambda checked: self._toggle_format("underline", checked))
        self.toolbar.addAction(bold)
        self.toolbar.addAction(italic)
        self.toolbar.addAction(underline)
        self.toolbar.addSeparator()

        self.font_family = QFontComboBox()
        self.font_family.currentFontChanged.connect(self._set_font)
        self.toolbar.addWidget(self.font_family)
        self.font_size = QComboBox()
        self.font_size.addItems(["9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32"])
        self.font_size.setCurrentText("11")
        self.font_size.currentTextChanged.connect(self._set_font_size)
        self.toolbar.addWidget(self.font_size)

        for label, alignment in (
            ("Left", Qt.AlignmentFlag.AlignLeft),
            ("Center", Qt.AlignmentFlag.AlignHCenter),
            ("Right", Qt.AlignmentFlag.AlignRight),
        ):
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, value=alignment: self.editor.setAlignment(value))
            self.toolbar.addAction(action)

    def _toggle_format(self, kind: str, enabled: bool) -> None:
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()
        if kind == "bold":
            fmt.setFontWeight(QFont.Weight.Bold if enabled else QFont.Weight.Normal)
        elif kind == "italic":
            fmt.setFontItalic(enabled)
        elif kind == "underline":
            fmt.setFontUnderline(enabled)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _set_font(self, font: QFont) -> None:
        fmt = self.editor.currentCharFormat()
        fmt.setFontFamily(font.family())
        self.editor.mergeCurrentCharFormat(fmt)

    def _set_font_size(self, value: str) -> None:
        if not value:
            return
        fmt = self.editor.currentCharFormat()
        fmt.setFontPointSize(float(value))
        self.editor.mergeCurrentCharFormat(fmt)

    def _populate_sources(self) -> None:
        self.source_combo.clear()
        for source in self.registered_sources:
            path = Path(source)
            if path.exists() and path.suffix.lower() in {".xlsx", ".xlsm", ".csv"}:
                self.source_combo.addItem(path.name, str(path))
        if self.source_combo.count():
            self._load_selected_source()

    def update_registered_sources(self, paths: list[str]) -> None:
        self.registered_sources = paths
        self._populate_sources()

    def _load_selected_source(self) -> None:
        source = self.source_combo.currentData()
        if not source:
            QMessageBox.information(
                self, "No data source", "Register an XLSX, XLSM, or CSV file in Data Sources first."
            )
            return
        try:
            path = Path(str(source))
            sheets = list_sheets(path)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheets)
            self.current_source_path = path
            self._load_columns()
        except Exception as exc:
            QMessageBox.critical(self, "Could not read data source", str(exc))

    def _load_columns(self) -> None:
        if self.current_source_path is None:
            return
        try:
            sheet = self.sheet_combo.currentText() or None
            self.columns, self.sample_record = read_columns_and_sample(
                self.current_source_path, sheet
            )
            self.field_list.clear()
            self.field_list.addItems(self.columns)
            self._refresh_preview()
            self.status_message.emit(f"Loaded {len(self.columns)} columns.")
        except Exception as exc:
            QMessageBox.critical(self, "Could not load columns", str(exc))

    def _insert_selected_field(self, *_args: object) -> None:
        item = self.field_list.currentItem()
        if item is None:
            return
        field_name = item.text()
        cursor = self.editor.textCursor()
        cursor.insertText("{{ " + field_name + " }}")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _render_preview_html(self) -> str:
        rendered = self.editor.toHtml()

        def replace(match: re.Match[str]) -> str:
            name = match.group(1).strip()
            value = self.sample_record.get(name, f"[Unknown field: {name}]")
            return html.escape("" if value is None else str(value))

        return _FIELD_PATTERN.sub(replace, rendered)

    def _refresh_preview(self) -> None:
        if hasattr(self, "preview"):
            self.preview.setHtml(self._render_preview_html())

    def new_template(self) -> None:
        self.current_template_path = None
        self.template_title.setText("Untitled template")
        self.editor.clear()
        self.editor.setPlaceholderText("Write your document and insert spreadsheet fields…")

    def open_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open DocuForge template", str(Path.home()), "DocuForge templates (*.dfgtpl)"
        )
        if not path:
            return
        try:
            payload = load_template(Path(path))
            self.editor.setHtml(payload["html"])
            self.current_template_path = Path(path)
            self.template_title.setText(payload.get("title", Path(path).stem))
            source_path = payload.get("data_source", "")
            index = self.source_combo.findData(source_path)
            if index >= 0:
                self.source_combo.setCurrentIndex(index)
                self._load_selected_source()
                sheet = payload.get("sheet", "")
                sheet_index = self.sheet_combo.findText(sheet)
                if sheet_index >= 0:
                    self.sheet_combo.setCurrentIndex(sheet_index)
                    self._load_columns()
            self._refresh_preview()
        except Exception as exc:
            QMessageBox.critical(self, "Could not open template", str(exc))

    def save_template(self) -> None:
        if self.current_template_path is None:
            self.save_template_as()
            return
        self._save_to_path(self.current_template_path)

    def save_template_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save DocuForge template", str(Path.home() / "Untitled.dfgtpl"),
            "DocuForge templates (*.dfgtpl)",
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() != ".dfgtpl":
            target = target.with_suffix(".dfgtpl")
        self._save_to_path(target)

    def _save_to_path(self, path: Path) -> None:
        try:
            source = str(self.current_source_path) if self.current_source_path else ""
            sheet = self.sheet_combo.currentText()
            save_template(
                path,
                title=path.stem,
                html=self.editor.toHtml(),
                source_path=source,
                sheet_name=sheet,
            )
            self.current_template_path = path
            self.template_title.setText(path.stem)
            self.status_message.emit(f"Saved template: {path.name}")
            QMessageBox.information(self, "Template saved", f"Saved {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Could not save template", str(exc))
