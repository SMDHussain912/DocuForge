"""DOCX import/export bridge for common editable Word content.

This adapter preserves common paragraphs, run formatting, tables and inline
pictures. Advanced Word constructs (tracked changes, floating shapes, fields,
section-specific headers and complex numbering) can be simplified.
"""
from __future__ import annotations

import base64
import html
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from docx import Document as WordDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


def _color(value: Any) -> str | None:
    try:
        return f"#{value.rgb}" if value.rgb else None
    except (AttributeError, TypeError):
        return None


def _paragraph_html(paragraph: Any, document: Any) -> str:
    chunks: list[str] = []
    for run in paragraph.runs:
        text = html.escape(run.text).replace("\n", "<br>")
        if run.bold:
            text = f"<strong>{text}</strong>"
        if run.italic:
            text = f"<em>{text}</em>"
        if run.underline:
            text = f"<u>{text}</u>"
        if run.font.strike:
            text = f"<s>{text}</s>"
        color = _color(run.font.color)
        if color:
            text = f'<span style="color:{color}">{text}</span>'
        if run.font.size:
            text = f'<span style="font-size:{run.font.size.pt:g}pt">{text}</span>'
        if run.font.name:
            text = f'<span style="font-family:{html.escape(run.font.name, quote=True)}">{text}</span>'
        for blip in run._element.xpath(".//a:blip"):
            rel = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
            if rel and rel in document.part.related_parts:
                part = document.part.related_parts[rel]
                data = base64.b64encode(part.blob).decode("ascii")
                text += f'<img src="data:{part.content_type};base64,{data}" width="320">'
        chunks.append(text)
    style = paragraph.style.name.lower() if paragraph.style else ""
    tag = "h1" if style.startswith("heading 1") else "h2" if style.startswith("heading 2") else "p"
    alignment = {
        WD_ALIGN_PARAGRAPH.CENTER: "center",
        WD_ALIGN_PARAGRAPH.RIGHT: "right",
        WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
    }.get(paragraph.alignment, "left")
    return f'<{tag} style="text-align:{alignment}">{"".join(chunks) or "<br>"}</{tag}>'


def import_docx(path: str | Path) -> str:
    """Convert a DOCX package to editable HTML for QTextEdit."""
    document = WordDocument(str(path))
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    output: list[str] = []
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            output.append(_paragraph_html(Paragraph(child, document), document))
        elif child.tag.endswith("}tbl"):
            table = Table(child, document)
            rows = []
            for row in table.rows:
                cells = []
                for cell in row.cells:
                    cells.append("<td>" + "".join(_paragraph_html(p, document) for p in cell.paragraphs) + "</td>")
                rows.append("<tr>" + "".join(cells) + "</tr>")
            output.append('<table border="1" cellspacing="0" cellpadding="4">' + "".join(rows) + "</table>")
    return "<html><body>" + "".join(output) + "</body></html>"


class _HTMLToDocx(HTMLParser):
    def __init__(self, document: Any) -> None:
        super().__init__(convert_charrefs=True)
        self.document = document
        self.paragraph = None
        self.format_stack: list[dict[str, Any]] = [{}]
        self.table = None
        self.row = None
        self.cell = None
        self.row_index = -1
        self.col_index = 0
        self.in_table = False

    @property
    def fmt(self) -> dict[str, Any]:
        return self.format_stack[-1]

    def _paragraph(self):
        if self.paragraph is None:
            if self.cell is not None:
                existing = self.cell.paragraphs
                self.paragraph = existing[0] if len(existing) == 1 and not existing[0].text and not existing[0].runs else self.cell.add_paragraph()
            else:
                self.paragraph = self.document.add_paragraph()
        return self.paragraph

    def _end_paragraph(self) -> None:
        self.paragraph = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag in {"p", "div", "h1", "h2", "li"}:
            self._end_paragraph()
            p = self._paragraph()
            if tag == "h1":
                p.style = "Heading 1"
            elif tag == "h2":
                p.style = "Heading 2"
            elif tag == "li":
                p.style = "List Bullet"
            align = re.search(r"text-align\s*:\s*(left|center|right|justify)", attr.get("style") or "")
            if align:
                p.alignment = {
                    "left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                    "right": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
                }[align.group(1)]
            self.format_stack.append(dict(self.fmt))
        elif tag in {"strong", "b", "em", "i", "u", "s", "span"}:
            new = dict(self.fmt)
            if tag in {"strong", "b"}: new["bold"] = True
            if tag in {"em", "i"}: new["italic"] = True
            if tag == "u": new["underline"] = True
            if tag == "s": new["strike"] = True
            style = attr.get("style") or ""
            color = re.search(r"color\s*:\s*(#[0-9a-fA-F]{6})", style)
            size = re.search(r"font-size\s*:\s*([0-9.]+)pt", style)
            family = re.search(r"font-family\s*:\s*([^;]+)", style)
            if color: new["color"] = color.group(1)
            if size: new["size"] = float(size.group(1))
            if family: new["font"] = family.group(1).strip(" ' \"")
            self.format_stack.append(new)
        elif tag == "br":
            self._paragraph().add_run().add_break()
        elif tag == "table":
            self._end_paragraph()
            self.table = self.document.add_table(rows=1, cols=1)
            self.table.style = "Table Grid"
            self.row = self.table.rows[0]
            self.row_index = 0
            self.col_index = 0
            self.in_table = True
        elif tag == "tr" and self.table is not None:
            if self.row_index > 0:
                self.row = self.table.add_row()
            self.row_index += 1
            self.col_index = 0
        elif tag == "td" and self.row is not None:
            while self.col_index >= len(self.row.cells):
                self.table.add_column(Inches(1))
            self.cell = self.row.cells[self.col_index]
            self.cell.text = ""
            self.paragraph = self.cell.paragraphs[0]
            self.col_index += 1
        elif tag == "img":
            src = attr.get("src") or ""
            match = re.match(r"data:image/(png|jpeg|jpg|gif|bmp);base64,(.+)", src)
            if match:
                import io
                self._paragraph().add_run().add_picture(io.BytesIO(base64.b64decode(match.group(2))), width=Inches(3.2))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "h1", "h2", "li"}:
            self._end_paragraph()
            if len(self.format_stack) > 1:
                self.format_stack.pop()
        elif tag in {"strong", "b", "em", "i", "u", "s", "span"}:
            if len(self.format_stack) > 1:
                self.format_stack.pop()
        elif tag == "td":
            self.cell = None
            self._end_paragraph()
        elif tag == "tr":
            self.row = None
        elif tag == "table":
            self.table = None
            self.row = None
            self.cell = None
            self.in_table = False

    def handle_data(self, data: str) -> None:
        if not data:
            return
        run = self._paragraph().add_run(data)
        run.bold = bool(self.fmt.get("bold"))
        run.italic = bool(self.fmt.get("italic"))
        run.underline = bool(self.fmt.get("underline"))
        run.font.strike = bool(self.fmt.get("strike"))
        if self.fmt.get("font"): run.font.name = self.fmt["font"]
        if self.fmt.get("size"): run.font.size = Pt(self.fmt["size"])
        if self.fmt.get("color"):
            run.font.color.rgb = RGBColor.from_string(self.fmt["color"].lstrip("#"))


def export_docx(editor_html: str, path: str | Path, title: str = "Untitled document") -> None:
    """Export supported editor HTML structures into a DOCX document."""
    document = WordDocument()
    document.core_properties.title = title
    parser = _HTMLToDocx(document)
    parser.feed(editor_html)
    parser.close()
    if not document.paragraphs and not document.tables:
        document.add_paragraph("")
    document.save(str(path))
