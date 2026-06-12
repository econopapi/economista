"""Small JSON file cache used by data connectors."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from economista.core.config import CacheConfig
from economista.core.query import DataQuery


class JsonCache:
    """File-backed JSON cache keyed by data queries."""

    def __init__(self, config: CacheConfig) -> None:
        self.config = config

    def get(self, query: DataQuery) -> Any | None:
        """Return cached JSON-compatible data when present and fresh."""
        if not self.config.enabled:
            return None

        path = self._path_for(query)
        if not path.exists():
            return None

        cached_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        expires_at = cached_at + timedelta(seconds=self.config.ttl_seconds)
        if expires_at < datetime.now(timezone.utc):
            return None

        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, query: DataQuery, payload: Any) -> None:
        """Store JSON-compatible data for a query."""
        if not self.config.enabled:
            return

        path = self._path_for(query)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def _path_for(self, query: DataQuery) -> Path:
        source = query.source.replace("/", "_")
        return self.config.directory / source / f"{query.cache_key()}.json"
