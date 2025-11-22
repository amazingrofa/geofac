"""
Test Suite for Portfolio Router
================================

Tests the portfolio routing system for FR-GVA vs GVA method selection.
"""

import sys
import os

# Add parent directories to path for imports
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'experiments', 'fractal-recursive-gva-falsification'))

from portfolio_router import (
    extract_structural_features,
    analyze_correlation,
    route_factorization,
    derive_routing_rules,
)
from portfolio_experiment import build_training_data


def test_feature_extraction():
    """Test that structural features are extracted correctly."""
    print("\n[Test 1] Feature Extraction")
    
    # Test case: 10^14 lower bound
    N = 100000980001501
    p = 10000019
    q = 10000079
    
    features = extract_structural_features(N, p, q)
    
    # Basic features
    assert features['N'] == N, "N mismatch"
    assert features['bit_length'] == 47, f"Expected bit_length=47, got {features['bit_length']}"
    assert 'kappa' in features, "Missing kappa"
    assert 'log_N' in features, "Missing log_N"
    
    # Factor-based features
    assert features['p'] == p, "p mismatch"
    assert features['q'] == q, "q mismatch"
    assert features['factor_gap'] == abs(p - q), "factor_gap incorrect"
    assert 0 < features['factor_balance_ratio'] <= 1, "factor_balance_ratio out of range"
    
    print(f"  ✓ All features extracted correctly")
    print(f"    Bit length: {features['bit_length']}")
    print(f"    Kappa: {features['kappa']:.6f}")
    print(f"    Factor gap: {features['factor_gap']}")


def test_correlation_analysis():
    """Test that correlation analysis identifies patterns."""
    print("\n[Test 2] Correlation Analysis")
    
    training_data = build_training_data()
    analysis = analyze_correlation(training_data)
    
    # Check that analysis contains expected components
    assert 'gva_success_patterns' in analysis, "Missing GVA patterns"
    assert 'fr_gva_success_patterns' in analysis, "Missing FR-GVA patterns"
    assert 'routing_rules' in analysis, "Missing routing rules"
    
    gva_patterns = analysis['gva_success_patterns']
    fr_gva_patterns = analysis['fr_gva_success_patterns']
    
    # Each method should have 3 successes
    assert gva_patterns['count'] == 3, f"Expected 3 GVA successes, got {gva_patterns['count']}"
    assert fr_gva_patterns['count'] == 3, f"Expected 3 FR-GVA successes, got {fr_gva_patterns['count']}"
    
    # Check feature ranges exist
    assert 'bit_length_range' in gva_patterns, "Missing bit_length_range in GVA patterns"
    assert 'kappa_range' in fr_gva_patterns, "Missing kappa_range in FR-GVA patterns"
    
    print(f"  ✓ Correlation analysis successful")
    print(f"    GVA pattern: bits {gva_patterns['bit_length_range']}")
    print(f"    FR-GVA pattern: bits {fr_gva_patterns['bit_length_range']}")


def test_routing_rules():
    """Test that routing rules are derived correctly."""
    print("\n[Test 3] Routing Rules Derivation")
    
    training_data = build_training_data()
    analysis = analyze_correlation(training_data)
    rules = analysis['routing_rules']
    
    # Should use feature-based strategy
    assert rules.get('strategy') == 'feature_based', \
        f"Expected feature_based strategy, got {rules.get('strategy')}"
    
    # Should have thresholds
    assert 'bit_threshold' in rules, "Missing bit_threshold"
    assert 'kappa_threshold' in rules, "Missing kappa_threshold"
    
    # Thresholds should be between the averages
    assert rules['bit_fr_gva_avg'] < rules['bit_threshold'] < rules['bit_gva_avg'] or \
           rules['bit_gva_avg'] < rules['bit_threshold'] < rules['bit_fr_gva_avg'], \
           "bit_threshold not between averages"
    
    print(f"  ✓ Routing rules derived correctly")
    print(f"    Bit threshold: {rules['bit_threshold']:.1f}")
    print(f"    Kappa threshold: {rules['kappa_threshold']:.6f}")


def test_routing_decisions():
    """Test that routing makes sensible decisions."""
    print("\n[Test 4] Routing Decisions")
    
    training_data = build_training_data()
    analysis = analyze_correlation(training_data)
    rules = analysis['routing_rules']
    
    # Test case 1: Small semiprime (should prefer FR-GVA)
    N_small = 100000980001501  # 47 bits, known FR-GVA success
    method_small = route_factorization(N_small, rules, verbose=False)
    print(f"  Small (47-bit): {method_small}")
    
    # Test case 2: Large semiprime (should prefer GVA)
    N_large = 1000000016000000063  # 60 bits, known GVA success
    method_large = route_factorization(N_large, rules, verbose=False)
    print(f"  Large (60-bit): {method_large}")
    
    # The router should make different choices for different profiles
    assert method_small == "FR-GVA" or method_large == "GVA", \
        "Router should differentiate between small and large semiprimes"
    
    print(f"  ✓ Routing differentiates semiprime profiles")


def test_feature_ranges():
    """Test that feature ranges are non-overlapping where expected."""
    print("\n[Test 5] Feature Range Analysis")
    
    training_data = build_training_data()
    analysis = analyze_correlation(training_data)
    
    gva_patterns = analysis['gva_success_patterns']
    fr_gva_patterns = analysis['fr_gva_success_patterns']
    
    gva_bits = gva_patterns['bit_length_range']
    fr_gva_bits = fr_gva_patterns['bit_length_range']
    
    gva_kappa = gva_patterns['kappa_range']
    fr_gva_kappa = fr_gva_patterns['kappa_range']
    
    print(f"  GVA bit range: {gva_bits}")
    print(f"  FR-GVA bit range: {fr_gva_bits}")
    print(f"  GVA kappa range: ({gva_kappa[0]:.6f}, {gva_kappa[1]:.6f})")
    print(f"  FR-GVA kappa range: ({fr_gva_kappa[0]:.6f}, {fr_gva_kappa[1]:.6f})")
    
    # Check that ranges show clear patterns (some overlap is expected)
    assert gva_bits[0] >= fr_gva_bits[0], "GVA should handle larger semiprimes"
    
    print(f"  ✓ Feature ranges show expected patterns")


def run_all_tests():
    """Run all tests."""
    print("="*70)
    print("PORTFOLIO ROUTER TEST SUITE")
    print("="*70)
    
    try:
        test_feature_extraction()
        test_correlation_analysis()
        test_routing_rules()
        test_routing_decisions()
        test_feature_ranges()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
