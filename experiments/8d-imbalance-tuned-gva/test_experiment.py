"""
8D Imbalance-Tuned GVA: Experiment Test Suite
==============================================

Compares 7D GVA vs 8D GVA on balanced and unbalanced semiprimes.

Test Strategy:
1. Balanced cases (ln(q/p) ≈ 0): Both should work, 7D may be faster
2. Moderately unbalanced (ln(q/p) ≈ 0.1-0.2): Test hypothesis threshold
3. Highly unbalanced (ln(q/p) ≈ 0.3-0.4): 8D should show advantage IF hypothesis holds

All test cases use semiprimes in operational range [10^14, 10^18] or validation gates.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

from gva_8d import gva_8d_factor_search, compute_imbalance_ratio
from gva_factorization import gva_factor_search
import time
from math import log


# Test cases: mix of balanced and unbalanced semiprimes
# All in operational range [10^14, 10^18]
TEST_CASES = [
    {
        'name': 'Balanced 47-bit (ln(q/p) ≈ 0)',
        'N': 100000001506523,  # 10000000 × 10000000.150652... ≈ balanced
        'p': 9999991,
        'q': 10000061,
        'expected_r': log(10000061 / 9999991),  # ≈ 0.000007
        'category': 'balanced'
    },
    {
        'name': 'Moderately unbalanced 48-bit (ln(q/p) ≈ 0.58)',
        'N': 177841110036541,  # q is 1.78× larger than p
        'p': 10000019,
        'q': 17783087,  # ≈ 1.78× larger
        'expected_r': log(17783087 / 10000019),  # ≈ 0.576
        'category': 'moderately_unbalanced'
    },
    {
        'name': 'Highly unbalanced 50-bit (ln(q/p) ≈ 1.39)',
        'N': 399999996000001,
        'p': 9999999,
        'q': 40000001,  # 4× larger
        'expected_r': log(40000001 / 9999999),  # ≈ 1.386
        'category': 'highly_unbalanced'
    },
    {
        'name': 'Gate 1 (30-bit balanced)',
        'N': 1073217479,
        'p': 32749,
        'q': 32771,
        'expected_r': log(32771 / 32749),  # ≈ 0.00067
        'category': 'balanced'
    },
]


def run_single_test(test_case, method='both', verbose=False):
    """
    Run test on a single case.
    
    Args:
        test_case: Test case dict
        method: '7d', '8d', or 'both'
        verbose: Print detailed output
        
    Returns:
        dict with results
    """
    N = test_case['N']
    expected_p = test_case['p']
    expected_q = test_case['q']
    name = test_case['name']
    expected_r = test_case['expected_r']
    
    print(f"\n{'='*70}")
    print(f"Test: {name}")
    print(f"N = {N}")
    print(f"Bit length: {N.bit_length()}")
    print(f"Expected factors: {expected_p} × {expected_q}")
    print(f"Expected imbalance r = ln(q/p) ≈ {expected_r:.6f}")
    print(f"{'='*70}")
    
    results = {
        'name': name,
        'N': N,
        'expected_p': expected_p,
        'expected_q': expected_q,
        'expected_r': expected_r,
        'category': test_case['category']
    }
    
    # Test 7D GVA (standard)
    if method in ['7d', 'both']:
        print("\n[7D GVA - Standard]")
        start_time = time.time()
        try:
            factors_7d = gva_factor_search(
                N,
                k_values=[0.30, 0.35, 0.40],
                max_candidates=50000,
                verbose=verbose,
                allow_any_range=True,
                use_geodesic_guidance=True
            )
            elapsed_7d = time.time() - start_time
            
            if factors_7d:
                p, q = factors_7d
                success = set(factors_7d) == {expected_p, expected_q}
                print(f"Result: {'✅ SUCCESS' if success else '❌ WRONG FACTORS'}")
                print(f"  Found: {p} × {q}")
                print(f"  Time: {elapsed_7d:.3f}s")
                results['7d_success'] = success
                results['7d_time'] = elapsed_7d
                results['7d_p'] = p
                results['7d_q'] = q
            else:
                print(f"Result: ❌ FAILED (no factors found)")
                print(f"  Time: {elapsed_7d:.3f}s")
                results['7d_success'] = False
                results['7d_time'] = elapsed_7d
        except Exception as e:
            print(f"Result: ❌ ERROR: {e}")
            results['7d_success'] = False
            results['7d_error'] = str(e)
    
    # Test 8D GVA (imbalance-tuned)
    if method in ['8d', 'both']:
        print("\n[8D GVA - Imbalance-Tuned]")
        start_time = time.time()
        try:
            factors_8d = gva_8d_factor_search(
                N,
                k_values=[0.30, 0.35, 0.40],
                theta_r_samples=50,
                theta_r_range=(-0.6, 0.6),
                max_candidates=50000,
                verbose=verbose,
                allow_any_range=True
            )
            elapsed_8d = time.time() - start_time
            
            if factors_8d:
                p, q = factors_8d
                success = set(factors_8d) == {expected_p, expected_q}
                print(f"Result: {'✅ SUCCESS' if success else '❌ WRONG FACTORS'}")
                print(f"  Found: {p} × {q}")
                print(f"  Time: {elapsed_8d:.3f}s")
                results['8d_success'] = success
                results['8d_time'] = elapsed_8d
                results['8d_p'] = p
                results['8d_q'] = q
            else:
                print(f"Result: ❌ FAILED (no factors found)")
                print(f"  Time: {elapsed_8d:.3f}s")
                results['8d_success'] = False
                results['8d_time'] = elapsed_8d
        except Exception as e:
            print(f"Result: ❌ ERROR: {e}")
            results['8d_success'] = False
            results['8d_error'] = str(e)
    
    return results


def run_all_tests(method='both', verbose=False):
    """Run all test cases and generate summary."""
    print("\n" + "="*70)
    print("8D IMBALANCE-TUNED GVA: HYPOTHESIS FALSIFICATION EXPERIMENT")
    print("="*70)
    print("\nHypothesis: Adding 8th dimension for imbalance tuning improves")
    print("factorization of unbalanced semiprimes (ln(q/p) > 0.1)")
    print("\nTest strategy:")
    print("  - Balanced cases: both methods should work")
    print("  - Unbalanced cases: 8D should show advantage IF hypothesis holds")
    print("="*70)
    
    all_results = []
    
    for test_case in TEST_CASES:
        result = run_single_test(test_case, method=method, verbose=verbose)
        all_results.append(result)
    
    # Generate summary
    print("\n" + "="*70)
    print("SUMMARY RESULTS")
    print("="*70)
    
    print("\n{:<40} {:>8} {:>8}".format("Test Case", "7D", "8D"))
    print("-"*70)
    
    for res in all_results:
        name = res['name'][:38]
        status_7d = "✅ PASS" if res.get('7d_success') else "❌ FAIL"
        status_8d = "✅ PASS" if res.get('8d_success') else "❌ FAIL"
        
        if method == '7d':
            print(f"{name:<40} {status_7d:>8}")
        elif method == '8d':
            print(f"{name:<40}          {status_8d:>8}")
        else:
            print(f"{name:<40} {status_7d:>8} {status_8d:>8}")
    
    # Category analysis
    print("\n" + "="*70)
    print("CATEGORY ANALYSIS")
    print("="*70)
    
    categories = {}
    for res in all_results:
        cat = res['category']
        if cat not in categories:
            categories[cat] = {'7d_pass': 0, '7d_total': 0, '8d_pass': 0, '8d_total': 0}
        
        if '7d_success' in res:
            categories[cat]['7d_total'] += 1
            if res['7d_success']:
                categories[cat]['7d_pass'] += 1
        
        if '8d_success' in res:
            categories[cat]['8d_total'] += 1
            if res['8d_success']:
                categories[cat]['8d_pass'] += 1
    
    for cat, stats in categories.items():
        print(f"\n{cat.upper().replace('_', ' ')}:")
        if stats['7d_total'] > 0:
            rate_7d = stats['7d_pass'] / stats['7d_total'] * 100
            print(f"  7D GVA: {stats['7d_pass']}/{stats['7d_total']} ({rate_7d:.0f}%)")
        if stats['8d_total'] > 0:
            rate_8d = stats['8d_pass'] / stats['8d_total'] * 100
            print(f"  8D GVA: {stats['8d_pass']}/{stats['8d_total']} ({rate_8d:.0f}%)")
    
    # Hypothesis verdict
    print("\n" + "="*70)
    print("HYPOTHESIS VERDICT")
    print("="*70)
    
    # Check if 8D shows advantage on unbalanced cases
    unbalanced_results = [r for r in all_results if r['category'] in ['moderately_unbalanced', 'highly_unbalanced']]
    
    if len(unbalanced_results) > 0:
        success_7d_unbal = sum(1 for r in unbalanced_results if r.get('7d_success'))
        success_8d_unbal = sum(1 for r in unbalanced_results if r.get('8d_success'))
        
        print(f"\nUnbalanced cases (n={len(unbalanced_results)}):")
        print(f"  7D success: {success_7d_unbal}/{len(unbalanced_results)}")
        print(f"  8D success: {success_8d_unbal}/{len(unbalanced_results)}")
        
        if success_8d_unbal > success_7d_unbal:
            print("\n✅ HYPOTHESIS SUPPORTED: 8D shows improvement on unbalanced cases")
        elif success_8d_unbal == success_7d_unbal and success_8d_unbal == 0:
            print("\n❌ HYPOTHESIS FALSIFIED: Both methods fail equally on unbalanced cases")
            print("   (8D provides no improvement despite 50× computational overhead)")
        elif success_8d_unbal == success_7d_unbal:
            print("\n⚠️  HYPOTHESIS UNCLEAR: 8D and 7D perform equally (both have some success)")
        else:
            print("\n❌ HYPOTHESIS FALSIFIED: 8D does not improve unbalanced factorization")
    else:
        print("\nInsufficient unbalanced test cases for verdict")
    
    return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='8D GVA Hypothesis Test')
    parser.add_argument('--method', choices=['7d', '8d', 'both'], default='both',
                        help='Which method to test')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    results = run_all_tests(method=args.method, verbose=args.verbose)
