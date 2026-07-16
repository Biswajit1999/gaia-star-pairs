from __future__ import annotations

import pytest

from gaia_wide_binary_consistency_audit.synthetic import DEFAULT_SEED, generate_demo_dataset, generate_synthetic_pairs


@pytest.fixture
def demo_pair_records():
    """Deterministic synthetic dataset shared across test modules."""
    return generate_demo_dataset(seed=DEFAULT_SEED)


@pytest.fixture
def consistent_pairs():
    """Synthetic pairs with well-calibrated (scale_factor=1.0) noise --
    should NOT be systematically flagged inconsistent (null-control fixture).
    """
    return [p.record for p in generate_synthetic_pairs(60, seed=DEFAULT_SEED, scale_factor=1.0)]


@pytest.fixture
def inconsistent_pairs():
    """Synthetic pairs with strongly inflated (scale_factor=6.0) noise --
    should be predominantly flagged inconsistent.
    """
    return [p.record for p in generate_synthetic_pairs(60, seed=DEFAULT_SEED, scale_factor=6.0)]
