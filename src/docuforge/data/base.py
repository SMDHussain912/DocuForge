"""Common data-source adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DataSourceInfo:
    """Describes a connected data source."""

    name: str
    source_type: str
    location: str | None = None


@dataclass(frozen=True, slots=True)
class TableInfo:
    """Describes a selectable table, worksheet, or query result."""

    name: str
    source_name: str
    item_type: str


class DataSourceAdapter(ABC):
    """Interface implemented by spreadsheet and database adapters."""

    @abstractmethod
    def connect(self) -> None:
        """Open or validate the underlying data source."""

    @abstractmethod
    def list_items(self) -> list[TableInfo]:
        """Return available tables, sheets, or selectable items."""

    @abstractmethod
    def read_records(self, item_name: str) -> list[dict[str, Any]]:
        """Read records without modifying the source."""

    @abstractmethod
    def close(self) -> None:
        """Release resources held by the adapter."""
