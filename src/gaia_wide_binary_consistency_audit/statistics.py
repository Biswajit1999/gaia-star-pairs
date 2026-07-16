"""Astrometric consistency statistics for Gaia wide-binary components.

Core science question: are the two components' quoted parallaxes and proper
motions consistent with each other given their quoted Gaia uncertainties?
For a genuinely bound (or at least co-moving, common-distance) pair the true
difference in parallax and in each proper-motion component is expected to be
small relative to the *combined* quoted uncertainty; the standard test is a
chi-square statistic on the standardized differences (docs/RESEARCH_BLUEPRINT.md,
docs/VALIDATION_CONTRACT.md).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError

# Degrees of freedom for the combined (parallax, pmra, pmdec) consistency test.
DOF_FULL = 3


@dataclass(frozen=True)
class PairConsistency:
    """Per-pair consistency statistic for one wide-binary candidate."""

    pair_id: str
    delta_parallax_mas: float
    delta_pmra_masyr: float
    delta_pmdec_masyr: float
    sigma_delta_parallax_mas: float
    sigma_delta_pmra_masyr: float
    sigma_delta_pmdec_masyr: float
    z_parallax: float
    z_pmra: float
    z_pmdec: float
    chi2: float
    dof: int
    p_value: float
    is_consistent: bool


def combined_uncertainty(sigma_a: float, sigma_b: float) -> float:
    """Combined 1-sigma uncertainty on a difference of two independent
    quantities, sigma = sqrt(sigma_a^2 + sigma_b^2).
    """
    if sigma_a < 0 or sigma_b < 0:
        raise ValueError("uncertainties must be non-negative")
    return float(np.sqrt(sigma_a**2 + sigma_b**2))


def pair_chi2_consistency(
    pair_id: str,
    parallax_a: float, parallax_a_err: float,
    parallax_b: float, parallax_b_err: float,
    pmra_a: float, pmra_a_err: float,
    pmra_b: float, pmra_b_err: float,
    pmdec_a: float, pmdec_a_err: float,
    pmdec_b: float, pmdec_b_err: float,
    alpha: float = 0.05,
) -> PairConsistency:
    """Chi-square test of parallax/pmra/pmdec consistency between the two
    components of a candidate wide binary, using only the quoted Gaia
    per-source uncertainties (no correlation term, since public Gaia
    catalogue rows do not expose the astrometric covariance matrix at the
    single-source level used here).

    Raises InsufficientDataError if any input is non-finite or any quoted
    uncertainty is non-positive (a zero/NaN uncertainty makes the
    standardized residual undefined, not merely "consistent").
    """
    values = [
        parallax_a, parallax_a_err, parallax_b, parallax_b_err,
        pmra_a, pmra_a_err, pmra_b, pmra_b_err,
        pmdec_a, pmdec_a_err, pmdec_b, pmdec_b_err,
    ]
    if not all(np.isfinite(v) for v in values):
        raise InsufficientDataError(f"pair {pair_id}: non-finite astrometric input")
    for err in (parallax_a_err, parallax_b_err, pmra_a_err, pmra_b_err, pmdec_a_err, pmdec_b_err):
        if err <= 0:
            raise InsufficientDataError(f"pair {pair_id}: non-positive quoted uncertainty {err}")

    d_plx = parallax_a - parallax_b
    d_pmra = pmra_a - pmra_b
    d_pmdec = pmdec_a - pmdec_b
    s_plx = combined_uncertainty(parallax_a_err, parallax_b_err)
    s_pmra = combined_uncertainty(pmra_a_err, pmra_b_err)
    s_pmdec = combined_uncertainty(pmdec_a_err, pmdec_b_err)

    z_plx = d_plx / s_plx
    z_pmra = d_pmra / s_pmra
    z_pmdec = d_pmdec / s_pmdec

    chi2 = float(z_plx**2 + z_pmra**2 + z_pmdec**2)
    p_value = float(stats.chi2.sf(chi2, DOF_FULL))

    return PairConsistency(
        pair_id=pair_id,
        delta_parallax_mas=float(d_plx),
        delta_pmra_masyr=float(d_pmra),
        delta_pmdec_masyr=float(d_pmdec),
        sigma_delta_parallax_mas=s_plx,
        sigma_delta_pmra_masyr=s_pmra,
        sigma_delta_pmdec_masyr=s_pmdec,
        z_parallax=float(z_plx),
        z_pmra=float(z_pmra),
        z_pmdec=float(z_pmdec),
        chi2=chi2,
        dof=DOF_FULL,
        p_value=p_value,
        is_consistent=bool(p_value >= alpha),
    )


def fraction_inconsistent(results: list[PairConsistency]) -> float:
    """Fraction of pairs flagged inconsistent at the configured alpha."""
    if not results:
        raise InsufficientDataError("no pair-consistency results to summarize")
    n_bad = sum(1 for r in results if not r.is_consistent)
    return float(n_bad / len(results))
