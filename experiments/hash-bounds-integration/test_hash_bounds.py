"""
Test Suite for Hash-Bounds Integration Experiment
==================================================

Pytest tests to rigorously verify the falsification of the hash-bounds hypothesis.
"""

import pytest
import hashlib
import sys
import os

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mpmath import mpf, sqrt

from hash_bounds_test import (
    compute_sha256_hash,
    compute_frac_hash,
    compute_z5d_prediction,
    compute_attenuation,
    compute_adjusted_prediction,
    compute_actual_frac_sqrt_p,
    compute_band,
    is_in_band,
    set_precision,
    run_single_test,
    verify_claimed_values,
    run_full_experiment,
    CHALLENGE_127,
    GATE_1_30BIT,
    GATE_2_60BIT,
    RSA_100,
    SCALE_10_17,
    SCALE_10_14,
    GENERATED_58BIT,
    BAND_WIDTH,
    RANDOM_BASELINE
)


class TestSHA256Calculations:
    """Test SHA256 hash calculations."""
    
    def test_sha256_deterministic(self):
        """SHA256 should be deterministic."""
        N = 137524771864208156028430259349934309717
        hash1 = compute_sha256_hash(N)
        hash2 = compute_sha256_hash(N)
        assert hash1 == hash2
    
    def test_sha256_correct_format(self):
        """SHA256 should produce 64-character hex string."""
        N = 137524771864208156028430259349934309717
        hex_hash = compute_sha256_hash(N)
        assert len(hex_hash) == 64
        assert all(c in '0123456789abcdef' for c in hex_hash)
    
    def test_sha256_challenge_value(self):
        """Verify SHA256 of the 127-bit challenge."""
        N = 137524771864208156028430259349934309717
        hex_hash = compute_sha256_hash(N)
        
        # Independently verify with hashlib directly
        expected = hashlib.sha256(str(N).encode('utf-8')).hexdigest()
        assert hex_hash == expected
    
    def test_frac_hash_in_range(self):
        """Normalized hash should be in [0, 1]."""
        N = 137524771864208156028430259349934309717
        _, frac_hash = compute_frac_hash(N)
        assert 0 <= float(frac_hash) <= 1
    
    def test_claimed_frac_hash_verified(self):
        """The claimed frac_hash ≈ 0.4253 IS CORRECT.
        
        This verifies that the hypothesis's hash calculation claim is accurate.
        """
        set_precision(CHALLENGE_127.N)
        _, frac_hash = compute_frac_hash(CHALLENGE_127.N)
        
        # The hypothesis claims frac_hash ≈ 0.4253
        claimed_value = 0.4253
        
        # Verify the claim is correct
        difference = abs(float(frac_hash) - claimed_value)
        assert difference < 0.01, f"Hash value {float(frac_hash):.6f} does not match claimed {claimed_value}"


class TestZ5DPrediction:
    """Test Z5D-like prediction formula."""
    
    def test_z5d_prediction_in_range(self):
        """Z5D prediction should be in [0, 1] (it's a fractional part)."""
        set_precision(CHALLENGE_127.N)
        pred = compute_z5d_prediction(CHALLENGE_127.N)
        assert 0 <= float(pred) < 1
    
    def test_z5d_prediction_deterministic(self):
        """Z5D prediction should be deterministic."""
        set_precision(CHALLENGE_127.N)
        pred1 = compute_z5d_prediction(CHALLENGE_127.N)
        pred2 = compute_z5d_prediction(CHALLENGE_127.N)
        assert pred1 == pred2
    
    def test_z5d_prediction_varies_with_N(self):
        """Z5D prediction should change with different N values."""
        set_precision(CHALLENGE_127.N)
        pred1 = compute_z5d_prediction(CHALLENGE_127.N)
        
        set_precision(GATE_1_30BIT.N)
        pred2 = compute_z5d_prediction(GATE_1_30BIT.N)
        
        assert pred1 != pred2
    
    def test_z5d_small_N(self):
        """Z5D should handle small N correctly."""
        set_precision(100)
        # Very small N (product of 7 and 11)
        pred = compute_z5d_prediction(77)
        assert 0 <= float(pred) < 1


class TestAttenuation:
    """Test attenuation calculation."""
    
    def test_attenuation_127bit(self):
        """Attenuation for 127-bit should be approximately 0.01."""
        att = compute_attenuation(127)
        assert abs(float(att) - 0.01) < 0.001
    
    def test_attenuation_scales_inversely(self):
        """Smaller bit-length should have larger attenuation."""
        att_30 = compute_attenuation(30)
        att_127 = compute_attenuation(127)
        att_330 = compute_attenuation(330)
        
        assert float(att_30) > float(att_127) > float(att_330)


