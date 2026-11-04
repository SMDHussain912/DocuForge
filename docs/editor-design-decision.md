# Editor Design Decision

**Status:** Proposed architecture direction

## Reference

WordCraft: https://github.com/storytold/wordcraft

The reference is a large Rust word processor. Its README describes a ribbon-based authoring workflow and the source tree separates document model, layout, rendering, editing engine, file-format adapters and front ends.

DocuForge will not copy or port its source code. We are using its documented architecture and observable workflows as a design reference.

## Decision

Do not treat the current QTextEdit/HTML prototype as the long-term editor. Build a structured page-based document designer with these independent modules:

1. Document model — sections, paragraphs, runs, tables, cells, objects, styles and typed dynamic-data nodes.
2. Editing session — caret/selection, active document, undo/redo and view state.
3. Command registry — stable commands shared by ribbon actions, menus and shortcuts.
4. Layout engine — text measurement, line breaking, tables, page flow, headers/footers and pagination.
5. Renderer — page preview and export-ready display representation.
6. Data-binding engine — field references, sample data, repeating regions and conditional blocks.
7. Format adapters — import/export of supported document formats.
8. Generation pipeline — resolve a template for each record/group, validate names, export and report results.

## UI direction

Use a modern ribbon interface with Home, Insert, Layout, Design, Data and View tabs. A page canvas is the central workspace. Supporting panes include Navigation, Styles, Data Fields, Properties and Preview.

The page canvas must show the actual page size and margins. A document should be authored as a document, not as a plain text input whose content is later placed into a PDF.

## Data binding is first-class

A dynamic field is a typed node in the document tree with a stable binding identity. It must not be stored solely as a visible placeholder string. The binding engine resolves the field using the selected data source, table/sheet and column.

Repeating table rows and sections are explicit model constructs. Conditional blocks use a constrained expression model, not arbitrary executable Python in templates.

## Technology spike

Before committing to a rendering implementation, compare:

- Qt native text/document primitives and custom page canvas.
- Qt WebEngine with an editable HTML surface and print/PDF support.
- A dedicated document model/layout/render pipeline implemented in Python, with a carefully isolated native or Qt rendering component.

The decision must be evaluated against cursor/editing fidelity, tables, pagination, font metrics, performance, Linux packaging, DOCX/ODT/PDF export, and ability to preserve typed dynamic field nodes.

## First editor foundation acceptance

- Structured document serialization and reopening.
- A4 page canvas with margins and zoom.
- Text editing and selection.
- Basic character and paragraph formatting.
- Insert/edit tables.
- Undo/redo.
- Insert dynamic field node at caret.
- Resolve dynamic field against a sample record.
- Tests for model serialization and field binding.

## Out of scope for the first editor foundation

Full Word parity, citations, tracked changes, equation authoring, chart authoring, advanced floating shapes, and exhaustive legacy-format fidelity.
