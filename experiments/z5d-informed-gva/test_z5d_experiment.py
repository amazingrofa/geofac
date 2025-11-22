"""
Z5D-Informed GVA Experiment Test Suite
=======================================

Comprehensive tests for the Z5D experiment framework to ensure correctness
before executing the expensive 127-bit challenge.

Tests cover:
1. Wheel residue filtering correctness
2. Z5D density simulation properties
3. Baseline FR-GVA functionality
4. Z5D-enhanced FR-GVA functionality
5. Comparison experiment framework
6. 60-bit validation cases

Run with: pytest test_z5d_experiment.py -v
"""

import sys
import os
import pytest
from math import log, isqrt
import csv
import json

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(__file__))

from wheel_residues import (
    WHEEL_MODULUS, WHEEL_SIZE, WHEEL_RESIDUE_SET,
    is_admissible, next_admissible, prev_admissible,
    count_admissible_in_range, effective_coverage, meets_gap_rule
)
from z5d_density_simulator import simulate_z5d_density, isqrt as z5d_isqrt
from baseline_fr_gva import baseline_fr_gva, adaptive_precision
from z5d_enhanced_fr_gva import z5d_enhanced_fr_gva
from comparison_experiment import (
    run_baseline_experiment, run_wheel_only_experiment,
    run_z5d_prior_only_experiment, run_full_z5d_experiment,
    CHALLENGE_127, EXPECTED_P, EXPECTED_Q
)


