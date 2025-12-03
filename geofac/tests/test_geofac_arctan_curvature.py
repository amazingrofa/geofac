import pytest
from geofac.geofac_arctan_curvature import kappa_n_curvature

def test_kappa_n_curvature():
    # Test with a prime number's divisor (e.g., 29 is prime, so divisor_count(29) should be 2)
    # Test with a composite number (e.g., 30) - should ideally give a different curvature
    assert kappa_n_curvature(899, 30, 1.0) > kappa_n_curvature(899, 29, 1.0) # Higher divisor count expected for 30 vs 29 as divisors of 899

if __name__ == "__main__":
    pytest.main(['-v', __file__])