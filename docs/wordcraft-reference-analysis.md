# WordCraft Reference Analysis

Reference: https://github.com/storytold/wordcraft

Repository metadata and source tree were inspected on 2026-11-05. WordCraft describes itself as an open-source word processor implemented in Rust, with a native desktop application and a WebAssembly build. Its README documents a ribbon workflow, DOCX support, tables, page layout, images, headers/footers, styles, review features, references, mail merge, and PDF export.

This document records architectural observations for DocuForge. It is not a specification to clone WordCraft or copy its implementation.

## 1. Observed architectural layers

| WordCraft area | Observed responsibility | DocuForge direction |
|---|---|---|
| `wordcraft-doc` | Structured document model: paragraphs, runs, tables, cells, sections, styles, parts, media | Domain-neutral document model with dynamic data nodes |
| `wordcraft-layout` | Line breaking, pagination, tables, headers/footers, hit-testing and page geometry | Dedicated layout/pagination service |
| `wordcraft-render` | Draws page display lists to raster output | Page renderer and preview surface |
| `wordcraft-docx` | DOCX read/write | Format adapters, starting with DOCX and ODT strategy research |
| `wordcraft-engine` | Editing session, selection, undo/redo, command registry | Editing session and command system |
| `wordcraft-ui-egui` | Word-style ribbon, editor canvas, panes and commands | PySide6 ribbon and page-canvas UI |

Evidence in reference source:
- `crates/doc/src/lib.rs` describes a structured `Document`, stories, paragraphs and tables.
- `crates/layout/src/lib.rs` describes document-to-pages layout, display lists and hit testing.
- `crates/render/src/lib.rs` exposes page rasterization.
- `crates/engine/src/session.rs` describes document, selection, undo/redo, layout and view state.
- `crates/engine/src/lib.rs` describes a command registry used by ribbon, menus and shortcuts.
- `crates/docx/src/lib.rs` describes DOCX package reading and writing.

## 2. UI and interaction patterns to learn from

The reference README and screenshots document:
- Ribbon tabs and grouped actions.
- Styles gallery and navigation pane.
- Document page canvas, rulers and page zoom.
- Insert workflows for tables, pictures, shapes, links, headers, footers, fields and symbols.
- Layout settings for margins, orientation, page size, columns, breaks and page borders.
- Table operations such as insert, merge/split, styles, borders and shading.
- Review and references workflows.
- Mail merge with recipient lists, field insertion, preview and finishing.

DocuForge should adopt familiar document-editor interaction patterns, not attempt full word-processor feature parity immediately.

## 3. Crucial DocuForge-specific extension

DocuForge is a data-driven document authoring application. Dynamic data is part of the document model, not a string replacement that happens after editing.

The model must support typed nodes such as:
- Text runs and paragraphs.
- Tables, rows and cells.
- Inline dynamic field references.
- Repeating row/section regions.
- Conditional regions.
- Image and signature placeholders.
- Page and document metadata fields.

A field reference should carry a stable source identity and field identity, rather than only a display label. This allows source columns to be renamed or mapped without silently changing document meaning.

## 4. Architecture decision direction

Adopt these concepts:
1. Structured document model independent of the GUI.
2. Separate editing session with selection and undo/redo.
3. Command registry so menus, ribbon actions and shortcuts invoke the same operations.
4. Layout service responsible for page breaks and pagination.
5. Page renderer used by preview and export.
6. Format adapters for reading/writing files.
7. A dynamic-data binding layer that resolves fields, repeating regions and conditions against a selected record or record group.

The initial PySide6/HTML editor is a prototype only. It should not become the canonical document representation. The HTML template experiment may remain available temporarily for evaluation, but the long-term editor should use a structured model and dedicated rendering pipeline.

## 5. Implementation strategy

Do not port WordCraft's Rust code into DocuForge. Its source is a separate, large, multi-crate implementation and is dual-licensed under MIT or Apache-2.0. We should study its documented architecture and interaction patterns, write our own Python implementation, and preserve attribution/licensing obligations if any reference code or assets are ever reused.

Recommended staged build:
- Editor foundation: document schema, commands, selection, undo/redo.
- Canvas: page geometry, text flow, page navigation and zoom.
- Authoring: formatting, paragraph styles, lists and tables.
- Data binding: field nodes, inspector, sample record preview.
- Repetition and rules: repeating table rows/sections and conditional blocks.
- Objects and page setup: images, header/footer, page numbering and sections.
- Persistence and export: native project format plus DOCX/ODT/PDF adapters.

## 6. Non-goals for the first editor milestone

Do not attempt to reproduce every Microsoft Word / WordCraft feature. Prioritize page layout, formatting, tables, images, template fields, repeating regions, conditional logic, preview and robust PDF generation.
