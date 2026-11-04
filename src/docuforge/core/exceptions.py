"""Domain-specific exceptions used across DocuForge."""


class DocuForgeError(Exception):
    """Base exception for expected application errors."""


class ConfigurationError(DocuForgeError):
    """Raised when application or project configuration is invalid."""


class DataSourceError(DocuForgeError):
    """Raised when a data source cannot be opened or read."""


class TemplateError(DocuForgeError):
    """Raised when a template is invalid or cannot be processed."""


class GenerationError(DocuForgeError):
    """Raised when document generation fails."""


class ExportError(DocuForgeError):
    """Raised when exporting a generated document fails."""
