import json
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import pytest

from economista import data
from economista.core.dataset import EconDataset
from economista.data import api as data_api
from economista.data.registry import ConnectorRegistry
from economista.data.sources.world_bank import WorldBankConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "world_bank"


def _load_fixture(name: str) -> Any:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _mock_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/country/MEX/indicator/NY.GDP.MKTP.CD" in path:
            return httpx.Response(
                200,
                json=[
                    _load_fixture("observations.json")[0],
                    [_load_fixture("observations.json")[1][0]],
                ],
            )
        if "/country/COL/indicator/NY.GDP.MKTP.CD" in path:
            return httpx.Response(
                200,
                json=[
                    _load_fixture("observations.json")[0],
                    [_load_fixture("observations.json")[1][1]],
                ],
            )
        if "/indicator/NY.GDP.MKTP.CD" in path:
            return httpx.Response(200, json=_load_fixture("indicator.json"))
        if "/sources/2/indicators" in path:
            return httpx.Response(200, json=_load_fixture("search.json"))
        if path.endswith("/country"):
            return httpx.Response(200, json=_load_fixture("geos.json"))
        if path.endswith("/topic"):
            return httpx.Response(200, json=_load_fixture("topics.json"))

        return httpx.Response(404, json={"message": [{"value": "not found"}]})

    return httpx.Client(transport=httpx.MockTransport(handler))


class MockWorldBankConnector(WorldBankConnector):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            cache=False,
            client=_mock_client(),
            request_interval=0,
            **kwargs,
        )


def test_world_bank_connector_normalizes_fetch() -> None:
    connector = WorldBankConnector(
        cache=False,
        client=_mock_client(),
        request_interval=0,
    )

    dataset = connector.fetch(
        indicator="NY.GDP.MKTP.CD",
        geo=["MEX", "COL"],
        start=2023,
        end=2023,
    )

    frame = dataset.to_pandas()
    assert isinstance(dataset, EconDataset)
    assert list(frame["geo"]) == ["MEX", "COL"]
    assert set(frame.columns) >= {
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
    }
    assert dataset.metadata.source == "world_bank"
    assert dataset.metadata.dataset == "wdi"
    assert dataset.metadata.time_coverage == ("2023", "2023")


def test_data_fetch_dispatches_to_world_bank(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    dataset = data.fetch(
        source="world_bank",
        dataset="wdi",
        indicator="NY.GDP.MKTP.CD",
        geo=["MEX", "COL"],
        start=2023,
        end=2023,
    )

    assert dataset.to_pandas()["value"].tolist() == [1790000000000.0, 363000000000.0]


def test_data_search_dispatches_to_world_bank(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search(
        source="world_bank",
        query="GDP current",
        limit=5,
    )

    assert isinstance(results, pd.DataFrame)
    assert results[["source", "dataset", "kind", "id", "name"]].to_dict(
        orient="records"
    ) == [
        {
            "source": "world_bank",
            "dataset": "wdi",
            "kind": "indicators",
            "id": "NY.GDP.MKTP.CD",
            "name": "GDP (current US$)",
        }
    ]


def test_data_search_can_return_plain_rows(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search(
        "GDP current",
        source="world_bank",
        kind="indicators",
        as_frame=False,
    )

    assert isinstance(results, list)
    assert results[0]["id"] == "NY.GDP.MKTP.CD"
    assert results[0]["kind"] == "indicators"


def test_data_search_geos_finds_country_codes(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search("Mexico", source="world_bank", kind="geos")

    assert isinstance(results, pd.DataFrame)
    assert results.iloc[0]["id"] == "MEX"
    assert results.iloc[0]["iso2"] == "MX"
    assert results.iloc[0]["iso3"] == "MEX"


def test_data_search_filters_geos_by_region(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search(
        source="world_bank",
        kind="geos",
        region="Europe",
        include_aggregates=False,
    )

    assert isinstance(results, pd.DataFrame)
    assert results["id"].tolist() == ["FRA"]


def test_data_search_topics(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search("debt", source="world_bank", kind="topics")

    assert isinstance(results, pd.DataFrame)
    assert results["name"].tolist() == ["External Debt"]


def test_data_search_all_uses_all_catalogs(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search("debt", source="world_bank", limit=None)

    assert isinstance(results, pd.DataFrame)
    assert results["kind"].tolist() == ["indicators", "topics"]
    assert results["id"].tolist() == ["DT.DOD.DECT.CD", "6"]


def test_data_search_without_source_uses_registered_connectors(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search("Argentina", kind="geos")

    assert isinstance(results, pd.DataFrame)
    assert results["id"].tolist() == ["ARG"]


def test_data_search_limit_none_returns_all_rows(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search(source="world_bank", kind="indicators", limit=None)

    assert isinstance(results, pd.DataFrame)
    assert results["id"].tolist() == [
        "NY.GDP.MKTP.CD",
        "SP.POP.TOTL",
        "DT.DOD.DECT.CD",
    ]


def test_data_search_rejects_non_positive_limit(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("world_bank", MockWorldBankConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    with pytest.raises(ValueError, match="positive integer"):
        data.search(source="world_bank", kind="indicators", limit=0)
