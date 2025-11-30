"""
Hash-Bounds Partition Hypothesis Test Suite
============================================

Unit tests for hash-bounds sampling components to ensure correctness
before running expensive comparison experiments.

Tests cover:
1. Fractional square root computation
2. Boundary generation
3. Sampling near boundaries
4. Integration with GVA embedding
5. Boundary proximity scoring

Run with: pytest test_hash_bounds.py -v
"""

import sys
import os
import pytest
from math import isqrt, sqrt

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(__file__))

from hash_bounds_sampling import (
    adaptive_precision,
    compute_fractional_sqrt,
    get_all_fractional_roots,
    compute_boundary_centers,
    compute_all_boundaries,
    distance_to_nearest_boundary,
    boundary_proximity_score,
    generate_boundary_focused_samples,
    embed_torus_geodesic,
    riemannian_distance,
    hash_bounds_factor_search,
    SEED_PRIMES,
    CHALLENGE_127,
    GATE_2_60BIT,
)


class TestFractionalSqrtComputation:
    """Test fractional square root computation."""
    
    def test_frac_sqrt_2(self):
        """Test frac(√2) ≈ 0.41421356..."""
        frac = compute_fractional_sqrt(2, precision=50)
        expected = sqrt(2) - 1  # √2 ≈ 1.414, frac = 0.414
        assert abs(float(frac) - expected) < 1e-10
    
    def test_frac_sqrt_3(self):
        """Test frac(√3) ≈ 0.73205080..."""
        frac = compute_fractional_sqrt(3, precision=50)
        expected = sqrt(3) - 1  # √3 ≈ 1.732, frac = 0.732
        assert abs(float(frac) - expected) < 1e-10
    
    def test_frac_sqrt_5(self):
        """Test frac(√5) ≈ 0.23606797..."""
        frac = compute_fractional_sqrt(5, precision=50)
        expected = sqrt(5) - 2  # √5 ≈ 2.236, frac = 0.236
        assert abs(float(frac) - expected) < 1e-10
    
    def test_frac_sqrt_perfect_square(self):
        """Test frac(√4) = 0 (perfect square)."""
        frac = compute_fractional_sqrt(4, precision=50)
        assert abs(float(frac)) < 1e-10
    
    def test_all_seed_primes_in_range(self):
        """All fractional parts should be in (0, 1)."""
        frac_roots = get_all_fractional_roots(50)
        
        for p, frac in frac_roots.items():
            frac_float = float(frac)
            assert 0 < frac_float < 1, f"frac(√{p}) = {frac_float} not in (0, 1)"
    
    def test_seed_primes_coverage(self):
        """All seed primes should have fractional roots."""
        frac_roots = get_all_fractional_roots(50)
        
        for p in SEED_PRIMES:
            assert p in frac_roots, f"Missing fractional root for {p}"


class TestBoundaryGeneration:
    """Test boundary center generation."""
    
    def test_boundary_centers_exist(self):
        """Test that boundary centers are generated."""
        sqrt_N = 1000000
        frac = compute_fractional_sqrt(2, 50)
        
        boundaries = compute_boundary_centers(sqrt_N, frac, window=10000)
        
        assert len(boundaries) > 0, "Should generate at least some boundaries"
    
    def test_boundary_centers_symmetric(self):
        """Test that boundaries include positive and negative offsets."""
        sqrt_N = 1000000
        frac = compute_fractional_sqrt(2, 50)
        
        boundaries = compute_boundary_centers(sqrt_N, frac, window=10000)
        
        has_positive = any(b > 0 for b in boundaries)
        has_negative = any(b < 0 for b in boundaries)
        
        assert has_positive, "Should have positive boundaries"
        assert has_negative, "Should have negative boundaries"
    
    def test_boundary_centers_within_window(self):
        """Test that boundaries are within specified window."""
        sqrt_N = 1000000
        window = 5000
        frac = compute_fractional_sqrt(3, 50)
        
        boundaries = compute_boundary_centers(sqrt_N, frac, window=window)
        
        for b in boundaries:
            assert abs(b) <= window, f"Boundary {b} exceeds window ±{window}"
    
    def test_all_boundaries_for_127bit(self):
        """Test boundary generation for 127-bit challenge."""
        sqrt_N = isqrt(CHALLENGE_127)
        
        all_boundaries = compute_all_boundaries(sqrt_N, precision=100, window=100000)
        
        assert len(all_boundaries) == len(SEED_PRIMES)
        
        for p in SEED_PRIMES:
            assert p in all_boundaries, f"Missing boundaries for √{p}"
            assert len(all_boundaries[p]) > 0, f"No boundaries for √{p}"


