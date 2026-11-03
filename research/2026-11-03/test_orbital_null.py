import numpy as np
import pytest
from orbital_null import circular_relative_speed_kms, projected_orbital_speed_quantiles, chi_square_noncentrality

def test_kepler_scaling():
    assert circular_relative_speed_kms(4, 100) == pytest.approx(2 * circular_relative_speed_kms(1, 100))
    assert circular_relative_speed_kms(1, 400) == pytest.approx(circular_relative_speed_kms(1, 100)/2)

def test_orientations_reproducible_and_physical():
    q = projected_orbital_speed_quantiles(1.2, 1000, n=2000, seed=3)
    assert np.array_equal(q, projected_orbital_speed_quantiles(1.2, 1000, n=2000, seed=3))
    assert 0 < q[0] < q[1] < q[2] < circular_relative_speed_kms(1.2, 1000)

def test_noncentrality_zero_and_positive():
    c = np.diag([4., 9.])
    assert chi_square_noncentrality([2, 3], c, [0, 0]) == {'observed_chi2':2., 'lambda':0., 'expected_chi2':2.}
    assert chi_square_noncentrality([2, 3], c, [2, 3])['expected_chi2'] == pytest.approx(4)

def test_reject_bad_covariance():
    with pytest.raises(np.linalg.LinAlgError):
        chi_square_noncentrality([1, 2], [[1, 2], [2, 1]], [1, 1])
