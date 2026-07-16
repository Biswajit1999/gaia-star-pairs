"""Bootstrap resampling and fit-convergence diagnostics.

Two intentionally separate concerns, per project convention:
`bootstrap_statistic` (non-parametric uncertainty on a summary statistic via
resampling) and `check_fit_convergence` (diagnosing whether a least-squares
fit is numerically trustworthy). Never conflate the two.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gaia_wide_binary_consistency_audit.exceptions import ConvergenceError, InsufficientDataError

DEFAULT_SEED = 20260713
DEFAULT_N_RESAMPLES = 1000


@dataclass(frozen=True)
class BootstrapResult:
    estimate: float
    ci_low: float
    ci_high: float
    n_resamples: int
    seed: int


def bootstrap_statistic(
    values: np.ndarray,
    statistic_fn,
    n_resamples: int = DEFAULT_N_RESAMPLES,
    seed: int = DEFAULT_SEED,
    ci: float = 0.68,
) -> BootstrapResult:
    """Non-parametric bootstrap uncertainty on ``statistic_fn(values)``.

    Resamples ``values`` with replacement ``n_resamples`` times (deterministic
    given ``seed``), evaluates ``statistic_fn`` on each resample, and returns
    a percentile confidence interval. Raises InsufficientDataError for empty
    or single-element input, where a bootstrap interval is not meaningful.
    """
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        raise InsufficientDataError(f"need at least 2 values to bootstrap, got {arr.size}")
    if n_resamples < 1:
        raise ValueError("n_resamples must be >= 1")

    rng = np.random.default_rng(seed)
    point_estimate = float(statistic_fn(arr))
    resample_stats = np.empty(n_resamples, dtype=float)
    n = arr.size
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        resample_stats[i] = statistic_fn(arr[idx])

    alpha = (1.0 - ci) / 2.0
    lo = float(np.quantile(resample_stats, alpha))
    hi = float(np.quantile(resample_stats, 1.0 - alpha))
    return BootstrapResult(
        estimate=point_estimate, ci_low=lo, ci_high=hi, n_resamples=n_resamples, seed=seed
    )


@dataclass(frozen=True)
class ConvergenceDiagnostics:
    condition_number: float
    reduced_chi_square: float
    converged: bool
    reason: str


def check_fit_convergence(
    covariance: np.ndarray,
    chi_square: float,
    dof: int,
    max_condition_number: float = 1e8,
    chi2_reduced_bounds: tuple[float, float] = (0.1, 10.0),
) -> ConvergenceDiagnostics:
    """Diagnose whether a least-squares fit converged to a trustworthy
    solution: the parameter covariance matrix must be well-conditioned (no
    near-degenerate parameter combinations) and the reduced chi-square must
    fall within a plausible range (neither wildly overfit nor wildly
    inconsistent with the assumed noise model).

    Raises ConvergenceError if ``dof`` <= 0 (chi-square/dof undefined) or the
    covariance matrix is not square.
    """
    cov = np.asarray(covariance, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ConvergenceError(f"covariance must be a square matrix, got shape {cov.shape}")
    if dof <= 0:
        raise ConvergenceError(f"degrees of freedom must be positive, got {dof}")

    try:
        condition_number = float(np.linalg.cond(cov))
    except np.linalg.LinAlgError as exc:
        raise ConvergenceError(f"covariance matrix condition number could not be computed: {exc}") from exc

    reduced_chi_square = float(chi_square / dof)

    reasons = []
    if not np.isfinite(condition_number) or condition_number > max_condition_number:
        reasons.append(f"ill-conditioned covariance (cond={condition_number:.3g})")
    lo, hi = chi2_reduced_bounds
    if not (lo <= reduced_chi_square <= hi):
        reasons.append(f"reduced chi-square {reduced_chi_square:.3g} outside [{lo}, {hi}]")

    converged = len(reasons) == 0
    reason = "converged" if converged else "; ".join(reasons)
    return ConvergenceDiagnostics(
        condition_number=condition_number,
        reduced_chi_square=reduced_chi_square,
        converged=converged,
        reason=reason,
    )
