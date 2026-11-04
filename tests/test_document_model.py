"""Tests for the structured document model and editor session."""

import json

import pytest

from docuforge.document.model import (
    Document,
    DynamicField,
    Paragraph,
    Table,
    TableCell,
    TableRow,
    TextRun,
    document_from_dict,
)
from docuforge.document.session import EditorSession, InsertParagraph, InsertText


def test_document_round_trip_preserves_typed_dynamic_field() -> None:
    document = Document()
    document.sections[0].blocks.append(Paragraph(runs=[
        TextRun("Employee: "),
        DynamicField(
            source_id="source-1",
            table_id="sheet-1",
            column_id="employee-name",
            display_name="Employee Name",
        ),
    ]))

    restored = document_from_dict(json.loads(document.to_json()))
    paragraph = restored.sections[0].blocks[0]

    assert isinstance(paragraph, Paragraph)
    assert isinstance(paragraph.runs[1], DynamicField)
    assert paragraph.runs[1].column_id == "employee-name"
    assert paragraph.runs[1].source_id == "source-1"


def test_table_round_trip_preserves_rows_and_cells() -> None:
    document = Document()
    document.sections[0].blocks.append(Table(rows=[
        TableRow(cells=[
            TableCell(blocks=[Paragraph(runs=[TextRun("Name")])]),
            TableCell(blocks=[Paragraph(runs=[TextRun("Role")])]),
        ])
    ]))

    restored = document_from_dict(json.loads(document.to_json()))
    table = restored.sections[0].blocks[0]

    assert isinstance(table, Table)
    assert len(table.rows) == 1
    assert len(table.rows[0].cells) == 2


def test_editor_session_insert_undo_redo() -> None:
    session = EditorSession()
    session.execute(InsertParagraph(0, 0, Paragraph()))
    session.execute(InsertText(0, 0, "Hello"))

    paragraph = session.document.sections[0].blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs[0].text == "Hello"
    assert session.can_undo

    assert session.undo()
    paragraph = session.document.sections[0].blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs == []

    assert session.redo()
    paragraph = session.document.sections[0].blocks[0]
    assert paragraph.runs[0].text == "Hello"


def test_unsupported_schema_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported document schema"):
        document_from_dict({"schema_version": 99})
