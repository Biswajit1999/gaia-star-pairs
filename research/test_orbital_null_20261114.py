import unittest
from orbital_null_20261114 import circular_speed_kms, projected_speed_quantiles, noncentral_chisquare_expectation

class OrbitalTests(unittest.TestCase):
    def test_one_au(self): self.assertAlmostEqual(circular_speed_kms(1, 1), 29.78, delta=.05)
    def test_scaling(self): self.assertAlmostEqual(circular_speed_kms(4, 1), 2*circular_speed_kms(1, 1))
    def test_seed(self): self.assertEqual(projected_speed_quantiles(1, 10, seed=7), projected_speed_quantiles(1, 10, seed=7))
    def test_quantile_order(self):
        a,b,c = projected_speed_quantiles(1, 10)
        self.assertTrue(0 <= a <= b <= c <= circular_speed_kms(1,10))
    def test_central(self): self.assertEqual(noncentral_chisquare_expectation([0,0],[1,2])["expected_chi2"], 2)
    def test_noncentral(self): self.assertEqual(noncentral_chisquare_expectation([2,0],[1,1])["variance_chi2"], 20)
    def test_invalid(self):
        with self.assertRaises(ValueError): circular_speed_kms(-1,1)

if __name__ == "__main__": unittest.main()
