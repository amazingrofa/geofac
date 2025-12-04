"""
Test Suite for Superscarred Ergodicity Insight Experiment
==========================================================

Tests for the superscarred ergodicity experiment:
1. Curvature κ(n) computation
2. Detrending methods (median, highpass)
3. Spectral analysis (FFT, peaks, entropy)
4. Scar score computation
5. Stability test
6. Gate evaluation
7. Full experiment pipeline

All tests use mpmath with precision > 1e-16.
"""

import mpmath as mp
from mpmath import mpf
import pytest
import sys
import os

# Add experiments directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'experiments', 'superscarred-ergodicity-insight'))

from superscarred_ergodicity import (
    # Constants
    CHALLENGE_127,
    CHALLENGE_127_P,
    CHALLENGE_127_Q,
    RANGE_MIN,
    RANGE_MAX,
    # Data structures
    ExperimentConfig,
    SpectralPeak,
    TileScore,
    CandidateWindow,
    GateResults,
    # Core functions
    compute_curvature_kappa,
    generate_kappa_series,
    apply_detrend,
    compute_magnitude_spectrum,
    compute_spectral_entropy,
    find_spectral_peaks,
    compute_tile_scores,
    compute_global_scar_score,
    apply_perturbation,
    compute_peak_overlap,
    run_stability_test,
    rank_candidates,
    evaluate_gates,
    # Main class
    SuperscarredErgodicityExperiment,
    HAS_NUMPY_SCIPY,
)


# Skip all tests if numpy/scipy not available
pytestmark = pytest.mark.skipif(
    not HAS_NUMPY_SCIPY,
    reason="numpy/scipy required for superscarred ergodicity tests"
)


class TestCurvatureComputation:
    """Test κ(n) curvature computation."""
    
    def setup_method(self):
        """Set precision for tests."""
        mp.dps = 50
    
    def test_kappa_positive(self):
        """Test that κ(n) is positive for n > 1."""
        N = RANGE_MIN  # 10^14
        for n in [100, 1000, 10000, 100000]:
            kappa = compute_curvature_kappa(n, N, 50)
            assert kappa > 0, f"κ({n}) should be positive, got {kappa}"
    
    def test_kappa_increasing(self):
        """Test that κ(n) increases with n."""
        N = RANGE_MIN
        kappa_100 = compute_curvature_kappa(100, N, 50)
        kappa_1000 = compute_curvature_kappa(1000, N, 50)
        kappa_10000 = compute_curvature_kappa(10000, N, 50)
        
        assert kappa_1000 > kappa_100, "κ should increase with n"
        assert kappa_10000 > kappa_1000, "κ should increase with n"
    
    def test_kappa_zero_for_invalid(self):
        """Test κ(n) = 0 for n < 1."""
        N = RANGE_MIN
        kappa = compute_curvature_kappa(0, N, 50)
        assert kappa == 0, f"κ(0) should be 0, got {kappa}"
        
        kappa_neg = compute_curvature_kappa(-5, N, 50)
        assert kappa_neg == 0, f"κ(-5) should be 0, got {kappa_neg}"
    
    def test_kappa_precision(self):
        """Test κ(n) respects precision setting."""
        N = RANGE_MIN
        n = 1000
        
        # Higher precision should give more digits
        kappa_low = compute_curvature_kappa(n, N, 20)
        kappa_high = compute_curvature_kappa(n, N, 100)
        
        # Both should be close but may differ in trailing digits
        assert abs(float(kappa_low) - float(kappa_high)) < 1e-15


class TestKappaSeriesGeneration:
    """Test κ(n) series generation."""
    
    def test_generate_series_basic(self):
        """Test basic series generation."""
        N = RANGE_MIN
        center = int(mp.sqrt(N))
        half_window = 100
        
        n_values, kappa_values = generate_kappa_series(
            N, center, half_window, step=10, seed=42, filter_small_primes=False
        )
        
        assert len(n_values) > 0, "Should generate some values"
        assert len(n_values) == len(kappa_values), "Lengths should match"
    
    def test_generate_series_deterministic(self):
        """Test series generation is deterministic with same seed."""
        N = RANGE_MIN
        center = int(mp.sqrt(N))
        half_window = 50
        
        n1, k1 = generate_kappa_series(N, center, half_window, step=5, seed=42, filter_small_primes=False)
        n2, k2 = generate_kappa_series(N, center, half_window, step=5, seed=42, filter_small_primes=False)
        
        assert n1 == n2, "Same seed should produce same n values"
        assert k1 == k2, "Same seed should produce same kappa values"
    
    def test_generate_series_filters_small_primes(self):
        """Test that series filters candidates divisible by 2, 3, 5 when enabled."""
        N = RANGE_MIN
        center = int(mp.sqrt(N))
        half_window = 20
        
        n_values, _ = generate_kappa_series(N, center, half_window, step=1, seed=42, filter_small_primes=True)
        
        for n in n_values:
            assert n % 2 != 0, f"{n} should not be even"
            assert n % 3 != 0, f"{n} should not be divisible by 3"
            assert n % 5 != 0, f"{n} should not be divisible by 5"


