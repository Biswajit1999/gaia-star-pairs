from __future__ import annotations

import pytest

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError
from gaia_wide_binary_consistency_audit.synthetic import generate_demo_dataset, generate_synthetic_pairs


def test_generate_synthetic_pairs_deterministic():
    p1 = generate_synthetic_pairs(10, seed=42)
    p2 = generate_synthetic_pairs(10, seed=42)
    assert [p.record.parallax_a for p in p1] == [p.record.parallax_a for p in p2]


def test_generate_synthetic_pairs_rejects_zero():
    with pytest.raises(InsufficientDataError):
        generate_synthetic_pairs(0)


def test_generate_synthetic_pairs_rejects_bad_scale():
    with pytest.raises(ValueError):
        generate_synthetic_pairs(5, scale_factor=0.0)


def test_generate_demo_dataset_has_both_populations():
    records = generate_demo_dataset()
    assert len(records) == 30
    prefixes = {r.pair_id[:5] for r in records}
    assert "DEMOC" in prefixes
    assert "DEMOI" in prefixes


def test_synthetic_pairs_have_positive_errors():
    pairs = generate_synthetic_pairs(15, seed=1)
    for p in pairs:
        r = p.record
        assert r.parallax_a_error > 0
        assert r.pmra_a_error > 0
        assert r.pmdec_b_error > 0
