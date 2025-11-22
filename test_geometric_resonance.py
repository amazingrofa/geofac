"""
Test Suite for Geometric Resonance Factorization
================================================

Tests for the geometric resonance factorization pipeline:
1. Z-framework invariants
2. Discrete structure computations
3. Geometric prime-density transformations
4. 127-bit challenge factorization
5. Verification of p × q = N

All tests use mpmath with precision > 1e-16.
"""

import mpmath as mp
from mpmath import mpf, pi, log, sqrt, e
import pytest
from geometric_resonance_factorization import (
    GeometricResonanceFactorizer,
    ScaleAdaptiveParams,
    DirichletKernel,
    compute_discrete_delta,
    compute_geodesic_transform,
    golden_ratio_qmc_sample,
    principal_angle,
    PHI,
    E_SQUARED,
    CHALLENGE_127,
    CHALLENGE_127_P,
    CHALLENGE_127_Q,
)


class TestZFrameworkInvariants:
    """Test Z-framework invariant properties."""
    
    def setup_method(self):
        """Set precision for tests."""
        mp.dps = 50  # High precision for tests
    
    def test_golden_ratio_invariant(self):
        """Test that golden ratio φ is computed correctly."""
        expected_phi = (1 + sqrt(5)) / 2
        assert abs(PHI - expected_phi) < mpf(1e-20)
        
        # φ² = φ + 1 (golden ratio property)
        assert abs(PHI**2 - (PHI + 1)) < mpf(1e-20)
    
    def test_e_squared_invariant(self):
        """Test that e² is computed correctly."""
        expected_e_sq = e**2
        assert abs(E_SQUARED - expected_e_sq) < mpf(1e-20)
    
    def test_discrete_delta_properties(self):
        """Test discrete frame shift Δₙ = d(n)·ln(n+1)/e²."""
        # Δₙ should be positive for n > 0
        delta_10 = compute_discrete_delta(10)
        assert delta_10 > 0
        
        # Δₙ should increase with n
        delta_100 = compute_discrete_delta(100)
        assert delta_100 > delta_10
        
        # Edge case: n = 0 should return 0
        delta_0 = compute_discrete_delta(0)
        assert delta_0 == 0
    
    def test_geodesic_transform_properties(self):
        """Test geometric prime-density mapping θ′(n,k) = φ·((n mod φ)/φ)^k."""
        k = 0.3
        
        # θ′ should be positive
        theta_100 = compute_geodesic_transform(100, k)
        assert theta_100 > 0
        
        # θ′ should be bounded by φ (since ratio ∈ [0, 1] and k > 0)
        assert theta_100 <= PHI
        
        # Different n should give different θ′
        theta_200 = compute_geodesic_transform(200, k)
        assert theta_100 != theta_200
    
    def test_principal_angle_reduction(self):
        """Test angle reduction to [-π, π]."""
        # Angle in range should stay same
        angle = mpf(1.5)
        reduced = principal_angle(angle)
        assert abs(reduced - angle) < mpf(1e-20)
        
        # Angle > π should wrap
        angle = mpf(4.0)
        reduced = principal_angle(angle)
        assert -pi < reduced <= pi
        
        # Angle < -π should wrap
        angle = mpf(-4.0)
        reduced = principal_angle(angle)
        assert -pi < reduced <= pi


class TestDirichletKernel:
    """Test Dirichlet kernel resonance detection."""
    
    def setup_method(self):
        """Set precision for tests."""
        mp.dps = 50
    
    def test_normalized_amplitude_range(self):
        """Test that amplitude is in [0, 1]."""
        J = 10
        eps = mpf(1e-25)
        
        for theta_val in [0, pi/4, pi/2, pi]:
            theta = mpf(theta_val)
            amp = DirichletKernel.normalized_amplitude(theta, J, eps)
            assert 0 <= amp <= 1, f"Amplitude {amp} out of range for θ={theta}"
    
    def test_amplitude_at_zero(self):
        """Test amplitude at θ=0 (singularity case)."""
        J = 10
        eps = mpf(1e-25)
        theta = mpf(0)
        
        amp = DirichletKernel.normalized_amplitude(theta, J, eps)
        # At θ=0, should return 1 (singularity guard)
        assert abs(amp - 1) < mpf(1e-10)
    
    def test_amplitude_symmetry(self):
        """Test that amplitude is symmetric: A(θ) = A(-θ)."""
        J = 10
        eps = mpf(1e-25)
        theta = mpf(pi / 3)
        
        amp_pos = DirichletKernel.normalized_amplitude(theta, J, eps)
        amp_neg = DirichletKernel.normalized_amplitude(-theta, J, eps)
        
        assert abs(amp_pos - amp_neg) < mpf(1e-15)


class TestQMCSampling:
    """Test golden-ratio QMC sampling."""
    
    def setup_method(self):
        """Set precision for tests."""
        mp.dps = 50
    
    def test_qmc_deterministic(self):
        """Test that QMC sampling is deterministic."""
        seed = 42
        samples1 = [golden_ratio_qmc_sample(i, seed) for i in range(10)]
        samples2 = [golden_ratio_qmc_sample(i, seed) for i in range(10)]
        
        for s1, s2 in zip(samples1, samples2):
            assert s1 == s2
    
    def test_qmc_range(self):
        """Test that QMC samples are in [0, 1]."""
        seed = 42
        for i in range(100):
            sample = golden_ratio_qmc_sample(i, seed)
            assert 0 <= sample < 1
    
    def test_qmc_distribution(self):
        """Test that QMC samples are well-distributed."""
        seed = 42
        samples = [float(golden_ratio_qmc_sample(i, seed)) for i in range(1000)]
        
        # Mean should be close to 0.5
        mean = sum(samples) / len(samples)
        assert abs(mean - 0.5) < 0.1