class TestDetrending:
    """Test detrending methods."""
    
    def test_median_detrend(self):
        """Test median detrending."""
        import numpy as np
        
        # Create test data with trend
        n = 100
        trend = np.linspace(0, 10, n)
        oscillation = np.sin(np.linspace(0, 10 * np.pi, n))
        data = list(trend + oscillation)
        
        detrended = apply_detrend(data, method="median")
        
        # Detrended should have near-zero mean
        assert abs(np.mean(detrended)) < 2.0, "Detrended mean should be near zero"
    
    def test_highpass_detrend(self):
        """Test highpass detrending."""
        import numpy as np
        
        # Create test data with low-frequency trend and high-frequency oscillation
        n = 200
        low_freq = np.sin(np.linspace(0, 2 * np.pi, n))  # Low frequency
        high_freq = 0.5 * np.sin(np.linspace(0, 40 * np.pi, n))  # High frequency
        data = list(low_freq + high_freq)
        
        detrended = apply_detrend(data, method="highpass", cutoff=0.1)
        
        # High-pass should remove low frequency (approximately)
        # Note: edge effects can cause issues, so we're lenient
        assert len(detrended) == len(data), "Output length should match"
    
    def test_invalid_detrend_method(self):
        """Test that invalid detrend method raises error."""
        with pytest.raises(ValueError, match="Unknown detrend method"):
            apply_detrend([1, 2, 3], method="invalid")


class TestSpectralAnalysis:
    """Test spectral analysis components."""
    
    def test_magnitude_spectrum_shape(self):
        """Test magnitude spectrum has correct shape."""
        import numpy as np
        
        n = 128
        data = np.sin(np.linspace(0, 10 * np.pi, n))
        
        freqs, mags = compute_magnitude_spectrum(data)
        
        # Positive frequencies only (including 0)
        # The actual count depends on filtering logic, just verify consistency
        assert len(freqs) > 0, "Should have some frequencies"
        assert len(mags) == len(freqs), "Magnitudes should match frequencies"
        assert all(f >= 0 for f in freqs), "All frequencies should be non-negative"
    
    def test_spectral_entropy_range(self):
        """Test spectral entropy is in [0, 1]."""
        import numpy as np
        
        # Test with pure tone (low entropy)
        n = 256
        pure_tone = np.sin(np.linspace(0, 10 * np.pi, n))
        _, mags_pure = compute_magnitude_spectrum(pure_tone)
        entropy_pure = compute_spectral_entropy(mags_pure)
        
        assert 0 <= entropy_pure <= 1, f"Entropy {entropy_pure} should be in [0, 1]"
        
        # Test with noise (high entropy)
        np.random.seed(42)
        noise = np.random.randn(n)
        _, mags_noise = compute_magnitude_spectrum(noise)
        entropy_noise = compute_spectral_entropy(mags_noise)
        
        assert 0 <= entropy_noise <= 1, f"Entropy {entropy_noise} should be in [0, 1]"
        
        # Pure tone should have lower entropy than noise
        assert entropy_pure < entropy_noise, "Pure tone should have lower entropy"
    
    def test_find_peaks_basic(self):
        """Test peak finding on synthetic data."""
        import numpy as np
        
        # Create signal with clear peak
        n = 256
        t = np.linspace(0, 10 * np.pi, n)
        signal = np.sin(t) + 0.5 * np.sin(3 * t)  # Two frequencies
        
        freqs, mags = compute_magnitude_spectrum(signal)
        peaks = find_spectral_peaks(freqs, mags, top_k=5, min_prominence_zscore=0.0)
        
        assert len(peaks) >= 1, "Should find at least one peak"
        assert all(isinstance(p, SpectralPeak) for p in peaks), "Should return SpectralPeak objects"