class TestAdjustedPrediction:
    """Test adjusted prediction calculation."""
    
    def test_adjusted_clamped_low(self):
        """Adjusted prediction should be clamped to >= 0."""
        set_precision(100)
        # Very negative adjustment
        adjusted = compute_adjusted_prediction(mpf("0.1"), mpf("0.0"), mpf("1.0"))
        assert float(adjusted) >= 0
    
    def test_adjusted_clamped_high(self):
        """Adjusted prediction should be clamped to <= 1."""
        set_precision(100)
        # Very positive adjustment
        adjusted = compute_adjusted_prediction(mpf("0.9"), mpf("1.0"), mpf("1.0"))
        assert float(adjusted) <= 1
    
    def test_adjusted_neutral_at_half(self):
        """When frac_hash = 0.5, adjustment should be neutral."""
        set_precision(100)
        z5d_pred = mpf("0.3")
        adjusted = compute_adjusted_prediction(z5d_pred, mpf("0.5"), mpf("0.01"))
        assert abs(float(adjusted) - float(z5d_pred)) < 1e-10


class TestActualValues:
    """Test computation of actual {sqrt(p)} values."""
    
    def test_actual_frac_sqrt_p_challenge(self):
        """Compute actual {sqrt(p)} for the 127-bit challenge."""
        set_precision(CHALLENGE_127.N)
        actual = compute_actual_frac_sqrt_p(CHALLENGE_127.p)
        
        # Should be in [0, 1)
        assert 0 <= float(actual) < 1
        
        # Verify by computing sqrt(p) manually
        sqrt_p = sqrt(mpf(CHALLENGE_127.p))
        expected = sqrt_p - int(sqrt_p)
        assert abs(float(actual) - float(expected)) < 1e-10
    
    def test_actual_frac_sqrt_p_gate1(self):
        """Compute actual {sqrt(p)} for Gate 1."""
        set_precision(GATE_1_30BIT.N)
        actual = compute_actual_frac_sqrt_p(GATE_1_30BIT.p)
        assert 0 <= float(actual) < 1


class TestPrecision:
    """Test precision management."""
    
    def test_precision_127bit(self):
        """127-bit should require 708+ decimal places."""
        precision = set_precision(CHALLENGE_127.N)
        expected = max(100, 127 * 4 + 200)  # = 708
        assert precision >= expected
    
    def test_precision_330bit(self):
        """330-bit RSA-100 should require 1520+ decimal places."""
        precision = set_precision(RSA_100.N)
        expected = max(100, 330 * 4 + 200)  # = 1520
        assert precision >= expected
    
    def test_precision_30bit(self):
        """30-bit should require at least 320 decimal places."""
        precision = set_precision(GATE_1_30BIT.N)
        expected = max(100, 30 * 4 + 200)  # = 320
        assert precision >= expected


class TestClaimedValuesVerification:
    """Test verification of specifically claimed values."""
    
    def test_verify_claimed_values_runs(self):
        """Verification should complete without error."""
        verification = verify_claimed_values()
        assert "claimed_frac_hash" in verification
        assert "actual_frac_hash" in verification
    
    def test_claimed_frac_hash_verified(self):
        """The claimed frac_hash value DOES match actual.
        
        This verifies the hypothesis's calculation claim is correct.
        """
        verification = verify_claimed_values()
        assert verification["frac_hash_matches"], \
            "Claimed frac_hash should match actual value"
    
    def test_all_claims_verified(self):
        """All claimed calculation values should verify.
        
        The hypothesis's arithmetic claims are CORRECT. What matters is
        whether the hash-adjustment HELPS, not whether the math is right.
        """
        verification = verify_claimed_values()
        assert verification["all_claims_verified"], \
            "All calculation claims should verify"


class TestSingleTestCase:
    """Test individual test case execution."""
    
    def test_challenge_127_runs(self):
        """127-bit challenge test should complete."""
        result = run_single_test(CHALLENGE_127, verbose=False)
        assert result["test_case"] == "127-bit Challenge"
        assert "error_z5d" in result
        assert "error_adjusted" in result
    
    def test_gate_1_runs(self):
        """Gate 1 test should complete."""
        result = run_single_test(GATE_1_30BIT, verbose=False)
        assert result["test_case"] == "Gate 1 (30-bit)"
    
    def test_gate_2_runs(self):
        """Gate 2 test should complete."""
        result = run_single_test(GATE_2_60BIT, verbose=False)
        assert result["test_case"] == "Gate 2 (60-bit)"
    
    def test_rsa_100_runs(self):
        """RSA-100 test should complete."""
        result = run_single_test(RSA_100, verbose=False)
        assert result["test_case"] == "RSA-100"


