"""Configuration defaults for economista."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_cache_dir


@dataclass(frozen=True)
class CacheConfig:
    """Local cache configuration."""

    enabled: bool = True
    ttl_seconds: int = 60 * 60 * 24 * 7
    directory: Path = Path(user_cache_dir("economista"))


@dataclass(frozen=True)
class EconomistaConfig:
    """Package-level configuration."""

    cache: CacheConfig = CacheConfig()


DEFAULT_CONFIG = EconomistaConfig()
