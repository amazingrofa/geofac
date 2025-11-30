"""
Hash-Bounds Partition Comparison Experiment
============================================

Compare boundary-focused sampling vs. uniform GVA sampling to test
the hash-bounds partition hypothesis.

Hypothesis: Fractional square roots of seed primes create natural boundaries
that partition the factor search space. Factors preferentially cluster near
these boundaries, and boundary-focused sampling should outperform uniform.

Falsification criteria:
1. Boundary-focused sampling does NOT find factors faster than uniform
2. Factors do NOT cluster near hash boundaries
3. No reduction in candidates tested
4. Boundary selection performs no better than random subspace selection
"""

import sys
import os
import json
import time
import random
from math import isqrt, sqrt
from typing import Dict, List

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from hash_bounds_sampling import (
    hash_bounds_factor_search,
    get_all_fractional_roots,
    compute_all_boundaries,
    boundary_proximity_score,
    adaptive_precision,
    SEED_PRIMES,
    CHALLENGE_127,
)

# Import baseline GVA for comparison
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
    from gva_factorization import gva_factor_search
except ImportError:
    gva_factor_search = None

# Test semiprimes in operational range [10^14, 10^18]
TEST_SEMIPRIMES = [
    # Gate 2: 60-bit (for quick validation)
    {
        'N': 1152921470247108503,
        'p': 1073741789,
        'q': 1073741827,
        'name': 'Gate 2 (60-bit)',
        'bit_length': 60,
    },
    # 64-bit validated example
    {
        'N': 18446736050711510819,
        'p': 4294966297,
        'q': 4294966427,
        'name': '64-bit validated',
        'bit_length': 64,
    },
]

# 127-bit challenge (secondary target)
CHALLENGE_INFO = {
    'N': CHALLENGE_127,
    'p': 10508623501177419659,
    'q': 13086849276577416863,
    'name': '127-bit challenge (Gate 3)',
    'bit_length': 127,
}


