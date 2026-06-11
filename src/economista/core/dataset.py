"""Dataset abstraction for economic data."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

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
            return cast(pd.DataFrame, self.frame.copy())

        return self.frame

    def validate(self) -> Self:
        """Validate the dataset against its schema when one is available."""
        if self.schema is not None:
            self.schema.validate(self.frame)

        return self

    def pipe(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Apply a function to this dataset."""
        return func(self, *args, **kwargs)