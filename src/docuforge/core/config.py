"""Application configuration primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    """Runtime paths and preferences for a DocuForge installation."""

    app_name: str = "DocuForge"
    data_dir: Path = field(default_factory=lambda: Path.home() / ".docuforge")
    log_level: str = "INFO"

    @property
    def projects_dir(self) -> Path:
        return self.data_dir / "projects"

    @property
    def templates_dir(self) -> Path:
        return self.data_dir / "templates"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    def ensure_directories(self) -> None:
        """Create application-owned directories if they do not exist."""
        for directory in (self.data_dir, self.projects_dir, self.templates_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)