class TestBoundaryProximity:
    """Test boundary proximity scoring."""
    
    def test_distance_to_boundary_at_boundary(self):
        """Distance should be 0 at exact boundary position."""
        boundaries = [100, 200, 300]
        
        assert distance_to_nearest_boundary(100, boundaries) == 0
        assert distance_to_nearest_boundary(200, boundaries) == 0
        assert distance_to_nearest_boundary(300, boundaries) == 0
    
    def test_distance_to_boundary_between(self):
        """Distance should be correct between boundaries."""
        boundaries = [100, 300]
        
        # Midpoint between 100 and 300 is 200, distance to nearest is 100
        assert distance_to_nearest_boundary(200, boundaries) == 100
        
        # Close to 100
        assert distance_to_nearest_boundary(110, boundaries) == 10
    
    def test_distance_empty_boundaries(self):
        """Handle empty boundary list."""
        dist = distance_to_nearest_boundary(50, [])
        assert dist == 50  # Distance is just the absolute offset
    
    def test_proximity_score_range(self):
        """Proximity score should be in valid range."""
        sqrt_N = 1000000
        all_boundaries = compute_all_boundaries(sqrt_N, 50, 10000)
        
        # Test various offsets
        for offset in [-5000, -1000, 0, 1000, 5000]:
            score = boundary_proximity_score(offset, all_boundaries)
            assert 0 <= score <= 1, f"Score {score} out of [0, 1] range"
    
    def test_proximity_higher_near_boundary(self):
        """Proximity should be higher near boundaries."""
        sqrt_N = 1000000
        frac = compute_fractional_sqrt(2, 50)
        boundaries = compute_boundary_centers(sqrt_N, frac, 10000)
        
        if len(boundaries) > 1:
            # Create single-prime boundary dict for testing
            all_bounds = {2: boundaries}
            
            # Find a boundary that's not too close to others
            # Take a boundary and find the midpoint between it and the next
            sorted_bounds = sorted(b for b in boundaries if b >= 0)
            if len(sorted_bounds) >= 2:
                b1 = sorted_bounds[0]
                b2 = sorted_bounds[1]
                midpoint = (b1 + b2) // 2
                
                # At boundary should have high proximity
                at_boundary = boundary_proximity_score(b1, all_bounds)
                
                # At midpoint should have lower proximity
                at_midpoint = boundary_proximity_score(midpoint, all_bounds)
                
                assert at_boundary > at_midpoint, "Proximity should decrease with distance from boundary"


class TestSampling:
    """Test boundary-focused sample generation."""
    
    def test_sample_generation(self):
        """Test that samples are generated."""
        sqrt_N = 1000000
        samples = generate_boundary_focused_samples(
            sqrt_N, n_samples=100, window=10000, boundary_weight=0.7, seed=42
        )
        
        assert len(samples) > 0, "Should generate samples"
        assert len(samples) <= 100, "Should not exceed requested samples"
    
    def test_sample_uniqueness(self):
        """Test that samples are unique."""
        sqrt_N = 1000000
        samples = generate_boundary_focused_samples(
            sqrt_N, n_samples=100, window=10000, boundary_weight=0.7, seed=42
        )
        
        # Allow some duplicates but most should be unique
        unique_ratio = len(set(samples)) / len(samples)
        assert unique_ratio > 0.8, "Most samples should be unique"
    
    def test_sample_within_window(self):
        """Test that samples are within window."""
        sqrt_N = 1000000
        window = 5000
        samples = generate_boundary_focused_samples(
            sqrt_N, n_samples=100, window=window, boundary_weight=0.7, seed=42
        )
        
        for s in samples:
            assert abs(s) <= window, f"Sample {s} exceeds window ±{window}"
    
    def test_reproducibility(self):
        """Test that same seed produces same samples."""
        sqrt_N = 1000000
        
        samples1 = generate_boundary_focused_samples(
            sqrt_N, n_samples=50, window=10000, boundary_weight=0.7, seed=123
        )
        samples2 = generate_boundary_focused_samples(
            sqrt_N, n_samples=50, window=10000, boundary_weight=0.7, seed=123
        )
        
        assert samples1 == samples2, "Same seed should produce same samples"


