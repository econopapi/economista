"""Economic data adapter for the external ``powerlaw`` package."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from importlib import import_module
from typing import Any

import numpy as np
import pandas as pd

from economista.core.dataset import EconDataset
from economista.core.errors import AnalysisError
from economista.core.metadata import EconMetadata

PowerLawData = EconDataset | pd.DataFrame | pd.Series | Sequence[float] | np.ndarray


@dataclass(frozen=True)
class DistributionComparison:
    """Likelihood-ratio comparison against an alternative distribution.

    A positive ratio favors the power law; the p-value measures evidence for
    the sign of that ratio, not absolute goodness of fit.
    """

    alternative: str
    log_likelihood_ratio: float
    p_value: float


@dataclass(frozen=True)
class PowerLawFit:
    """Power-law fit plus economic provenance and a way into the full library."""

    alpha: float
    xmin: float
    ks_distance: float
    sigma: float
    n_total: int
    n_tail: int
    discrete: bool
    column: str | None
    metadata: EconMetadata | None
    raw_fit: Any

    def compare_to(self, alternative: str) -> DistributionComparison:
        """Compare the fitted power law with another ``powerlaw`` distribution."""
        if not alternative or alternative == "power_law":
            raise AnalysisError("Choose an alternative other than 'power_law'.")
        try:
            ratio, p_value = self.raw_fit.distribution_compare(
                "power_law", alternative
            )
        except Exception as exc:
            raise AnalysisError(
                f"Could not compare the power law with {alternative!r}: {exc}"
            ) from exc
        return DistributionComparison(
            alternative=alternative,
            log_likelihood_ratio=float(ratio),
            p_value=float(p_value),
        )


def _values_and_context(
    data: PowerLawData, column: str
) -> tuple[np.ndarray, str | None, EconMetadata | None]:
    metadata = None
    if isinstance(data, EconDataset):
        metadata = deepcopy(data.metadata)
        data = data.to_pandas()

    if isinstance(data, pd.DataFrame):
        if column not in data.columns:
            raise AnalysisError(f"Column {column!r} is absent from the data.")
        selected = data[column]
        if not isinstance(selected, pd.Series):
            raise AnalysisError(f"Column {column!r} must identify one numeric series.")
        array = selected.to_numpy()
        selected_column: str | None = column
    elif isinstance(data, pd.Series):
        if column != "value":
            raise AnalysisError("'column' applies only to DataFrame or EconDataset.")
        array = data.to_numpy()
        selected_column = data.name if isinstance(data.name, str) else None
    else:
        if column != "value":
            raise AnalysisError("'column' applies only to DataFrame or EconDataset.")
        try:
            array = np.asarray(data)
        except (TypeError, ValueError) as exc:
            raise AnalysisError(
                "Power-law data must be one-dimensional and numeric."
            ) from exc
        selected_column = None

    if array.ndim != 1:
        raise AnalysisError("Power-law data must be one-dimensional.")
    try:
        values = np.asarray(array, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise AnalysisError("Power-law data must contain numeric values.") from exc
    if values.size < 2:
        raise AnalysisError("At least two observations are required.")
    if not np.isfinite(values).all() or (values <= 0).any():
        raise AnalysisError("Power-law data must contain finite, positive values.")
    return values, selected_column, metadata


def fit_power_law(
    data: PowerLawData,
    *,
    column: str = "value",
    discrete: bool = False,
    xmin: float | None = None,
) -> PowerLawFit:
    """Fit a power-law tail to positive observations.

    ``powerlaw`` estimates ``xmin`` if omitted. This is an unweighted fit;
    survey expansion factors require a separate survey-aware analysis.
    """
    values, selected_column, metadata = _values_and_context(data, column)
    if discrete and not np.equal(values, np.floor(values)).all():
        raise AnalysisError("Discrete power-law data must contain integers.")
    if xmin is not None and (
        not np.isfinite(xmin) or xmin <= 0 or xmin > float(values.max())
    ):
        raise AnalysisError("xmin must be positive, finite, and within the data range.")
    if xmin is not None and np.count_nonzero(values >= xmin) < 2:
        raise AnalysisError("At least two observations must remain above xmin.")

    try:
        powerlaw = import_module("powerlaw")
    except ImportError as exc:
        raise AnalysisError(
            "Install the analysis extra with 'pip install economista[analysis]'."
        ) from exc
    try:
        raw_fit = powerlaw.Fit(
            values,
            discrete=discrete,
            xmin=xmin,
            parameter_ranges={"alpha": (1.0, None)},
            verbose=False,
        )
        law = raw_fit.power_law
        fit_xmin = float(raw_fit.xmin)
        n_tail = int(np.count_nonzero(values >= fit_xmin))
        if n_tail < 2 or not np.isfinite(float(law.alpha)):
            raise AnalysisError("The selected tail does not support a finite fit.")
        result = PowerLawFit(
            alpha=float(law.alpha),
            xmin=fit_xmin,
            ks_distance=float(law.D),
            sigma=float(law.standard_err),
            n_total=int(values.size),
            n_tail=n_tail,
            discrete=discrete,
            column=selected_column,
            metadata=metadata,
            raw_fit=raw_fit,
        )
    except AnalysisError:
        raise
    except Exception as exc:
        raise AnalysisError(f"Could not fit a power-law tail: {exc}") from exc
    return result
