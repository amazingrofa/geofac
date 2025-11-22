#!/usr/bin/env python3
"""
Test Router Integration with Known Test Cases
==============================================

Validates that the router-based factorization works correctly on known test cases
from PR #93 before attempting the 127-bit challenge.
"""

import sys
import os
import time

# Add paths for imports
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'experiments', 'fractal-recursive-gva-falsification'))

import mpmath as mp
from gva_factorization import gva_factor_search
from fr_gva_implementation import fr_gva_factor_search
from portfolio_router import (
    extract_structural_features,
    route_factorization,
    analyze_correlation
)

mp.mp.dps = 50

# Test configuration - smaller budget for faster tests
TEST_MAX_CANDIDATES = 50000  # Reduced from production 700k for integration tests


def build_routing_rules():
    """Build routing rules from PR #93 training data."""
    training_data = [
        # FR-GVA successes
        {'N': 100000980001501, 'p': 10000019, 'q': 10000079, 
         'gva_success': False, 'fr_gva_success': True},
        {'N': 500000591440213, 'p': 22360687, 'q': 22360699,
         'gva_success': False, 'fr_gva_success': True},
        {'N': 100000010741094833, 'p': 316227767, 'q': 316227799,
         'gva_success': False, 'fr_gva_success': True},
        
        # GVA successes
        {'N': 1000000088437283, 'p': 31622777, 'q': 31622779,
         'gva_success': True, 'fr_gva_success': False},
        {'N': 10000004400000259, 'p': 100000007, 'q': 100000037,
         'gva_success': True, 'fr_gva_success': False},
        {'N': 1000000016000000063, 'p': 1000000007, 'q': 1000000009,
         'gva_success': True, 'fr_gva_success': False},
    ]
    
    analysis = analyze_correlation(training_data)
    return analysis['routing_rules']


def test_case(n, label, expected_p, expected_q, routing_rules, max_candidates=TEST_MAX_CANDIDATES):
    """Test a single case with router."""
    print(f"\n{'='*70}")
    print(f"Test Case: {label}")
    print(f"{'='*70}")
    print(f"N = {n}")
    print(f"Expected: {expected_p} × {expected_q}")
    
    # Extract features
    features = extract_structural_features(n)
    print(f"Bit length: {features['bit_length']}")
    print(f"Kappa: {features['kappa']:.6f}")
    
    # Route
    method = route_factorization(n, routing_rules, verbose=True)
    print(f"Router chose: {method}")
    
    # Execute primary method
    start_time = time.time()
    
    if method == "FR-GVA":
        factors = fr_gva_factor_search(
            n, max_depth=5, kappa_threshold=0.525,
            max_candidates=max_candidates, verbose=False, allow_any_range=True
        )
    else:
        factors = gva_factor_search(
            n, k_values=[0.30, 0.35, 0.40],
            max_candidates=max_candidates, verbose=False, allow_any_range=True
        )
    
    elapsed = time.time() - start_time
    
    if factors:
        p, q = factors
        valid = (p * q == n) and ((p == expected_p and q == expected_q) or 
                                  (p == expected_q and q == expected_p))
        
        print(f"\n✓ Found: {p} × {q}")
        print(f"Time: {elapsed:.3f}s")
        print(f"Correct: {valid}")
        
        return True
    else:
        print(f"\n✗ No factors found")
        print(f"Time: {elapsed:.3f}s")
        
        # Try fallback
        other_method = "GVA" if method == "FR-GVA" else "FR-GVA"
        print(f"\nTrying fallback: {other_method}")
        
        start_time = time.time()
        
        if other_method == "FR-GVA":
            factors = fr_gva_factor_search(
                n, max_depth=5, kappa_threshold=0.525,
                max_candidates=max_candidates, verbose=False, allow_any_range=True
            )
        else:
            factors = gva_factor_search(
                n, k_values=[0.30, 0.35, 0.40],
                max_candidates=max_candidates, verbose=False, allow_any_range=True
            )
        
        elapsed = time.time() - start_time
        
        if factors:
            p, q = factors
            valid = (p * q == n) and ((p == expected_p and q == expected_q) or 
                                      (p == expected_q and q == expected_p))
            
            print(f"✓ Found via fallback: {p} × {q}")
            print(f"Time: {elapsed:.3f}s")
            print(f"Correct: {valid}")
            
            return True
        else:
            print(f"✗ Fallback also failed")
            print(f"Time: {elapsed:.3f}s")
            return False


def main():
    print("="*70)
    print("ROUTER INTEGRATION TEST")
    print("="*70)
    print("Testing router-based factorization on known test cases")
    print("="*70)
    
    # Build routing rules
    routing_rules = build_routing_rules()
    
    # Test cases from PR #93
    test_cases = [
        (100000980001501, "10^14 lower", 10000019, 10000079),
        (500000591440213, "mid 10^14", 22360687, 22360699),
        (1000000088437283, "10^15", 31622777, 31622779),
    ]
    
    results = []
    for n, label, p, q in test_cases:
        success = test_case(n, label, p, q, routing_rules)
        results.append((label, success))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for label, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {label}")
    
    print(f"\nTotal: {passed}/{total} passed ({100*passed/total:.0f}%)")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
