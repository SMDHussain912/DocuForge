"""Read spreadsheet headers and a sample record for template design."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


SUPPORTED_SUFFIXES = {".xlsx", ".xlsm", ".csv"}


def list_sheets(path: Path) -> list[str]:
    """List selectable sheets; CSV files expose a single virtual sheet."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return ["CSV"]
    if suffix in {".xlsx", ".xlsm"}:
        from openpyxl import load_workbook

        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            return list(workbook.sheetnames)
        finally:
            workbook.close()
    raise ValueError(f"Spreadsheet format not supported yet: {suffix}")


def read_columns_and_sample(path: Path, sheet_name: str | None = None) -> tuple[list[str], dict[str, Any]]:
    """Return normalized column labels and the first non-empty data row."""
    suffix = path.suffix.lower()

    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = csv.reader(stream)
            header = next(rows, [])
            values = next(rows, [])
    elif suffix in {".xlsx", ".xlsm"}:
        from openpyxl import load_workbook

        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            selected = sheet_name or workbook.sheetnames[0]
            if selected not in workbook.sheetnames:
                raise ValueError(f"Worksheet not found: {selected}")
            worksheet = workbook[selected]
            iterator = worksheet.iter_rows(values_only=True)
            header = list(next(iterator, ()))
            values = list(next(iterator, ()))
        finally:
            workbook.close()
    else:
        raise ValueError(f"Spreadsheet format not supported yet: {suffix}")

    columns: list[str] = []
    for index, value in enumerate(header):
        label = str(value).strip() if value is not None else ""
        columns.append(label or f"Column {index + 1}")

    sample: dict[str, Any] = {}
    for index, column in enumerate(columns):
        value = values[index] if index < len(values) else ""
        sample[column] = "" if value is None else value

    if not columns:
        raise ValueError("The selected data source has no header row.")
    return columns, sample