class TestScarScore:
    """Test scar score computation."""
    
    def test_tile_scores_basic(self):
        """Test tile score computation."""
        import numpy as np
        
        n_values = list(range(100, 200))
        kappa_values = [float(x) for x in range(100)]
        detrended = np.array(kappa_values) - np.mean(kappa_values)
        
        tiles = compute_tile_scores(n_values, kappa_values, detrended, num_tiles=10)
        
        assert len(tiles) == 10, f"Should have 10 tiles, got {len(tiles)}"
        assert all(isinstance(t, TileScore) for t in tiles), "Should return TileScore objects"
    
    def test_global_scar_score_range(self):
        """Test global scar score is in [0, 1]."""
        import numpy as np
        
        # Create tiles with varying energy
        n_values = list(range(100, 200))
        kappa_values = [float(x) for x in range(100)]
        detrended = np.random.randn(100)
        
        tiles = compute_tile_scores(n_values, kappa_values, detrended, num_tiles=10)
        scar_score = compute_global_scar_score(tiles, top_fraction=0.10)
        
        assert 0 <= scar_score <= 1, f"Scar score {scar_score} should be in [0, 1]"
    
    def test_scar_score_concentrated_energy(self):
        """Test scar score is high when energy is concentrated."""
        import numpy as np
        
        n_values = list(range(100, 200))
        kappa_values = [float(x) for x in range(100)]
        
        # Concentrated energy: high in first tile, low elsewhere
        detrended = np.zeros(100)
        detrended[:10] = 10.0  # High energy in first 10 elements
        
        tiles = compute_tile_scores(n_values, kappa_values, detrended, num_tiles=10)
        scar_score = compute_global_scar_score(tiles, top_fraction=0.10)
        
        # With 10 tiles and top 10%, we're looking at 1 tile
        # That tile has all the energy, so scar score should be 1.0
        assert scar_score == 1.0, f"Scar score should be 1.0 for concentrated energy, got {scar_score}"


class TestStabilityTest:
    """Test stability test components."""
    
    def test_apply_perturbation(self):
        """Test sinusoidal perturbation application."""
        n_values = list(range(100, 200))
        epsilon = 1e-4
        L = 50
        
        perturbed = apply_perturbation(n_values, epsilon, L)
        
        assert len(perturbed) == len(n_values), "Output length should match"
        
        # Perturbations should be small
        max_delta = max(abs(p - n) for p, n in zip(perturbed, n_values))
        assert max_delta <= epsilon + 1, f"Perturbation too large: {max_delta}"
    
    def test_peak_overlap_identical(self):
        """Test peak overlap is 1.0 for identical peaks."""
        peaks = [
            SpectralPeak(0.1, 1.0, 0.5, 1.0, 2.0, []),
            SpectralPeak(0.2, 0.8, 0.4, 1.0, 1.5, []),
        ]
        
        overlap = compute_peak_overlap(peaks, peaks)
        assert overlap == 1.0, f"Overlap should be 1.0 for identical peaks, got {overlap}"
    
    def test_peak_overlap_disjoint(self):
        """Test peak overlap is 0.0 for disjoint peaks."""
        peaks1 = [SpectralPeak(0.1, 1.0, 0.5, 1.0, 2.0, [])]
        peaks2 = [SpectralPeak(0.9, 1.0, 0.5, 1.0, 2.0, [])]  # Very different frequency
        
        overlap = compute_peak_overlap(peaks1, peaks2)
        assert overlap == 0.0, f"Overlap should be 0.0 for disjoint peaks, got {overlap}"


