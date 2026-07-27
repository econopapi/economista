import json
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import pytest

from economista import data
from economista.core.errors import DatasetNotFoundError, UnsupportedFrequencyError
from economista.data import api as data_api
from economista.data.registry import ConnectorRegistry
from economista.data.sources.imf import IMFDataMapperConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "imf"


def _load_fixture(name: str) -> Any:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _mock_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/NGDP_RPCH" in path:
            return httpx.Response(200, json=_load_fixture("observations.json"))
        for catalog in ("indicators", "countries", "regions", "groups"):
            if path.endswith(f"/{catalog}"):
                return httpx.Response(200, json=_load_fixture(f"{catalog}.json"))
        return httpx.Response(404, json={"error": "not found"})

    return httpx.Client(transport=httpx.MockTransport(handler))


class MockIMFDataMapperConnector(IMFDataMapperConnector):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            cache=False,
            client=_mock_client(),
            request_interval=0,
            **kwargs,
        )


def test_imf_datamapper_normalizes_and_filters_fetch() -> None:
    connector = IMFDataMapperConnector(
        cache=False,
        client=_mock_client(),
        request_interval=0,
    )

    dataset = connector.fetch(
        indicator="NGDP_RPCH",
        geo=["MEX", "COL"],
        start=2023,
        end=2023,
    )

    frame = dataset.to_pandas()
    assert frame[["geo", "time", "value"]].to_dict(orient="records") == [
        {"geo": "MEX", "time": "2023", "value": 3.2},
        {"geo": "COL", "time": "2023", "value": 1.1},
    ]
    assert frame["geo_name"].tolist() == ["Mexico", "Colombia"]
    assert frame["dataset"].tolist() == ["WEO", "WEO"]
    assert dataset.metadata.source == "imf"
    assert dataset.metadata.dataset == "WEO"
    assert dataset.metadata.frequency == "annual"
    assert dataset.metadata.source_updated_at is not None
    assert dataset.metadata.time_coverage == ("2023", "2023")


def test_data_fetch_dispatches_to_imf_datamapper(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("imf", MockIMFDataMapperConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    dataset = data.fetch(
        source="imf",
        indicator="NGDP_RPCH",
        geo="MEX",
        start=2024,
        end=2024,
    )

    assert dataset.to_pandas()["value"].tolist() == [1.5]


def test_imf_datamapper_searches_indicators_and_geos() -> None:
    connector = MockIMFDataMapperConnector()

    indicators = connector.search(
        "real GDP", kind="indicators", dataset="WEO", limit=None
    )
    geos = connector.search("Mexico", kind="geos")
    groups = connector.search(kind="geos", geo_type="group")

    assert indicators[0]["id"] == "NGDP_RPCH"
    assert indicators[0]["projection_year"] == 2026
    assert geos == [
        {
            "source": "imf",
            "dataset": "datamapper",
            "kind": "geos",
            "id": "MEX",
            "name": "Mexico",
            "geo_type": "country",
        }
    ]
    assert groups[0]["id"] == "ADVEC"
    assert groups[0]["geo_type"] == "group"


def test_imf_datamapper_topics_are_not_fabricated() -> None:
    connector = MockIMFDataMapperConnector()

    assert connector.search(kind="topics", limit=None) == []


def test_imf_datamapper_rejects_non_annual_frequency() -> None:
    connector = MockIMFDataMapperConnector()

    with pytest.raises(UnsupportedFrequencyError, match="annual"):
        connector.fetch(indicator="NGDP_RPCH", frequency="quarterly")


def test_imf_datamapper_rejects_dataset_mismatch() -> None:
    connector = MockIMFDataMapperConnector()

    with pytest.raises(DatasetNotFoundError, match="belongs"):
        connector.fetch(indicator="NGDP_RPCH", dataset="FM")


def test_imf_datamapper_rejects_custom_fetch_params() -> None:
    connector = MockIMFDataMapperConnector()

    with pytest.raises(ValueError, match="custom fetch params"):
        connector.fetch(indicator="NGDP_RPCH", params={"periods": "2024"})


def test_data_search_dispatches_to_imf_datamapper(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    registry = ConnectorRegistry()
    registry.register("imf", MockIMFDataMapperConnector)
    monkeypatch.setattr(data_api, "DEFAULT_REGISTRY", registry)

    results = data.search(source="imf", query="Mexico", kind="geos")

    assert isinstance(results, pd.DataFrame)
    assert results.iloc[0]["id"] == "MEX"
    assert results.iloc[0]["geo_type"] == "country"
