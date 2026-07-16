from __future__ import annotations

import numpy as np
import pytest

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError
from gaia_wide_binary_consistency_audit.statistics import (
    combined_uncertainty,
    fraction_inconsistent,
    pair_chi2_consistency,
)


def test_combined_uncertainty_pythagorean():
    assert combined_uncertainty(3.0, 4.0) == pytest.approx(5.0)


def test_combined_uncertainty_rejects_negative():
    with pytest.raises(ValueError):
        combined_uncertainty(-1.0, 1.0)


def test_identical_components_are_consistent():
    result = pair_chi2_consistency(
        "P1", 10.0, 0.1, 10.0, 0.1, 5.0, 0.1, 5.0, 0.1, -3.0, 0.1, -3.0, 0.1
    )
    assert result.chi2 == pytest.approx(0.0, abs=1e-9)
    assert result.is_consistent
    assert result.p_value == pytest.approx(1.0, abs=1e-6)


def test_large_discrepancy_is_inconsistent():
    result = pair_chi2_consistency(
        "P2", 10.0, 0.05, 15.0, 0.05, 5.0, 0.05, 5.0, 0.05, -3.0, 0.05, -3.0, 0.05
    )
    assert not result.is_consistent
    assert result.chi2 > 10.0


def test_nonfinite_input_raises():
    with pytest.raises(InsufficientDataError):
        pair_chi2_consistency("P3", np.nan, 0.1, 1.0, 0.1, 1, 0.1, 1, 0.1, 1, 0.1, 1, 0.1)


def test_nonpositive_uncertainty_raises():
    with pytest.raises(InsufficientDataError):
        pair_chi2_consistency("P4", 1.0, 0.0, 1.0, 0.1, 1, 0.1, 1, 0.1, 1, 0.1, 1, 0.1)


def test_fraction_inconsistent_empty_raises():
    with pytest.raises(InsufficientDataError):
        fraction_inconsistent([])


def test_fraction_inconsistent_counts_correctly():
    good = pair_chi2_consistency("A", 1, 0.1, 1, 0.1, 1, 0.1, 1, 0.1, 1, 0.1, 1, 0.1)
    bad = pair_chi2_consistency("B", 1, 0.01, 5, 0.01, 1, 0.01, 1, 0.01, 1, 0.01, 1, 0.01)
    assert fraction_inconsistent([good, good, bad]) == pytest.approx(1 / 3)