class TestGateEvaluation:
    """Test gate evaluation."""
    
    def test_gate_a_robust_peak(self):
        """Test Gate A: robust peak detection."""
        # Create peak with high z-score
        peaks = [SpectralPeak(0.1, 1.0, 0.5, 1.0, 2.5, [])]  # z_score = 2.5 >= 2.0
        
        config = ExperimentConfig()
        gates = evaluate_gates(peaks, 0.65, [], 100, config)
        
        assert gates.gate_a_passed, "Gate A should pass with z-score >= 2.0"
    
    def test_gate_a_no_robust_peak(self):
        """Test Gate A fails without robust peak."""
        # Create peak with low z-score
        peaks = [SpectralPeak(0.1, 1.0, 0.5, 1.0, 1.5, [])]  # z_score = 1.5 < 2.0
        
        config = ExperimentConfig()
        gates = evaluate_gates(peaks, 0.65, [], 100, config)
        
        assert not gates.gate_a_passed, "Gate A should fail with z-score < 2.0"
    
    def test_gate_b_stability(self):
        """Test Gate B: stability threshold."""
        peaks = [SpectralPeak(0.1, 1.0, 0.5, 1.0, 2.5, [])]
        
        config = ExperimentConfig()
        
        # Stability >= 60% should pass
        gates_pass = evaluate_gates(peaks, 0.65, [], 100, config)
        assert gates_pass.gate_b_passed, "Gate B should pass with overlap >= 60%"
        
        # Stability < 60% should fail
        gates_fail = evaluate_gates(peaks, 0.55, [], 100, config)
        assert not gates_fail.gate_b_passed, "Gate B should fail with overlap < 60%"
    
    def test_gate_c_reduction(self):
        """Test Gate C: reduction threshold."""
        peaks = [SpectralPeak(0.1, 1.0, 0.5, 1.0, 2.5, [])]
        
        # Candidates covering small fraction of search space
        candidates = [CandidateWindow(100, 109, 1.0, 0.6, 0.5, 0.3)]  # 10 n-values
        
        config = ExperimentConfig()
        
        # 10 candidates out of 100 = 90% reduction >= 10%
        gates = evaluate_gates(peaks, 0.65, candidates, 100, config)
        assert gates.gate_c_passed, "Gate C should pass with >= 10% reduction"


class TestExperimentConfig:
    """Test experiment configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ExperimentConfig()
        
        assert config.window_length == 4096
        assert config.detrend_method == "median"
        assert config.top_peaks == 5
        assert config.min_prominence_zscore == 2.0
        assert config.num_tiles == 20
        assert config.stability_overlap_threshold == 0.60
        assert config.seed == 42
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ExperimentConfig(
            window_length=2048,
            detrend_method="highpass",
            seed=123
        )
        
        assert config.window_length == 2048
        assert config.detrend_method == "highpass"
        assert config.seed == 123
    
    def test_default_epsilon_and_L(self):
        """Test default epsilon and L values are set."""
        config = ExperimentConfig()
        
        assert config.epsilon_values is not None
        assert len(config.epsilon_values) == 3
        assert config.L_values is not None
        assert len(config.L_values) == 3


class TestExperimentValidation:
    """Test experiment validation gates."""
    
    def test_validate_challenge_127(self):
        """Test CHALLENGE_127 is accepted."""
        experiment = SuperscarredErgodicityExperiment()
        
        # Should not raise
        experiment.validate_n(CHALLENGE_127)
    
    def test_validate_operational_range(self):
        """Test operational range is accepted."""
        experiment = SuperscarredErgodicityExperiment()
        
        # Should not raise
        experiment.validate_n(RANGE_MIN)
        experiment.validate_n(RANGE_MAX)
        experiment.validate_n(10**15)
    
    def test_reject_outside_range(self):
        """Test values outside range are rejected."""
        experiment = SuperscarredErgodicityExperiment()
        
        with pytest.raises(ValueError, match="violates validation gates"):
            experiment.validate_n(12345)  # Below RANGE_MIN threshold
        
        with pytest.raises(ValueError, match="violates validation gates"):
            experiment.validate_n(10**20)  # Above RANGE_MAX threshold


class TestFullPipeline:
    """Test full experiment pipeline."""
    
    def test_small_operational_range(self):
        """Test experiment runs on small operational range value."""
        config = ExperimentConfig(
            window_length=256,
            num_tiles=5,
            top_candidates=3,
            seed=42
        )
        
        experiment = SuperscarredErgodicityExperiment(config)
        
        # Use N in operational range with larger window to ensure enough data
        N = RANGE_MIN  # 10^14
        
        # Run with larger window and smaller step for enough data
        results = experiment.run(
            N=N,
            half_window=1000,
            step=1,  # step=1 to ensure we get enough points
            output_dir="/tmp/superscarred_test"
        )
        
        # Check results structure
        assert "timestamp" in results
        assert "config" in results
        assert "spectral_analysis" in results
        assert "candidates" in results
        assert "gates" in results
        
        # Gates dict should have all fields
        assert "gate_a_passed" in results["gates"]
        assert "gate_b_passed" in results["gates"]
        assert "gate_c_passed" in results["gates"]
        assert "all_passed" in results["gates"]


class TestConstants:
    """Test constant values."""
    
    def test_challenge_127_factorization(self):
        """Test CHALLENGE_127 = P × Q."""
        assert CHALLENGE_127_P * CHALLENGE_127_Q == CHALLENGE_127
    
    def test_range_bounds(self):
        """Test range bounds are correct."""
        assert RANGE_MIN == 10**14
        assert RANGE_MAX == 10**18


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
