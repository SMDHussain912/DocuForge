from pathlib import Path

import pytest

from docuforge.generation.naming import (
    build_output_path,
    find_duplicate_paths,
    sanitize_filename,
)


def test_sanitize_filename_replaces_invalid_characters() -> None:
    assert sanitize_filename('North/East: "Team"') == "North_East_ _Team_"


def test_sanitize_filename_rejects_empty_values() -> None:
    with pytest.raises(ValueError):
        sanitize_filename(" . ")


def test_build_output_path_adds_extension(tmp_path: Path) -> None:
    assert build_output_path(tmp_path, "Order", "pdf") == tmp_path / "Order.pdf"


def test_find_duplicate_paths_is_case_insensitive(tmp_path: Path) -> None:
    paths = [tmp_path / "Order.pdf", tmp_path / "order.PDF"]
    assert find_duplicate_paths(paths) == [paths[1]]
