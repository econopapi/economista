"""World Bank / World Development Indicators connector."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any
from unicodedata import normalize

import httpx
import pandas as pd

from economista.core.cache import JsonCache
from economista.core.config import DEFAULT_CONFIG
from economista.core.dataset import EconDataset
from economista.core.errors import (
    DatasetNotFoundError,
    IndicatorNotFoundError,
    SourceUnavailableError,
)
from economista.core.metadata import EconMetadata
from economista.core.query import DataQuery
from economista.core.schema import CANONICAL_ECON_SCHEMA
from economista.data.base import BaseConnector, SearchKind, SearchRows

JsonObject = dict[str, Any]


class WorldBankConnector(BaseConnector):
    """Connector for World Bank World Development Indicators."""

    source = "world_bank"
    dataset = "wdi"
    base_url = "https://api.worldbank.org/v2"

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
            headers={"User-Agent": "economista.py"},
            timeout=timeout,
        )
        self._cache_store = cache_store or JsonCache(DEFAULT_CONFIG.cache)

    def fetch(self, query: DataQuery | None = None, **kwargs: Any) -> EconDataset:
        """Fetch WDI observations and return a canonical EconDataset."""
        data_query = self._coerce_query(query, **kwargs)
        self._validate_dataset(data_query.dataset)

        cached_payload = self._cache_store.get(data_query) if self.cache else None
        if cached_payload is None:
            payload = self._fetch_payload(data_query)
            if self.cache:
                self._cache_store.set(data_query, payload)
        else:
            payload = cached_payload

        dataset = self._dataset_from_payload(data_query, payload)
        return dataset.validate()

    def search(
        self,
        query: str | None = None,
        *,
        dataset: str | None = None,
        kind: SearchKind = "all",
        limit: int | None = 25,
        **kwargs: Any,
    ) -> SearchRows:
        """Search WDI catalog entries by id, name, notes, or classifications."""
        self._validate_dataset(dataset)
        self._validate_search_kind(kind)
        self._validate_search_limit(limit)
        self._validate_search_filters(kwargs)

        catalogs = ("indicators", "geos", "topics") if kind == "all" else (kind,)
        results: SearchRows = []
        for catalog in catalogs:
            rows = self._catalog_rows(catalog)
            results.extend(self._filter_search_rows(rows, query=query, filters=kwargs))

        return self._apply_search_limit(results, limit)

    def available_geos(
        self,
        query: str | None = None,
        *,
        dataset: str | None = None,
        limit: int | None = 25,
        **kwargs: Any,
    ) -> SearchRows:
        """Return World Bank geographic entities."""
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
        """Return WDI indicators."""
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
        """Return World Bank topics."""
        return self.search(
            query=query,
            dataset=dataset,
            kind="topics",
            limit=limit,
            **kwargs,
        )

    def _coerce_query(self, query: DataQuery | None, **kwargs: Any) -> DataQuery:
        if query is not None:
            return query

        return DataQuery(source=self.source, **kwargs)

    def _validate_dataset(self, dataset: str | None) -> None:
        if dataset not in (None, self.dataset):
            raise DatasetNotFoundError(
                "World Bank connector currently supports only dataset='wdi'."
            )

    def _fetch_payload(self, query: DataQuery) -> JsonObject:
        indicators = self._split_codes(query.indicator, "indicator")
        geos = self._split_codes(query.geo, "geo")
        params: dict[str, Any] = {
            "format": "json",
            "per_page": 1000,
        }
        date_range = self._date_range(query.start, query.end)
        if date_range is not None:
            params["date"] = date_range
        if query.frequency is not None:
            params["frequency"] = query.frequency
        params.update(query.params)

        rows_payload = self._empty_payload()
        for indicator in indicators:
            for geo in geos:
                country_payload = self._request_all_pages(
                    f"{self.base_url}/country/{geo}/indicator/{indicator}",
                    params=params,
                )
                rows_payload["rows"].extend(country_payload["rows"])

        indicator_payload = self._empty_payload()
        for indicator in indicators:
            single_indicator_payload = self._request_all_pages(
                f"{self.base_url}/indicator/{indicator}",
                params={"format": "json", "per_page": 1000},
            )
            indicator_payload["rows"].extend(single_indicator_payload["rows"])

        return {
            "rows": rows_payload,
            "indicators": indicator_payload,
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        }

    def _dataset_from_payload(self, query: DataQuery, payload: Any) -> EconDataset:
        if not isinstance(payload, dict):
            raise SourceUnavailableError("World Bank cache payload is invalid.")

        rows = self._payload_rows(payload.get("rows"))
        indicator_metadata = self._indicator_metadata(payload.get("indicators"))
        downloaded_at = str(payload.get("downloaded_at"))
        records: list[dict[str, Any]] = []

        for row in rows:
            indicator = self._nested_dict(row, "indicator")
            country = self._nested_dict(row, "country")
            indicator_id = str(indicator.get("id", ""))
            indicator_info = indicator_metadata.get(indicator_id, {})
            records.append(
                {
                    "geo": str(row.get("countryiso3code") or country.get("id") or ""),
                    "geo_name": str(country.get("value", "")),
                    "time": row.get("date"),
                    "value": row.get("value"),
                    "indicator": indicator_id,
                    "indicator_name": str(
                        indicator.get("value") or indicator_info.get("name") or ""
                    ),
                    "unit": str(row.get("unit") or indicator_info.get("unit") or ""),
                    "frequency": self._frequency_from_query(query),
                    "source": self.source,
                    "dataset": self.dataset,
                    "downloaded_at": downloaded_at,
                }
            )

        frame = pd.DataFrame.from_records(records)
        if frame.empty:
            raise IndicatorNotFoundError("World Bank returned no observations.")

        econ_metadata = EconMetadata(
            source=self.source,
            dataset=self.dataset,
            indicator=query.indicator,
            indicator_name=self._single_indicator_name(indicator_metadata),
            unit=self._single_indicator_unit(indicator_metadata),
            frequency=self._frequency_from_query(query),
            geo_coverage=self._geo_coverage(query.geo),
            time_coverage=self._observed_time_coverage(frame),
            downloaded_at=datetime.fromisoformat(downloaded_at),
            license="World Bank Open Data",
            methodology_url="https://datahelpdesk.worldbank.org/",
            query=query.to_dict(),
        )
        history = [{"operation": "fetch", "query": query.to_dict()}]

        return EconDataset(
            frame=frame,
            metadata=econ_metadata,
            schema=CANONICAL_ECON_SCHEMA,
            history=history,
        )

    def _request_all_pages(self, url: str, params: dict[str, Any]) -> JsonObject:
        page = 1
        pages = 1
        all_rows: list[JsonObject] = []
        metadata: JsonObject = {}

        while page <= pages:
            page_params = {**params, "page": page}
            payload = self._request_json(url, page_params)
            page_metadata, rows = self._parse_world_bank_payload(payload)
            metadata = page_metadata
            pages = int(page_metadata.get("pages", 1) or 1)
            all_rows.extend(rows)
            page += 1

        return {"metadata": metadata, "rows": all_rows}

    def _empty_payload(self) -> JsonObject:
        return {"metadata": {}, "rows": []}

    def _catalog_rows(self, catalog: str) -> SearchRows:
        payload = self._catalog_payload(catalog)
        if catalog == "indicators":
            return self._indicator_catalog_rows(payload)
        if catalog == "geos":
            return self._geo_catalog_rows(payload)
        if catalog == "topics":
            return self._topic_catalog_rows(payload)

        raise ValueError(f"Unsupported World Bank catalog {catalog!r}.")

    def _catalog_payload(self, catalog: str) -> JsonObject:
        data_query = DataQuery(
            source=self.source,
            dataset=self.dataset,
            params={"catalog": catalog},
        )
        cached_payload = self._cache_store.get(data_query) if self.cache else None
        if cached_payload is not None:
            if not isinstance(cached_payload, dict):
                raise SourceUnavailableError("World Bank cache payload is invalid.")
            return cached_payload

        path_by_catalog = {
            "indicators": "/sources/2/indicators",
            "geos": "/country",
            "topics": "/topic",
        }
        try:
            path = path_by_catalog[catalog]
        except KeyError as error:
            raise ValueError(f"Unsupported World Bank catalog {catalog!r}.") from error

        payload = self._request_all_pages(
            f"{self.base_url}{path}",
            params={"format": "json", "per_page": 1000},
        )
        if self.cache:
            self._cache_store.set(data_query, payload)

        return payload

    def _indicator_catalog_rows(self, payload: JsonObject) -> SearchRows:
        rows: SearchRows = []
        for item in self._payload_rows(payload):
            indicator_id = str(item.get("id", ""))
            name = str(item.get("name", ""))
            source = self._nested_dict(item, "source")
            rows.append(
                {
                    "source": self.source,
                    "dataset": self.dataset,
                    "kind": "indicators",
                    "id": indicator_id,
                    "name": name,
                    "unit": str(item.get("unit", "")),
                    "source_note": str(item.get("sourceNote", "")),
                    "source_organization": str(
                        item.get("sourceOrganization") or source.get("value") or ""
                    ),
                    "topics": self._topic_values(item.get("topics")),
                }
            )

        return rows

    def _geo_catalog_rows(self, payload: JsonObject) -> SearchRows:
        rows: SearchRows = []
        for item in self._payload_rows(payload):
            region = self._nested_value(item, "region")
            iso3 = str(item.get("id", ""))
            rows.append(
                {
                    "source": self.source,
                    "dataset": self.dataset,
                    "kind": "geos",
                    "id": iso3,
                    "name": str(item.get("name", "")),
                    "iso2": str(item.get("iso2Code", "")),
                    "iso3": iso3,
                    "region": region,
                    "income_level": self._nested_value(item, "incomeLevel"),
                    "lending_type": self._nested_value(item, "lendingType"),
                    "is_aggregate": region.casefold() == "aggregates",
                }
            )

        return rows

    def _topic_catalog_rows(self, payload: JsonObject) -> SearchRows:
        rows: SearchRows = []
        for item in self._payload_rows(payload):
            rows.append(
                {
                    "source": self.source,
                    "dataset": self.dataset,
                    "kind": "topics",
                    "id": str(item.get("id", "")),
                    "name": str(item.get("value") or item.get("name") or ""),
                    "description": str(item.get("sourceNote", "")),
                }
            )

        return rows

    def _filter_search_rows(
        self,
        rows: SearchRows,
        *,
        query: str | None,
        filters: dict[str, Any],
    ) -> SearchRows:
        tokens = self._search_tokens(query)
        return [
            row
            for row in rows
            if self._matches_query(row, tokens) and self._matches_filters(row, filters)
        ]

    def _matches_query(self, row: dict[str, Any], tokens: list[str]) -> bool:
        if not tokens:
            return True

        haystack = self._normalize_search_text(
            " ".join(str(value) for value in row.values())
        )
        return all(token in haystack for token in tokens)

    def _matches_filters(self, row: dict[str, Any], filters: dict[str, Any]) -> bool:
        if (
            "include_aggregates" in filters
            and not filters["include_aggregates"]
            and bool(row.get("is_aggregate"))
        ):
            return False
        if "region" in filters and not self._field_matches(
            row,
            "region",
            filters["region"],
        ):
            return False
        if "income_level" in filters and not self._field_matches(
            row,
            "income_level",
            filters["income_level"],
        ):
            return False

        return not (
            "topic" in filters
            and not self._field_matches(row, "topics", filters["topic"])
        )

    def _field_matches(self, row: dict[str, Any], field: str, expected: Any) -> bool:
        if expected is None:
            return True

        actual = self._normalize_search_text(str(row.get(field, "")))
        expected_values = expected if isinstance(expected, list) else [expected]
        return any(
            self._normalize_search_text(str(value)) in actual
            for value in expected_values
        )

    def _validate_search_kind(self, kind: str) -> None:
        if kind not in {"all", "indicators", "geos", "topics"}:
            raise ValueError(
                "World Bank search kind must be one of 'all', 'indicators', "
                "'geos', or 'topics'."
            )

    def _validate_search_limit(self, limit: int | None) -> None:
        if limit is not None and limit <= 0:
            raise ValueError("search limit must be a positive integer or None.")

    def _validate_search_filters(self, filters: dict[str, Any]) -> None:
        supported_filters = {"include_aggregates", "region", "income_level", "topic"}
        unsupported = set(filters) - supported_filters
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(f"Unsupported World Bank search filters: {names}.")

    def _apply_search_limit(self, rows: SearchRows, limit: int | None) -> SearchRows:
        if limit is None:
            return rows

        return rows[:limit]

    def _request_json(self, url: str, params: dict[str, Any]) -> Any:
        retry_statuses = {429, 502, 503, 504}
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
                        "World Bank API returned HTTP "
                        f"{error.response.status_code} for {error.request.url}."
                    ) from error
                time.sleep(2**attempt)
            except httpx.RequestError as error:
                last_error = error
                if attempt >= self.max_retries:
                    raise SourceUnavailableError(
                        f"Could not reach World Bank API at {error.request.url}."
                    ) from error
                time.sleep(2**attempt)
            except ValueError as error:
                raise SourceUnavailableError(
                    "World Bank API returned invalid JSON."
                ) from error

        raise SourceUnavailableError("World Bank API request failed.") from last_error

    def _parse_world_bank_payload(
        self,
        payload: Any,
    ) -> tuple[JsonObject, list[JsonObject]]:
        if isinstance(payload, dict) and "message" in payload:
            raise SourceUnavailableError(self._world_bank_error_message(payload))

        if not isinstance(payload, list) or len(payload) < 2:
            raise SourceUnavailableError(
                "World Bank API returned an unexpected payload."
            )

        metadata = payload[0]
        rows = payload[1]
        if not isinstance(metadata, dict):
            raise SourceUnavailableError("World Bank API metadata is invalid.")
        if rows is None:
            return metadata, []
        if not isinstance(rows, list):
            raise SourceUnavailableError("World Bank API rows are invalid.")

        typed_rows = [row for row in rows if isinstance(row, dict)]
        return metadata, typed_rows

    def _world_bank_error_message(self, payload: dict[str, Any]) -> str:
        messages = payload.get("message")
        if not isinstance(messages, list):
            return "World Bank API returned an error."

        parts: list[str] = []
        for message in messages:
            if isinstance(message, dict):
                value = message.get("value") or message.get("key") or message.get("id")
                if value is not None:
                    parts.append(str(value))

        return "; ".join(parts) if parts else "World Bank API returned an error."

    def _payload_rows(self, payload: Any) -> list[JsonObject]:
        if not isinstance(payload, dict):
            return []

        rows = payload.get("rows", [])
        if not isinstance(rows, list):
            return []

        return [row for row in rows if isinstance(row, dict)]

    def _indicator_metadata(self, payload: Any) -> dict[str, JsonObject]:
        indicators: dict[str, JsonObject] = {}
        for item in self._payload_rows(payload):
            indicator_id = str(item.get("id", ""))
            indicators[indicator_id] = item

        return indicators

    def _nested_dict(self, row: JsonObject, key: str) -> JsonObject:
        value = row.get(key, {})
        return value if isinstance(value, dict) else {}

    def _nested_value(self, row: JsonObject, key: str) -> str:
        value = self._nested_dict(row, key)
        return str(value.get("value", ""))

    def _topic_values(self, value: Any) -> str:
        if not isinstance(value, list):
            return ""

        topics = []
        for item in value:
            if isinstance(item, dict):
                topic = item.get("value") or item.get("name") or item.get("id")
                if topic is not None:
                    topics.append(str(topic))

        return "; ".join(topics)

    def _single_indicator_name(self, metadata: dict[str, JsonObject]) -> str | None:
        names = {str(item.get("name", "")) for item in metadata.values()}
        names.discard("")
        return names.pop() if len(names) == 1 else None

    def _single_indicator_unit(self, metadata: dict[str, JsonObject]) -> str | None:
        units = {str(item.get("unit", "")) for item in metadata.values()}
        units.discard("")
        return units.pop() if len(units) == 1 else None

    def _split_codes(self, value: str | list[str] | None, field: str) -> list[str]:
        if value is None:
            raise ValueError(f"World Bank fetch requires {field}.")
        if isinstance(value, str):
            return [value]

        return value

    def _search_tokens(self, query: str | None) -> list[str]:
        if query is None:
            return []

        return self._normalize_search_text(query).split()

    def _normalize_search_text(self, value: str) -> str:
        ascii_text = normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        text = ascii_text.casefold().replace("$", " dollars ")
        return re.sub(r"[^a-z0-9]+", " ", text)

    def _date_range(
        self,
        start: int | str | None,
        end: int | str | None,
    ) -> str | None:
        if start is None and end is None:
            return None
        if start is None:
            return str(end)
        if end is None:
            return str(start)

        return f"{start}:{end}"

    def _frequency_from_query(self, query: DataQuery) -> str:
        return query.frequency or "annual"

    def _geo_coverage(self, geo: str | list[str] | None) -> list[str] | None:
        if geo is None:
            return None
        if isinstance(geo, str):
            return [geo]

        return geo

    def _time_coverage(
        self,
        start: int | str | None,
        end: int | str | None,
    ) -> tuple[str | int, str | int] | None:
        if start is None and end is None:
            return None
        if start is None:
            return (end, end) if end is not None else None
        if end is None:
            return (start, start)

        return (start, end)

    def _observed_time_coverage(self, frame: pd.DataFrame) -> tuple[str, str] | None:
        if "time" not in frame:
            return None

        values = [str(value) for value in frame["time"].dropna().tolist()]
        if not values:
            return None

        return (min(values), max(values))