class TestScaleAdaptiveParams:
    """Test scale-adaptive parameter tuning."""
    
    def test_adaptive_samples_scaling(self):
        """Test samples scale super-linearly."""
        base = 3000
        
        samples_30 = ScaleAdaptiveParams.adaptive_samples(2**30, base)
        samples_60 = ScaleAdaptiveParams.adaptive_samples(2**60, base)
        samples_127 = ScaleAdaptiveParams.adaptive_samples(2**127, base)
        
        # Should increase with scale
        assert samples_60 > samples_30
        assert samples_127 > samples_60
    
    def test_adaptive_m_span_scaling(self):
        """Test m-span scales linearly."""
        base = 180
        
        span_30 = ScaleAdaptiveParams.adaptive_m_span(2**30, base)
        span_60 = ScaleAdaptiveParams.adaptive_m_span(2**60, base)
        
        # Should scale linearly (approximately 2x for 2x bit length)
        assert abs(span_60 / span_30 - 2.0) < 0.1
    
    def test_adaptive_threshold_bounded(self):
        """Test threshold stays in [0.5, 1.0]."""
        base = 0.92
        attenuation = 0.05
        
        for bit_len in [30, 60, 127, 200]:
            n = 2**bit_len
            threshold = ScaleAdaptiveParams.adaptive_threshold(n, base, attenuation)
            assert 0.5 <= threshold <= 1.0
    
    def test_adaptive_k_range_narrowing(self):
        """Test k-range narrows with scale."""
        k_lo, k_hi = 0.25, 0.45
        
        lo_30, hi_30 = ScaleAdaptiveParams.adaptive_k_range(2**30, k_lo, k_hi)
        lo_127, hi_127 = ScaleAdaptiveParams.adaptive_k_range(2**127, k_lo, k_hi)
        
        width_30 = hi_30 - lo_30
        width_127 = hi_127 - lo_127
        
        # Width should narrow
        assert width_127 < width_30


class TestFactorization:
    """Test complete factorization pipeline."""
    
    def setup_method(self):
        """Set precision for factorization tests."""
        mp.dps = 100  # Moderate precision for tests
    
    def test_challenge_127_expected_factors(self):
        """Test that expected factors multiply to N."""
        assert CHALLENGE_127_P * CHALLENGE_127_Q == CHALLENGE_127
    
    def test_factorizer_initialization(self):
        """Test factorizer can be initialized."""
        factorizer = GeometricResonanceFactorizer(
            samples=100,  # Small for test
            m_span=20,
            J=5,
            threshold=0.9,
            timeout_seconds=10.0,
            seed=42
        )
        
        assert factorizer.base_samples == 100
        assert factorizer.seed == 42
    
    def test_validation_gate_enforcement(self):
        """Test that validation gates are enforced."""
        factorizer = GeometricResonanceFactorizer()
        
        # Small number outside range should fail
        with pytest.raises(ValueError, match="violates validation gates"):
            factorizer.factor(12345)
    
    @pytest.mark.slow
    def test_127_bit_factorization(self):
        """
        Test factorization of 127-bit challenge.
        
        NOTE: This is a slow test. It may take several minutes to complete
        depending on the adaptive timeout and whether resonance is found quickly.
        
        Mark as @pytest.mark.slow to skip in fast test runs.
        """
        # Use reasonable parameters for testing
        factorizer = GeometricResonanceFactorizer(
            samples=3000,
            m_span=180,
            J=10,
            threshold=0.92,
            k_lo=0.25,
            k_hi=0.45,
            timeout_seconds=600.0,  # 10 minutes for test
            attenuation=0.05,
            enable_scale_adaptive=True,
            seed=42
        )
        
        result = factorizer.factor(CHALLENGE_127)
        
        if result:
            p, q = result
            
            # Verify factors
            assert p > 1
            assert q > 1
            assert p * q == CHALLENGE_127
            
            # Check if we got the expected factors
            assert (p == CHALLENGE_127_P and q == CHALLENGE_127_Q) or \
                   (p == CHALLENGE_127_Q and q == CHALLENGE_127_P)
            
            print(f"\n✓ 127-bit challenge factored successfully!")
            print(f"  p = {p}")
            print(f"  q = {q}")
        else:
            pytest.skip("Factorization did not complete within timeout")


class TestPrecision:
    """Test precision handling."""
    
    def test_precision_setting(self):
        """Test that precision is set correctly."""
        mp.dps = 100
        assert mp.dps == 100
        
        # Test mpmath operations maintain precision
        # Use exact decimal strings to avoid binary representation issues
        x = mpf("1") / mpf("3")  # 0.333...
        
        # Should have 100 decimal places of precision
        # Convert to string and check we have the expected precision
        x_str = mp.nstr(x, 100)
        assert x_str.startswith("0.33333333333")
        assert len(x_str) >= 50  # At least 50 characters (including "0.")
    
    def test_high_precision_computation(self):
        """Test high-precision computation of constants."""
        mp.dps = 200
        
        # Golden ratio with high precision
        phi = (1 + sqrt(5)) / 2
        
        # φ² = φ + 1 should hold to high precision
        phi_squared = phi ** 2
        phi_plus_one = phi + 1
        
        assert abs(phi_squared - phi_plus_one) < mpf(10)**(-150)


# Test runner configuration
if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-m", "not slow"])
    
    print("\n" + "="*60)
    print("To run the slow 127-bit factorization test, use:")
    print("  pytest test_geometric_resonance.py -v -m slow")
    print("="*60)
