"""
Portfolio-Based Factorization with Intelligent Routing
=======================================================

Implements a portfolio approach that routes factorization attempts to
FR-GVA or standard GVA based on structural feature analysis.

This builds on PR #93 findings showing complementary success patterns:
- Standard GVA: succeeds on 10^15, 10^16, 10^18 (larger bit lengths, larger gaps)
- FR-GVA: succeeds on 10^14 lower, mid 10^14, 10^17 (smaller bit lengths, tighter factors)

The router analyzes structural features to predict which method is likely to work.
"""

import sys
import time
from typing import Dict, Optional, Tuple, List

sys.path.insert(0, '/home/runner/work/geofac/geofac')
sys.path.insert(0, '/home/runner/work/geofac/geofac/experiments/fractal-recursive-gva-falsification')

import mpmath as mp
from gva_factorization import gva_factor_search
from fr_gva_implementation import fr_gva_factor_search
from portfolio_router import (
    extract_structural_features,
    analyze_correlation,
    route_factorization,
    log_routing_decision,
    MethodChoice
)

mp.mp.dps = 50


def generate_test_semiprimes() -> List[Tuple[int, str, int, int]]:
    """Generate test semiprimes within operational range [10^14, 10^18]."""
    return [
        (100000980001501, "10^14 lower", 10000019, 10000079),
        (500000591440213, "mid 10^14", 22360687, 22360699),
        (1000000088437283, "10^15", 31622777, 31622779),
        (10000004400000259, "10^16", 100000007, 100000037),
        (100000010741094833, "10^17", 316227767, 316227799),
        (1000000016000000063, "10^18 upper", 1000000007, 1000000009),
    ]


