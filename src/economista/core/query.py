"""Data query abstraction."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256
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

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation of the query."""
        return asdict(self)

    def cache_key(self) -> str:
        """Return a stable hash suitable for cache file names."""
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return sha256(payload.encode("utf-8")).hexdigest()
