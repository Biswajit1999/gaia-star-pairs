"""Conditional orbital-motion null for wide pairs; no Gaia calibration inference."""
import numpy as np

G = 6.67430e-11
MSUN = 1.98847e30
AU = 1.495978707e11

def circular_relative_speed_kms(mass_solar, separation_au):
    """Relative speed of a circular two-body orbit at true 3D separation."""
    m, r = np.broadcast_arrays(np.asarray(mass_solar, float), np.asarray(separation_au, float))
    if np.any(m <= 0) or np.any(r <= 0) or not np.all(np.isfinite(m+r)):
        raise ValueError('positive finite mass and separation required')
    return np.sqrt(G * m * MSUN / (r * AU)) / 1000

def projected_orbital_speed_quantiles(mass_solar, projected_au, n=20000, seed=11):
    """Isotropic circular-orbit orientation, conditional on projected separation.

    A projected separation is not the 3D separation. Sample random orbital
    plane normals and phase, then deproject each realization consistently.
    """
    if n < 2 or not np.isfinite(projected_au) or projected_au <= 0:
        raise ValueError('invalid sample count or separation')
    rng = np.random.default_rng(seed)
    position = rng.normal(size=(n, 3))
    position /= np.linalg.norm(position, axis=1)[:, None]
    rand = rng.normal(size=(n, 3))
    tangent = rand - np.sum(rand * position, axis=1)[:, None] * position
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    projected_fraction = np.linalg.norm(position[:, :2], axis=1)
    r_true = projected_au / projected_fraction
    v = circular_relative_speed_kms(mass_solar, r_true)
    vsky = v * np.linalg.norm(tangent[:, :2], axis=1)
    return np.quantile(vsky, [0.05, 0.5, 0.95])

def chi_square_noncentrality(delta, covariance, orbital_signal):
    """Expected chi-square = dimension + lambda for Gaussian residuals.

    delta is an observed difference; orbital_signal is a hypothetical
    nonzero mean, not a fitted Gaia orbit.
    """
    d = np.asarray(delta, float)
    s = np.asarray(orbital_signal, float)
    c = np.asarray(covariance, float)
    if d.ndim != 1 or d.shape != s.shape or c.shape != (d.size, d.size):
        raise ValueError('incompatible dimensions')
    np.linalg.cholesky(c)
    return {'observed_chi2': float(d @ np.linalg.solve(c, d)),
            'lambda': float(s @ np.linalg.solve(c, s)),
            'expected_chi2': float(d.size + s @ np.linalg.solve(c, s))}
