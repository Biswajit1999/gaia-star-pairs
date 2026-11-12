import numpy as np
import pytest
from research.gaia_pair_uncertainty_20261112 import projected_pair, transverse_variance, seeded_speed_quantiles

def test_projected_geometry():
    s,v,e = projected_pair(10, 2, [10,0], 1)
    assert s == pytest.approx(200)
    assert v == pytest.approx(4.74047)
    assert e > 0

def test_speed_scaling():
    _,v,_ = projected_pair(10,1,[10,0],1)
    _,v2,_ = projected_pair(20,1,[10,0],1)
    assert v == pytest.approx(2*v2)

def test_delta_method_matches_finite_difference():
    mu=np.array([3.,4.]); p=10.
    cov=np.diag([0.01,0.04]); sp=.1
    expected=transverse_variance(p,sp,mu,cov)
    grad=np.array([4.74047*3/(p*5),4.74047*4/(p*5)])
    assert expected == pytest.approx(grad@cov@grad+(4.74047*5/p**2*sp)**2)

def test_mc_reproducible():
    a=seeded_speed_quantiles(10,.1,[3,4],np.eye(2)*.01,draws=1000,seed=7)
    b=seeded_speed_quantiles(10,.1,[3,4],np.eye(2)*.01,draws=1000,seed=7)
    np.testing.assert_array_equal(a,b)
    assert np.all(np.diff(a)>0)

def test_invalid_covariance():
    with pytest.raises(ValueError):
        transverse_variance(10,.1,[3,4],[[1,2],[2,1]])