class TestWheelResidues:
    """Test wheel residue filtering."""
    
    def test_wheel_constants(self):
        """Verify wheel constants."""
        assert WHEEL_MODULUS == 210
        assert WHEEL_SIZE == 48
        assert len(WHEEL_RESIDUE_SET) == 48
    
    def test_pruning_factor(self):
        """Verify ~77% pruning factor."""
        pruning = (WHEEL_MODULUS - WHEEL_SIZE) / WHEEL_MODULUS
        assert 0.77 <= pruning <= 0.78
        assert abs(pruning - 0.7714) < 0.01
    
    def test_admissibility_known_primes(self):
        """Known large primes should be admissible."""
        # All primes > 7 must be admissible
        known_primes = [11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        for p in known_primes:
            assert is_admissible(p), f"Prime {p} should be admissible"
    
    def test_admissibility_small_primes(self):
        """Small primes 2,3,5,7 are NOT in wheel residues."""
        for p in [2, 3, 5, 7]:
            assert not is_admissible(p)
    
    def test_admissibility_composites(self):
        """Composites with small factors should not be admissible."""
        # Multiples of 2, 3, 5, 7
        assert not is_admissible(12)  # 2 × 6
        assert not is_admissible(15)  # 3 × 5
        assert not is_admissible(14)  # 2 × 7
        assert not is_admissible(21)  # 3 × 7
    
    def test_next_admissible(self):
        """Test next_admissible finds correct values."""
        assert next_admissible(1) == 1
        assert next_admissible(2) == 11
        assert next_admissible(11) == 11
        assert next_admissible(12) == 13
    
    def test_prev_admissible(self):
        """Test prev_admissible finds correct values."""
        assert prev_admissible(11) == 11
        assert prev_admissible(12) == 11
        assert prev_admissible(13) == 13
        assert prev_admissible(14) == 13
    
    def test_count_in_range(self):
        """Test counting admissible values in ranges."""
        # Full cycle should have exactly 48
        count = count_admissible_in_range(0, 210)
        assert count == 48
        
        # Multiple cycles
        count = count_admissible_in_range(0, 420)
        expected = 2 * 48
        assert abs(count - expected) <= 2  # Allow small edge effects
    
    def test_effective_coverage(self):
        """Test effective coverage calculation."""
        # Coverage factor = 48/210 ≈ 0.2286
        coverage = effective_coverage(1000)
        expected = 1000 * (48 / 210)
        assert abs(coverage - expected) < 1
    
    def test_gap_rule_127bit(self):
        """Test gap rule for 127-bit context."""
        sqrt_n = isqrt(CHALLENGE_127)
        expected_gap = log(float(sqrt_n))
        
        # Small windows should fail
        assert not meets_gap_rule(100, expected_gap)
        assert not meets_gap_rule(200, expected_gap)
        
        # Larger windows should pass
        assert meets_gap_rule(1000, expected_gap)
        assert meets_gap_rule(2000, expected_gap)


class TestZ5DDensitySimulation:
    """Test Z5D density simulation."""
    
    def test_isqrt_correctness(self):
        """Test integer square root."""
        assert z5d_isqrt(0) == 0
        assert z5d_isqrt(1) == 1
        assert z5d_isqrt(4) == 2
        assert z5d_isqrt(9) == 3
        assert z5d_isqrt(15) == 3
        assert z5d_isqrt(16) == 4
    
    def test_isqrt_127bit(self):
        """Test isqrt on 127-bit challenge."""
        sqrt_n = z5d_isqrt(CHALLENGE_127)
        # Verify it's correct
        assert sqrt_n * sqrt_n <= CHALLENGE_127
        assert (sqrt_n + 1) * (sqrt_n + 1) > CHALLENGE_127
    
    def test_density_simulation_structure(self):
        """Test density simulation produces expected structure."""
        sqrt_n = z5d_isqrt(CHALLENGE_127)
        histogram = simulate_z5d_density(sqrt_n, window=10000, bin_width=100, seed=42)
        
        # Should produce bins
        assert len(histogram) > 0
        
        # All densities should be positive
        for density in histogram.values():
            assert density > 0
        
        # Check bin centers are in expected range
        bin_centers = list(histogram.keys())
        assert min(bin_centers) >= -10000
        assert max(bin_centers) <= 10000
    
    def test_density_values_reasonable(self):
        """Test density values are in reasonable range."""
        sqrt_n = z5d_isqrt(CHALLENGE_127)
        base_density = 1.0 / log(float(sqrt_n))
        
        histogram = simulate_z5d_density(sqrt_n, window=10000, bin_width=100, seed=42)
        
        # All densities should be within ±50% of base (with variation)
        for density in histogram.values():
            assert 0.5 * base_density <= density <= 1.5 * base_density


class TestBaselineFRGVA:
    """Test baseline FR-GVA functionality."""
    
    def test_adaptive_precision(self):
        """Test adaptive precision formula."""
        # 127-bit: 127 * 4 + 200 = 708
        expected = max(100, 127 * 4 + 200)
        actual = adaptive_precision(CHALLENGE_127)
        assert actual == expected
        
        # Small numbers should get minimum precision
        assert adaptive_precision(100) >= 100
    
    def test_baseline_runs_without_error(self):
        """Test baseline FR-GVA runs without crashing on small case."""
        # Use small test case: 60-bit semiprime
        N = 1152921470247108503  # 60-bit: 1073741789 × 1073741827
        
        # Run with minimal budget to ensure it doesn't crash
        result = baseline_fr_gva(N, max_candidates=10, delta_window=1000, verbose=False)
        
        # May or may not find factors with small budget, but should not crash
        if result is not None:
            p, q = result
            assert p * q == N


class TestZ5DEnhancedFRGVA:
    """Test Z5D-enhanced FR-GVA functionality."""
    
    def test_enhanced_runs_without_error(self):
        """Test enhanced FR-GVA runs without crashing."""
        # Use small test case
        N = 1152921470247108503  # 60-bit
        
        # Create temporary density file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['bin_center', 'count', 'density'])
            for i in range(-10, 11):
                writer.writerow([i * 1000, 20, 0.02])
            temp_file = f.name
        
        try:
            # Run with minimal budget
            result = z5d_enhanced_fr_gva(
                N, 
                z5d_density_file=temp_file,
                max_candidates=10, 
                delta_window=1000,
                z5d_weight_beta=0.1,
                use_wheel_filter=True,
                use_z5d_stepping=False,
                verbose=False
            )
            
            # Should not crash
            if result is not None:
                p, q = result
                assert p * q == N
        finally:
            os.unlink(temp_file)
    
    def test_wheel_filter_mode(self):
        """Test wheel-filter-only mode."""
        N = 1152921470247108503
        
        # Wheel filter without Z5D should work
        result = z5d_enhanced_fr_gva(
            N,
            z5d_density_file=None,
            max_candidates=10,
            delta_window=1000,
            use_wheel_filter=True,
            use_z5d_stepping=False,
            verbose=False
        )
        
        # Should run without error
        assert result is None or isinstance(result, tuple)


class TestComparisonFramework:
    """Test comparison experiment framework."""
    
    def test_challenge_constants(self):
        """Verify challenge constants are correct."""
        assert EXPECTED_P * EXPECTED_Q == CHALLENGE_127
        
        # Verify p and q are in correct range
        sqrt_n = isqrt(CHALLENGE_127)
        assert EXPECTED_P < sqrt_n < EXPECTED_Q
    
    def test_comparison_structure(self):
        """Test comparison framework structure."""
        # This test just verifies the functions can be called
        # without actually running expensive computations
        
        # Check functions are callable
        assert callable(run_baseline_experiment)
        assert callable(run_wheel_only_experiment)
        assert callable(run_z5d_prior_only_experiment)
        assert callable(run_full_z5d_experiment)


class TestIntegration:
    """Integration tests for full workflow."""
    
    def test_density_file_exists(self):
        """Verify density histogram file exists."""
        density_file = os.path.join(os.path.dirname(__file__), "z5d_density_histogram.csv")
        assert os.path.exists(density_file), "Density histogram should exist"
        
        # Verify it's readable
        with open(density_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert 'bin_center' in header or header[0] == 'bin_center'
    
    def test_metadata_file_exists(self):
        """Verify metadata file exists."""
        metadata_file = os.path.join(os.path.dirname(__file__), "z5d_density_metadata.txt")
        assert os.path.exists(metadata_file), "Metadata file should exist"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
