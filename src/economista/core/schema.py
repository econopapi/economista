"""Schema validation for economic datasets."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from economista.core.errors import SchemaValidationError


@dataclass(frozen=True)
class EconSchema:
    """Minimal schema definition for canonical economic data."""

    required_columns: tuple[str, ...]
    optional_columns: tuple[str, ...] = ()
    primary_keys: tuple[str, ...] | None = None
    value_column: str = "value"
    time_column: str = "time"
    geo_column: str = "geo"

    def validate(self, frame: pd.DataFrame) -> None:
        """Validate that required columns exist in a DataFrame."""
        missing = [col for col in self.required_columns if col not in frame.columns]

        if missing:
            raise SchemaValidationError(
                f"Missing required columns: {', '.join(missing)}"
            )


CANONICAL_ECON_SCHEMA = EconSchema(
    required_columns=(
        "geo",
        "geo_name",
        "time",
        "value",
        "indicator",
        "indicator_name",
        "unit",
        "frequency",
        "source",
        "dataset",
        "downloaded_at",
    ),
    optional_columns=(
        "sector",
        "product",
        "currency",
        "seasonal_adjustment",
        "price_base",
        "notes",
    ),
    primary_keys=("geo", "time", "indicator", "source", "dataset"),
)
