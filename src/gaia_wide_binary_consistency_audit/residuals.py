"""Normalised-residual scale estimation and per-bin aggregation.

If quoted Gaia uncertainties were perfectly calibrated, the standardized
differences (z-scores) computed in `statistics.pair_chi2_consistency` would
have unit scatter (std ~ 1) within each bin. This module estimates that
empirical scale per bin, which is the basis for required figure #2
("normalised residuals") and #3 ("scale vs magnitude") in
docs/FIGURE_AND_UI_SPEC.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError
from gaia_wide_binary_consistency_audit.statistics import PairConsistency


@dataclass(frozen=True)
class BinScale:
    bin_label: str
    n_pairs: int
    rms_z_parallax: float
    rms_z_pmra: float
    rms_z_pmdec: float
    rms_z_combined: float


def normalized_residual_vector(result: PairConsistency) -> np.ndarray:
    """The three standardized (z-score) residuals for one pair, stacked."""
    return np.array([result.z_parallax, result.z_pmra, result.z_pmdec], dtype=float)


def rms(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise InsufficientDataError("cannot compute RMS of an empty array")
    return float(np.sqrt(np.mean(arr**2)))


def bin_scale(bin_label: str, results: list[PairConsistency]) -> BinScale:
    """Empirical residual scale for one bin. If quoted uncertainties are
    well-calibrated the RMS z-scores should all be close to 1; values well
    above 1 indicate underestimated uncertainties (or genuine astrophysical
    inconsistency e.g. an unresolved third body), values well below 1
    indicate overestimated uncertainties.
    """
    if not results:
        raise InsufficientDataError(f"bin '{bin_label}' has no pairs to compute a scale from")
    z_plx = np.array([r.z_parallax for r in results])
    z_pmra = np.array([r.z_pmra for r in results])
    z_pmdec = np.array([r.z_pmdec for r in results])
    z_all = np.concatenate([z_plx, z_pmra, z_pmdec])
    return BinScale(
        bin_label=bin_label,
        n_pairs=len(results),
        rms_z_parallax=rms(z_plx),
        rms_z_pmra=rms(z_pmra),
        rms_z_pmdec=rms(z_pmdec),
        rms_z_combined=rms(z_all),
    )


def bin_scales_by_group(
    groups: dict[str, list[str]], results_by_id: dict[str, PairConsistency]
) -> list[BinScale]:
    """Compute a BinScale for every group; groups whose pair_ids do not
    resolve in results_by_id are skipped with the missing count surfaced via
    the caller-visible return value (empty groups never silently vanish --
    callers should log the difference between len(groups) and len(returned)).
    """
    scales = []
    for label, pair_ids in groups.items():
        matched = [results_by_id[pid] for pid in pair_ids if pid in results_by_id]
        if not matched:
            continue
        scales.append(bin_scale(label, matched))
    return scales
