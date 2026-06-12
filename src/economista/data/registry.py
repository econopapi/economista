"""Connector registry for economista.data."""

from __future__ import annotations

from typing import Any

from economista.core.errors import SourceUnavailableError
from economista.data.base import BaseConnector


class ConnectorRegistry:
    """Map source names to connector classes."""

    def __init__(self) -> None:
        self._connectors: dict[str, type[BaseConnector]] = {}

    def register(self, source: str, connector: type[BaseConnector]) -> None:
        """Register a connector class for a source name."""
        self._connectors[source] = connector

    def get(self, source: str, **kwargs: Any) -> BaseConnector:
        """Instantiate the connector registered for a source."""
        try:
            connector = self._connectors[source]
        except KeyError as error:
            available = ", ".join(sorted(self._connectors)) or "none"
            raise SourceUnavailableError(
                f"Unknown data source {source!r}. Available sources: {available}."
            ) from error

        return connector(**kwargs)

    def available_sources(self) -> tuple[str, ...]:
        """Return registered source names."""
        return tuple(sorted(self._connectors))
