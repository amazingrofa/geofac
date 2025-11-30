"""
Tests for Hash-Bounds Falsification Experiment

Validates that the experiment is reproducible and produces consistent results.
"""

import pytest
from pathlib import Path
import sys

# Add experiment directory to path
experiment_dir = Path(__file__).parent
sys.path.insert(0, str(experiment_dir))

from hash_bounds_test import (
    compute_adaptive_precision,
    fractional_part,
    theta_prime,
    compute_mock_z5d_prediction,
    compute_hash_bounds,
    is_in_bounds,
    analyze_validation_gate,
    run_experiment,
)

import mpmath as mp


class TestPrecisionCalculation:
    """Tests for adaptive precision calculation."""

    def test_30_bit_precision(self):
        """Test precision for 30-bit number."""
        n = 1073217479  # Gate 1
        precision = compute_adaptive_precision(n)
        # 30 × 4 + 200 = 320
        assert precision >= 320, f"Expected >= 320, got {precision}"

    def test_60_bit_precision(self):
        """Test precision for 60-bit number."""
        n = 1152921470247108503  # Gate 2
        precision = compute_adaptive_precision(n)
        # 60 × 4 + 200 = 440
        assert precision >= 440, f"Expected >= 440, got {precision}"

    def test_127_bit_precision(self):
        """Test precision for 127-bit number."""
        n = 137524771864208156028430259349934309717  # Gate 3
        precision = compute_adaptive_precision(n)
        # 127 × 4 + 200 = 708
        assert precision >= 708, f"Expected >= 708, got {precision}"


class TestFractionalPart:
    """Tests for fractional part computation."""

    def test_integer_has_zero_fractional(self):
        """Test that integers have zero fractional part."""
        mp.dps = 50
        result = fractional_part(mp.mpf(5))
        assert abs(float(result)) < 1e-40, f"Expected ~0, got {result}"

    def test_half_fractional(self):
        """Test fractional part of x.5."""
        mp.dps = 50
        result = fractional_part(mp.mpf("3.5"))
        assert abs(float(result) - 0.5) < 1e-40, f"Expected 0.5, got {result}"

    def test_fractional_part_in_range(self):
        """Test fractional part is always in [0, 1)."""
        mp.dps = 50
        test_values = [1.234, 5.999, 100.001, 0.123]
        for val in test_values:
            result = fractional_part(mp.mpf(val))
            assert 0 <= float(result) < 1, f"Fractional part of {val} = {result} not in [0,1)"


class TestThetaPrime:
    """Tests for θ'(n,k) function."""

    def test_theta_prime_positive(self):
        """Test that θ'(n,k) returns positive value."""
        mp.dps = 50
        result = theta_prime(1000, 0.3)
        assert result > 0, f"θ'(1000, 0.3) should be positive, got {result}"

    def test_theta_prime_bounded(self):
        """Test that θ'(n,k) is reasonably bounded."""
        mp.dps = 50
        result = theta_prime(1000, 0.3)
        # θ'(n,k) = φ·((n mod φ)/φ)^k should be < 2φ ≈ 3.24
        assert result < 4, f"θ'(1000, 0.3) = {result} is unexpectedly large"

    def test_theta_prime_consistency(self):
        """Test that θ'(n,k) is deterministic."""
        mp.dps = 50
        result1 = theta_prime(12345, 0.3)
        result2 = theta_prime(12345, 0.3)
        assert result1 == result2, "θ' should be deterministic"


class TestMockZ5DPrediction:
    """Tests for mock Z5D prediction."""

    def test_z5d_returns_fractional(self):
        """Test that Z5D prediction is in [0, 1)."""
        mp.dps = 50
        p = 10508623501177419659  # CHALLENGE_127 smaller factor
        result = compute_mock_z5d_prediction(p)
        assert 0 <= float(result) < 1, f"Z5D prediction {result} not in [0,1)"

    def test_z5d_for_small_prime(self):
        """Test Z5D prediction for small prime."""
        mp.dps = 50
        p = 32749  # Gate 1 factor
        result = compute_mock_z5d_prediction(p)
        assert 0 <= float(result) < 1, f"Z5D prediction {result} not in [0,1)"


class TestHashBounds:
    """Tests for hash-bounds computation."""

    def test_bounds_width(self):
        """Test that bounds have correct width."""
        mp.dps = 50
        center = mp.mpf(0.5)
        width = 0.155
        lower, upper = compute_hash_bounds(center, width)
        actual_width = float(upper - lower)
        assert abs(actual_width - width) < 1e-10, f"Expected width {width}, got {actual_width}"

    def test_bounds_centered(self):
        """Test that bounds are centered on prediction."""
        mp.dps = 50
        center = mp.mpf(0.5)
        lower, upper = compute_hash_bounds(center, 0.155)
        midpoint = float((lower + upper) / 2)
        assert abs(midpoint - 0.5) < 1e-10, f"Bounds not centered: midpoint = {midpoint}"


