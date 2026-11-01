"""Conditional projected wide-binary kinematics for the retained Gaia DR3 sample.

No radial velocities, orbit inclinations, astrometric covariances, or lens masses
are inferred. These are diagnostics, not binary-membership or gravity tests.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

KMS_PER_AU_PER_YEAR = 4.7404704635
CIRCULAR_SPEED_1AU_KMS = 29.7846918
FIELDS = (
    'pair_id', 'parallax_a', 'parallax_b', 'parallax_a_error', 'parallax_b_error',
    'pmra_a', 'pmra_b', 'pmra_a_error', 'pmra_b_error',
    'pmdec_a', 'pmdec_b', 'pmdec_a_error', 'pmdec_b_error', 'separation_arcsec',
)


def load_pairs(path: str | Path) -> list[dict[str, float | str]]:
    """Read the repository-retained pair CSV without querying any archive."""
    with Path(path).open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError('missing Gaia pair columns')
        rows = [{key: (row[key] if key == 'pair_id' else float(row[key]))
                 for key in FIELDS} for row in reader]
    if not rows:
        raise ValueError('no pair records')
    return rows


def _components(row: dict) -> tuple[float, float, float, float, float, float]:
    plx = (row['parallax_a'] + row['parallax_b']) / 2.0
    sigma_plx = np.hypot(row['parallax_a_error'], row['parallax_b_error']) / 2.0
    dra = row['pmra_a'] - row['pmra_b']
    ddec = row['pmdec_a'] - row['pmdec_b']
    sigma_ra = np.hypot(row['pmra_a_error'], row['pmra_b_error'])
    sigma_dec = np.hypot(row['pmdec_a_error'], row['pmdec_b_error'])
    values = (plx, sigma_plx, dra, ddec, sigma_ra, sigma_dec)
    if not all(np.isfinite(values)) or plx <= 0 or sigma_plx <= 0 or sigma_ra <= 0 or sigma_dec <= 0:
        raise ValueError('invalid astrometric measurement')
    if not np.isfinite(row['separation_arcsec']) or row['separation_arcsec'] <= 0:
        raise ValueError('invalid angular separation')
    return values


def projected_kinematics(row: dict, mass_msun: float = 1.2) -> dict[str, float]:
    """Projected separation, relative tangential speed and circular/escape scales.

    Assumes common distance 1000/parallax_mas pc and an illustrative total
    mass. A sky-plane relative velocity exceeding projected escape speed is
    not a definitive unbound classification (perspective/selection effects).
    """
    if not np.isfinite(mass_msun) or mass_msun <= 0:
        raise ValueError('mass_msun must be positive')
    plx, _, dra, ddec, _, _ = _components(row)
    separation_au = 1000.0 * row['separation_arcsec'] / plx
    speed = KMS_PER_AU_PER_YEAR * np.hypot(dra, ddec) / plx
    circular = CIRCULAR_SPEED_1AU_KMS * np.sqrt(mass_msun / separation_au)
    return {'separation_au': float(separation_au), 'relative_speed_kms': float(speed),
            'circular_speed_kms': float(circular), 'escape_speed_kms': float(np.sqrt(2) * circular),
            'speed_to_projected_escape': float(speed / (np.sqrt(2) * circular))}


def delta_method_speed_sigma(row: dict, pm_correlation: float = 0.0) -> float:
    """First-order speed sigma with *hypothetical* within-difference PM rho.

    The cross-component correlation is not available in this retained CSV.
    Parallax and PM errors are assumed independent. At zero relative PM,
    the speed norm is non-differentiable and this approximation is rejected.
    """
    if not np.isfinite(pm_correlation) or abs(pm_correlation) >= 1:
        raise ValueError('require |pm_correlation| < 1')
    plx, sigma_plx, dra, ddec, sigma_ra, sigma_dec = _components(row)
    norm = float(np.hypot(dra, ddec))
    if norm == 0:
        raise ValueError('delta method undefined at zero relative proper motion')
    factor = KMS_PER_AU_PER_YEAR / plx
    g_ra = factor * dra / norm
    g_dec = factor * ddec / norm
    g_plx = -factor * norm / plx
    variance = (g_ra * sigma_ra)**2 + (g_dec * sigma_dec)**2
    variance += 2 * pm_correlation * g_ra * g_dec * sigma_ra * sigma_dec
    variance += (g_plx * sigma_plx)**2
    return float(np.sqrt(max(0.0, variance)))


def monte_carlo_speed_ratio(
    row: dict, *, mass_msun: float = 1.2, mass_fractional_sigma: float = 0.0,
    pm_correlation: float = 0.0, draws: int = 10000, seed: int = 20261101,
) -> dict[str, float]:
    """Conditional Monte Carlo over parallax, PM and a lognormal mass prior.

    Rejects non-positive sampled parallax rather than silently clipping it.
    Returns rejection fraction to expose weak-parallax limitations.
    """
    if draws < 100 or mass_fractional_sigma < 0 or not np.isfinite(mass_fractional_sigma):
        raise ValueError('draws >=100 and finite non-negative mass scatter required')
    if not np.isfinite(mass_msun) or mass_msun <= 0 or not np.isfinite(pm_correlation) or abs(pm_correlation) >= 1:
        raise ValueError('invalid mass or PM correlation')
    plx, s_plx, dra, ddec, s_ra, s_dec = _components(row)
    rng = np.random.default_rng(seed)
    p = rng.normal(plx, s_plx, draws)
    z1, z2 = rng.normal(size=(2, draws))
    ra = dra + s_ra * z1
    dec = ddec + s_dec * (pm_correlation * z1 + np.sqrt(1 - pm_correlation**2) * z2)
    # lognormal median = mass_msun; relative log scatter explicitly specified.
    mass = mass_msun * np.exp(mass_fractional_sigma * rng.normal(size=draws))
    valid = p > 0
    if valid.sum() < 100:
        raise ValueError('too few positive parallax samples')
    sep = 1000.0 * row['separation_arcsec'] / p[valid]
    speed = KMS_PER_AU_PER_YEAR * np.hypot(ra[valid], dec[valid]) / p[valid]
    escape = np.sqrt(2) * CIRCULAR_SPEED_1AU_KMS * np.sqrt(mass[valid] / sep)
    ratio = speed / escape
    q = np.quantile(ratio, [0.16, 0.5, 0.84])
    return {'ratio_q16': float(q[0]), 'ratio_median': float(q[1]),
            'ratio_q84': float(q[2]), 'fraction_above_projected_escape': float(np.mean(ratio > 1)),
            'parallax_rejection_fraction': float(np.mean(~valid)), 'n_valid': int(valid.sum())}


def chi2_components(row: dict) -> dict[str, float]:
    """Separate the catalogue's diagonal chi-square into distance and PM terms."""
    _, _, dra, ddec, s_ra, s_dec = _components(row)
    dplx = row['parallax_a'] - row['parallax_b']
    s_plx = np.hypot(row['parallax_a_error'], row['parallax_b_error'])
    parallax = float((dplx / s_plx)**2)
    proper_motion = float((dra / s_ra)**2 + (ddec / s_dec)**2)
    return {'parallax_chi2': parallax, 'proper_motion_chi2': proper_motion,
            'total_chi2': parallax + proper_motion}
