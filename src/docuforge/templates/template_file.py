"""Persistence helpers for DocuForge's editable HTML template files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TEMPLATE_SCHEMA_VERSION = 1
TEMPLATE_SUFFIX = ".dfgtpl"


def save_template(
    path: Path,
    *,
    title: str,
    html: str,
    source_path: str = "",
    sheet_name: str = "",
) -> None:
    """Save an editor document and its optional data-source binding."""
    if path.suffix.lower() != TEMPLATE_SUFFIX:
        path = path.with_suffix(TEMPLATE_SUFFIX)
    payload = {
        "schema_version": TEMPLATE_SCHEMA_VERSION,
        "title": title.strip() or "Untitled template",
        "html": html,
        "data_source": source_path,
        "sheet": sheet_name,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_template(path: Path) -> dict[str, Any]:
    """Load and validate a DocuForge template file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != TEMPLATE_SCHEMA_VERSION:
        raise ValueError("Unsupported template schema version.")
    if not isinstance(payload.get("html"), str):
        raise ValueError("Template file does not contain valid editor content.")
    return payload
