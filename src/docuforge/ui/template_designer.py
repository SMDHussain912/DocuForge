"""Visual rich-text template designer with persistent inline data-field chips."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFontComboBox, QHBoxLayout, QLabel, QListWidget,
    QMessageBox, QPushButton, QSplitter, QTextBrowser, QTextEdit, QToolBar,
    QVBoxLayout, QWidget,
)

from docuforge.templates.spreadsheet import list_sheets, read_columns_and_sample
from docuforge.templates.template_file import load_template, save_template

_FIELD_TOKEN = re.compile(r"⟦DFG:([0-9a-f-]{36})⟧")


class TemplateDesigner(QWidget):
    """Author a free-form document and insert data fields at the text cursor."""

    status_message = Signal(str)

    def __init__(self, registered_sources: list[str]) -> None:
        super().__init__()
        self.registered_sources = registered_sources
        self.current_template_path: Path | None = None
        self.current_source_path: Path | None = None
        self.sample_record: dict[str, Any] = {}
        self.columns: list[str] = []
        self.fields: dict[str, dict[str, Any]] = {}
        self._loading = False
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
        self.source_combo.setMinimumWidth(220)
        self.sheet_combo = QComboBox()
        self.sheet_combo.setMinimumWidth(140)
        self.refresh_button = QPushButton("Load fields")
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
        left_layout.addWidget(QLabel("DATA FIELDS"))
        self.field_list = QListWidget()
        self.field_list.setToolTip("Double-click a field to insert it at the document cursor.")
        self.field_list.itemDoubleClicked.connect(self._insert_selected_field)
        left_layout.addWidget(self.field_list, 1)
        insert_button = QPushButton("＋ Insert field at cursor")
        insert_button.setObjectName("PrimaryButton")
        insert_button.clicked.connect(self._insert_selected_field)
        left_layout.addWidget(insert_button)
        left_layout.addWidget(QLabel("Tip: click inside the document first, then insert a field."))

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(QLabel("DOCUMENT DESIGNER"))
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self._build_toolbar()
        center_layout.addWidget(self.toolbar)
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText(
            "Start designing your document here…\n\n"
            "Write anything, position the cursor wherever a value belongs, "
            "then insert a field from the Data Fields panel."
        )
        center_layout.addWidget(self.editor, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("LIVE RECORD PREVIEW"))
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(False)
        right_layout.addWidget(self.preview, 1)
        preview_button = QPushButton("Refresh preview")
        preview_button.clicked.connect(self._refresh_preview)
        right_layout.addWidget(preview_button)

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setSizes([220, 600, 340])
        root.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        new_button = QPushButton("New template")
        new_button.clicked.connect(self.new_template)
        open_button = QPushButton("Open template…")
        open_button.clicked.connect(self.open_template)
        save_as_button = QPushButton("Save as…")
        save_as_button.clicked.connect(self.save_template_as)
        save_button = QPushButton("Save")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_template)
        bottom.addWidget(new_button)
        bottom.addWidget(open_button)
        bottom.addStretch()
        bottom.addWidget(save_as_button)
        bottom.addWidget(save_button)
        root.addLayout(bottom)
        self.editor.textChanged.connect(self._refresh_preview)

    def _build_toolbar(self) -> None:
        for label, kind in (("B", "bold"), ("I", "italic"), ("U", "underline")):
            action = QAction(label, self)
            action.setToolTip(kind.title())
            action.setCheckable(True)
            action.triggered.connect(lambda checked, value=kind: self._toggle_format(value, checked))
            self.toolbar.addAction(action)
        self.toolbar.addSeparator()
        self.font_family = QFontComboBox()
        self.font_family.currentFontChanged.connect(self._set_font)
        self.toolbar.addWidget(self.font_family)
        self.font_size = QComboBox()
        self.font_size.addItems(["9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32"])
        self.font_size.setCurrentText("11")
        self.font_size.currentTextChanged.connect(self._set_font_size)
        self.toolbar.addWidget(self.font_size)
        self.toolbar.addSeparator()
        for label, alignment in (
            ("Left", Qt.AlignmentFlag.AlignLeft),
            ("Center", Qt.AlignmentFlag.AlignHCenter),
            ("Right", Qt.AlignmentFlag.AlignRight),
        ):
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=alignment: self.editor.setAlignment(value)
            )
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
        if value:
            fmt = self.editor.currentCharFormat()
            fmt.setFontPointSize(float(value))
            self.editor.mergeCurrentCharFormat(fmt)

    def _populate_sources(self) -> None:
        self.source_combo.clear()
        for source in self.registered_sources:
            path = Path(source)
            if path.exists() and path.suffix.lower() in {".xlsx", ".xlsm", ".ods", ".csv"}:
                self.source_combo.addItem(path.name, str(path))
        if self.source_combo.count():
            self._load_selected_source()
        else:
            self.field_list.clear()
            self.columns = []
            self.sample_record = {}
            self.current_source_path = None
            self._refresh_preview()

    def update_registered_sources(self, paths: list[str]) -> None:
        self.registered_sources = paths
        self._populate_sources()

    def _load_selected_source(self) -> None:
        source = self.source_combo.currentData()
        if not source:
            QMessageBox.information(
                self, "No data source", "Add a spreadsheet or CSV in Data Sources first."
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
            self.columns, self.sample_record = read_columns_and_sample(
                self.current_source_path, self.sheet_combo.currentText() or None
            )
            self.field_list.clear()
            self.field_list.addItems(self.columns)
            self._refresh_preview()
            self.status_message.emit(f"Loaded {len(self.columns)} fields.")
        except Exception as exc:
            QMessageBox.critical(self, "Could not load fields", str(exc))

    def _insert_selected_field(self, *_args: object) -> None:
        item = self.field_list.currentItem()
        if item is None:
            QMessageBox.information(self, "Select a field", "Choose a field from the Data Fields panel.")
            return
        if self.current_source_path is None:
            QMessageBox.information(self, "No source", "Connect a data source before inserting fields.")
            return

        column = item.text()
        field_id = str(uuid4())
        token = f"⟦DFG:{field_id}⟧"
        metadata = {
            "id": field_id,
            "source_id": str(self.current_source_path.resolve()),
            "table_id": self.sheet_combo.currentText() or self.current_source_path.stem,
            "column_id": column,
            "display_name": column,
            "fallback": "",
            "format_kind": "text",
        }
        self.fields[field_id] = metadata
        fmt = QTextCharFormat(self.editor.currentCharFormat())
        fmt.setForeground(QColor("#174EA6"))
        fmt.setBackground(QColor("#DCEBFF"))
        fmt.setFontWeight(QFont.Weight.DemiBold)
        fmt.setToolTip(f"Data field: {column}")
        cursor = self.editor.textCursor()
        cursor.insertText(token, fmt)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self._refresh_preview()

    def _render_preview_html(self) -> str:
        rendered = self.editor.toHtml()

        def replace(match: re.Match[str]) -> str:
            field_id = match.group(1)
            metadata = self.fields.get(field_id)
            if metadata is None:
                return html.escape("[Missing field]")
            name = metadata.get("column_id", "")
            value = self.sample_record.get(name, metadata.get("fallback", ""))
            return html.escape("" if value is None else str(value))

        return _FIELD_TOKEN.sub(replace, rendered)

    def _refresh_preview(self) -> None:
        if hasattr(self, "preview"):
            self.preview.setHtml(self._render_preview_html())

    def new_template(self) -> None:
        self.current_template_path = None
        self.template_title.setText("Untitled template")
        self.fields.clear()
        self._loading = True
        self.editor.clear()
        self._loading = False
        self._refresh_preview()

    def open_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open DocuForge template", str(Path.home()),
            "DocuForge templates (*.dfgtpl)",
        )
        if path:
            self.open_template_path(Path(path))

    def open_template_path(self, path: Path) -> None:
        try:
            payload = load_template(path)
            self._loading = True
            self.editor.setHtml(payload["html"])
            self.fields = dict(payload.get("fields", {}))
            self.current_template_path = path
            self.template_title.setText(payload.get("title", path.stem))
            source_path = payload.get("data_source", "")
            index = self.source_combo.findData(source_path)
            if index >= 0:
                self.source_combo.setCurrentIndex(index)
                self._load_selected_source()
                sheet_index = self.sheet_combo.findText(payload.get("sheet", ""))
                if sheet_index >= 0:
                    self.sheet_combo.setCurrentIndex(sheet_index)
                    self._load_columns()
            self._loading = False
            self._refresh_preview()
            self.status_message.emit(f"Opened template: {path.name}")
        except Exception as exc:
            self._loading = False
            QMessageBox.critical(self, "Could not open template", str(exc))

    def save_template(self) -> None:
        if self.current_template_path is None:
            self.save_template_as()
        else:
            self._save_to_path(self.current_template_path)

    def save_template_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save DocuForge template", str(Path.home() / "Untitled.dfgtpl"),
            "DocuForge templates (*.dfgtpl)",
        )
        if path:
            target = Path(path)
            if target.suffix.lower() != ".dfgtpl":
                target = target.with_suffix(".dfgtpl")
            self._save_to_path(target)

    def _save_to_path(self, path: Path) -> None:
        try:
            source = str(self.current_source_path) if self.current_source_path else ""
            save_template(
                path,
                title=path.stem,
                html=self.editor.toHtml(),
                source_path=source,
                sheet_name=self.sheet_combo.currentText(),
                fields=self.fields,
            )
            self.current_template_path = path
            self.template_title.setText(path.stem)
            self.status_message.emit(f"Saved template: {path.name}")
            QMessageBox.information(self, "Template saved", f"Saved {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Could not save template", str(exc))
