# DocuForge — Architecture

## Purpose

DocuForge turns structured data and reusable templates into validated batches of documents. The counting-staff workflow is a domain example; core modules must remain domain-neutral.

## Logical components

### Presentation
PySide6 screens display projects, data sources, templates, generation options, previews, and results. Widgets must not contain data access or document-generation rules. The future visual editor uses a ribbon, page canvas, side panes and a status bar.

### Application services
Coordinate use cases such as connecting a source, validating template mappings, previewing output names, and running a batch.

### Data sources
Adapters expose a common contract for connecting, listing selectable items, reading records, and releasing resources. Planned adapters include XLSX, XLSM, ODS, CSV, and SQL databases.

### Document model
A structured, GUI-independent model stores sections, paragraphs, text runs, tables, rows, cells, images, page settings, styles, and typed dynamic data nodes. The previous HTML editor is a prototype; HTML is not the canonical model.

### Editing engine
An editing session owns the active document, selection/caret, view state, undo/redo history and command registry. UI buttons, menus and shortcuts call shared commands.

### Layout and pagination
A dedicated service transforms document structure and page settings into pages, positioned text, tables and objects. It owns line breaking, page breaks, headers/footers and layout measurement.

### Rendering
A renderer consumes page display data and produces the on-screen preview and export-ready page representation. GUI widgets do not calculate final pagination.

### Data binding
The binding engine resolves stable source/table/column references against sample records or batch records. Repeating rows/sections and conditions are typed model nodes, not ad-hoc string replacements.

### Templates
Template persistence stores document structure, source bindings and schema version. Template adapters import/export supported formats where possible.

### Generation
The generation engine combines validated document templates with data records or grouped records. Batch execution must report per-item success and failure.

### Export
Exporters convert generated documents/pages to target formats. LibreOffice integration belongs behind an exporter boundary; no business logic should depend on Writer Basic macros.

## Design rules

- Source data is read-only during generation.
- Validate planned output paths before writing.
- Never silently overwrite existing files.
- Keep source adapters and exporters replaceable.
- Use typed domain objects at module boundaries.
- Preserve causes in actionable error logs.
- Test core logic without requiring a GUI or LibreOffice process.
- Keep the document model independent of PySide6 widgets.
- Keep commands independent of ribbon/menu placement.
- Keep dynamic field identity separate from its visible label.

## Reference-informed editor direction

The WordCraft reference was studied at https://github.com/storytold/wordcraft. Its documented separation between structured document model, layout/pagination, rendering, editing session/commands, file formats and UI informs DocuForge's editor architecture. DocuForge will implement its own model and workflows in Python. Its key extension is first-class spreadsheet/database field binding, repeating data regions, conditions and batch generation.

See:
- [WordCraft reference analysis](wordcraft-reference-analysis.md)
- [Visual editor requirements](editor-requirements.md)

## Decisions intentionally deferred

- The concrete page layout engine and font measurement strategy.
- Whether Qt WebEngine or a native Qt canvas is the first editing surface.
- Native DOCX/ODT import/export strategy versus LibreOffice UNO integration.
- Canonical document serialization format and migration rules.
- Database credential storage policy.
- Parallel versus sequential batch execution.
- Packaging and platform support matrix.

Resolve these with focused technical spikes before production implementation depends on them.
