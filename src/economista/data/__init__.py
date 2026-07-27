"""Unified data access interface."""

from economista.data.api import fetch, search
from economista.data.base import BaseConnector
from economista.data.registry import ConnectorRegistry
from economista.data.sources.imf import IMFDataMapperConnector
from economista.data.sources.world_bank import WorldBankConnector

__all__ = [
    "BaseConnector",
    "ConnectorRegistry",
    "IMFDataMapperConnector",
    "WorldBankConnector",
    "fetch",
    "search",
]
