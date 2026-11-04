"""Structured document model and editing primitives for DocuForge."""

from docuforge.document.session import EditorSession, InsertInlineField, InsertParagraph, InsertText, RemoveInlineNode
from docuforge.document.model import (
    Document,
    DynamicField,
    ImageBlock,
    PageSettings,
    Paragraph,
    Section,
    Table,
    TableCell,
    TableRow,
    TextRun,
    document_from_dict,
)

__all__ = [
    "Document", "DynamicField", "ImageBlock", "PageSettings", "Paragraph",
    "Section", "Table", "TableCell", "TableRow", "TextRun", "document_from_dict",
    "EditorSession", "InsertInlineField", "InsertParagraph", "InsertText", "RemoveInlineNode",
]
