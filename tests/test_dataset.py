import json

import pandas as pd
import pytest

from economista.core.dataset import EconDataset
from economista.core.metadata import EconMetadata
from economista.core.schema import CANONICAL_ECON_SCHEMA


def test_dataset_exports_json_and_csv_with_metadata(tmp_path) -> None:  # type: ignore[no-untyped-def]
    dataset = EconDataset(
        frame=pd.DataFrame(
            {
                "geo": ["MEX"],
                "geo_name": ["Mexico"],
                "time": ["2023"],
                "value": [1.0],
                "indicator": ["GDP"],
                "indicator_name": ["GDP"],
                "unit": ["usd"],
                "frequency": ["annual"],
                "source": ["test"],
                "dataset": ["fixture"],
                "downloaded_at": ["2026-06-11T00:00:00+00:00"],
            }
        ),
        metadata=EconMetadata(source="test", dataset="fixture"),
        schema=CANONICAL_ECON_SCHEMA,
    )

    dataset.validate()
    json_path = tmp_path / "dataset.json"
    csv_path = tmp_path / "dataset.csv"

    data = dataset.to_json(json_path)
    dataset.to_csv(csv_path)

    assert data["metadata"]["source"] == "test"
    assert json.loads(json_path.read_text(encoding="utf-8"))["data"][0]["geo"] == "MEX"
    assert csv_path.exists()
    assert csv_path.with_suffix(".csv.metadata.json").exists()


def test_dataset_exports_parquet_with_metadata(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("pyarrow")
    dataset = EconDataset(
        frame=pd.DataFrame({"geo": ["MEX"], "value": [1.0]}),
        metadata=EconMetadata(source="test"),
    )
    path = tmp_path / "dataset.parquet"

    dataset.to_parquet(path)

    assert path.exists()
    assert path.with_suffix(".parquet.metadata.json").exists()
