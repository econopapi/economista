"""Base classes for data connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from economista.core.dataset import EconDataset
from economista.core.query import DataQuery


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
        query: str,
        limit: int = 20,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search source indicators."""
