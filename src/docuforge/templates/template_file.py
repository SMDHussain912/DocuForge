"""Persistence helpers for DocuForge templates (legacy HTML + typed field metadata)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TEMPLATE_SCHEMA_VERSION = 2
TEMPLATE_SUFFIX = ".dfgtpl"


def save_template(
    path: Path,
    *,
    title: str,
    html: str,
    source_path: str = "",
    sheet_name: str = "",
    fields: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Save rich-text HTML and typed metadata for inline dynamic fields."""
    if path.suffix.lower() != TEMPLATE_SUFFIX:
        path = path.with_suffix(TEMPLATE_SUFFIX)
    payload = {
        "schema_version": TEMPLATE_SCHEMA_VERSION,
        "title": title.strip() or "Untitled template",
        "html": html,
        "data_source": source_path,
        "sheet": sheet_name,
        "fields": fields or {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_template(path: Path) -> dict[str, Any]:
    """Load v1 legacy templates and v2 templates with typed field metadata."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    version = payload.get("schema_version")
    if version not in {1, TEMPLATE_SCHEMA_VERSION}:
        raise ValueError("Unsupported template schema version.")
    if not isinstance(payload.get("html"), str):
        raise ValueError("Template file does not contain valid editor content.")
    fields = payload.get("fields", {})
    if not isinstance(fields, dict):
        raise ValueError("Template field metadata must be an object.")
    payload["fields"] = fields
    return payload
