# Document Editor — Milestone 1

## Delivered

DocuForge now has a Word-style editing workspace, opened from the **Document Editor** navigation item or by creating/editing a native template.

- Ribbon tabs: Home, Insert, Layout and Design.
- Rich-text editing with font family/size, bold, italic, underline and paragraph alignment.
- Insert tables, pictures, hyperlinks, dates, page separators, and editable header/footer markers.
- A4 page workspace with portrait/landscape and margin presets.
- Word count and page-count status.
- XLSX, XLSM and CSV data-source selection, field insertion and live sample-record preview.
- Native `.dfgtpl` save/open compatibility with existing schema v1 and v2 templates.

## Known boundaries

- The editing surface uses Qt rich-text. It is a functional rich-text editor, not a custom Word-compatible pagination/rendering engine.
- Header/footer controls insert editable markers into the document body; true repeating page headers and footers require the pagination layer.
- Page breaks are currently represented by separators in the rich-text document.
- ODS appears in the source picker but its reader is not implemented yet.
- Dynamic fields remain visible DocuForge tokens with associated metadata; the structured document model and EditorSession are not yet the editor's canonical backing store.
- DOCX/ODT import/export and batch generation are not part of this milestone.

## Verification

The remote GitHub editing environment cannot execute pytest or launch the Qt GUI. Run `pip install -e ".[dev]"`, `pytest`, and `python -m docuforge` locally to verify the integrated changes.
