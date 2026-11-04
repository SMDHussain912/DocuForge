# DocuForge — Initial Architecture

## Purpose

DocuForge turns structured data and reusable templates into validated batches of documents. The counting-staff workflow is a domain example; core modules must remain domain-neutral.

## Logical components

### Presentation
PySide6 screens display projects, data sources, templates, generation options, previews, and results. Widgets must not contain data access or document-generation rules.

### Application services
Coordinate use cases such as connecting a source, validating template mappings, previewing output names, and running a batch.

### Data sources
Adapters expose a common contract for connecting, listing selectable items, reading records, and releasing resources. Planned adapters include XLSX, ODS, CSV, and SQL databases.

### Templates
Template adapters inspect supported formats and resolve placeholders. The template model and mapping rules will be specified before selecting a full rendering implementation.

### Generation
The generation engine combines validated records and template mappings into generated document artifacts. Batch execution must report per-item success and failure.

### Export
Exporters convert generated artifacts to target formats. LibreOffice integration belongs behind an exporter boundary; no business logic should depend on Writer Basic macros.

## Design rules

- Source data is read-only during generation.
- Validate planned output paths before writing.
- Never silently overwrite existing files.
- Keep source adapters and exporters replaceable.
- Use typed domain objects at module boundaries.
- Preserve causes in actionable error logs.
- Test core logic without requiring a GUI or LibreOffice process.

## Decisions intentionally deferred

- Native DOCX/ODT template authoring versus LibreOffice UNO-driven templates.
- Internal generated-document representation.
- Database connection and credential storage policy.
- Project configuration schema and migration strategy.
- Parallel versus sequential batch execution.
- Packaging and platform support matrix.

Resolve these decisions with focused technical spikes before implementation depends on them.
