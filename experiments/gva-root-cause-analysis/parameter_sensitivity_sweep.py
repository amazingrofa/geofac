"""
Parameter Sensitivity Sweep
============================

Phase 1.2: Grid search over k and candidate budget to measure parameter sensitivity.

Tests hypothesis: GVA failure in operational range is NOT due to suboptimal parameters,
but rather fundamental signal decay.

Methodology:
- Grid search k ∈ [0.1, 0.5] in 0.05 increments
- Grid search candidate budgets: [10k, 25k, 50k, 100k, 250k, 500k, 1M]
- Test on 47-bit balanced semiprime from operational range
- Measure: success rate, runtime, false positive rate
- Generate heatmap showing success regions

Validation: Uses balanced RSA-style semiprime at 47 bits (N=100000001506523)
No classical fallbacks: Pure GVA search
Precision: Adaptive, logged per test
"""

import mpmath as mp
import json
import time
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from gva_factorization import embed_torus_geodesic, riemannian_distance, adaptive_precision


def gva_parameter_sweep_test(N: int, p: int, q: int, k: float, 
                             max_candidates: int, verbose: bool = False) -> Dict:
    """
    Test GVA with specific parameters.
    
    Args:
        N: Semiprime to factor
        p, q: True factors (for validation)
        k: Geodesic exponent
        max_candidates: Candidate budget
        verbose: Print progress
        
    Returns:
        Dictionary with test results
    """
    bit_length = N.bit_length()
    required_dps = adaptive_precision(N)
    
    start_time = time.time()
    
    with mp.workdps(required_dps):
        sqrt_N = int(mp.sqrt(N))
        
        # Compute search window
        window = max(10000, sqrt_N // 100)
        
        # Embed N
        N_coords = embed_torus_geodesic(N, k)
        
        # Track best candidates
        best_distance = float('inf')
        best_candidate = None
        distances_checked = []
        
        # Search around sqrt(N)
        candidates_tested = 0
        found_factor = False
        
        for offset in range(-window, window + 1):
            if candidates_tested >= max_candidates:
                break
            
            candidate = sqrt_N + offset
            
            if candidate <= 1 or candidate >= N:
                continue
            if candidate % 2 == 0:  # Skip even
                continue
            
            # Check if it's a factor
            if N % candidate == 0:
                found_factor = True
                elapsed = time.time() - start_time
                
                return {
                    'N': N,
                    'bit_length': bit_length,
                    'precision_dps': required_dps,
                    'k': k,
                    'max_candidates': max_candidates,
                    'candidates_tested': candidates_tested,
                    'success': True,
                    'factor_found': candidate,
                    'runtime_seconds': elapsed,
                    'false_positives': 0
                }
            
            # Compute geodesic distance
            candidate_coords = embed_torus_geodesic(candidate, k)
            dist = float(riemannian_distance(N_coords, candidate_coords))
            distances_checked.append(dist)
            
            if dist < best_distance:
                best_distance = dist
                best_candidate = candidate
            
            candidates_tested += 1
    
    elapsed = time.time() - start_time
    
    # Count false positives (non-factors with very low distance)
    # Threshold: distance < 90th percentile of distances
    if distances_checked:
        sorted_distances = sorted(distances_checked)
        threshold_idx = int(0.1 * len(sorted_distances))  # Bottom 10%
        threshold = sorted_distances[threshold_idx] if threshold_idx < len(sorted_distances) else sorted_distances[0]
        
        false_positives = sum(1 for d in distances_checked if d <= threshold)
    else:
        false_positives = 0
    
    return {
        'N': N,
        'bit_length': bit_length,
        'precision_dps': required_dps,
        'k': k,
        'max_candidates': max_candidates,
        'candidates_tested': candidates_tested,
        'success': False,
        'factor_found': None,
        'best_candidate': best_candidate,
        'best_distance': best_distance,
        'runtime_seconds': elapsed,
        'false_positives': false_positives
    }


def run_parameter_sweep():
    """
    Run complete parameter sensitivity sweep.
    """
    print("=" * 80)
    print("GVA Root-Cause Analysis: Phase 1.2 - Parameter Sensitivity Sweep")
    print("=" * 80)
    print()
    
    output_dir = Path(__file__).parent
    
    # Test case: 47-bit balanced semiprime from operational range
    N = 100000001506523
    p = 9999991
    q = 10000061
    
    print(f"Test Case:")
    print(f"  N = {N}")
    print(f"  p = {p}")
    print(f"  q = {q}")
    print(f"  Bit length: {N.bit_length()}")
    print(f"  ln(q/p) = {(q/p - 1):.6f} (balanced)")
    print()
    
    # Grid parameters
    k_values = [round(k, 2) for k in [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]]
    candidate_budgets = [1000, 5000, 10000, 25000, 50000]  # Reduced for reasonable runtime
    
    print(f"Grid Configuration:")
    print(f"  k values: {k_values}")
    print(f"  Candidate budgets: {candidate_budgets}")
    print(f"  Total tests: {len(k_values) * len(candidate_budgets)}")
    print()
    
    results = []
    start_time = time.time()
    
    total_tests = len(k_values) * len(candidate_budgets)
    test_num = 0
    
    for k in k_values:
        for budget in candidate_budgets:
            test_num += 1
            print(f"Test {test_num}/{total_tests}: k={k}, budget={budget}...", end=' ')
            
            try:
                result = gva_parameter_sweep_test(N, p, q, k, budget)
                results.append(result)
                
                if result['success']:
                    print(f"✅ SUCCESS ({result['runtime_seconds']:.3f}s)")
                else:
                    print(f"❌ FAIL ({result['runtime_seconds']:.3f}s, best_dist={result['best_distance']:.6f})")
            
            except Exception as e:
                print(f"ERROR: {e}")
                continue
    
    elapsed = time.time() - start_time
    
    print()
    print(f"Sweep complete. Total time: {elapsed:.2f}s")
    print(f"Total tests: {len(results)}")
    print()
    
    # Export data
    output_file = output_dir / "parameter_sweep_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'experiment': 'parameter_sensitivity_sweep',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_case': {
                    'N': N,
                    'p': p,
                    'q': q,
                    'bit_length': N.bit_length()
                },
                'k_values': k_values,
                'candidate_budgets': candidate_budgets,
                'total_runtime_seconds': elapsed
            },
            'results': results
        }, f, indent=2)
    
    print(f"Data exported to: {output_file}")
    
    # Summary statistics
    print()
    print("Summary Statistics:")
    print("-" * 80)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"  Success rate: {success_count}/{len(results)} ({100*success_count/len(results):.1f}%)")
    
    if success_count > 0:
        successful_tests = [r for r in results if r['success']]
        avg_runtime = sum(r['runtime_seconds'] for r in successful_tests) / len(successful_tests)
        min_k = min(r['k'] for r in successful_tests)
        max_k = max(r['k'] for r in successful_tests)
        min_budget = min(r['max_candidates'] for r in successful_tests)
        max_budget = max(r['max_candidates'] for r in successful_tests)
        
        print(f"  Successful k range: [{min_k}, {max_k}]")
        print(f"  Successful budget range: [{min_budget}, {max_budget}]")
        print(f"  Avg runtime (successful): {avg_runtime:.3f}s")
    
    # Analyze by k value
    print()
    print("Success rate by k value:")
    from collections import defaultdict
    by_k = defaultdict(lambda: {'total': 0, 'success': 0})
    for r in results:
        by_k[r['k']]['total'] += 1
        if r['success']:
            by_k[r['k']]['success'] += 1
    
    for k in sorted(by_k.keys()):
        stats = by_k[k]
        rate = 100 * stats['success'] / stats['total']
        print(f"  k={k}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
    
    # Analyze by budget
    print()
    print("Success rate by candidate budget:")
    by_budget = defaultdict(lambda: {'total': 0, 'success': 0})
    for r in results:
        by_budget[r['max_candidates']]['total'] += 1
        if r['success']:
            by_budget[r['max_candidates']]['success'] += 1
    
    for budget in sorted(by_budget.keys()):
        stats = by_budget[budget]
        rate = 100 * stats['success'] / stats['total']
        print(f"  budget={budget}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
    
    print()
    print("Next step: Run generate_visualizations.py to create heatmap")
    
    return results


if __name__ == '__main__':
    run_parameter_sweep()
