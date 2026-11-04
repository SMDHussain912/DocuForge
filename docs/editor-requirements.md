# DocuForge Visual Document Designer — Requirements

## Product goal

Provide a page-based document authoring environment similar in workflow to a modern desktop word processor. Users design complete documents visually, then bind selected content locations to spreadsheet/database fields and generate document batches.

The editor must be useful even when no data source is attached. Data binding enhances normal document authoring; it must not replace it.

## Primary workflow

1. Create or open a DocuForge template.
2. Choose a page size and configure margins/orientation.
3. Write and format static document content.
4. Insert tables, images, headers, footers and page fields.
5. Connect a data source and select a worksheet/table.
6. Insert dynamic fields at the caret or into a table cell.
7. Configure repeating rows/sections and conditional regions.
8. Choose a sample record and preview the resolved document.
9. Validate missing fields and layout overflow.
10. Save the template and use it in batch generation.

## Editing surface

### Document canvas
- Paginated page view with paper background and visible page boundaries.
- Zoom, page navigation and fit-to-width.
- Rulers and margin guides.
- Click-to-place caret, text selection and keyboard editing.
- Undo and redo.
- Page break and section break visualization.

### Ribbon and formatting
- Home: font family, size, bold, italic, underline, color, highlight, alignment, indents, spacing, bullets and numbering.
- Insert: table, image, hyperlink, page number, date/time, header, footer, page break and dynamic field.
- Layout: paper size, orientation, margins, columns, page borders and section setup.
- Design: themes, styles, watermark and page color.
- Data: source selection, field list, repeating regions, conditions and sample-record preview.
- View: zoom, navigation pane, rulers, formatting marks and page modes.

### Tables
- Insert table by row/column grid.
- Add/remove rows and columns.
- Resize column widths and row heights.
- Cell alignment, padding, borders and shading.
- Merge/split cells.
- Header rows and repeating table headers.
- Dynamic repeating row bound to a record collection.

### Images and objects
- Insert local image.
- Resize and align image.
- Text wrapping can be added after basic inline images.
- Placeholders for signatures, seals and logos should remain distinct from resolved image values.

## Dynamic data model

Dynamic field nodes must be explicit typed objects. Suggested conceptual shape:

```json
{
  "type": "field",
  "id": "field-node-unique-id",
  "binding": {
    "source_id": "source-uuid",
    "table_id": "sheet-or-table-id",
    "column_id": "stable-column-id"
  },
  "format": {
    "kind": "text"
  },
  "fallback": ""
}
```

The exact schema and stable column identity strategy are subject to the data model design.

### Repeating regions
- Repeating table rows bind to a collection or selected data group.
- Repeating sections produce a block per input record.
- Empty collections must follow an explicit policy: render no rows, render a fallback, or stop with validation error.

### Conditions
- Conditional blocks may show/hide content based on a field and a typed comparison.
- No arbitrary Python expressions inside templates.
- Condition operators must be allowlisted and validated.

### Preview and validation
- Preview uses a selectable sample record.
- Missing fields and invalid bindings must be visible before generation.
- Preview must distinguish sample-resolved values from editable static content.
- Report overflow and page-count changes where feasible.

## Non-functional requirements
- Source data is read-only.
- Autosave/recovery should protect unsaved editing work.
- Editing operations should be undoable where appropriate.
- Layout and UI must remain separate.
- Templates need explicit schema versions and migrations.
- No silent overwrites.
- Large documents should be paginated incrementally or with caching once performance requires it.

## Delivery phases
1. Structured document model and editor session.
2. Page canvas and pagination spike.
3. Command system, undo/redo and basic text editing.
4. Formatting, tables and images.
5. Dynamic field binding and preview.
6. Repeating rows/sections and conditions.
7. Template persistence and export integration.

## Acceptance criteria for editor foundation
- Create, edit and save a structured document without requiring a data source.
- Reopen saved content with page settings and text intact.
- Execute undo and redo for basic edits.
- Insert a dynamic field node without flattening it into plain text.
- Render a page preview from the document model.
- Unit tests cover document serialization, field validation and edit history.
