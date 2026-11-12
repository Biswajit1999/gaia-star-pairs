"""Conditional Gaia projected-pair kinematics; units: mas, mas/yr, arcsec, pc, km/s.

Independent Gaussian astrometry is assumed except for an optional two-axis
proper-motion covariance. These are sensitivity calculations, not binding tests.
"""
from math import hypot, sqrt, isfinite
import numpy as np

K = 4.74047  # km/s for (arcsec/year)*pc
GMSUN_AU = 887.0  # (km/s)^2 AU, rounded astronomical constant

def projected_pair(parallax_mas, separation_arcsec, dmu_masyr, mass_msun):
    """Projected separation (AU), transverse relative speed and escape-speed ceiling."""
    p = float(parallax_mas)
    theta = float(separation_arcsec)
    mu = np.asarray(dmu_masyr, dtype=float)
    mass = float(mass_msun)
    if not (np.isfinite([p, theta, mass]).all() and p > 0 and theta > 0 and mass > 0
            and mu.shape == (2,) and np.isfinite(mu).all()):
        raise ValueError("positive finite parallax, separation, mass and finite 2-vector required")
    separation_au = 1000.0 * theta / p
    v = K * np.linalg.norm(mu) / p
    escape = sqrt(2 * GMSUN_AU * mass / separation_au)
    return separation_au, v, escape

def transverse_variance(parallax_mas, sigma_parallax_mas, dmu_masyr, cov_mu):
    """First-order variance of relative transverse speed; parallax independent of mu."""
    p = float(parallax_mas)
    sp = float(sigma_parallax_mas)
    mu = np.asarray(dmu_masyr, dtype=float)
    cov = np.asarray(cov_mu, dtype=float)
    if p <= 0 or sp < 0 or not np.isfinite([p, sp]).all() or mu.shape != (2,) or cov.shape != (2,2):
        raise ValueError("invalid astrometric dimensions")
    if not np.isfinite(mu).all() or not np.isfinite(cov).all() or not np.allclose(cov,cov.T) or np.linalg.eigvalsh(cov).min() < -1e-12:
        raise ValueError("invalid covariance")
    norm = np.linalg.norm(mu)
    if norm == 0:
        raise ValueError("speed derivative undefined at zero relative proper motion")
    grad = K * mu / (p * norm)
    dp = -K * norm / p**2
    return float(grad @ cov @ grad + (dp*sp)**2)

def seeded_speed_quantiles(parallax_mas, sigma_parallax_mas, dmu_masyr, cov_mu, draws=10000, seed=42):
    """Seeded Monte Carlo sensitivity; rejects non-positive parallax draws."""
    if not isinstance(draws, int) or draws < 100:
        raise ValueError("draws must be >= 100")
    # Validate covariance and input first.
    transverse_variance(parallax_mas, sigma_parallax_mas, dmu_masyr, cov_mu)
    rng = np.random.default_rng(seed)
    p = rng.normal(parallax_mas, sigma_parallax_mas, draws)
    if np.any(p <= 0):
        raise ValueError("parallax sampling crossed zero: use a distance posterior")
    mu = rng.multivariate_normal(dmu_masyr, cov_mu, draws)
    speed = K * np.linalg.norm(mu, axis=1) / p
    return np.quantile(speed, [0.05, 0.5, 0.95])
