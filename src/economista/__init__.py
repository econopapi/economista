"""economista.

La biblioteca definitiva para datos, análisis e investigación económica
aplicada en Python.
"""

from __future__ import annotations

from importlib.metadata import PackageMetadata, PackageNotFoundError, metadata, version

from economista.core.dataset import EconDataset
from economista.core.metadata import EconMetadata
from economista.core.query import DataQuery
from economista.core.schema import EconSchema

_DISTRIBUTION_NAME = "economista"


def _load_package_metadata() -> PackageMetadata | None:
    """Load installed package metadata when available."""
    try:
        return metadata(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return None


def _metadata_value(package_metadata: PackageMetadata | None, key: str) -> str:
    """Return a package metadata value when available."""
    if package_metadata is None:
        return ""

    try:
        return package_metadata[key]
    except KeyError:
        return ""


_package_metadata = _load_package_metadata()

try:
    __version__ = version(_DISTRIBUTION_NAME)
except PackageNotFoundError:
    __version__ = "0.0.0"

if _package_metadata is None:
    __authors__: list[str] = []
    __maintainers__: list[str] = []
else:
    __authors__ = _package_metadata.get_all("Author-email") or []
    __maintainers__ = _package_metadata.get_all("Maintainer-email") or []

__author__ = ", ".join(__authors__)
__maintainer__ = ", ".join(__maintainers__)
__summary__ = _metadata_value(_package_metadata, "Summary")
__python_requires__ = _metadata_value(_package_metadata, "Requires-Python")

__all__ = [
    "__version__",
    "__author__",
    "__authors__",
    "__maintainer__",
    "__maintainers__",
    "__summary__",
    "__python_requires__",
    "EconDataset",
    "EconMetadata",
    "DataQuery",
    "EconSchema",
]