# Conditional orbital-motion null (14 November 2026)

Scope: [issue #3](https://github.com/Biswajit1999/gaia-star-pairs/issues/3). This module does not modify the retained Gaia DR3 pairs or fit an orbit.

For a **hypothetical circular orbit** at true 3D separation r and total mass M, relative speed is sqrt(G*M/r). Isotropic velocity orientation at fixed r gives projected speed v*sqrt(1-u^2), u uniform [-1,1]. This is not the posterior conditional on observed sky-projected separation: a separation/orientation/eccentricity prior is needed. Quantiles use seeded Monte Carlo, not Gaia measurements.

If independent standardized Gaussian residual components have nonzero means mu_i/sigma_i, their sum of squares has noncentral chi-square expectation k+lambda and variance 2(k+2lambda), lambda=sum((mu_i/sigma_i)^2). Correlated astrometric residuals require a full covariance treatment and cannot be inferred from this diagonal formula. The illustrative SVG is theoretical, not an inferred orbit or gravity test.

Run: `cd research && python -m unittest -v test_orbital_null_20261114.py`.
Scientific implementation was assisted by AI. Biswajit Jana is the requested authenticated commit author; no observational or calibration claim is made.
