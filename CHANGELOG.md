# Changelog

## 0.3.0 - 2026-07-12

### Added

- Expanded `economista.data.search` into a tabular catalog exploration API.
- Added World Bank/WDI catalog search for indicators, geographies, ISO codes,
  regions, income levels, lending types, and topics.
- Added `available_geos`, `available_indicators`, and `available_topics` helper
  methods to the connector contract.
- Added `examples/data_search_exploration.ipynb` as a notebook guide for the new
  search workflow.
- Added fixture-based coverage for World Bank geographies and topics.

### Changed

- `data.search` now returns a `pandas.DataFrame` by default for notebook-friendly
  exploration.
- `data.search(as_frame=False)` returns plain `list[dict[str, Any]]` rows.
- `data.search` now supports `kind="all"`, `kind="indicators"`, `kind="geos"`,
  `kind="topics"`, `source=None`, `limit=None`, and source-specific filters.
- World Bank `fetch` metadata now reports observed `time_coverage` when possible.
- CI now runs mypy once with a stable Python 3.12 target while keeping runtime
  tests across the supported Python matrix.

### Notes

- Search is lexical catalog exploration. It does not implement semantic search,
  embeddings, NLP, or full indicator-country coverage checks.
