from economista.core.query import DataQuery


def test_query_cache_key_is_stable_for_equal_queries() -> None:
    first = DataQuery(
        source="world_bank",
        dataset="wdi",
        indicator="NY.GDP.MKTP.CD",
        geo=["MEX", "COL"],
        params={"b": 2, "a": 1},
    )
    second = DataQuery(
        source="world_bank",
        dataset="wdi",
        indicator="NY.GDP.MKTP.CD",
        geo=["MEX", "COL"],
        params={"a": 1, "b": 2},
    )

    assert first.to_dict()["source"] == "world_bank"
    assert first.cache_key() == second.cache_key()