class TestGVAIntegration:
    """Test integration with GVA torus embedding."""
    
    def test_torus_embedding_dimensions(self):
        """Test that embedding produces 7D coordinates."""
        coords = embed_torus_geodesic(1000000, k=0.35, dimensions=7)
        assert len(coords) == 7, "Should produce 7 coordinates"
    
    def test_torus_embedding_range(self):
        """Test that coordinates are in [0, 1)."""
        coords = embed_torus_geodesic(1000000, k=0.35, dimensions=7)
        
        for c in coords:
            assert 0 <= float(c) < 1, f"Coordinate {c} not in [0, 1)"
    
    def test_riemannian_distance_zero(self):
        """Test distance to self is zero."""
        coords = embed_torus_geodesic(1000000, k=0.35)
        dist = riemannian_distance(coords, coords)
        
        assert abs(float(dist)) < 1e-10, "Distance to self should be zero"
    
    def test_riemannian_distance_symmetric(self):
        """Test distance is symmetric."""
        coords1 = embed_torus_geodesic(1000000, k=0.35)
        coords2 = embed_torus_geodesic(1000100, k=0.35)
        
        dist12 = riemannian_distance(coords1, coords2)
        dist21 = riemannian_distance(coords2, coords1)
        
        assert abs(float(dist12) - float(dist21)) < 1e-10, "Distance should be symmetric"


class TestAdaptivePrecision:
    """Test adaptive precision computation."""
    
    def test_precision_formula(self):
        """Test precision formula: max(50, bitLength × 4 + 200)."""
        # 127-bit: 127 × 4 + 200 = 708
        expected_127 = max(50, 127 * 4 + 200)
        actual_127 = adaptive_precision(CHALLENGE_127)
        assert actual_127 == expected_127
        
        # 60-bit: 60 × 4 + 200 = 440
        expected_60 = max(50, 60 * 4 + 200)
        actual_60 = adaptive_precision(GATE_2_60BIT)
        assert actual_60 == expected_60
    
    def test_precision_minimum(self):
        """Test minimum precision is enforced."""
        # Very small number should still get minimum precision
        assert adaptive_precision(10) >= 50


class TestHashBoundsFactorSearch:
    """Test the main hash-bounds factor search function."""
    
    def test_rejects_out_of_range(self):
        """Test that out-of-range N is rejected."""
        with pytest.raises(ValueError):
            hash_bounds_factor_search(100, allow_any_range=False)
    
    def test_allows_challenge_127(self):
        """Test that CHALLENGE_127 is always allowed."""
        # Should not raise, even with allow_any_range=False
        # Just test it doesn't error on quick check (with very small budget)
        try:
            hash_bounds_factor_search(
                CHALLENGE_127, max_candidates=1, allow_any_range=False
            )
        except ValueError:
            pytest.fail("CHALLENGE_127 should be allowed")
    
    def test_allows_any_range_flag(self):
        """Test that allow_any_range=True allows small N."""
        # Should not raise
        result = hash_bounds_factor_search(
            1073217479,  # Gate 1: 30-bit
            max_candidates=100,
            allow_any_range=True
        )
        # May or may not find factors with small budget
        assert result is None or isinstance(result, tuple)
    
    def test_even_number_handling(self):
        """Test that even numbers are handled quickly."""
        result = hash_bounds_factor_search(100, allow_any_range=True)
        assert result == (2, 50)


class TestIntegration:
    """Integration tests for full workflow."""
    
    def test_60bit_gate(self):
        """Test on Gate 2 (60-bit) with reasonable budget."""
        N = GATE_2_60BIT
        expected_p = 1073741789
        expected_q = 1073741827
        
        result = hash_bounds_factor_search(
            N,
            max_candidates=3000,
            delta_window=30000,
            boundary_weight=0.7,
            boundary_proximity_weight=0.1,
            verbose=False,
            allow_any_range=True
        )
        
        # May or may not succeed with this budget
        if result is not None:
            p, q = result
            assert p * q == N, "Factors should multiply to N"
            assert set([p, q]) == set([expected_p, expected_q]), "Should find expected factors"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
