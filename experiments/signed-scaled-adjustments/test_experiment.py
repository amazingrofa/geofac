"""
Tests for Signed or Scaled Adjustments Experiment

Validates that the experiment is reproducible and produces consistent results.
"""

import pytest
import json
from pathlib import Path
import sys

# Add experiment directory to path
experiment_dir = Path(__file__).parent
sys.path.insert(0, str(experiment_dir))

from experiment import (
    theta_prime,
    fermat_factorization_with_adjustment,
    generate_test_semiprimes,
    run_experiment,
)


def test_theta_prime_calculation():
    """Test that θ'(n,k) produces expected values."""
    # Test with known input
    result = theta_prime(1000, 0.3)
    
    # θ'(n,k) = φ · ((n mod φ) / φ)^k
    # Should produce a value in reasonable range [0, 2]
    assert 0 <= result <= 2, f"θ'(1000, 0.3) = {result} is out of expected range"


def test_fermat_control_balanced_semiprime():
    """Test that Fermat's method without adjustment factors balanced semiprimes immediately."""
    # Very small balanced semiprime where p and q are very close
    # p = 1009, q = 1013, n = 1009 * 1013 = 1022117
    # sqrt(1022117) ≈ 1011.0, (p+q)/2 = 1011
    n = 1022117
    p_expected = 1009
    q_expected = 1013
    
    p_found, q_found, iterations = fermat_factorization_with_adjustment(
        n, k_adjustment=None, max_iterations=10
    )
    
    assert p_found == p_expected, f"Expected p={p_expected}, got {p_found}"
    assert q_found == q_expected, f"Expected q={q_expected}, got {q_found}"
    assert iterations <= 2, f"Expected very few iterations for balanced semiprime, got {iterations}"


def test_fermat_positive_adjustment_fails():
    """Test that positive k-adjustment fails to factor (overshoots)."""
    # Small balanced semiprime
    n = 1022117
    
    p_found, q_found, iterations = fermat_factorization_with_adjustment(
        n, k_adjustment=0.3, adjustment_sign=1, adjustment_scale=1.0, max_iterations=100
    )
    
    # Should fail to find factors within iteration limit
    assert p_found is None, "Positive adjustment should fail"
    assert iterations == 100, f"Should hit iteration limit, got {iterations}"


def test_fermat_negative_adjustment_clamped():
    """Test that negative k-adjustment is clamped to control baseline."""
    # Small balanced semiprime
    n = 1022117
    p_expected = 1009
    q_expected = 1013
    
    p_found, q_found, iterations = fermat_factorization_with_adjustment(
        n, k_adjustment=0.3, adjustment_sign=-1, adjustment_scale=1.0, max_iterations=10
    )
    
    # Should succeed (clamped to control)
    assert p_found == p_expected, f"Expected p={p_expected}, got {p_found}"
    assert q_found == q_expected, f"Expected q={q_expected}, got {q_found}"
    assert iterations <= 2, "Negative adjustment should match control (few iterations)"


def test_semiprime_generation_reproducible():
    """Test that semiprime generation is reproducible with fixed seed."""
    semiprimes1 = generate_test_semiprimes(
        count=3,
        min_val=10**14,
        max_val=10**15,
        min_gap=100,
        max_gap=1000,
        seed=42,
    )
    
    semiprimes2 = generate_test_semiprimes(
        count=3,
        min_val=10**14,
        max_val=10**15,
        min_gap=100,
        max_gap=1000,
        seed=42,
    )
    
    # Should be identical
    assert len(semiprimes1) == len(semiprimes2), "Length mismatch"
    for sp1, sp2 in zip(semiprimes1, semiprimes2):
        assert sp1["n"] == sp2["n"], f"Semiprime mismatch: {sp1['n']} != {sp2['n']}"
        assert sp1["p"] == sp2["p"], f"Prime p mismatch"
        assert sp1["q"] == sp2["q"], f"Prime q mismatch"


def test_results_json_exists():
    """Test that results.json exists and has correct structure."""
    results_path = experiment_dir / "results.json"
    assert results_path.exists(), "results.json should exist"
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    # Validate structure
    assert "metadata" in data, "Missing metadata"
    assert "semiprimes" in data, "Missing semiprimes"
    assert "strategies" in data, "Missing strategies"
    assert "detailed_results" in data, "Missing detailed_results"
    assert "strategy_summaries" in data, "Missing strategy_summaries"
    
    # Validate metadata
    metadata = data["metadata"]
    assert metadata["seed"] == 42, "Seed should be 42"
    assert metadata["precision_dps"] == 50, "Precision should be 50"
    assert metadata["num_semiprimes"] == 10, "Should have 10 semiprimes"
    
    # Validate strategy summaries
    summaries = data["strategy_summaries"]
    assert len(summaries) == 7, "Should have 7 strategies"
    
    # Check control
    control = summaries[0]
    assert control["label"] == "Control (no adjustment)"
    assert control["success_rate"] == 1.0, "Control should have 100% success"
    assert control["avg_iterations_all"] == 0.0, "Control should average 0 iterations"
    
    # Check positive k=0.3
    positive = summaries[1]
    assert positive["label"] == "Positive k=0.3 (original)"
    assert positive["success_rate"] == 0.0, "Positive should have 0% success"
    assert positive["avg_iterations_all"] == 100000.0, "Positive should hit timeout"
    
    # Check negative k=0.3
    negative = summaries[2]
    assert negative["label"] == "Negative k=0.3 (corrective)"
    assert negative["success_rate"] == 1.0, "Negative should have 100% success"
    assert negative["avg_iterations_all"] == 0.0, "Negative should average 0 iterations (clamped)"


@pytest.mark.slow
def test_full_experiment_reproducibility():
    """
    Test that running the full experiment produces consistent results.
    
    WARNING: This is a slow test (~3 minutes). Run with `pytest -m slow`.
    """
    results = run_experiment(num_semiprimes=3, seed=99, max_iterations=10000)
    
    # Validate structure
    assert "metadata" in results
    assert "strategy_summaries" in results
    
    # Validate that positive adjustments fail
    summaries = results["strategy_summaries"]
    for summary in summaries:
        if summary["adjustment_sign"] == 1 and summary["k_value"] is not None:
            # Positive adjustments should fail
            assert summary["success_rate"] == 0.0, f"Positive strategy {summary['label']} should fail"
        elif summary["adjustment_sign"] == -1 and summary["k_value"] is not None:
            # Negative adjustments should match control
            assert summary["success_rate"] == 1.0, f"Negative strategy {summary['label']} should succeed"
            assert summary["avg_iterations_all"] == 0.0, f"Negative strategy should average 0 iterations"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
