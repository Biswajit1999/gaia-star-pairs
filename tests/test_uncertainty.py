from __future__ import annotations

import numpy as np
import pytest

from gaia_wide_binary_consistency_audit.exceptions import ConvergenceError, InsufficientDataError
from gaia_wide_binary_consistency_audit.uncertainty import (
    bootstrap_statistic,
    check_fit_convergence,
)


def test_bootstrap_statistic_is_deterministic():
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    r1 = bootstrap_statistic(values, np.mean, n_resamples=200, seed=20260713)
    r2 = bootstrap_statistic(values, np.mean, n_resamples=200, seed=20260713)
    assert r1.ci_low == r2.ci_low
    assert r1.ci_high == r2.ci_high
    assert r1.estimate == pytest.approx(np.mean(values))


def test_bootstrap_statistic_ci_brackets_estimate():
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    result = bootstrap_statistic(values, np.median, n_resamples=1000, seed=20260713)
    assert result.ci_low <= result.estimate <= result.ci_high
    assert result.n_resamples == 1000


def test_bootstrap_statistic_rejects_too_small_input():
    with pytest.raises(InsufficientDataError):
        bootstrap_statistic(np.array([1.0]), np.mean)


def test_check_fit_convergence_well_conditioned():
    cov = np.eye(2)
    diag = check_fit_convergence(cov, chi_square=3.0, dof=3)
    assert diag.converged
    assert diag.reduced_chi_square == pytest.approx(1.0)


def test_check_fit_convergence_ill_conditioned_flagged():
    cov = np.array([[1.0, 0.999999999], [0.999999999, 1.0]])
    diag = check_fit_convergence(cov, chi_square=3.0, dof=3, max_condition_number=1e4)
    assert not diag.converged
    assert "ill-conditioned" in diag.reason


def test_check_fit_convergence_bad_reduced_chi2_flagged():
    cov = np.eye(2)
    diag = check_fit_convergence(cov, chi_square=500.0, dof=3)
    assert not diag.converged
    assert "reduced chi-square" in diag.reason


def test_check_fit_convergence_rejects_nonsquare():
    with pytest.raises(ConvergenceError):
        check_fit_convergence(np.zeros((2, 3)), chi_square=1.0, dof=1)


def test_check_fit_convergence_rejects_zero_dof():
    with pytest.raises(ConvergenceError):
        check_fit_convergence(np.eye(2), chi_square=1.0, dof=0)
