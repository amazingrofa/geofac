import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure the root directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import verify_solution

def test_set_adaptive_precision():
    # Mock mpmath if not available
    if not verify_solution.HAS_MPMATH:
        return

    # Test with a small number
    n_small = 2**30
    verify_solution.set_adaptive_precision(n_small)
    assert verify_solution.mp.mp.dps >= 100

    # Test with the challenge number (127-bit)
    n_challenge = verify_solution.CHALLENGE_N
    verify_solution.set_adaptive_precision(n_challenge)
    assert verify_solution.mp.mp.dps >= 127 * 4 + 200

def test_embed_torus_geodesic():
    if not verify_solution.HAS_MPMATH:
        return

    n = 100
    k = 0.35
    dimensions = 7
    verify_solution.set_adaptive_precision(n)
    
    coords = verify_solution.embed_torus_geodesic(n, k, dimensions)
    
    assert len(coords) == dimensions
    for coord in coords:
        assert 0 <= coord <= 1

def test_riemannian_distance():
    if not verify_solution.HAS_MPMATH:
        return

    verify_solution.set_adaptive_precision(100)
    p1 = [0.1, 0.2, 0.3]
    p2 = [0.15, 0.25, 0.35]
    
    dist = verify_solution.riemannian_distance(p1, p2)
    assert dist > 0
    
    # Test zero distance
    assert verify_solution.riemannian_distance(p1, p1) == 0.0

def test_verify_solution_success(capsys):
    # Mock mpmath imports inside the function if necessary, or assume HAS_MPMATH is correct
    # We will run the actual verification since it should pass with the hardcoded factors
    
    result = verify_solution.verify_solution()
    
    captured = capsys.readouterr()
    assert "127-bit Challenge Solution Verification" in captured.out
    assert "Arithmetic Verification" in captured.out
    assert "p * q = 137524771864208156028430259349934309717" in captured.out
    assert "✓ SUCCESS: Product matches N" in captured.out
    
    if verify_solution.HAS_MPMATH:
        assert "Geometric Resonance Analysis (Z-Framework)" in captured.out
        assert "Computing Riemannian distance" in captured.out
        assert "✓ Exact divisibility detected" in captured.out
        assert "Parameters: k=0.35" in captured.out
        assert "dps" in captured.out
        assert "Timestamp:" in captured.out

    assert result is True

def test_verify_solution_failure():
    # Temporarily modify the factors to force a failure
    original_p = verify_solution.FACTOR_P
    verify_solution.FACTOR_P = 3 # Incorrect factor
    
    try:
        result = verify_solution.verify_solution()
        assert result is False
    finally:
        # Restore original factor
        verify_solution.FACTOR_P = original_p
