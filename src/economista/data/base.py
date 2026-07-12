"""Base classes for data connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from economista.core.dataset import EconDataset
from economista.core.query import DataQuery

SearchKind = Literal["all", "indicators", "geos", "topics"]
SearchRows = list[dict[str, Any]]


class BaseConnector(ABC):
    """Base class for external data source connectors."""

    source: str

    def __init__(self, *, cache: bool = True, timeout: int = 30) -> None:
        self.cache = cache
        self.timeout = timeout

    @abstractmethod
    def fetch(self, query: DataQuery | None = None, **kwargs: Any) -> EconDataset:
        """Fetch data from the source."""

    @abstractmethod
    def search(
        self,
        query: str | None = None,
        *,
        dataset: str | None = None,
        kind: SearchKind = "all",
        limit: int | None = 25,
        **kwargs: Any,
    ) -> SearchRows:
        """Search source catalogs."""

    def available_geos(
        self,
        query: str | None = None,
        *,
        dataset: str | None = None,
        limit: int | None = 25,
        **kwargs: Any,
    ) -> SearchRows:
        """Return available geographic entities for the source."""
        return self.search(
            query=query,
            dataset=dataset,
            kind="geos",
            limit=limit,
            **kwargs,
        )

    def available_indicators(
        self,
        query: str | None = None,
        *,
        dataset: str | None = None,
        limit: int | None = 25,
        **kwargs: Any,
    ) -> SearchRows:
        """Return available indicators for the source."""
        return self.search(
            query=query,
            dataset=dataset,
            kind="indicators",
            limit=limit,
            **kwargs,
        )

    def available_topics(
        self,
        query: str | None = None,
        *,
        dataset: str | None = None,
        limit: int | None = 25,
        **kwargs: Any,
    ) -> SearchRows:
        """Return available topics for the source."""
        return self.search(
            query=query,
            dataset=dataset,
            kind="topics",
            limit=limit,
            **kwargs,
        )
