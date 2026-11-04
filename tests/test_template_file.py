"""Tests for native DocuForge template persistence."""

import json

from docuforge.templates.template_file import load_template, save_template


def test_template_round_trip_keeps_inline_field_metadata(tmp_path) -> None:
    path = tmp_path / "letter.dfgtpl"
    fields = {
        "field-123": {
            "id": "field-123",
            "source_id": "/data/employees.xlsx",
            "table_id": "Employees",
            "column_id": "EMP_NAME",
            "display_name": "Employee Name",
            "fallback": "",
            "format_kind": "text",
        }
    }
    save_template(
        path,
        title="Appointment Letter",
        html="<p>Hello ⟦DFG:field-123⟧</p>",
        source_path="/data/employees.xlsx",
        sheet_name="Employees",
        fields=fields,
    )

    restored = load_template(path)
    assert restored["schema_version"] == 2
    assert restored["fields"] == fields
    assert restored["sheet"] == "Employees"


def test_template_loader_accepts_legacy_v1(tmp_path) -> None:
    path = tmp_path / "legacy.dfgtpl"
    path.write_text(json.dumps({
        "schema_version": 1,
        "title": "Legacy",
        "html": "<p>Legacy template</p>",
        "data_source": "",
        "sheet": "",
    }), encoding="utf-8")

    restored = load_template(path)
    assert restored["title"] == "Legacy"
    assert restored["fields"] == {}