def run_uniform_gva(N: int, max_candidates: int = 10000, 
                    delta_window: int = 100000,
                    verbose: bool = False) -> Dict:
    """
    Run uniform GVA sampling (baseline).
    
    Returns:
        Dict with results and metrics
    """
    start_time = time.time()
    
    if gva_factor_search is not None:
        result = gva_factor_search(
            N,
            k_values=[0.35],
            max_candidates=max_candidates,
            verbose=verbose,
            allow_any_range=True
        )
    else:
        # Fallback: simple uniform search
        sqrt_N = isqrt(N)
        result = None
        tested = 0
        
        phi_inv = (sqrt(5) - 1) / 2  # 1/φ, golden ratio conjugate
        for i in range(max_candidates):
            alpha = (i * phi_inv) % 1.0
            offset = int(alpha * 2 * delta_window - delta_window)
            candidate = sqrt_N + offset
            
            if candidate <= 1 or candidate >= N or candidate % 2 == 0:
                continue
            
            tested += 1
            if N % candidate == 0:
                result = (candidate, N // candidate)
                break
    
    elapsed = time.time() - start_time
    
    success = result is not None
    if success:
        p, q = result
        verified = (p * q == N)
    else:
        p, q = None, None
        verified = False
    
    return {
        'name': 'Uniform GVA',
        'success': success,
        'verified': verified,
        'elapsed': elapsed,
        'p': p,
        'q': q,
        'max_candidates': max_candidates,
        'delta_window': delta_window,
        'method': 'uniform',
    }


def run_hash_bounds_focused(N: int, max_candidates: int = 10000,
                            delta_window: int = 100000,
                            boundary_weight: float = 0.7,
                            boundary_proximity_weight: float = 0.1,
                            seed: int = 42,
                            verbose: bool = False) -> Dict:
    """
    Run hash-bounds focused sampling (treatment).
    
    Returns:
        Dict with results and metrics
    """
    start_time = time.time()
    
    result = hash_bounds_factor_search(
        N,
        k_value=0.35,
        max_candidates=max_candidates,
        delta_window=delta_window,
        boundary_weight=boundary_weight,
        boundary_proximity_weight=boundary_proximity_weight,
        seed=seed,
        verbose=verbose,
        allow_any_range=True
    )
    
    elapsed = time.time() - start_time
    
    success = result is not None
    if success:
        p, q = result
        verified = (p * q == N)
    else:
        p, q = None, None
        verified = False
    
    return {
        'name': f'Hash-Bounds (bw={boundary_weight}, pw={boundary_proximity_weight})',
        'success': success,
        'verified': verified,
        'elapsed': elapsed,
        'p': p,
        'q': q,
        'max_candidates': max_candidates,
        'delta_window': delta_window,
        'method': 'hash_bounds',
        'boundary_weight': boundary_weight,
        'boundary_proximity_weight': boundary_proximity_weight,
        'seed': seed,
    }


def analyze_factor_boundary_clustering(N: int, p: int, q: int) -> Dict:
    """
    Analyze whether known factors cluster near hash boundaries.
    
    Args:
        N: Semiprime
        p: First factor
        q: Second factor
        
    Returns:
        Dict with clustering analysis
    """
    sqrt_N = isqrt(N)
    precision = adaptive_precision(N)
    
    # Compute offsets of factors from sqrt_N
    p_offset = p - sqrt_N
    q_offset = q - sqrt_N
    
    # Compute boundaries
    window = max(abs(p_offset), abs(q_offset)) + 1000
    all_boundaries = compute_all_boundaries(sqrt_N, precision, window)
    
    # Compute proximity scores for actual factors
    p_prox = boundary_proximity_score(p_offset, all_boundaries)
    q_prox = boundary_proximity_score(q_offset, all_boundaries)
    
    # Compute expected proximity for random positions
    # Sample random positions and compute their average proximity
    random.seed(42)
    
    random_proxs = []
    for _ in range(1000):
        rand_offset = random.randint(-window, window)
        rand_prox = boundary_proximity_score(rand_offset, all_boundaries)
        random_proxs.append(rand_prox)
    
    avg_random_prox = sum(random_proxs) / len(random_proxs)
    
    # Factor proximity relative to random
    p_relative = p_prox / avg_random_prox if avg_random_prox > 0 else 0
    q_relative = q_prox / avg_random_prox if avg_random_prox > 0 else 0
    
    return {
        'sqrt_N': sqrt_N,
        'p': p,
        'q': q,
        'p_offset': p_offset,
        'q_offset': q_offset,
        'p_boundary_proximity': p_prox,
        'q_boundary_proximity': q_prox,
        'avg_random_proximity': avg_random_prox,
        'p_relative_to_random': p_relative,
        'q_relative_to_random': q_relative,
        'p_clusters_near_boundary': p_prox > avg_random_prox * 1.5,
        'q_clusters_near_boundary': q_prox > avg_random_prox * 1.5,
    }


def run_ablation_study(N: int, p: int, q: int, 
                      max_candidates: int = 5000,
                      delta_window: int = 50000,
                      verbose: bool = False) -> List[Dict]:
    """
    Run ablation study testing each component separately.
    
    Tests:
    1. Uniform baseline
    2. Each seed prime individually
    3. All boundaries combined
    4. Different boundary weights
    
    Returns:
        List of experiment results
    """
    results = []
    
    # 1. Uniform baseline
    print("  Testing: Uniform baseline...")
    r = run_uniform_gva(N, max_candidates, delta_window, verbose)
    r['ablation'] = 'uniform_baseline'
    results.append(r)
    
    # 2. Full hash-bounds with default weights
    print("  Testing: Full hash-bounds (default)...")
    r = run_hash_bounds_focused(N, max_candidates, delta_window, 
                                boundary_weight=0.7, 
                                boundary_proximity_weight=0.1,
                                verbose=verbose)
    r['ablation'] = 'hash_bounds_default'
    results.append(r)
    
    # 3. Different boundary weights
    for bw in [0.3, 0.5, 0.9]:
        print(f"  Testing: Hash-bounds (boundary_weight={bw})...")
        r = run_hash_bounds_focused(N, max_candidates, delta_window,
                                    boundary_weight=bw,
                                    boundary_proximity_weight=0.1,
                                    verbose=verbose)
        r['ablation'] = f'hash_bounds_bw_{bw}'
        results.append(r)
    
    # 4. Different proximity weights
    for pw in [0.0, 0.3, 0.5]:
        print(f"  Testing: Hash-bounds (proximity_weight={pw})...")
        r = run_hash_bounds_focused(N, max_candidates, delta_window,
                                    boundary_weight=0.7,
                                    boundary_proximity_weight=pw,
                                    verbose=verbose)
        r['ablation'] = f'hash_bounds_pw_{pw}'
        results.append(r)
    
    return results


def print_experiment_summary(results: List[Dict]):
    """Print summary of experiment results."""
    print()
    print("=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)
    print()
    
    # Header
    print(f"{'Experiment':<40} {'Success':<10} {'Time (s)':<12} {'Method':<15}")
    print("-" * 77)
    
    for r in results:
        success_str = "✓" if r['success'] else "✗"
        time_str = f"{r['elapsed']:.3f}"
        method_str = r.get('ablation', r['method'])[:14]
        name_str = r['name'][:39]
        
        print(f"{name_str:<40} {success_str:<10} {time_str:<12} {method_str:<15}")
    
    print("-" * 77)
    print()


def print_clustering_analysis(analysis: Dict):
    """Print factor clustering analysis."""
    print()
    print("=" * 70)
    print("FACTOR BOUNDARY CLUSTERING ANALYSIS")
    print("=" * 70)
    print()
    
    print(f"√N = {analysis['sqrt_N']}")
    print(f"p = {analysis['p']} (offset: {analysis['p_offset']:+d})")
    print(f"q = {analysis['q']} (offset: {analysis['q_offset']:+d})")
    print()
    
    print("Boundary Proximity Scores:")
    print(f"  p proximity: {analysis['p_boundary_proximity']:.4f}")
    print(f"  q proximity: {analysis['q_boundary_proximity']:.4f}")
    print(f"  Avg random proximity: {analysis['avg_random_proximity']:.4f}")
    print()
    
    print("Relative to Random:")
    print(f"  p: {analysis['p_relative_to_random']:.2f}x random expectation")
    print(f"  q: {analysis['q_relative_to_random']:.2f}x random expectation")
    print()
    
    p_cluster = "YES" if analysis['p_clusters_near_boundary'] else "NO"
    q_cluster = "YES" if analysis['q_clusters_near_boundary'] else "NO"
    print(f"Clusters near boundary (>1.5x random):")
    print(f"  p: {p_cluster}")
    print(f"  q: {q_cluster}")
    print()


def run_full_comparison():
    """Run full comparison experiment on all test semiprimes."""
    print("=" * 70)
    print("HASH-BOUNDS PARTITION HYPOTHESIS")
    print("FALSIFICATION EXPERIMENT")
    print("=" * 70)
    print()
    
    print("Seed Primes:", SEED_PRIMES)
    print("Fractional roots:")
    frac_roots = get_all_fractional_roots(50)
    for p, frac in frac_roots.items():
        print(f"  frac(√{p}) = {float(frac):.10f}")
    print()
    
    all_results = []
    all_clustering = []
    
    for semi_info in TEST_SEMIPRIMES:
        N = semi_info['N']
        p = semi_info['p']
        q = semi_info['q']
        name = semi_info['name']
        
        print("=" * 70)
        print(f"TEST: {name}")
        print("=" * 70)
        print(f"N = {N}")
        print(f"Expected: {p} × {q}")
        print()
        
        # Run comparison
        print("Running experiments...")
        
        # Scale parameters based on bit length
        bit_len = N.bit_length()
        if bit_len <= 50:
            max_cand = 3000
            window = 30000
        elif bit_len <= 65:
            max_cand = 5000
            window = 50000
        else:
            max_cand = 10000
            window = 100000
        
        # Baseline
        print("  Uniform GVA baseline...")
        uniform_result = run_uniform_gva(N, max_cand, window, verbose=False)
        uniform_result['test_name'] = name
        all_results.append(uniform_result)
        
        # Hash-bounds
        print("  Hash-bounds focused...")
        bounds_result = run_hash_bounds_focused(N, max_cand, window, 
                                                 boundary_weight=0.7,
                                                 boundary_proximity_weight=0.1,
                                                 verbose=False)
        bounds_result['test_name'] = name
        all_results.append(bounds_result)
        
        # Factor clustering analysis
        print("  Analyzing factor clustering...")
        clustering = analyze_factor_boundary_clustering(N, p, q)
        clustering['test_name'] = name
        all_clustering.append(clustering)
        
        print()
        print_clustering_analysis(clustering)
    
    # Summary
    print("=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    print_experiment_summary(all_results)
    
    # Hypothesis evaluation
    print("=" * 70)
    print("HYPOTHESIS EVALUATION")
    print("=" * 70)
    print()
    
    # Check falsification criteria
    uniform_successes = sum(1 for r in all_results if r['method'] == 'uniform' and r['success'])
    bounds_successes = sum(1 for r in all_results if r['method'] == 'hash_bounds' and r['success'])
    
    uniform_avg_time = sum(r['elapsed'] for r in all_results if r['method'] == 'uniform') / max(1, len([r for r in all_results if r['method'] == 'uniform']))
    bounds_avg_time = sum(r['elapsed'] for r in all_results if r['method'] == 'hash_bounds') / max(1, len([r for r in all_results if r['method'] == 'hash_bounds']))
    
    clusters_near_boundary = sum(1 for c in all_clustering 
                                 if c['p_clusters_near_boundary'] or c['q_clusters_near_boundary'])
    
    print("Falsification Criteria Assessment:")
    print()
    
    # Criterion 1: Does boundary-focused find factors faster?
    if bounds_avg_time < uniform_avg_time * 0.8:
        print("  Criterion 1: Hash-bounds is faster → NOT falsified")
        c1_falsified = False
    else:
        print("  Criterion 1: Hash-bounds is NOT significantly faster → Falsified")
        c1_falsified = True
    
    # Criterion 2: Do factors cluster near boundaries?
    if clusters_near_boundary >= len(all_clustering) / 2:
        print("  Criterion 2: Factors cluster near boundaries → NOT falsified")
        c2_falsified = False
    else:
        print("  Criterion 2: Factors do NOT cluster near boundaries → Falsified")
        c2_falsified = True
    
    # Criterion 3: Success rate comparison
    if bounds_successes > uniform_successes:
        print("  Criterion 3: Hash-bounds has better success rate → NOT falsified")
        c3_falsified = False
    else:
        print("  Criterion 3: Hash-bounds does NOT have better success → Falsified")
        c3_falsified = True
    
    print()
    
    if c1_falsified or c2_falsified or c3_falsified:
        print("VERDICT: HYPOTHESIS FALSIFIED")
        print("At least one falsification criterion is satisfied.")
    else:
        print("VERDICT: HYPOTHESIS NOT FALSIFIED (requires more testing)")
        print("None of the falsification criteria are conclusively satisfied.")
    
    print()
    
    # Export results
    output_dir = os.path.dirname(__file__)
    results_file = os.path.join(output_dir, "comparison_results.json")
    
    export_data = {
        'experiments': all_results,
        'clustering_analysis': all_clustering,
        'falsification_criteria': {
            'criterion_1_faster': not c1_falsified,
            'criterion_2_clustering': not c2_falsified,
            'criterion_3_success_rate': not c3_falsified,
        },
        'verdict': 'falsified' if (c1_falsified or c2_falsified or c3_falsified) else 'not_falsified',
    }
    
    with open(results_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print(f"Results exported to: {results_file}")
    print()
    
    print("=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_full_comparison()
