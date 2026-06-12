"""Public data API."""

from __future__ import annotations

from typing import Any

from economista.core.dataset import EconDataset
from economista.core.query import DataQuery
from economista.data.registry import ConnectorRegistry
from economista.data.sources.world_bank import WorldBankConnector

DEFAULT_REGISTRY = ConnectorRegistry()
DEFAULT_REGISTRY.register(WorldBankConnector.source, WorldBankConnector)


def fetch(*args: Any, **kwargs: Any) -> EconDataset:
    """Fetch economic data from a configured source."""
    query = _query_from_args(*args, **kwargs)
    connector = DEFAULT_REGISTRY.get(query.source)
    return connector.fetch(query)


def search(
    *,
    source: str,
    query: str,
    limit: int = 20,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Search economic indicators in a configured source."""
    connector = DEFAULT_REGISTRY.get(source)
    return connector.search(query=query, limit=limit, **kwargs)


def _query_from_args(*args: Any, **kwargs: Any) -> DataQuery:
    if args:
        if len(args) == 1 and isinstance(args[0], DataQuery):
            return args[0]
        raise TypeError("fetch accepts either a DataQuery or keyword arguments.")

    return DataQuery(**kwargs)
