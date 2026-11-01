# Gaia DR3 wide-double-white-dwarf kinematic sensitivity

This optional analysis is separate from the existing uncertainty-calibration audit. It uses the **retained** `data/processed/real_pairs.csv` (30 pairs) and does not download new data. Reproduce with `python -m research.run_wide_binary_kinematics --input data/processed/real_pairs.csv`. The runner writes `results/wide_binary_kinematics.json`.

Three distinct checks are provided:

1. **Projected orbital scales:** common-distance approximation `d_pc = 1000 / mean_parallax_mas`, projected separation `r_AU = separation_arcsec * d_pc`, relative sky-plane velocity `v_t = 4.7404704635 * |delta_mu_masyr| / mean_parallax_mas` km/s, and circular/escape speeds at **assumed** total mass 1.2 solar masses. These are *projected* quantities, not 3D orbital solutions. No lens masses or gravity anomalies are inferred.
2. **Covariance sensitivity:** first-order delta-method uncertainty for `v_t`, comparing unmeasured cross-component proper-motion correlations rho=0 and rho=0.5. Gaia single-source covariance entries and inter-source correlations are **not** in this retained CSV; the scenarios are explicitly hypothetical.
3. **Non-Gaussian sensitivity:** 3,000 seeded Monte Carlo draws per pair of parallax and proper-motion differences, plus a *hypothetical* lognormal total-mass prior with median 1.2 solar masses and log scatter 0.2. Nonpositive parallax samples are rejected and their fraction reported. The ratio to projected escape speed is not a membership classifier.

The separate `chi2_components` diagnostic identifies whether the existing diagonal astrometric chi-square is driven primarily by parallax or relative proper motion; it preserves the exact repository statistic under its assumptions.

**Limits:** The original sample is only 30 white-dwarf pairs and is selection-biased. Relative proper motion includes true orbital motion, possible perspective effects, and observational error. A projected speed greater than a projected escape speed does not establish that a pair is unbound. Distances from inverse parallax become unreliable for weak parallaxes; reported conditional Monte Carlo intervals do not account for distance priors or Gaia covariance. The work does not recalibrate Gaia uncertainties or provide a test of gravity. The original sample and browser implementation remain unchanged.

Local check: `python -m pytest -q tests/test_wide_binary_kinematics.py` (requires NumPy and pytest). GitHub CI also executes the runner on the retained 30-pair CSV.
