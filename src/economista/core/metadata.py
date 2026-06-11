"""Economic metadata objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class EconMetadata:
    """Metadata describing the economic context of a dataset."""

    source: str
    dataset: str | None = None
    indicator: str | list[str] | None = None
    indicator_name: str | None = None
    unit: str | None = None
    frequency: str | None = None
    geo_coverage: list[str] | None = None
    time_coverage: tuple[str | int, str | int] | None = None
    currency: str | None = None
    price_base: str | int | None = None
    seasonal_adjustment: str | None = None
    downloaded_at: datetime | None = None
    source_updated_at: datetime | None = None
    license: str | None = None
    methodology_url: str | None = None
    citation: str | None = None
    notes: str | None = None
    query: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return metadata as a dictionary."""
        data = asdict(self)

        for key in ("downloaded_at", "source_updated_at"):
            value = data[key]
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        return data
