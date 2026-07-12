"""Public data API."""

from __future__ import annotations

from typing import Any

import pandas as pd

from economista.core.dataset import EconDataset
from economista.core.query import DataQuery
from economista.data.base import SearchKind, SearchRows
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
    query: str | None = None,
    *,
    source: str | None = None,
    dataset: str | None = None,
    kind: SearchKind = "all",
    limit: int | None = 25,
    as_frame: bool = True,
    **kwargs: Any,
) -> pd.DataFrame | SearchRows:
    """Search economic catalogs in one or more configured sources."""
    _validate_limit(limit)

    if source is None:
        rows: SearchRows = []
        for registered_source in DEFAULT_REGISTRY.available_sources():
            connector = DEFAULT_REGISTRY.get(registered_source)
            rows.extend(
                connector.search(
                    query=query,
                    dataset=dataset,
                    kind=kind,
                    limit=None,
                    **kwargs,
                )
            )
        rows = _apply_limit(rows, limit)
    else:
        connector = DEFAULT_REGISTRY.get(source)
        rows = connector.search(
            query=query,
            dataset=dataset,
            kind=kind,
            limit=limit,
            **kwargs,
        )

    if not as_frame:
        return rows

    return _search_frame(rows)


def _query_from_args(*args: Any, **kwargs: Any) -> DataQuery:
    if args:
        if len(args) == 1 and isinstance(args[0], DataQuery):
            return args[0]
        raise TypeError("fetch accepts either a DataQuery or keyword arguments.")

    return DataQuery(**kwargs)


def _validate_limit(limit: int | None) -> None:
    if limit is not None and limit <= 0:
        raise ValueError("search limit must be a positive integer or None.")


def _apply_limit(rows: SearchRows, limit: int | None) -> SearchRows:
    if limit is None:
        return rows

    return rows[:limit]


def _search_frame(rows: SearchRows) -> pd.DataFrame:
    common_columns = ["source", "dataset", "kind", "id", "name"]
    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        return pd.DataFrame(columns=common_columns)

    extra_columns = [column for column in frame.columns if column not in common_columns]
    ordered_frame: pd.DataFrame = frame.loc[:, common_columns + extra_columns]
    return ordered_frame
