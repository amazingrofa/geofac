#!/usr/bin/env python3
"""
Unit tests for Theil-Sen estimator implementation.

Validates correctness of core algorithm and robustness properties.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from theil_sen_estimator import theil_sen, ols_regression, evaluate_fit


def test_perfect_line():
    """Test on perfect line y = 2x + 3 (no noise)"""
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [5.0, 7.0, 9.0, 11.0, 13.0]  # y = 2x + 3
    
    m_ts, b_ts = theil_sen(x, y)
    m_ols, b_ols = ols_regression(x, y)
    
    # Both should recover exact parameters
    assert abs(m_ts - 2.0) < 1e-10, f"Theil-Sen slope error: {abs(m_ts - 2.0)}"
    assert abs(b_ts - 3.0) < 1e-10, f"Theil-Sen intercept error: {abs(b_ts - 3.0)}"
    assert abs(m_ols - 2.0) < 1e-10, f"OLS slope error: {abs(m_ols - 2.0)}"
    assert abs(b_ols - 3.0) < 1e-10, f"OLS intercept error: {abs(b_ols - 3.0)}"
    
    print("✓ Perfect line test passed")


def test_single_outlier():
    """Test robustness to single outlier"""
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    y = [3.0, 5.0, 7.0, 9.0, 11.0, 100.0]  # Last point is outlier
    
    # True line: y = 2x + 1 (ignoring outlier)
    m_ts, b_ts = theil_sen(x, y)
    m_ols, b_ols = ols_regression(x, y)
    
    # Theil-Sen should be close to true parameters
    ts_slope_error = abs(m_ts - 2.0)
    ols_slope_error = abs(m_ols - 2.0)
    
    # Theil-Sen should be much better than OLS
    assert ts_slope_error < 0.5, f"Theil-Sen not robust enough: error = {ts_slope_error}"
    assert ols_slope_error > 1.0, f"OLS should be worse: error = {ols_slope_error}"
    assert ts_slope_error < ols_slope_error / 3, "Theil-Sen should be 3× better than OLS"
    
    print(f"✓ Single outlier test passed (TS error: {ts_slope_error:.3f}, OLS error: {ols_slope_error:.3f})")


def test_edge_cases():
    """Test edge cases"""
    
    # Minimum points (n=2)
    x = [0.0, 1.0]
    y = [1.0, 3.0]
    m_ts, b_ts = theil_sen(x, y)
    assert abs(m_ts - 2.0) < 1e-10, "Failed on n=2"
    assert abs(b_ts - 1.0) < 1e-10, "Failed on n=2"
    
    # Negative slope
    x = [1.0, 2.0, 3.0]
    y = [10.0, 8.0, 6.0]  # y = -2x + 12
    m_ts, b_ts = theil_sen(x, y)
    assert abs(m_ts - (-2.0)) < 1e-10, "Failed on negative slope"
    assert abs(b_ts - 12.0) < 1e-10, "Failed on negative slope"
    
    print("✓ Edge cases test passed")


def test_evaluate_fit():
    """Test fit evaluation metrics"""
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [3.0, 5.0, 7.0, 9.0, 11.0]  # Perfect line
    
    fit = evaluate_fit(x, y, 2.0, 1.0)
    
    # Perfect fit should have zero residuals
    assert fit['mad'] < 1e-10, f"MAD should be zero: {fit['mad']}"
    assert fit['ssr'] < 1e-10, f"SSR should be zero: {fit['ssr']}"
    
    # All residuals should be near zero
    assert all(abs(r) < 1e-10 for r in fit['residuals']), "Residuals not zero"
    
    print("✓ Evaluate fit test passed")


def test_insufficient_data():
    """Test error handling for insufficient data"""
    try:
        theil_sen([1.0], [2.0])
        assert False, "Should raise ValueError for n=1"
    except ValueError as e:
        assert "at least 2 points" in str(e)
    
    try:
        theil_sen([1.0, 1.0], [2.0, 3.0])  # All x identical
        assert False, "Should raise ValueError for identical x"
    except ValueError as e:
        assert "identical" in str(e).lower()
    
    print("✓ Error handling test passed")


def run_all_tests():
    """Run all unit tests"""
    print("\n=== Running Theil-Sen Unit Tests ===\n")
    
    test_perfect_line()
    test_single_outlier()
    test_edge_cases()
    test_evaluate_fit()
    test_insufficient_data()
    
    print("\n=== All Tests Passed ===\n")


if __name__ == '__main__':
    run_all_tests()
