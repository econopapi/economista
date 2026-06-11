"""Public data API."""

from __future__ import annotations

from typing import Any

from economista.core.dataset import EconDataset
from economista.core.errors import SourceUnavailableError


def fetch(*args: Any, **kwargs: Any) -> EconDataset:
    """Fetch economic data from a configured source.

    This function is part of the public API, but connectors are not implemented yet.
    """
    raise SourceUnavailableError(
        "No data connectors are available yet. "
        "The first planned connector is World Bank/WDI."
    )


def search(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    """Search economic indicators in a configured source."""
    raise SourceUnavailableError(
        "Search is not available yet. "
        "The first planned implementation is World Bank/WDI search."
    )
