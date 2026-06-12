"""Core abstractions for economista."""

from economista.core.dataset import EconDataset
from economista.core.metadata import EconMetadata
from economista.core.query import DataQuery
from economista.core.schema import CANONICAL_ECON_SCHEMA, EconSchema

__all__ = [
    "CANONICAL_ECON_SCHEMA",
    "EconDataset",
    "EconMetadata",
    "DataQuery",
    "EconSchema",
]
