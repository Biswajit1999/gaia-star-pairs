"""Synthetic wide-binary pair astrometry generator.

Generates pairs with a KNOWN, injected true difference (zero, by
construction, for a genuinely co-moving pair) in parallax/pmra/pmdec, plus
Gaussian measurement noise scaled by the quoted per-component uncertainty
and an optional `scale_factor` that inflates/deflates the *true* noise
relative to the *quoted* uncertainty -- this lets tests and `--demo` runs
validate that `statistics.pair_chi2_consistency` recovers scale_factor~1
(well-calibrated), scale_factor>1 (underestimated errors), etc.

All synthetic data is clearly labelled and MUST NOT be presented as a real
scientific result (CLAUDE_TASK.md).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError
from gaia_wide_binary_consistency_audit.io import PairRecord

DEFAULT_SEED = 20260713

# Deterministic base astrometry so synthetic pairs land in realistic ranges.
_PARALLAX_RANGE_MAS = (2.0, 20.0)
_PARALLAX_ERR_RANGE_MAS = (0.02, 0.15)
_PM_RANGE_MASYR = (-50.0, 50.0)
_PM_ERR_RANGE_MASYR = (0.02, 0.20)
_G_MAG_RANGE = (9.0, 19.0)
_SEP_RANGE_ARCSEC = (1.0, 90.0)
_RUWE_RANGE = (0.9, 1.6)


@dataclass(frozen=True)
class SyntheticPair:
    record: PairRecord
    true_scale_factor: float  # ratio of injected noise sigma to quoted sigma; 1.0 = well-calibrated


def generate_synthetic_pairs(
    n_pairs: int, seed: int = DEFAULT_SEED, scale_factor: float = 1.0, label_prefix: str = "SYN"
) -> list[SyntheticPair]:
    """Generate ``n_pairs`` synthetic wide-binary candidates.

    For each pair the true parallax/pmra/pmdec difference between component
    A and B is exactly zero by construction (a perfectly co-moving pair);
    the *measured* difference is drawn from a Gaussian with sigma equal to
    ``scale_factor`` times the quoted combined uncertainty. scale_factor=1.0
    means quoted uncertainties are perfectly calibrated (recovered RMS
    z-score should be ~1); scale_factor>1 injects underestimated
    uncertainties (RMS z-score should recover > 1).
    """
    if n_pairs < 1:
        raise InsufficientDataError("n_pairs must be >= 1 to generate synthetic pairs")
    if scale_factor <= 0:
        raise ValueError("scale_factor must be positive")

    rng = np.random.default_rng(seed)
    pairs: list[SyntheticPair] = []
    for i in range(n_pairs):
        parallax_true = float(rng.uniform(*_PARALLAX_RANGE_MAS))
        pmra_true = float(rng.uniform(*_PM_RANGE_MASYR))
        pmdec_true = float(rng.uniform(*_PM_RANGE_MASYR))

        plx_err_a = float(rng.uniform(*_PARALLAX_ERR_RANGE_MAS))
        plx_err_b = float(rng.uniform(*_PARALLAX_ERR_RANGE_MAS))
        pmra_err_a = float(rng.uniform(*_PM_ERR_RANGE_MASYR))
        pmra_err_b = float(rng.uniform(*_PM_ERR_RANGE_MASYR))
        pmdec_err_a = float(rng.uniform(*_PM_ERR_RANGE_MASYR))
        pmdec_err_b = float(rng.uniform(*_PM_ERR_RANGE_MASYR))

        combined_plx_sigma = float(np.sqrt(plx_err_a**2 + plx_err_b**2)) * scale_factor
        combined_pmra_sigma = float(np.sqrt(pmra_err_a**2 + pmra_err_b**2)) * scale_factor
        combined_pmdec_sigma = float(np.sqrt(pmdec_err_a**2 + pmdec_err_b**2)) * scale_factor

        d_plx = float(rng.normal(0.0, combined_plx_sigma))
        d_pmra = float(rng.normal(0.0, combined_pmra_sigma))
        d_pmdec = float(rng.normal(0.0, combined_pmdec_sigma))

        # Split the injected difference symmetrically between A and B so the
        # reported per-component values sum to the injected combined delta.
        parallax_a = parallax_true + d_plx / 2.0
        parallax_b = parallax_true - d_plx / 2.0
        pmra_a = pmra_true + d_pmra / 2.0
        pmra_b = pmra_true - d_pmra / 2.0
        pmdec_a = pmdec_true + d_pmdec / 2.0
        pmdec_b = pmdec_true - d_pmdec / 2.0

        record = PairRecord(
            pair_id=f"{label_prefix}{i:04d}",
            source_id_a=f"{label_prefix}{i:04d}A",
            source_id_b=f"{label_prefix}{i:04d}B",
            parallax_a=parallax_a, parallax_a_error=plx_err_a,
            parallax_b=parallax_b, parallax_b_error=plx_err_b,
            pmra_a=pmra_a, pmra_a_error=pmra_err_a,
            pmra_b=pmra_b, pmra_b_error=pmra_err_b,
            pmdec_a=pmdec_a, pmdec_a_error=pmdec_err_a,
            pmdec_b=pmdec_b, pmdec_b_error=pmdec_err_b,
            mean_g_mag=float(rng.uniform(*_G_MAG_RANGE)),
            separation_arcsec=float(rng.uniform(*_SEP_RANGE_ARCSEC)),
            ruwe_a=float(rng.uniform(*_RUWE_RANGE)),
            ruwe_b=float(rng.uniform(*_RUWE_RANGE)),
        )
        pairs.append(SyntheticPair(record=record, true_scale_factor=scale_factor))
    return pairs


def generate_demo_dataset(seed: int = DEFAULT_SEED) -> list[PairRecord]:
    """A single deterministic demo dataset mixing well-calibrated pairs with
    a smaller injected-inconsistent subset, used by `--demo` analysis/figure
    runs and by conftest.py fixtures. Clearly synthetic; never used as a
    stand-in for real results in reports.
    """
    consistent = generate_synthetic_pairs(24, seed=seed, scale_factor=1.0, label_prefix="DEMOC")
    inconsistent = generate_synthetic_pairs(6, seed=seed + 1, scale_factor=4.0, label_prefix="DEMOI")
    return [p.record for p in consistent] + [p.record for p in inconsistent]
