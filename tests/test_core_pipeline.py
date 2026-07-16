from __future__ import annotations

import numpy as np
import pytest

from gaia_wide_binary_consistency_audit.core import run_pipeline
from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError
from gaia_wide_binary_consistency_audit.synthetic import generate_synthetic_pairs


def test_run_pipeline_rejects_empty_input():
    with pytest.raises(InsufficientDataError):
        run_pipeline([])


def test_run_pipeline_processes_demo_dataset(demo_pair_records):
    result = run_pipeline(demo_pair_records)
    assert result.n_input == 30
    assert result.n_processed == 30
    assert 0.0 <= result.fraction_inconsistent <= 1.0
    assert result.magnitude_bin_scales
    assert result.separation_bin_scales
    assert result.quality_bin_scales


def test_null_control_well_calibrated_pairs_mostly_consistent(consistent_pairs):
    """Null control: synthetic pairs generated with scale_factor=1.0 (quoted
    uncertainties exactly correct) should NOT be flagged predominantly
    inconsistent. At alpha=0.05 we expect roughly ~5% false positives, so
    the fraction flagged inconsistent should be well below 50%.
    """
    result = run_pipeline(consistent_pairs)
    assert result.fraction_inconsistent < 0.25


def test_injection_recovery_inflated_noise_flagged_inconsistent(inconsistent_pairs):
    """Injection-recovery gate: synthetic pairs generated with strongly
    inflated true noise (scale_factor=6.0) relative to the quoted
    uncertainty should be predominantly flagged inconsistent.
    """
    result = run_pipeline(inconsistent_pairs)
    assert result.fraction_inconsistent > 0.5


def test_injection_recovery_scale_monotonic():
    """The empirical RMS z-score scale recovered by the pipeline should
    increase monotonically (broadly) with the injected true scale factor --
    this is the core scale-recovery validation check.
    """
    scales = [0.5, 1.0, 2.0, 4.0]
    recovered = []
    for s in scales:
        pairs = [p.record for p in generate_synthetic_pairs(50, seed=20260713, scale_factor=s)]
        result = run_pipeline(pairs)
        z_all = np.concatenate(
            [
                [r.z_parallax for r in result.consistency_results],
                [r.z_pmra for r in result.consistency_results],
                [r.z_pmdec for r in result.consistency_results],
            ]
        )
        recovered.append(float(np.sqrt(np.mean(z_all**2))))
    assert recovered[0] < recovered[-1]
    assert all(np.isfinite(recovered))


def test_run_pipeline_one_bad_pair_does_not_abort(demo_pair_records):
    """A single malformed record (non-positive uncertainty) must be excluded
    with a warning, not abort the whole run.
    """
    import dataclasses

    bad_record = dataclasses.replace(demo_pair_records[0], parallax_a_error=0.0)
    records = [bad_record] + demo_pair_records[1:]
    result = run_pipeline(records)
    assert result.n_input == len(records)
    assert result.n_processed == len(records) - 1
    assert any("excluded" in w for w in result.warnings)


def test_run_pipeline_underpopulated_bin_warns():
    pairs = [p.record for p in generate_synthetic_pairs(3, seed=7, scale_factor=1.0)]
    result = run_pipeline(pairs)
    assert any("underpowered" in w for w in result.warnings)
