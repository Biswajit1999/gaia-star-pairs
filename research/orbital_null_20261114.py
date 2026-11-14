"""Conditional circular-orbit projected speed and noncentral chi-square diagnostics."""
import math
import random

G = 6.67430e-11
M_SUN = 1.98847e30
AU = 149597870700.0

def circular_speed_kms(mass_solar, separation_au):
    """Relative circular speed for total mass and true 3-D separation."""
    if not all(math.isfinite(v) and v > 0 for v in (mass_solar, separation_au)):
        raise ValueError("mass and true separation must be positive finite")
    return math.sqrt(G * M_SUN * mass_solar / (AU * separation_au)) / 1000

def projected_speed_quantiles(mass_solar, separation_au, *, draws=10000, seed=0):
    """Isotropic velocity direction at fixed true radius, not observed separation."""
    if isinstance(draws, bool) or not isinstance(draws, int) or draws < 10:
        raise ValueError("draws must be >=10")
    v = circular_speed_kms(mass_solar, separation_au)
    rng = random.Random(seed)
    samples = sorted(v * math.sqrt(1 - rng.uniform(-1, 1)**2) for _ in range(draws))
    return tuple(samples[round(q * (draws - 1))] for q in (0.05, 0.5, 0.95))

def noncentral_chisquare_expectation(mean_offsets, sigmas):
    """E[sum((X_i/sigma_i)^2)] for independent Gaussian X_i."""
    mu, sig = tuple(mean_offsets), tuple(sigmas)
    if not mu or len(mu) != len(sig) or any(not math.isfinite(x) for x in mu) or any(not math.isfinite(s) or s <= 0 for s in sig):
        raise ValueError("finite offsets and positive uncertainties required")
    lam = sum((m / s)**2 for m, s in zip(mu, sig))
    return {"degrees_of_freedom": len(mu), "noncentrality": lam,
            "expected_chi2": len(mu) + lam, "variance_chi2": 2 * (len(mu) + 2 * lam)}
