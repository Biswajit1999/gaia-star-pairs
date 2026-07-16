"""Pipeline orchestration for the Gaia wide-binary astrometric consistency audit.

`run_pipeline` wires io -> quality (binning) -> statistics (chi2 consistency)
-> residuals (per-bin scale) for a list of pair records, never aborting the
whole run for one bad pair (per-pair failures are caught and converted to
warning strings, per CLAUDE_TASK.md / docs/ERROR_HANDLING.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from gaia_wide_binary_consistency_audit.exceptions import (
    ConvergenceError,
    DataSchemaError,
    InsufficientDataError,
)
from gaia_wide_binary_consistency_audit.io import PairRecord
from gaia_wide_binary_consistency_audit.quality import assign_pair_bins
from gaia_wide_binary_consistency_audit.residuals import BinScale, bin_scales_by_group
from gaia_wide_binary_consistency_audit.statistics import PairConsistency, fraction_inconsistent, pair_chi2_consistency


@dataclass(frozen=True)
class PipelineResult:
    consistency_results: list[PairConsistency]
    magnitude_bin_scales: list[BinScale]
    separation_bin_scales: list[BinScale]
    quality_bin_scales: list[BinScale]
    fraction_inconsistent: float
    n_input: int
    n_processed: int
    warnings: list[str] = field(default_factory=list)


def run_pipeline(records: list[PairRecord], alpha: float = 0.05) -> PipelineResult:
    """Process every pair record into a consistency result and per-bin
    scales. Raises InsufficientDataError immediately for empty input;
    otherwise a single malformed/degenerate pair produces a warning string
    rather than aborting the whole run.
    """
    if not records:
        raise InsufficientDataError("run_pipeline received zero pair records")

    warnings: list[str] = []
    consistency_results: list[PairConsistency] = []
    bin_assignments = []

    for record in records:
        try:
            result = pair_chi2_consistency(
                pair_id=record.pair_id,
                parallax_a=record.parallax_a, parallax_a_err=record.parallax_a_error,
                parallax_b=record.parallax_b, parallax_b_err=record.parallax_b_error,
                pmra_a=record.pmra_a, pmra_a_err=record.pmra_a_error,
                pmra_b=record.pmra_b, pmra_b_err=record.pmra_b_error,
                pmdec_a=record.pmdec_a, pmdec_a_err=record.pmdec_a_error,
                pmdec_b=record.pmdec_b, pmdec_b_err=record.pmdec_b_error,
                alpha=alpha,
            )
            bins = assign_pair_bins(
                pair_id=record.pair_id,
                mean_g_mag=record.mean_g_mag,
                separation_arcsec=record.separation_arcsec,
                ruwe_a=record.ruwe_a,
                ruwe_b=record.ruwe_b,
            )
        except (InsufficientDataError, ConvergenceError, DataSchemaError) as exc:
            warnings.append(f"pair {record.pair_id}: excluded ({type(exc).__name__}: {exc})")
            continue
        consistency_results.append(result)
        bin_assignments.append(bins)

    if not consistency_results:
        raise InsufficientDataError(
            f"all {len(records)} input pairs were excluded; see warnings for reasons"
        )

    results_by_id = {r.pair_id: r for r in consistency_results}
    mag_groups: dict[str, list[str]] = {}
    sep_groups: dict[str, list[str]] = {}
    qual_groups: dict[str, list[str]] = {}
    for b in bin_assignments:
        mag_groups.setdefault(b.magnitude_bin, []).append(b.pair_id)
        sep_groups.setdefault(b.separation_bin, []).append(b.pair_id)
        qual_groups.setdefault(b.quality_flag, []).append(b.pair_id)

    magnitude_bin_scales = bin_scales_by_group(mag_groups, results_by_id)
    separation_bin_scales = bin_scales_by_group(sep_groups, results_by_id)
    quality_bin_scales = bin_scales_by_group(qual_groups, results_by_id)

    for label, ids in {**mag_groups, **sep_groups, **qual_groups}.items():
        if len(ids) < 3:
            warnings.append(f"bin '{label}' has only {len(ids)} pair(s); scale estimate is underpowered")

    return PipelineResult(
        consistency_results=consistency_results,
        magnitude_bin_scales=magnitude_bin_scales,
        separation_bin_scales=separation_bin_scales,
        quality_bin_scales=quality_bin_scales,
        fraction_inconsistent=fraction_inconsistent(consistency_results),
        n_input=len(records),
        n_processed=len(consistency_results),
        warnings=warnings,
    )


@dataclass(frozen=True)
class Summary:
    count: int
    median: float
    mad: float


def validate_numeric(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("values must be one-dimensional")
    if arr.size == 0:
        raise ValueError("values must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError("values contain non-finite entries")
    return arr


def robust_summary(values: np.ndarray) -> Summary:
    arr = validate_numeric(values)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return Summary(count=int(arr.size), median=median, mad=mad)


def demo_series(seed: int = 20260713, size: int = 128) -> np.ndarray:
    """Return deterministic synthetic data labelled only for smoke testing."""
    if size < 8:
        raise ValueError("size must be at least 8")
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.0, size=size)
