from pathlib import Path

from docuforge.core.config import AppConfig


def test_config_directories_are_created(tmp_path: Path) -> None:
    config = AppConfig(data_dir=tmp_path / "docuforge")

    config.ensure_directories()

    assert config.data_dir.is_dir()
    assert config.projects_dir.is_dir()
    assert config.templates_dir.is_dir()
    assert config.logs_dir.is_dir()
