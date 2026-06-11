import economista


def test_public_package_metadata_exists() -> None:
    assert economista.__version__
    assert isinstance(economista.__author__, str)
    assert isinstance(economista.__authors__, list)
    assert isinstance(economista.__maintainer__, str)
    assert isinstance(economista.__maintainers__, list)
    assert isinstance(economista.__summary__, str)
    assert isinstance(economista.__python_requires__, str)