class TestInBounds:
    """Tests for bounds checking."""

    def test_value_in_normal_bounds(self):
        """Test value within normal bounds."""
        mp.dps = 50
        assert is_in_bounds(mp.mpf(0.5), mp.mpf(0.4), mp.mpf(0.6)) is True

    def test_value_outside_normal_bounds(self):
        """Test value outside normal bounds."""
        mp.dps = 50
        assert is_in_bounds(mp.mpf(0.7), mp.mpf(0.4), mp.mpf(0.6)) is False

    def test_value_at_lower_boundary(self):
        """Test value at lower boundary."""
        mp.dps = 50
        assert is_in_bounds(mp.mpf(0.4), mp.mpf(0.4), mp.mpf(0.6)) is True

    def test_value_at_upper_boundary(self):
        """Test value at upper boundary."""
        mp.dps = 50
        assert is_in_bounds(mp.mpf(0.6), mp.mpf(0.4), mp.mpf(0.6)) is True


class TestValidationGates:
    """Tests for validation gate analysis."""

    def test_gate1_analysis(self):
        """Test Gate 1 (30-bit) analysis."""
        result = analyze_validation_gate(
            gate_name="Gate 1 (30-bit)",
            n=1073217479,
            p=32749,
            q=32771,
        )
        
        # Verify structure
        assert "gate_name" in result
        assert "actual_frac_p" in result
        assert "z5d_pred_p" in result
        assert "p_in_bounds" in result
        assert "error_p" in result
        
        # Verify values are reasonable
        assert 0 <= result["actual_frac_p"] < 1
        assert 0 <= result["z5d_pred_p"] < 1
        assert result["error_p"] >= 0

    def test_gate2_analysis(self):
        """Test Gate 2 (60-bit) analysis."""
        result = analyze_validation_gate(
            gate_name="Gate 2 (60-bit)",
            n=1152921470247108503,
            p=1073741789,
            q=1073741827,
        )
        
        assert "gate_name" in result
        assert result["precision_dps"] >= 440  # 60 × 4 + 200

    def test_gate3_analysis(self):
        """Test Gate 3 (127-bit CHALLENGE) analysis."""
        result = analyze_validation_gate(
            gate_name="Gate 3 (127-bit)",
            n=137524771864208156028430259349934309717,
            p=10508623501177419659,
            q=13086849276577416863,
        )
        
        assert "gate_name" in result
        assert result["precision_dps"] >= 708  # 127 × 4 + 200
        
        # Verify specific CHALLENGE_127 values from hypothesis
        # Actual {√p} ≈ 0.228200298... for p=10508623501177419659
        actual_frac_p = result["actual_frac_p"]
        assert abs(actual_frac_p - 0.228200298) < 0.001, \
            f"Expected {'{'}√p{'}'} ≈ 0.228, got {actual_frac_p}"


class TestExperiment:
    """Tests for full experiment execution."""

    def test_experiment_runs(self):
        """Test that experiment runs without errors."""
        results = run_experiment(seed=42)
        
        assert "metadata" in results
        assert "gate_results" in results
        assert "summary" in results

    def test_experiment_has_three_gates(self):
        """Test that experiment analyzes all three gates."""
        results = run_experiment(seed=42)
        
        assert len(results["gate_results"]) == 3

    def test_experiment_produces_verdict(self):
        """Test that experiment produces a verdict."""
        results = run_experiment(seed=42)
        
        verdict = results["summary"]["verdict"]
        assert verdict in ["FALSIFIED", "SUPPORTED", "INCONCLUSIVE"], \
            f"Unexpected verdict: {verdict}"

    def test_experiment_reproducibility(self):
        """Test that experiment produces consistent results."""
        results1 = run_experiment(seed=42)
        results2 = run_experiment(seed=42)
        
        # Key metrics should match
        assert results1["summary"]["coverage_rate"] == results2["summary"]["coverage_rate"]
        assert results1["summary"]["verdict"] == results2["summary"]["verdict"]


class TestChallengeNumberVerification:
    """Tests to verify CHALLENGE_127 specific claims from hypothesis."""

    def test_challenge_127_sqrt_p_fractional(self):
        """Verify {√p} ≈ 0.228200298 for p=10508623501177419659."""
        p = 10508623501177419659
        precision = compute_adaptive_precision(p)
        mp.dps = precision
        
        sqrt_p = mp.sqrt(mp.mpf(p))
        frac_p = fractional_part(sqrt_p)
        
        # Hypothesis claims {√p} ≈ 0.228200298
        expected = 0.228200298
        assert abs(float(frac_p) - expected) < 0.0001, \
            f"Expected {'{'}√p{'}'} ≈ {expected}, got {float(frac_p)}"

    def test_challenge_127_z5d_prediction_differs(self):
        """Test that Z5D prediction differs significantly from actual {√p}."""
        p = 10508623501177419659
        precision = compute_adaptive_precision(p)
        mp.dps = precision
        
        sqrt_p = mp.sqrt(mp.mpf(p))
        actual_frac = float(fractional_part(sqrt_p))
        
        z5d_pred = float(compute_mock_z5d_prediction(p))
        
        # The hypothesis claims Z5D predicts ~0.878 vs actual ~0.228
        # This is a massive discrepancy
        error = abs(actual_frac - z5d_pred)
        
        # Error should be substantial (hypothesis claims ~0.65 difference)
        assert error > 0.5, \
            f"Expected large error, got {error}: actual={actual_frac}, pred={z5d_pred}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
