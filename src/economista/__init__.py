"""economista.

La biblioteca definitiva para datos, análisis e investigación económica 
aplicada en Python."""

from economista._version import __version__
from economista.core.dataset import EconDataset
from economista.core.metadata import EconMetadata
from economista.core.query import DataQuery
from economista.core.schema import EconSchema

__all__ = [
    "__version__",
    "EconDataset",
    "EconMetadata",
    "DataQuery",
    "EconSchema",
]
