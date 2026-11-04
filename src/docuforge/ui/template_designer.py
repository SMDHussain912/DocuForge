"""Visual rich-text template designer with persistent inline data-field chips."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtCore import QSizeF
from PySide6.QtGui import QAction, QColor, QFont, QTextCharFormat, QTextImageFormat, QDrag
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFontComboBox, QHBoxLayout, QLabel, QListWidget,
    QMessageBox, QPushButton, QSplitter, QTextBrowser, QTextEdit, QToolBar,
    QVBoxLayout, QWidget, QTabWidget, QScrollArea, QInputDialog,
)

from docuforge.templates.spreadsheet import list_sheets, read_columns_and_sample
from docuforge.templates.docx_io import import_docx, export_docx
from docuforge.templates.template_file import load_template, save_template

_FIELD_TOKEN = re.compile(r"⟦DFG:([0-9a-f-]{36})⟧|«([^»]+)»")


class FieldListWidget(QListWidget):
    """List whose items can be dragged into the document editor."""
    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        item = self.currentItem()
        if item is None:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-docuforge-field", item.text().encode("utf-8"))
        mime.setText(item.text())
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class DropTextEdit(QTextEdit):
    """Rich-text editor accepting data-field drops from the field browser."""
    fieldDropped = Signal(str)
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-docuforge-field"):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)
    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-docuforge-field"):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)
    def dropEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-docuforge-field"):
            column = bytes(event.mimeData().data("application/x-docuforge-field")).decode("utf-8")
            self.setTextCursor(self.cursorForPosition(event.position().toPoint()))
            self.fieldDropped.emit(column)
            event.acceptProposedAction()
            return
        super().dropEvent(event)



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
        self.refresh_button.clicked.connect(self._load_columns)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        self.sheet_combo.currentIndexChanged.connect(self._load_columns)
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
        left_layout.addWidget(QLabel("DATA FIELDS  ·  DRAG INTO DOCUMENT"))
        self.field_list = FieldListWidget()
        self.field_list.setDragEnabled(True)
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
        center_layout.addWidget(QLabel("DOCUMENT EDITOR  ·  TABLE TOOLS IN TABLE TAB"))
        self.ribbon = QTabWidget()
        self.ribbon.setDocumentMode(True)
        self.toolbar = QToolBar("Home")
        self.toolbar.setMovable(False)
        self._build_toolbar()
        self.ribbon.addTab(self.toolbar, "Home")
        self._build_insert_ribbon()
        self._build_table_ribbon()
        self._build_layout_ribbon()
        self._build_design_ribbon()
        self._build_data_ribbon()
        self._build_view_ribbon()
        self.editor = DropTextEdit()
        self.editor.fieldDropped.connect(self._insert_field_by_name)
        self.editor.setAcceptRichText(True)
        self.editor.setObjectName("DocumentCanvas")
        self.editor.setFixedWidth(794)
        self.editor.setMinimumHeight(1123)
        self.editor.document().setPageSize(QSizeF(794, 1123))
        self.editor.document().setDocumentMargin(72)
        self.editor.setPlaceholderText(
            "Start designing your document here…\n\n"
            "Write anything, position the cursor wherever a value belongs, "
            "then insert a field from the Data Fields panel."
        )
        page_scroll = QScrollArea()
        page_scroll.setWidgetResizable(True)
        page_scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        page_scroll.setObjectName("PageScroll")
        page_scroll.setWidget(self.editor)
        center_layout.addWidget(self.ribbon)
        center_layout.addWidget(page_scroll, 1)

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

        self.data_panel = left
        self.preview_panel = right
        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setSizes([220, 600, 340])
        root.addWidget(splitter, 1)
        self.word_count = QLabel("0 words")
        self.page_count = QLabel("1 page")
        stats = QHBoxLayout()
        stats.addWidget(self.word_count)
        stats.addStretch()
        stats.addWidget(self.page_count)
        root.addLayout(stats)

        bottom = QHBoxLayout()
        new_button = QPushButton("New template")
        new_button.clicked.connect(self.new_template)
        open_button = QPushButton("Open template…")
        open_button.clicked.connect(self.open_template)
        save_as_button = QPushButton("Save as…")
        save_as_button.clicked.connect(self.save_template_as)
        export_button = QPushButton("Export DOCX…")
        export_button.clicked.connect(self.export_docx_as)
        save_button = QPushButton("Save")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_template)
        bottom.addWidget(new_button)
        bottom.addWidget(open_button)
        bottom.addStretch()
        bottom.addWidget(save_as_button)
        bottom.addWidget(export_button)
        bottom.addWidget(save_button)
        root.addLayout(bottom)
        self.editor.textChanged.connect(self._refresh_preview)
        self.editor.textChanged.connect(self._update_document_stats)
        self.setStyleSheet("#PageScroll { background:#DDE2EA; } #DocumentCanvas { background:white; color:#20242B; border:1px solid #C9CDD4; padding:0; }")

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


    def _add_ribbon_tab(self, name: str, actions: list[tuple[str, object]]) -> None:
        bar = QToolBar(name)
        bar.setMovable(False)
        self.ribbon.addTab(bar, name)
        for label, callback in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            bar.addAction(action)

    def _build_insert_ribbon(self) -> None:
        self._add_ribbon_tab("Insert", [
            ("Table", self._insert_table), ("Picture", self._insert_picture),
            ("Hyperlink", self._insert_hyperlink), ("Date", self._insert_date),
            ("Page break", self._insert_page_break),
            ("Header marker", lambda: self._insert_marker("HEADER")),
            ("Footer marker", lambda: self._insert_marker("FOOTER")),
        ])

    def _build_table_ribbon(self) -> None:
        self._add_ribbon_tab("Table", [
            ("Insert table", self._insert_table),
            ("Add row above", lambda: self._table_insert_row(False)),
            ("Add row below", lambda: self._table_insert_row(True)),
            ("Delete row", self._table_delete_row),
            ("Add column left", lambda: self._table_insert_column(False)),
            ("Add column right", lambda: self._table_insert_column(True)),
            ("Delete column", self._table_delete_column),
            ("Merge cells", self._table_merge_cells),
            ("Split cell", self._table_split_cell),
            ("Cell shading", self._table_cell_shading),
            ("Table borders", self._table_borders),
        ])

    def _current_table(self):
        return self.editor.textCursor().currentTable()

    def _table_insert_row(self, below: bool) -> None:
        table = self._current_table()
        if table is None:
            self.status_message.emit("Place the cursor inside a table first.")
            return
        cell = table.cellAt(self.editor.textCursor())
        table.insertRows(cell.row() + (1 if below else 0), 1)

    def _table_delete_row(self) -> None:
        table = self._current_table()
        if table is None: return
        cell = table.cellAt(self.editor.textCursor())
        if table.rows() > 1: table.removeRows(cell.row(), 1)

    def _table_insert_column(self, right: bool) -> None:
        table = self._current_table()
        if table is None: return
        cell = table.cellAt(self.editor.textCursor())
        table.insertColumns(cell.column() + (1 if right else 0), 1)

    def _table_delete_column(self) -> None:
        table = self._current_table()
        if table is None: return
        cell = table.cellAt(self.editor.textCursor())
        if table.columns() > 1: table.removeColumns(cell.column(), 1)

    def _table_merge_cells(self) -> None:
        table = self._current_table()
        cursor = self.editor.textCursor()
        if table is None or not cursor.hasSelection():
            self.status_message.emit("Select multiple adjacent table cells first.")
            return
        first = table.cellAt(cursor.selectionStart())
        last = table.cellAt(max(cursor.selectionStart(), cursor.selectionEnd() - 1))
        if first.isValid() and last.isValid():
            top, left = min(first.row(), last.row()), min(first.column(), last.column())
            bottom, right = max(first.row(), last.row()), max(first.column(), last.column())
            table.mergeCells(top, left, bottom - top + 1, right - left + 1)

    def _table_split_cell(self) -> None:
        table = self._current_table()
        if table is None: return
        rows, ok = QInputDialog.getInt(self, "Split cell", "Rows", 1, 1, 20)
        if not ok: return
        columns, ok = QInputDialog.getInt(self, "Split cell", "Columns", 2, 1, 20)
        if ok:
            cell = table.cellAt(self.editor.textCursor())
            table.splitCell(cell.row(), cell.column(), rows, columns)

    def _table_cell_shading(self) -> None:
        from PySide6.QtWidgets import QColorDialog
        table = self._current_table()
        if table is None: return
        color = QColorDialog.getColor(QColor("#E8F0FE"), self, "Choose cell color")
        if color.isValid():
            cell = table.cellAt(self.editor.textCursor())
            fmt = cell.format()
            fmt.setBackground(color)
            cell.setFormat(fmt)

    def _table_borders(self) -> None:
        table = self._current_table()
        if table is None: return
        fmt = table.format()
        fmt.setBorder(0.8)
        fmt.setBorderBrush(QColor("#8993A4"))
        fmt.setCellPadding(6)
        fmt.setCellSpacing(0)
        table.setFormat(fmt)

    def _build_layout_ribbon(self) -> None:
        self._add_ribbon_tab("Layout", [
            ("A4 portrait", lambda: self._set_page_layout(False)),
            ("A4 landscape", lambda: self._set_page_layout(True)),
            ("Normal margins", lambda: self.editor.document().setDocumentMargin(72)),
            ("Narrow margins", lambda: self.editor.document().setDocumentMargin(36)),
            ("Wide margins", lambda: self.editor.document().setDocumentMargin(90)),
        ])

    def _build_design_ribbon(self) -> None:
        self._add_ribbon_tab("Design", [
            ("Title", lambda: self._apply_heading(24)),
            ("Heading 1", lambda: self._apply_heading(18)),
            ("Heading 2", lambda: self._apply_heading(14)),
            ("Normal", lambda: self._apply_heading(11, False)),
            ("Clear formatting", self._clear_formatting),
        ])

    def _build_data_ribbon(self) -> None:
        self._add_ribbon_tab("Data", [
            ("Insert data field", self._insert_selected_field),
            ("Refresh source fields", self._load_selected_source),
            ("Refresh preview", self._refresh_preview),
        ])

    def _build_view_ribbon(self) -> None:
        self._add_ribbon_tab("View", [
            ("Toggle data fields", lambda: self.data_panel.setVisible(not self.data_panel.isVisible())),
            ("Toggle preview", lambda: self.preview_panel.setVisible(not self.preview_panel.isVisible())),
        ])

    def _update_document_stats(self) -> None:
        words = len(re.findall(r"\\b[\\w'-]+\\b", self.editor.toPlainText()))
        self.word_count.setText(f"{words} words")
        self.page_count.setText(f"{max(1, self.editor.document().pageCount())} pages")

    def _insert_table(self) -> None:
        rows, ok = QInputDialog.getInt(self, "Insert table", "Rows", 3, 1, 50)
        if not ok: return
        cols, ok = QInputDialog.getInt(self, "Insert table", "Columns", 3, 1, 20)
        if ok: self.editor.textCursor().insertTable(rows, cols)

    def _insert_picture(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Insert picture", str(Path.home()), "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if path:
            image = QTextImageFormat()
            image.setName(path)
            image.setWidth(320)
            self.editor.textCursor().insertImage(image)

    def _insert_hyperlink(self) -> None:
        url, ok = QInputDialog.getText(self, "Insert hyperlink", "URL")
        if ok and url.strip():
            fmt = QTextCharFormat()
            fmt.setAnchor(True)
            fmt.setAnchorHref(url.strip())
            fmt.setForeground(QColor("#1769AA"))
            fmt.setFontUnderline(True)
            label, accepted = QInputDialog.getText(self, "Link text", "Display text", text=url.strip())
            if accepted: self.editor.textCursor().insertText(label or url.strip(), fmt)

    def _insert_date(self) -> None:
        from datetime import date
        self.editor.textCursor().insertText(date.today().strftime("%d %B %Y"))

    def _insert_page_break(self) -> None:
        cursor = self.editor.textCursor()
        cursor.insertBlock()
        cursor.insertHtml("<hr>")
        cursor.insertBlock()

    def _insert_marker(self, label: str) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold)
        fmt.setForeground(QColor("#64748B"))
        cursor = self.editor.textCursor()
        cursor.insertText(f"[{label}]", fmt)
        cursor.insertBlock()

    def _set_page_layout(self, landscape: bool) -> None:
        width, height = (1123, 794) if landscape else (794, 1123)
        self.editor.document().setPageSize(QSizeF(width, height))
        self.editor.setFixedWidth(width)
        self.editor.setMinimumHeight(height)

    def _apply_heading(self, size: int, bold: bool = True) -> None:
        fmt = self.editor.currentCharFormat()
        fmt.setFontPointSize(size)
        fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _clear_formatting(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontFamily("Arial")
        fmt.setFontPointSize(11)
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setForeground(QColor("#20242B"))
        self.editor.mergeCurrentCharFormat(fmt)

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
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        for source in self.registered_sources:
            path = Path(source)
            if path.exists() and path.suffix.lower() in {".xlsx", ".xlsm", ".ods", ".csv"}:
                self.source_combo.addItem(path.name, str(path))
        self.source_combo.blockSignals(False)
        if self.source_combo.count():
            self._on_source_changed()
        else:
            self.field_list.clear()
            self.columns = []
            self.sample_record = {}
            self.current_source_path = None
            self._refresh_preview()

    def update_registered_sources(self, paths: list[str]) -> None:
        self.registered_sources = paths
        self._populate_sources()

    def _on_source_changed(self, *_args: object) -> None:
        source = self.source_combo.currentData()
        if not source:
            QMessageBox.information(
                self, "No data source", "Add a spreadsheet or CSV in Data Sources first."
            )
            return
        try:
            path = Path(str(source))
            sheets = list_sheets(path)
            previous_sheet = self.sheet_combo.currentText()
            self.sheet_combo.blockSignals(True)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheets)
            if previous_sheet in sheets:
                self.sheet_combo.setCurrentText(previous_sheet)
            self.sheet_combo.blockSignals(False)
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
        self._insert_field_by_name(item.text())

    def _insert_field_by_name(self, column: str) -> None:
        if self.current_source_path is None:
            QMessageBox.information(self, "No source", "Connect a data source before inserting fields.")
            return
        field_id = str(uuid4())
        token = f"«{column}»"
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
            if field_id:
                metadata = self.fields.get(field_id)
            else:
                label = match.group(2)
                metadata = next((entry for entry in self.fields.values() if entry.get("display_name") == label or entry.get("column_id") == label), None)
            if metadata is None:
                return html.escape(match.group(0))
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
            "Documents (*.dfgtpl *.docx);;DocuForge templates (*.dfgtpl);;Word documents (*.docx)",
        )
        if path:
            self.open_template_path(Path(path))

    def open_template_path(self, path: Path) -> None:
        try:
            if path.suffix.lower() == ".docx":
                payload = {"html": import_docx(path), "fields": {}, "title": path.stem, "data_source": "", "sheet": ""}
            else:
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
            if target.suffix.lower() not in {".dfgtpl", ".docx"}:
                target = target.with_suffix(".dfgtpl")
            self._save_to_path(target)

    def export_docx_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Word document", str(Path.home() / "Untitled.docx"), "Word documents (*.docx)")
        if path:
            target = Path(path)
            if target.suffix.lower() != ".docx":
                target = target.with_suffix(".docx")
            self._save_to_path(target)

    def _save_to_path(self, path: Path) -> None:
        try:
            if path.suffix.lower() == ".docx":
                export_docx(self.editor.toHtml(), path, path.stem)
                self.current_template_path = path
                self.template_title.setText(path.stem)
                self.status_message.emit(f"Exported Word document: {path.name}")
                QMessageBox.information(self, "DOCX exported", f"Saved Word document to {path}")
                return
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
