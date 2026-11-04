from pathlib import Path

from docx import Document

from docuforge.templates.docx_io import export_docx, import_docx


def test_docx_import_and_export_preserves_common_content(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    document = Document()
    paragraph = document.add_paragraph()
    paragraph.add_run("Hello ").bold = True
    paragraph.add_run("DocuForge")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Name"
    table.cell(0, 1).text = "Value"
    row = table.add_row()
    row.cells[0].text = "Ada"
    row.cells[1].text = "42"
    document.save(source)

    editor_html = import_docx(source)
    assert "<strong>Hello </strong>" in editor_html
    assert "<table" in editor_html
    assert "Ada" in editor_html

    output = tmp_path / "roundtrip.docx"
    export_docx(editor_html, output, "Round trip")
    reopened = Document(output)
    assert "Hello DocuForge" in "\n".join(p.text for p in reopened.paragraphs)
    assert len(reopened.tables) == 1
    assert reopened.tables[0].cell(1, 0).text == "Ada"
    assert reopened.tables[0].cell(1, 1).text == "42"
