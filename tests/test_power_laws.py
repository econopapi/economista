"""Tests of the public economic adapter to powerlaw."""

import numpy as np
import pandas as pd
import pytest

from economista.analysis import PowerLawFit, fit_power_law, power_laws
from economista.core.dataset import EconDataset
from economista.core.errors import AnalysisError
from economista.core.metadata import EconMetadata


def test_continuous_fit_preserves_context_and_compares_models() -> None:
    observations = np.random.default_rng(17).pareto(2.0, 2_000) + 1.0
    metadata = EconMetadata(source="synthetic", dataset="pareto", unit="index")
    dataset = EconDataset(
        frame=pd.DataFrame({"value": observations}), metadata=metadata
    )

    result = fit_power_law(dataset, xmin=1.0)
    comparison = result.compare_to("lognormal")

    assert isinstance(result, PowerLawFit)
    assert 2.7 < result.alpha < 3.3
    assert result.xmin == 1.0
    assert result.n_total == result.n_tail == 2_000
    assert 0 <= result.ks_distance < 0.1
    assert result.metadata == metadata
    assert result.metadata is not metadata
    assert comparison.alternative == "lognormal"
    assert np.isfinite(comparison.log_likelihood_ratio)
    assert 0 <= comparison.p_value <= 1
    assert result.raw_fit.power_law.alpha == result.alpha


def test_discrete_dataframe_and_series_inputs() -> None:
    values = np.arange(10, 110)
    result = fit_power_law(
        pd.DataFrame({"population": values}),
        column="population",
        discrete=True,
        xmin=10,
    )
    series_result = fit_power_law(
        pd.Series(values, name="population"), discrete=True, xmin=10
    )

    assert result.discrete is True
    assert result.column == "population"
    assert result.n_tail == len(values)
    assert series_result.column == "population"


@pytest.mark.parametrize(
    ("data", "kwargs"),
    [
        ([1.0, 0.0, 3.0], {}),
        ([1.0, np.nan, 3.0], {}),
        ([[1.0, 2.0], [3.0, 4.0]], {}),
        ([1.0], {}),
        ([1.0, 2.5, 3.0], {"discrete": True}),
        ([1.0, 2.0, 3.0], {"xmin": 4}),
        (pd.DataFrame({"income": [1.0, 2.0]}), {}),
    ],
)
def test_invalid_inputs_raise_analysis_error(
    data: object, kwargs: dict[str, object]
) -> None:
    with pytest.raises(AnalysisError):
        fit_power_law(data, **kwargs)  # type: ignore[arg-type]


def test_invalid_comparison_raises_analysis_error() -> None:
    result = fit_power_law([1.1, 2.2, 3.3, 4.4], xmin=1)
    with pytest.raises(AnalysisError):
        result.compare_to("power_law")


def test_missing_analysis_extra_has_install_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_module(name: str) -> None:
        raise ImportError(name)

    monkeypatch.setattr(power_laws, "import_module", missing_module)
    with pytest.raises(AnalysisError, match="economista\\[analysis\\]"):
        fit_power_law([1.0, 2.0, 3.0])
