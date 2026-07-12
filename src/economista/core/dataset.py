"""Dataset abstraction for economic data."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from typing_extensions import Self

from economista.core.metadata import EconMetadata
from economista.core.schema import EconSchema


@dataclass
class EconDataset:
    """Economic dataset composed of a pandas DataFrame plus metadata."""

    frame: pd.DataFrame
    metadata: EconMetadata
    schema: EconSchema | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_pandas(self, copy: bool = True) -> pd.DataFrame:
        """Return the underlying pandas DataFrame."""
        if copy:
            return self.frame.copy()

        return self.frame

    def to_dict(self) -> dict[str, Any]:
        """Return data and metadata as JSON-serializable dictionaries."""
        records = json.loads(
            self.frame.to_json(orient="records", date_format="iso", default_handler=str)
        )
        return {
            "data": records,
            "metadata": self.metadata.to_dict(),
            "history": self.history,
        }

    def to_json(self, path: str | Path | None = None) -> dict[str, Any]:
        """Return the dataset as a dictionary and optionally write JSON to disk."""
        data = self.to_dict()
        if path is not None:
            Path(path).write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )

        return data

    def to_csv(
        self,
        path: str | Path,
        *,
        include_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """Write the DataFrame to CSV and metadata to a sidecar JSON file."""
        output_path = Path(path)
        self.frame.to_csv(output_path, index=False, **kwargs)
        if include_metadata:
            self._write_metadata_sidecar(output_path)

    def to_parquet(
        self,
        path: str | Path,
        *,
        include_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """Write the DataFrame to Parquet and metadata to a sidecar JSON file."""
        output_path = Path(path)
        self.frame.to_parquet(output_path, index=False, **kwargs)
        if include_metadata:
            self._write_metadata_sidecar(output_path)

    def validate(self) -> Self:
        """Validate the dataset against its schema when one is available."""
        if self.schema is not None:
            self.schema.validate(self.frame)

        return self

    def pipe(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Apply a function to this dataset."""
        return func(self, *args, **kwargs)

    def _write_metadata_sidecar(self, output_path: Path) -> None:
        metadata_path = output_path.with_suffix(f"{output_path.suffix}.metadata.json")
        metadata_path.write_text(
            json.dumps(
                self.metadata.to_dict(),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
