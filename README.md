# DocuForge

Reusable desktop document-generation and batch-export platform.

DocuForge connects structured data sources to reusable document templates, generates documents in batches, and exports them to formats such as PDF, DOCX, and ODT.

## Current status

Phase 0 — Foundation. This repository contains the initial Python package, a PySide6 application shell, configuration and logging utilities, a data-source adapter contract, filename utilities, and starter tests. A production merge/export pipeline is not implemented yet.

## Planned capabilities

- Read XLSX, ODS, and CSV sources.
- Connect to supported SQL databases through adapters.
- Browse tables, sheets, and records.
- Manage reusable templates and field mappings.
- Generate documents individually or in batches.
- Preview output names and detect collisions.
- Export PDF, DOCX, and ODT.
- Keep generation logs and per-item error reports.

## Architecture

    PySide6 UI
       |
    Application Services
       |----------------------|
    Data Source Manager    Template Manager
       |                      |
    Data Adapters         Template Adapters
       |                      |
    Data Processing ----- Document Generation
                                |
                           Export Manager
                                |
                         PDF / DOCX / ODT

The UI will not contain business logic. Data-source and exporter implementations will follow explicit interfaces. LibreOffice integration will be isolated behind an exporter; the application will not depend on Writer Basic macros.

## Technology direction

- Python 3.11+
- PySide6 desktop interface
- openpyxl for XLSX
- odfpy for ODS
- SQLAlchemy for SQL connectivity
- pytest for automated tests
- LibreOffice for office-document rendering and PDF conversion where appropriate

## Development setup

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -e ".[dev]"

Run the application:

    python -m docuforge

Run tests:

    pytest

## Principles

1. Keep presentation, application, data, generation, and export concerns separate.
2. Never modify source data during generation.
3. Validate inputs and output paths before writing.
4. Never silently overwrite existing output.
5. Keep filenames and document content configurable.
6. Test core logic independently of the GUI and LibreOffice.
7. Report partial batch failures clearly.

## Roadmap

- [x] Initial repository and package foundation
- [ ] Complete architecture and component contracts
- [ ] Spreadsheet adapters and data-source discovery
- [ ] Template model and placeholder mapping
- [ ] Generation pipeline and batch execution
- [ ] PDF, DOCX, and ODT exporters
- [ ] Desktop workflows and preview screens
- [ ] Packaging and release

License selection is pending. Until a license is added, all rights are reserved by the repository owner.
