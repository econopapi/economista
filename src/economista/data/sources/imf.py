"""IMF DataMapper API v2 connector."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any
from unicodedata import normalize
from urllib.parse import quote

import httpx
import pandas as pd

from economista.core.cache import JsonCache
from economista.core.config import DEFAULT_CONFIG
from economista.core.dataset import EconDataset
from economista.core.errors import (
    DatasetNotFoundError,
    IndicatorNotFoundError,
    SourceUnavailableError,
    UnsupportedFrequencyError,
)
from economista.core.metadata import EconMetadata
from economista.core.query import DataQuery
from economista.core.schema import CANONICAL_ECON_SCHEMA
from economista.data.base import BaseConnector, SearchKind, SearchRows

JsonObject = dict[str, Any]


class IMFDataMapperConnector(BaseConnector):
    """Connector for the public IMF DataMapper API v2.

    DataMapper is a curated, annual-data surface of IMF datasets. It is distinct
    from the authenticated IMF SDMX API and deliberately has no credential support.
    """

    source = "imf"
    api_name = "IMF DataMapper API v2"
    base_url = "https://www.imf.org/external/datamapper/api/v2"

    def __init__(
        self,
        *,
        cache: bool = True,
        timeout: int = 30,
        max_retries: int = 2,
        request_interval: float = 0.25,
        client: httpx.Client | None = None,
        cache_store: JsonCache | None = None,
    ) -> None:
        super().__init__(cache=cache, timeout=timeout)
        self.max_retries = max_retries
        self.request_interval = request_interval
        self._client = client or httpx.Client(
            follow_redirects=True,
            # DataMapper currently rejects the project-specific agent used by
            # the World Bank connector, but accepts the standard httpx agent.
            headers={"User-Agent": "python-httpx/0.28.1"},
            timeout=timeout,
        )
        self._cache_store = cache_store or JsonCache(DEFAULT_CONFIG.cache)

    def fetch(self, query: DataQuery | None = None, **kwargs: Any) -> EconDataset:
        """Fetch annual DataMapper observations as a canonical EconDataset."""
        data_query = self._coerce_query(query, **kwargs)
        self._validate_frequency(data_query.frequency)
        self._validate_periods(data_query.start, data_query.end)
        self._validate_fetch_params(data_query.params)

        cached_payload = self._cache_store.get(data_query) if self.cache else None
        if cached_payload is None:
            payload = self._fetch_payload(data_query)
            if self.cache:
                self._cache_store.set(data_query, payload)
        else:
            payload = cached_payload

        return self._dataset_from_payload(data_query, payload).validate()

    def search(
        self,
        query: str | None = None,
        *,
        dataset: str | None = None,
        kind: SearchKind = "all",
        limit: int | None = 25,
        **kwargs: Any,
    ) -> SearchRows:
        """Search DataMapper indicators and geographic entities lexically."""
        self._validate_search_kind(kind)
        self._validate_search_limit(limit)
        self._validate_search_filters(kwargs)

        catalogs = self._catalogs_for_kind(kind)
        rows: SearchRows = []
        for catalog in catalogs:
            catalog_rows = self._catalog_rows(catalog)
            rows.extend(
                self._filter_search_rows(
                    catalog_rows,
                    query=query,
                    dataset=dataset,
                    filters=kwargs,
                )
            )

        return self._apply_search_limit(rows, limit)

    def _coerce_query(self, query: DataQuery | None, **kwargs: Any) -> DataQuery:
        if query is not None:
            if query.source != self.source:
                raise ValueError(
                    f"IMF DataMapper connector cannot fetch source={query.source!r}."
                )
            return query
        return DataQuery(source=self.source, **kwargs)

    def _fetch_payload(self, query: DataQuery) -> JsonObject:
        indicators = self._split_codes(query.indicator, "indicator")

        payloads: dict[str, Any] = {}
        for indicator in indicators:
            # DataMapper's documented geo and period filters can return the
            # unfiltered universe or a 403. Fetch the indicator once and apply
            # requested geography and period filters below instead.
            url = f"{self.base_url}/{quote(indicator, safe='')}"
            payloads[indicator] = self._request_json(url, {})

        return {
            "payloads": payloads,
            "geos": self._geo_catalog(),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        }

    def _dataset_from_payload(self, query: DataQuery, payload: Any) -> EconDataset:
        if not isinstance(payload, dict):
            raise SourceUnavailableError("IMF DataMapper cache payload is invalid.")

        raw_payloads = payload.get("payloads")
        geo_catalog = payload.get("geos")
        downloaded_at = payload.get("downloaded_at")
        if not isinstance(raw_payloads, dict) or not isinstance(geo_catalog, dict):
            raise SourceUnavailableError("IMF DataMapper cache payload is invalid.")
        if not isinstance(downloaded_at, str):
            raise SourceUnavailableError(
                "IMF DataMapper download timestamp is invalid."
            )

        requested_geos = set(self._split_codes(query.geo, "geo", required=False))
        records: list[dict[str, Any]] = []
        indicator_metadata: dict[str, JsonObject] = {}

        for requested_indicator, raw_payload in raw_payloads.items():
            metadata, values = self._parse_data_payload(raw_payload)
            item_metadata = metadata.get(requested_indicator, {})
            if not item_metadata:
                raise IndicatorNotFoundError(
                    f"IMF DataMapper did not return indicator {requested_indicator!r}."
                )
            indicator_metadata[requested_indicator] = item_metadata
            dataset = str(item_metadata.get("dataset", ""))
            if (
                query.dataset is not None
                and dataset.casefold() != query.dataset.casefold()
            ):
                raise DatasetNotFoundError(
                    f"Indicator {requested_indicator!r} belongs to DataMapper "
                    f"dataset {dataset!r}, not {query.dataset!r}."
                )

            series_by_geo = values.get(requested_indicator, {})
            if not isinstance(series_by_geo, dict):
                raise SourceUnavailableError("IMF DataMapper observations are invalid.")

            for geo, observations in series_by_geo.items():
                if requested_geos and geo not in requested_geos:
                    continue
                if not isinstance(geo, str) or not isinstance(observations, dict):
                    continue
                geo_info = geo_catalog.get(geo, {})
                geo_name = str(geo_info.get("name", geo))
                for observation_time, value in observations.items():
                    if not self._within_periods(
                        observation_time, query.start, query.end
                    ):
                        continue
                    records.append(
                        {
                            "geo": geo,
                            "geo_name": geo_name,
                            "time": str(observation_time),
                            "value": value,
                            "indicator": requested_indicator,
                            "indicator_name": str(item_metadata.get("label", "")),
                            "unit": str(item_metadata.get("unit", "")),
                            "frequency": "annual",
                            "source": self.source,
                            "dataset": dataset,
                            "notes": str(item_metadata.get("description", "")),
                            "downloaded_at": downloaded_at,
                        }
                    )

        frame = pd.DataFrame.from_records(records)
        if frame.empty:
            raise IndicatorNotFoundError("IMF DataMapper returned no observations.")

        actual_datasets = {
            str(item.get("dataset", ""))
            for item in indicator_metadata.values()
            if item.get("dataset")
        }
        econ_metadata = EconMetadata(
            source=self.source,
            dataset=actual_datasets.pop() if len(actual_datasets) == 1 else None,
            indicator=query.indicator,
            indicator_name=self._single_metadata_value(indicator_metadata, "label"),
            unit=self._single_metadata_value(indicator_metadata, "unit"),
            frequency="annual",
            geo_coverage=sorted(frame["geo"].unique().tolist()),
            time_coverage=self._observed_time_coverage(frame),
            downloaded_at=datetime.fromisoformat(downloaded_at),
            source_updated_at=self._single_last_modified(indicator_metadata),
            license="IMF Data Terms and Conditions",
            methodology_url="https://www.imf.org/external/datamapper/api/",
            citation="International Monetary Fund, IMF DataMapper API v2.",
            query=query.to_dict(),
        )
        return EconDataset(
            frame=frame,
            metadata=econ_metadata,
            schema=CANONICAL_ECON_SCHEMA,
            history=[{"operation": "fetch", "query": query.to_dict()}],
        )

    def _geo_catalog(self) -> dict[str, JsonObject]:
        catalog: dict[str, JsonObject] = {}
        for catalog_name in ("countries", "regions", "groups"):
            for row in self._catalog_rows(catalog_name):
                catalog[str(row["id"])] = {
                    "name": row["name"],
                    "geo_type": row["geo_type"],
                }
        return catalog

    def _catalogs_for_kind(self, kind: SearchKind) -> tuple[str, ...]:
        if kind == "indicators":
            return ("indicators",)
        if kind == "geos":
            return ("countries", "regions", "groups")
        if kind == "topics":
            return ()
        return ("indicators", "countries", "regions", "groups")

    def _catalog_rows(self, catalog: str) -> SearchRows:
        payload = self._catalog_payload(catalog)
        entries = payload.get(catalog)
        if not isinstance(entries, dict):
            raise SourceUnavailableError(
                f"IMF DataMapper {catalog} catalog is invalid."
            )

        rows: SearchRows = []
        geo_type_by_catalog = {
            "countries": "country",
            "regions": "region",
            "groups": "group",
        }
        for identifier, details in entries.items():
            if not isinstance(identifier, str) or not isinstance(details, dict):
                continue
            if catalog == "indicators":
                rows.append(
                    {
                        "source": self.source,
                        "dataset": str(details.get("dataset", "")),
                        "kind": "indicators",
                        "id": identifier,
                        "name": str(details.get("label", "")),
                        "description": str(details.get("description", "")),
                        "unit": str(details.get("unit", "")),
                        "source_dataset": str(details.get("source", "")),
                        "projection_year": details.get("projection-year"),
                        "last_modified": str(details.get("last-modified", "")),
                    }
                )
            else:
                rows.append(
                    {
                        "source": self.source,
                        "dataset": "datamapper",
                        "kind": "geos",
                        "id": identifier,
                        "name": str(details.get("label", "")),
                        "geo_type": geo_type_by_catalog[catalog],
                    }
                )
        return rows

    def _catalog_payload(self, catalog: str) -> JsonObject:
        data_query = DataQuery(source=self.source, params={"catalog": catalog})
        cached_payload = self._cache_store.get(data_query) if self.cache else None
        if cached_payload is not None:
            if not isinstance(cached_payload, dict):
                raise SourceUnavailableError("IMF DataMapper cache payload is invalid.")
            return cached_payload

        payload = self._request_json(f"{self.base_url}/{catalog}", {})
        if not isinstance(payload, dict):
            raise SourceUnavailableError(
                f"IMF DataMapper {catalog} catalog is invalid."
            )
        if self.cache:
            self._cache_store.set(data_query, payload)
        return payload

    def _filter_search_rows(
        self,
        rows: SearchRows,
        *,
        query: str | None,
        dataset: str | None,
        filters: dict[str, Any],
    ) -> SearchRows:
        tokens = self._search_tokens(query)
        filtered: SearchRows = []
        for row in rows:
            if dataset is not None and row["dataset"].casefold() != dataset.casefold():
                continue
            if "geo_type" in filters and row.get("geo_type") != filters["geo_type"]:
                continue
            if self._matches_query(row, tokens):
                filtered.append(row)
        return filtered

    def _matches_query(self, row: dict[str, Any], tokens: list[str]) -> bool:
        if not tokens:
            return True
        haystack = self._normalize_search_text(" ".join(map(str, row.values())))
        return all(token in haystack for token in tokens)

    def _request_json(self, url: str, params: dict[str, Any]) -> Any:
        retry_statuses = {429, 500, 502, 503, 504}
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.request_interval > 0:
                    time.sleep(self.request_interval)
                response = self._client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as error:
                last_error = error
                if (
                    error.response.status_code not in retry_statuses
                    or attempt >= self.max_retries
                ):
                    raise SourceUnavailableError(
                        "IMF DataMapper API returned HTTP "
                        f"{error.response.status_code} for {error.request.url}."
                    ) from error
                time.sleep(2**attempt)
            except httpx.RequestError as error:
                last_error = error
                if attempt >= self.max_retries:
                    raise SourceUnavailableError(
                        f"Could not reach IMF DataMapper API at {error.request.url}."
                    ) from error
                time.sleep(2**attempt)
            except ValueError as error:
                raise SourceUnavailableError(
                    "IMF DataMapper API returned invalid JSON."
                ) from error
        raise SourceUnavailableError(
            "IMF DataMapper API request failed."
        ) from last_error

    def _parse_data_payload(
        self, payload: Any
    ) -> tuple[dict[str, JsonObject], dict[str, Any]]:
        if not isinstance(payload, dict):
            raise SourceUnavailableError(
                "IMF DataMapper API returned an unexpected payload."
            )
        raw_metadata = payload.get("indicators")
        raw_values = payload.get("values")
        if not isinstance(raw_metadata, dict) or not isinstance(raw_values, dict):
            raise SourceUnavailableError("IMF DataMapper API payload is invalid.")
        metadata = {
            identifier: details
            for identifier, details in raw_metadata.items()
            if isinstance(identifier, str) and isinstance(details, dict)
        }
        return metadata, raw_values

    def _validate_frequency(self, frequency: str | None) -> None:
        if frequency is not None and frequency.casefold() not in {"annual", "a"}:
            raise UnsupportedFrequencyError(
                "IMF DataMapper API v2 supports annual observations only."
            )

    def _validate_periods(
        self, start: int | str | None, end: int | str | None
    ) -> None:
        for value in (start, end):
            if value is not None and not str(value).isdigit():
                raise ValueError("IMF DataMapper periods must be whole calendar years.")
        if start is not None and end is not None and int(start) > int(end):
            raise ValueError("IMF DataMapper start year must not be after end year.")

    def _validate_fetch_params(self, params: dict[str, Any]) -> None:
        if params:
            names = ", ".join(sorted(params))
            raise ValueError(
                "IMF DataMapper does not support custom fetch params. "
                f"Use indicator, geo, start, and end instead of: {names}."
            )

    def _validate_search_kind(self, kind: str) -> None:
        if kind not in {"all", "indicators", "geos", "topics"}:
            raise ValueError(
                "IMF DataMapper search kind must be one of 'all', 'indicators', "
                "'geos', or 'topics'."
            )

    def _validate_search_limit(self, limit: int | None) -> None:
        if limit is not None and limit <= 0:
            raise ValueError("search limit must be a positive integer or None.")

    def _validate_search_filters(self, filters: dict[str, Any]) -> None:
        unsupported = set(filters) - {"geo_type"}
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(f"Unsupported IMF DataMapper search filters: {names}.")

    def _split_codes(
        self, value: str | list[str] | None, field: str, *, required: bool = True
    ) -> list[str]:
        if value is None:
            if required:
                raise ValueError(f"IMF DataMapper fetch requires {field}.")
            return []
        return [value] if isinstance(value, str) else value

    def _within_periods(
        self, value: Any, start: int | str | None, end: int | str | None
    ) -> bool:
        try:
            year = int(str(value))
        except ValueError:
            return False
        return (start is None or year >= int(start)) and (
            end is None or year <= int(end)
        )

    def _single_metadata_value(
        self, metadata: dict[str, JsonObject], field: str
    ) -> str | None:
        values = {str(item.get(field, "")) for item in metadata.values()}
        values.discard("")
        return values.pop() if len(values) == 1 else None

    def _single_last_modified(
        self, metadata: dict[str, JsonObject]
    ) -> datetime | None:
        value = self._single_metadata_value(metadata, "last-modified")
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _observed_time_coverage(self, frame: pd.DataFrame) -> tuple[str, str] | None:
        values = [str(value) for value in frame["time"].dropna().tolist()]
        return (min(values), max(values)) if values else None

    def _search_tokens(self, query: str | None) -> list[str]:
        return self._normalize_search_text(query).split() if query is not None else []

    def _normalize_search_text(self, value: str) -> str:
        ascii_text = normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z0-9]+", " ", ascii_text.casefold())

    def _apply_search_limit(self, rows: SearchRows, limit: int | None) -> SearchRows:
        return rows if limit is None else rows[:limit]
