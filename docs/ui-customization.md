# Workspace UI and Customization

## Available in the first UI milestone

DocuForge now provides a navigable desktop workspace with Dashboard, Data Sources, Templates, Generate, History, and Settings sections.

The following preferences are saved locally through Qt QSettings:

- Appearance: System, Light, or Dark.
- Accent color: Blue, Violet, Teal, Green, Orange, or Rose.
- Interface font size: 9–18 pt.
- Default export format: PDF, ODT, or DOCX.
- Default output directory.

The Data Sources screen can register XLSX, XLSM, ODS, and CSV file paths. The Templates screen can register ODT and DOCX file paths. Registered paths are stored in the local application settings; source and template files are not copied or modified.

## Current limitations

Registration is not the same as parsing or connecting. Spreadsheet inspection, template parsing, placeholder mapping, generation, export, and generation history are not implemented in this UI milestone. The Generate and History screens communicate this status rather than presenting non-functional controls.

## Future customization scope

Customization will expand to include per-project settings, template field mappings, output naming rules, record grouping, page/export options, reusable presets, and configurable validation policies. These will be introduced as actual capabilities with corresponding tests, not as decorative settings.
