"""GUI-independent, serializable document model.

The model deliberately stores dynamic fields as typed nodes instead of flattening
them into placeholder strings. UI widgets and rendering backends must not own it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, TypeAlias
from uuid import uuid4


def _id() -> str:
    return str(uuid4())


@dataclass(slots=True)
class TextRun:
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    font_family: str | None = None
    font_size_pt: float | None = None
    color: str | None = None
    id: str = field(default_factory=_id)
    type: str = field(default="text", init=False)


@dataclass(slots=True)
class DynamicField:
    """Reference to a stable source/table/column identity."""

    source_id: str
    table_id: str
    column_id: str
    display_name: str
    fallback: str = ""
    format_kind: str = "text"
    id: str = field(default_factory=_id)
    type: str = field(default="field", init=False)


InlineNode: TypeAlias = TextRun | DynamicField


@dataclass(slots=True)
class Paragraph:
    runs: list[InlineNode] = field(default_factory=list)
    alignment: str = "left"
    style_name: str | None = None
    space_before_pt: float = 0
    space_after_pt: float = 8
    line_spacing: float = 1.0
    id: str = field(default_factory=_id)
    type: str = field(default="paragraph", init=False)


@dataclass(slots=True)
class TableCell:
    blocks: list[BlockNode] = field(default_factory=list)
    width_pt: float | None = None
    vertical_alignment: str = "middle"
    padding_pt: float = 4
    id: str = field(default_factory=_id)


@dataclass(slots=True)
class TableRow:
    cells: list[TableCell] = field(default_factory=list)
    repeat_as_header: bool = False
    id: str = field(default_factory=_id)


@dataclass(slots=True)
class Table:
    rows: list[TableRow] = field(default_factory=list)
    column_widths_pt: list[float] = field(default_factory=list)
    border_color: str = "#808080"
    border_width_pt: float = 0.5
    id: str = field(default_factory=_id)
    type: str = field(default="table", init=False)


@dataclass(slots=True)
class ImageBlock:
    asset_id: str
    alt_text: str = ""
    width_pt: float | None = None
    height_pt: float | None = None
    alignment: str = "center"
    id: str = field(default_factory=_id)
    type: str = field(default="image", init=False)


BlockNode: TypeAlias = Paragraph | Table | ImageBlock


@dataclass(slots=True)
class PageSettings:
    size: str = "A4"
    width_pt: float = 595.276
    height_pt: float = 841.89
    orientation: str = "portrait"
    margin_top_pt: float = 72
    margin_right_pt: float = 72
    margin_bottom_pt: float = 72
    margin_left_pt: float = 72


@dataclass(slots=True)
class Section:
    blocks: list[BlockNode] = field(default_factory=list)
    page_settings: PageSettings = field(default_factory=PageSettings)
    header: list[Paragraph] = field(default_factory=list)
    footer: list[Paragraph] = field(default_factory=list)
    id: str = field(default_factory=_id)


@dataclass(slots=True)
class Document:
    title: str = "Untitled document"
    sections: list[Section] = field(default_factory=lambda: [Section()])
    styles: dict[str, dict[str, Any]] = field(default_factory=dict)
    schema_version: int = 1
    id: str = field(default_factory=_id)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation with explicit node types."""
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def _inline_from_dict(data: dict[str, Any]) -> InlineNode:
    kind = data.get("type")
    if kind == "text":
        return TextRun(
            text=str(data.get("text", "")),
            bold=bool(data.get("bold", False)),
            italic=bool(data.get("italic", False)),
            underline=bool(data.get("underline", False)),
            font_family=data.get("font_family"),
            font_size_pt=data.get("font_size_pt"),
            color=data.get("color"),
            id=str(data.get("id") or _id()),
        )
    if kind == "field":
        return DynamicField(
            source_id=str(data["source_id"]),
            table_id=str(data["table_id"]),
            column_id=str(data["column_id"]),
            display_name=str(data.get("display_name", data["column_id"])),
            fallback=str(data.get("fallback", "")),
            format_kind=str(data.get("format_kind", "text")),
            id=str(data.get("id") or _id()),
        )
    raise ValueError(f"Unsupported inline node type: {kind!r}")


def _paragraph_from_dict(data: dict[str, Any]) -> Paragraph:
    return Paragraph(
        runs=[_inline_from_dict(item) for item in data.get("runs", [])],
        alignment=str(data.get("alignment", "left")),
        style_name=data.get("style_name"),
        space_before_pt=float(data.get("space_before_pt", 0)),
        space_after_pt=float(data.get("space_after_pt", 8)),
        line_spacing=float(data.get("line_spacing", 1)),
        id=str(data.get("id") or _id()),
    )


def _block_from_dict(data: dict[str, Any]) -> BlockNode:
    kind = data.get("type")
    if kind == "paragraph":
        return _paragraph_from_dict(data)
    if kind == "image":
        return ImageBlock(
            asset_id=str(data["asset_id"]),
            alt_text=str(data.get("alt_text", "")),
            width_pt=data.get("width_pt"),
            height_pt=data.get("height_pt"),
            alignment=str(data.get("alignment", "center")),
            id=str(data.get("id") or _id()),
        )
    if kind == "table":
        rows: list[TableRow] = []
        for row_data in data.get("rows", []):
            cells: list[TableCell] = []
            for cell_data in row_data.get("cells", []):
                cells.append(TableCell(
                    blocks=[_block_from_dict(block) for block in cell_data.get("blocks", [])],
                    width_pt=cell_data.get("width_pt"),
                    vertical_alignment=str(cell_data.get("vertical_alignment", "middle")),
                    padding_pt=float(cell_data.get("padding_pt", 4)),
                    id=str(cell_data.get("id") or _id()),
                ))
            rows.append(TableRow(
                cells=cells,
                repeat_as_header=bool(row_data.get("repeat_as_header", False)),
                id=str(row_data.get("id") or _id()),
            ))
        return Table(
            rows=rows,
            column_widths_pt=[float(x) for x in data.get("column_widths_pt", [])],
            border_color=str(data.get("border_color", "#808080")),
            border_width_pt=float(data.get("border_width_pt", 0.5)),
            id=str(data.get("id") or _id()),
        )
    raise ValueError(f"Unsupported block node type: {kind!r}")


def document_from_dict(data: dict[str, Any]) -> Document:
    """Validate and rebuild a document from its serialized dictionary."""
    if data.get("schema_version") != 1:
        raise ValueError(f"Unsupported document schema version: {data.get('schema_version')!r}")
    sections: list[Section] = []
    for section_data in data.get("sections", []):
        page = section_data.get("page_settings", {})
        settings = PageSettings(**{
            key: page[key] for key in PageSettings.__dataclass_fields__ if key in page
        })
        sections.append(Section(
            blocks=[_block_from_dict(block) for block in section_data.get("blocks", [])],
            page_settings=settings,
            header=[_paragraph_from_dict(p) for p in section_data.get("header", [])],
            footer=[_paragraph_from_dict(p) for p in section_data.get("footer", [])],
            id=str(section_data.get("id") or _id()),
        ))
    if not sections:
        sections = [Section()]
    return Document(
        title=str(data.get("title") or "Untitled document"),
        sections=sections,
        styles=dict(data.get("styles", {})),
        schema_version=1,
        id=str(data.get("id") or _id()),
    )
