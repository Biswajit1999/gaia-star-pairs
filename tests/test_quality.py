from __future__ import annotations

import pytest

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError
from gaia_wide_binary_consistency_audit.quality import (
    assign_pair_bins,
    group_by,
    magnitude_bin,
    quality_flag,
    separation_bin,
)


def test_magnitude_bin_boundaries():
    assert magnitude_bin(10.0) == "G<=12"
    assert magnitude_bin(13.0) == "12<G<=15"
    assert magnitude_bin(16.0) == "15<G<=18"
    assert magnitude_bin(20.0) == "G>18"


def test_magnitude_bin_rejects_nonfinite():
    with pytest.raises(InsufficientDataError):
        magnitude_bin(float("nan"))


def test_separation_bin_boundaries():
    assert separation_bin(2.0) == "<5as"
    assert separation_bin(10.0) == "5-20as"
    assert separation_bin(30.0) == "20-60as"
    assert separation_bin(100.0) == ">60as"


def test_quality_flag_good_and_flagged():
    assert quality_flag(1.0, 1.1) == "good"
    assert quality_flag(1.0, 2.0) == "flagged"


def test_assign_pair_bins():
    b = assign_pair_bins("P1", mean_g_mag=13.5, separation_arcsec=8.0, ruwe_a=1.0, ruwe_b=1.1)
    assert b.pair_id == "P1"
    assert b.magnitude_bin == "12<G<=15"
    assert b.separation_bin == "5-20as"
    assert b.quality_flag == "good"


def test_group_by_groups_correctly():
    bins = [
        assign_pair_bins("A", 10.0, 2.0, 1.0, 1.0),
        assign_pair_bins("B", 10.0, 2.0, 1.0, 1.0),
        assign_pair_bins("C", 20.0, 2.0, 1.0, 1.0),
    ]
    groups = group_by(bins, "magnitude_bin")
    assert groups["G<=12"] == ["A", "B"]
    assert groups["G>18"] == ["C"]


def test_group_by_empty_raises():
    with pytest.raises(InsufficientDataError):
        group_by([], "magnitude_bin")