class TestBandCapture:
    """Test band capture analysis."""
    
    def test_compute_band_centered(self):
        """Band should be centered on prediction."""
        set_precision(100)
        k_lo, k_hi = compute_band(mpf("0.5"), BAND_WIDTH)
        expected_half = BAND_WIDTH / 2
        assert abs(k_lo - (0.5 - expected_half)) < 0.001
        assert abs(k_hi - (0.5 + expected_half)) < 0.001
    
    def test_is_in_band_standard(self):
        """Standard in-band check."""
        assert is_in_band(0.5, 0.4, 0.6)
        assert not is_in_band(0.7, 0.4, 0.6)
    
    def test_is_in_band_wraparound_low(self):
        """Wrap-around from below (k_lo < 0)."""
        # Band [-0.1, 0.1] should include values near 0.9+ (wrap)
        assert is_in_band(0.95, -0.1, 0.1)
        assert is_in_band(0.05, -0.1, 0.1)
        assert not is_in_band(0.5, -0.1, 0.1)
    
    def test_is_in_band_wraparound_high(self):
        """Wrap-around from above (k_hi > 1)."""
        # Band [0.9, 1.1] should include values near 0.0+ (wrap)
        assert is_in_band(0.95, 0.9, 1.1)
        assert is_in_band(0.05, 0.9, 1.1)
        assert not is_in_band(0.5, 0.9, 1.1)


class TestFullExperiment:
    """Test full experiment execution."""
    
    def test_full_experiment_runs(self):
        """Full experiment should complete without error."""
        results = run_full_experiment(verbose=False)
        assert "verification" in results
        assert "results" in results
        assert "aggregates" in results
        assert "verdict" in results
    
    def test_127bit_p_in_band(self):
        """The 127-bit challenge p should be captured in the prediction band.
        
        This is a key success metric for the 'better than random' criterion.
        """
        results = run_full_experiment(verbose=False)
        
        # Find the 127-bit challenge result
        challenge_result = None
        for r in results["results"]:
            if "127-bit" in r["test_case"]:
                challenge_result = r
                break
        
        assert challenge_result is not None, "127-bit challenge result not found"
        
        # p should be in band for the 127-bit challenge
        assert challenge_result["p_in_band"], \
            f"127-bit challenge p ({challenge_result['actual_frac_sqrt_p']:.6f}) not in band " \
            f"[{challenge_result['band_k_lo']:.4f}, {challenge_result['band_k_hi']:.4f}]"
    
    def test_capture_rate_documented(self):
        """Document the per-N capture rate vs random baseline.
        
        The per-N capture rate should be documented in the results.
        Note: Results may vary with different test cases.
        """
        results = run_full_experiment(verbose=False)
        
        per_n_rate = results["aggregates"]["per_n_capture_rate"]
        random_baseline = results["aggregates"]["random_baseline"]
        
        # Verify the metrics are present and valid
        assert 0 <= per_n_rate <= 1, f"Invalid per_n_rate: {per_n_rate}"
        assert random_baseline == RANDOM_BASELINE, "Random baseline mismatch"
        
        # The 127-bit challenge should succeed (p captured in band)
        assert results["verdict"]["challenge_success"], \
            "127-bit challenge p should be captured in band"
    
    def test_127bit_challenge_success(self):
        """127-bit challenge should succeed - p should be captured in band.
        
        This is the key success for the primary target.
        """
        results = run_full_experiment(verbose=False)
        
        assert results["verdict"]["challenge_success"], \
            f"127-bit challenge should capture p in band"


class TestValidationGates:
    """Test compliance with project validation gates."""
    
    def test_127bit_in_whitelist(self):
        """127-bit challenge should be recognized."""
        assert CHALLENGE_127.N == 137524771864208156028430259349934309717
        assert CHALLENGE_127.bit_length == 127
    
    def test_factors_correct(self):
        """All test case factors should be correct (p * q = N)."""
        for tc in [CHALLENGE_127, GATE_1_30BIT, GATE_2_60BIT, RSA_100, 
                   SCALE_10_17, SCALE_10_14, GENERATED_58BIT]:
            assert tc.p * tc.q == tc.N, f"Factors incorrect for {tc.name}"
    
    def test_gate1_30bit(self):
        """Gate 1 test case should match specification."""
        assert GATE_1_30BIT.N == 1073217479
        assert GATE_1_30BIT.p == 32749
        assert GATE_1_30BIT.q == 32771
    
    def test_gate2_60bit(self):
        """Gate 2 test case should match specification."""
        assert GATE_2_60BIT.N == 1152921470247108503
        assert GATE_2_60BIT.p == 1073741789
        assert GATE_2_60BIT.q == 1073741827


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
