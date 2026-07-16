from __future__ import annotations

import pytest

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError
from gaia_wide_binary_consistency_audit.residuals import bin_scale, bin_scales_by_group, rms
from gaia_wide_binary_consistency_audit.statistics import pair_chi2_consistency


def test_rms_basic():
    assert rms([3.0, 4.0]) == pytest.approx((25 / 2) ** 0.5)


def test_rms_empty_raises():
    with pytest.raises(InsufficientDataError):
        rms([])


def test_bin_scale_near_one_for_well_calibrated():
    results = [
        pair_chi2_consistency(f"P{i}", 10.0, 0.1, 10.0 + d, 0.1, 1, 0.1, 1, 0.1, 1, 0.1, 1, 0.1)
        for i, d in enumerate([0.05, -0.05, 0.1, -0.1, 0.0, 0.08])
    ]
    scale = bin_scale("test_bin", results)
    assert scale.n_pairs == 6
    assert scale.rms_z_combined > 0


def test_bin_scale_empty_raises():
    with pytest.raises(InsufficientDataError):
        bin_scale("empty", [])


def test_bin_scales_by_group_skips_unmatched_ids():
    result = pair_chi2_consistency("P1", 10.0, 0.1, 10.0, 0.1, 1, 0.1, 1, 0.1, 1, 0.1, 1, 0.1)
    groups = {"bin_a": ["P1"], "bin_b": ["missing_id"]}
    scales = bin_scales_by_group(groups, {"P1": result})
    labels = [s.bin_label for s in scales]
    assert "bin_a" in labels
    assert "bin_b" not in labels
