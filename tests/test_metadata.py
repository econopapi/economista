from datetime import datetime

from economista.core.metadata import EconMetadata


def test_metadata_serializes_datetime() -> None:
    metadata = EconMetadata(
        source="world_bank",
        downloaded_at=datetime(2026, 6, 11, 13, 0, 0),
    )

    data = metadata.to_dict()

    assert data["source"] == "world_bank"
    assert data["downloaded_at"] == "2026-06-11T13:00:00"
