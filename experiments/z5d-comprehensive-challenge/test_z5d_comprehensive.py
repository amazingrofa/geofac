"""
Test Suite for Z5D Comprehensive Challenge
===========================================

Pytest tests for all components.
"""

import pytest
import os
import sys
import json
from math import log, isqrt

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(__file__))

from z5d_api import (
    prime_counting_function, estimate_prime_index, predict_prime_band,
    local_prime_density, prioritize_delta_bands, adaptive_step_size
)
from calibrate_bands import (
    generate_balanced_semiprime, next_prime, miller_rabin
)
from z5d_pipeline import (
    generate_z5d_candidates, z5d_pipeline_search, is_admissible
)


# Test Z5D API
class TestZ5DAPI:
    """Test Z5D API adapter."""
    
    def test_prime_counting_basic(self):
        """Test π(x) approximation."""
        # π(10) = 4 (primes: 2, 3, 5, 7)
        # PNT approximation has larger error for small x
        assert prime_counting_function(10) >= 2
        assert prime_counting_function(10) <= 10
        
        # π(100) = 25
        assert prime_counting_function(100) >= 20
        assert prime_counting_function(100) <= 35
    
    def test_estimate_prime_index(self):
        """Test prime index estimation."""
        # p_10 = 29
        k = estimate_prime_index(29)
        assert 8 <= k <= 12
        
        # Large prime
        k = estimate_prime_index(1e10)
        assert k > 0
    
    def test_predict_prime_band(self):
        """Test band prediction."""
        sqrt_N = 10**10
        k_minus, k_plus = predict_prime_band(sqrt_N, epsilon=0.02)
        
        assert k_minus > 0
        assert k_plus > k_minus
        assert k_plus - k_minus > 1000  # Reasonable band width
    
    def test_local_density(self):
        """Test density calculation."""
        density = local_prime_density(1e10)
        expected = 1.0 / log(1e10)
        
        assert abs(density - expected) < 1e-6
    
    def test_prioritize_bands(self):
        """Test band prioritization."""
        sqrt_N = 10**10
        bands = prioritize_delta_bands(sqrt_N, delta_max=10000, num_bands=5)
        
        assert len(bands) == 5
        assert all('density' in b for b in bands)
        assert all('priority' in b for b in bands)
        
        # Check sorted by density
        densities = [b['density'] for b in bands]
        assert densities == sorted(densities, reverse=True)
    
    def test_adaptive_step_size(self):
        """Test adaptive stepping."""
        high_density = 0.1
        low_density = 0.01
        
        step_high = adaptive_step_size(high_density)
        step_low = adaptive_step_size(low_density)
        
        # Low density should have larger steps
        assert step_low >= step_high


# Test Calibration
class TestCalibration:
    """Test calibration components."""
    
    def test_miller_rabin(self):
        """Test primality testing."""
        assert miller_rabin(2)
        assert miller_rabin(3)
        assert miller_rabin(17)
        assert miller_rabin(97)
        assert not miller_rabin(4)
        assert not miller_rabin(100)
    
    def test_next_prime(self):
        """Test next prime finder."""
        assert next_prime(10) == 11
        assert next_prime(11) == 11
        assert next_prime(100) == 101
    
    def test_generate_balanced_semiprime(self):
        """Test semiprime generation."""
        N, p, q = generate_balanced_semiprime(60)
        
        # Verify N = p × q
        assert N == p * q
        
        # Verify p < q
        assert p < q
        
        # Verify both prime
        assert miller_rabin(p, k=15)
        assert miller_rabin(q, k=15)
        
        # Verify bit-length approximately 60
        assert 58 <= N.bit_length() <= 62
        
        # Verify balanced (both near √N within factor of 2)
        sqrt_N = isqrt(N)
        # For balanced semiprimes, p and q should each be within 2x of sqrt
        assert abs(p - sqrt_N) < sqrt_N * 2
        assert abs(q - sqrt_N) < sqrt_N * 2


# Test Pipeline
class TestPipeline:
    """Test Z5D pipeline."""
    
    def test_wheel_filter(self):
        """Test wheel admissibility."""
        # 1 is admissible
        assert is_admissible(1)
        
        # Even numbers not admissible (except 2)
        assert not is_admissible(4)
        assert not is_admissible(100)
        
        # Multiples of 3, 5, 7 not admissible
        assert not is_admissible(15)
        assert not is_admissible(21)
    
    def test_candidate_generation(self):
        """Test candidate stream."""
        N = 1073217479  # 30-bit test case
        sqrt_N = isqrt(N)
        
        candidates = list(generate_z5d_candidates(
            N, sqrt_N, delta_max=1000, num_bands=3, verbose=False
        ))
        
        # Should generate candidates
        assert len(candidates) > 0
        
        # Each should have required fields
        for c in candidates[:10]:
            assert 'candidate' in c
            assert 'delta' in c
            assert 'residue' in c
            assert 'density' in c
            assert 'amplitude' in c
            assert 'band_id' in c
    
    def test_small_semiprime_search(self):
        """Test pipeline on small semiprime."""
        # 30-bit Gate 1: 1,073,217,479 = 32,749 × 32,771
        N = 1073217479
        p_true = 32749
        q_true = 32771
        
        result = z5d_pipeline_search(
            N,
            max_candidates=10000,
            delta_max=5000,
            num_bands=3,
            verbose=False
        )
        
        # Should find factors
        assert result is not None
        p, q = result
        assert p * q == N
        assert {p, q} == {p_true, q_true}


# Test Integration
class TestIntegration:
    """Integration tests for full pipeline."""
    
    def test_parameters_schema(self):
        """Test parameter JSON schema."""
        # If challenge_params.json exists, validate it
        params_path = os.path.join(
            os.path.dirname(__file__),
            'challenge_params.json'
        )
        
        if os.path.exists(params_path):
            with open(params_path, 'r') as f:
                params = json.load(f)
            
            # Check required fields
            assert 'challenge' in params
            assert 'z5d_config' in params
            assert 'budget' in params
            
            assert 'N' in params['challenge']
            assert 'epsilon' in params['z5d_config']
            assert 'total_budget' in params['budget']
    
    def test_log_format(self):
        """Test run log format."""
        # If run_log.jsonl exists, validate it
        log_path = os.path.join(
            os.path.dirname(__file__),
            'run_log.jsonl'
        )
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                first_line = f.readline()
                log_entry = json.loads(first_line)
            
            # Should have type field
            assert 'type' in log_entry


# Validation gates
class TestValidationGates:
    """Test against project validation gates."""
    
    def test_gate1_30bit(self):
        """Gate 1: 30-bit quick check."""
        N = 1073217479  # = 32,749 × 32,771
        
        result = z5d_pipeline_search(
            N,
            max_candidates=10000,
            delta_max=5000,
            num_bands=3,
            verbose=False
        )
        
        assert result is not None, "Failed Gate 1: 30-bit quick check"
    
    def test_127bit_whitelist(self):
        """Test 127-bit challenge is recognized."""
        N = 137524771864208156028430259349934309717
        
        # Just verify it's in the allowed range
        assert N.bit_length() == 127
        assert N > 10**14  # Above 10^14 floor


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])
