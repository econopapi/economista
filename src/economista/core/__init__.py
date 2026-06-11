"""Core abstractions for economista."""

from economista.core.dataset import EconDataset
from economista.core.metadata import EconMetadata
from economista.core.query import DataQuery
from economista.core.schema import EconSchema

__all__ = [
    "EconDataset",
    "EconMetadata",
    "DataQuery",
    "EconSchema",
]
