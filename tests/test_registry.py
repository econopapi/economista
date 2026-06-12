import pytest

from economista.core.errors import SourceUnavailableError
from economista.data.registry import ConnectorRegistry
from economista.data.sources.world_bank import WorldBankConnector


def test_registry_resolves_registered_connector() -> None:
    registry = ConnectorRegistry()
    registry.register("world_bank", WorldBankConnector)

    connector = registry.get("world_bank", cache=False)

    assert isinstance(connector, WorldBankConnector)
    assert registry.available_sources() == ("world_bank",)


def test_registry_rejects_unknown_source() -> None:
    registry = ConnectorRegistry()

    with pytest.raises(SourceUnavailableError):
        registry.get("fred")
