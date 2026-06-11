"""Data query abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DataQuery:
    """Standardized user intent before dispatching to a data connector."""

    source: str
    dataset: str | None = None
    indicator: str | list[str] | None = None
    geo: str | list[str] | None = None
    start: int | str | None = None
    end: int | str | None = None
    frequency: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