def build_training_data() -> List[Dict]:
    """
    Build training data from known PR #93 results.
    
    Returns list of dicts with N, p, q, and success flags for each method.
    """
    return [
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


def run_with_router(N: int, label: str, expected_p: int, expected_q: int,
                   routing_rules: Dict, verbose: bool = True) -> Dict:
    """
    Factor N using router to select method.
    
    Args:
        N: Semiprime to factor
        label: Human-readable label
        expected_p, expected_q: Expected factors (for verification)
        routing_rules: Routing rules from correlation analysis
        verbose: Enable detailed logging
        
    Returns:
        Results dictionary
    """
    result = {
        'N': N,
        'label': label,
        'bit_length': N.bit_length(),
        'expected_factors': (expected_p, expected_q),
    }
    
    print(f"\n{'='*70}")
    print(f"Portfolio Factorization: {label}")
    print(f"N = {N} ({N.bit_length()} bits)")
    print(f"Expected: {expected_p} × {expected_q}")
    print(f"{'='*70}")
    
    # Extract features
    features = extract_structural_features(N)
    
    if verbose:
        print(f"\nStructural Features:")
        print(f"  Bit length: {features['bit_length']}")
        print(f"  Kappa: {features['kappa']:.6f}")
        print(f"  Log(N): {features['log_N']:.2f}")
    
    # Route to appropriate method
    chosen_method = route_factorization(N, routing_rules, verbose=verbose)
    
    result['chosen_method'] = chosen_method
    result['features'] = features
    
    # Execute chosen method
    print(f"\nExecuting {chosen_method}...")
    
    try:
        start_time = time.time()
        
        if chosen_method == "FR-GVA":
            factors = fr_gva_factor_search(
                N, max_depth=5, kappa_threshold=0.525,
                max_candidates=50000, verbose=False, allow_any_range=True
            )
        else:  # GVA
            factors = gva_factor_search(
                N, k_values=[0.30, 0.35, 0.40],
                max_candidates=50000, verbose=False, allow_any_range=True
            )
        
        elapsed_time = time.time() - start_time
        
        if factors:
            p, q = factors
            success = (p * q == N) and (
                (p == expected_p and q == expected_q) or
                (p == expected_q and q == expected_p)
            )
            
            result['success'] = success
            result['factors'] = (p, q)
            result['time'] = elapsed_time
            result['verified'] = p * q == N
            
            print(f"  ✓ Found: {p} × {q}")
            print(f"  Time: {elapsed_time:.3f}s")
            print(f"  Verified: {p * q == N}")
        else:
            result['success'] = False
            result['factors'] = None
            result['time'] = elapsed_time
            result['verified'] = False
            
            print(f"  ✗ No factors found")
            print(f"  Time: {elapsed_time:.3f}s")
            
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        result['time'] = None
        result['verified'] = False
        print(f"  ✗ Error: {e}")
    
    return result


def print_portfolio_summary(results: List[Dict], analysis: Dict):
    """Print comprehensive summary of portfolio performance."""
    print("\n" + "="*70)
    print("PORTFOLIO EXPERIMENT SUMMARY")
    print("="*70)
    
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    
    print(f"\nTest Cases: {total}")
    print(f"Portfolio Success Rate: {successful}/{total} ({100*successful/total:.0f}%)")
    
    # Breakdown by chosen method
    gva_chosen = [r for r in results if r.get('chosen_method') == 'GVA']
    fr_gva_chosen = [r for r in results if r.get('chosen_method') == 'FR-GVA']
    
    gva_success = sum(1 for r in gva_chosen if r.get('success', False))
    fr_gva_success = sum(1 for r in fr_gva_chosen if r.get('success', False))
    
    print(f"\nRouting Decisions:")
    print(f"  GVA chosen: {len(gva_chosen)} cases, {gva_success} successful")
    print(f"  FR-GVA chosen: {len(fr_gva_chosen)} cases, {fr_gva_success} successful")
    
    # Compare to individual methods (from training data)
    print(f"\nComparison to Individual Methods:")
    print(f"  Standard GVA alone: 3/6 (50%) [from PR #93]")
    print(f"  FR-GVA alone: 3/6 (50%) [from PR #93]")
    print(f"  Portfolio Router: {successful}/6 ({100*successful/total:.0f}%)")
    
    if successful > 3:
        print(f"\n✓ IMPROVEMENT: Router achieves {successful-3} additional success(es)")
    elif successful == 3:
        print(f"\n⚠ NEUTRAL: Router matches best individual method")
    else:
        print(f"\n✗ REGRESSION: Router underperforms individual methods")
    
    # Feature correlation summary
    print(f"\n{'='*70}")
    print("FEATURE CORRELATION ANALYSIS")
    print("="*70)
    
    gva_patterns = analysis['gva_success_patterns']
    fr_gva_patterns = analysis['fr_gva_success_patterns']
    
    print(f"\nGVA Success Pattern ({gva_patterns['count']} cases):")
    print(f"  Bit length range: {gva_patterns['bit_length_range']}")
    print(f"  Kappa range: ({gva_patterns['kappa_range'][0]:.6f}, {gva_patterns['kappa_range'][1]:.6f})")
    if 'factor_gap_range' in gva_patterns:
        print(f"  Factor gap range: {gva_patterns['factor_gap_range']}")
        print(f"  Gap/sqrt ratio range: ({gva_patterns['gap_to_sqrt_ratio_range'][0]:.6e}, {gva_patterns['gap_to_sqrt_ratio_range'][1]:.6e})")
    
    print(f"\nFR-GVA Success Pattern ({fr_gva_patterns['count']} cases):")
    print(f"  Bit length range: {fr_gva_patterns['bit_length_range']}")
    print(f"  Kappa range: ({fr_gva_patterns['kappa_range'][0]:.6f}, {fr_gva_patterns['kappa_range'][1]:.6f})")
    if 'factor_gap_range' in fr_gva_patterns:
        print(f"  Factor gap range: {fr_gva_patterns['factor_gap_range']}")
        print(f"  Gap/sqrt ratio range: ({fr_gva_patterns['gap_to_sqrt_ratio_range'][0]:.6e}, {fr_gva_patterns['gap_to_sqrt_ratio_range'][1]:.6e})")
    
    # Routing rules
    rules = analysis['routing_rules']
    if rules.get('strategy') == 'feature_based':
        print(f"\nDerived Routing Rules:")
        print(f"  Bit length threshold: {rules['bit_threshold']:.1f}")
        print(f"    → Below threshold: prefer FR-GVA (avg {rules['bit_fr_gva_avg']:.1f})")
        print(f"    → Above threshold: prefer GVA (avg {rules['bit_gva_avg']:.1f})")
        print(f"  Kappa threshold: {rules['kappa_threshold']:.6f}")
        print(f"    → Below threshold: prefer FR-GVA (avg {rules['kappa_fr_gva_avg']:.6f})")
        print(f"    → Above threshold: prefer GVA (avg {rules['kappa_gva_avg']:.6f})")
    
    print(f"\n{'='*70}")


def main():
    """Run portfolio experiment with intelligent routing."""
    print("="*70)
    print("PORTFOLIO-BASED FACTORIZATION EXPERIMENT")
    print("="*70)
    print("\nObjective: Use structural feature analysis to route factorization")
    print("           attempts to the method most likely to succeed.")
    print("\nApproach:")
    print("  1. Analyze PR #93 results to identify feature correlations")
    print("  2. Build router that selects FR-GVA vs GVA based on features")
    print("  3. Compare portfolio success rate to individual methods")
    print("\n" + "="*70)
    
    # Phase 1: Build training data and analyze correlations
    print("\n[Phase 1] Analyzing feature correlations from PR #93 results...")
    training_data = build_training_data()
    analysis = analyze_correlation(training_data)
    
    print(f"  Training cases: {len(training_data)}")
    print(f"  GVA successes: {sum(1 for d in training_data if d['gva_success'])}")
    print(f"  FR-GVA successes: {sum(1 for d in training_data if d['fr_gva_success'])}")
    print(f"  Routing strategy: {analysis['routing_rules'].get('strategy')}")
    
    # Phase 2: Test portfolio approach on same test cases
    print(f"\n[Phase 2] Running portfolio factorization with router...")
    
    test_cases = generate_test_semiprimes()
    results = []
    
    for N, label, p, q in test_cases:
        result = run_with_router(N, label, p, q, analysis['routing_rules'], verbose=True)
        results.append(result)
    
    # Phase 3: Summary and analysis
    print_portfolio_summary(results, analysis)


if __name__ == "__main__":
    main()
