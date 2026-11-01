import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.wide_binary_kinematics import (  # noqa: E402
    KMS_PER_AU_PER_YEAR, chi2_components, delta_method_speed_sigma,
    monte_carlo_speed_ratio, projected_kinematics,
)


def pair():
    return dict(parallax_a=10., parallax_b=10., parallax_a_error=.05,
                parallax_b_error=.05, pmra_a=10., pmra_b=9.,
                pmra_a_error=.1, pmra_b_error=.1, pmdec_a=5.,
                pmdec_b=5., pmdec_a_error=.1, pmdec_b_error=.1,
                separation_arcsec=10.)


def test_projected_conversion_and_mass_scaling():
    r = projected_kinematics(pair(), mass_msun=1)
    assert r['separation_au'] == pytest.approx(1000)
    assert r['relative_speed_kms'] == pytest.approx(KMS_PER_AU_PER_YEAR / 10)
    assert projected_kinematics(pair(), 4)['escape_speed_kms'] == pytest.approx(2 * r['escape_speed_kms'])


def test_component_swap_invariant():
    p = pair()
    for key in ['parallax', 'pmra', 'pmdec']:
        for suffix in ['', '_error']:
            a, b = key + '_a' + suffix, key + '_b' + suffix
            p[a], p[b] = p[b], p[a]
    assert projected_kinematics(p) == pytest.approx(projected_kinematics(pair()))
    assert chi2_components(p) == pytest.approx(chi2_components(pair()))


def test_chi2_split():
    p = pair()
    p['parallax_b'] = 9.9
    c = chi2_components(p)
    assert c['total_chi2'] == pytest.approx(c['parallax_chi2'] + c['proper_motion_chi2'])
    assert c['proper_motion_chi2'] == pytest.approx(50)


def test_delta_method_correlated_pm_and_zero_norm():
    p = pair()
    p['pmdec_b'] = 4.
    assert delta_method_speed_sigma(p, .8) > delta_method_speed_sigma(p, 0)
    p['pmra_b'], p['pmdec_b'] = p['pmra_a'], p['pmdec_a']
    with pytest.raises(ValueError, match='zero'):
        delta_method_speed_sigma(p)


def test_delta_method_matches_small_error_monte_carlo():
    p = pair()
    p['parallax_a_error'] = p['parallax_b_error'] = .001
    p['pmra_a_error'] = p['pmra_b_error'] = .002
    rng = np.random.default_rng(5)
    n = 40000
    plx = rng.normal(10, np.hypot(.001, .001) / 2, n)
    dra = rng.normal(1, np.hypot(.002, .002), n)
    speed = KMS_PER_AU_PER_YEAR * np.abs(dra) / plx
    assert np.std(speed) == pytest.approx(delta_method_speed_sigma(p), rel=.025)


def test_monte_carlo_seed_and_mass_prior():
    a = monte_carlo_speed_ratio(pair(), draws=3000, seed=42)
    b = monte_carlo_speed_ratio(pair(), draws=3000, seed=42)
    assert a == b
    assert a['ratio_q16'] < a['ratio_median'] < a['ratio_q84']
    c = monte_carlo_speed_ratio(pair(), mass_msun=4, draws=3000, seed=42)
    assert c['ratio_median'] < a['ratio_median']


def test_reject_invalid_inputs():
    p = pair()
    p['parallax_b'] = -20
    with pytest.raises(ValueError):
        projected_kinematics(p)
    with pytest.raises(ValueError):
        delta_method_speed_sigma(pair(), pm_correlation=1)
    with pytest.raises(ValueError):
        monte_carlo_speed_ratio(pair(), draws=10)
