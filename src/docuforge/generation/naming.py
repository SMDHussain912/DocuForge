"""Utilities for validating and normalizing generated filenames."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(value: str, replacement: str = "_") -> str:
    """Return a filesystem-safe filename component."""
    cleaned = _INVALID_FILENAME_CHARS.sub(replacement, value).strip().rstrip(". ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        raise ValueError("Filename must contain at least one valid character.")
    if cleaned.upper() in _WINDOWS_RESERVED_NAMES:
        cleaned = f"_{cleaned}"
    return cleaned


def build_output_path(directory: Path, filename: str, extension: str = ".pdf") -> Path:
    """Build an output path, normalizing the extension exactly once."""
    safe_name = sanitize_filename(filename)
    normalized_extension = extension if extension.startswith(".") else f".{extension}"
    return directory / f"{safe_name}{normalized_extension}"


def find_duplicate_paths(paths: Iterable[Path]) -> list[Path]:
    """Return paths that occur more than once, case-insensitively."""
    seen: set[str] = set()
    duplicates: list[Path] = []
    for path in paths:
        key = str(path).casefold()
        if key in seen and path not in duplicates:
            duplicates.append(path)
        seen.add(key)
    return duplicates
