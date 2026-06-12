import json
from pathlib import Path
from typing import Any

import httpx

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

    assert results == [
        {
            "id": "NY.GDP.MKTP.CD",
            "name": "GDP (current US$)",
            "source": "world_bank",
            "dataset": "wdi",
        }
    ]
