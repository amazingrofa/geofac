"""
Rehearsal on 60-96 bit Semiprimes
==================================

Tests 4 variants on balanced semiprimes at increasing bit-lengths:
1. Baseline: uniform sampling, no filters
2. Wheel-only: 210-wheel filter
3. Z5D-only: Z5D stepping (no wheel)
4. Full Z5D: wheel + Z5D stepping + GVA ranking

For each variant and bit-length:
- Test with candidate budgets: 10^4, 10^5, 10^6
- Log success/failure, samples-to-factor, δ-span covered
- Compute coverage metric C = (δ_span × wheel_coverage) / log(√N)
- Fit success probability curve

Exports: rehearsal_results.json
"""

import json
import os
import time
from math import log, isqrt
from typing import Dict, List, Optional, Tuple
from z5d_pipeline import (
    generate_z5d_candidates, adaptive_precision, WHEEL_SIZE, WHEEL_MODULUS
)
from calibrate_bands import (
    generate_balanced_semiprime, miller_rabin, next_prime
)
import mpmath as mp


def baseline_search(N: int, sqrt_N: int, max_candidates: int) -> Optional[Tuple]:
    """Baseline: uniform δ-sampling, no filters."""
    for delta in range(max_candidates):
        for sign in [1, -1]:
            candidate = sqrt_N + sign * delta
            if candidate > 1 and N % candidate == 0:
                return (candidate, N // candidate, delta, delta)
    return None


def wheel_only_search(N: int, sqrt_N: int, max_candidates: int) -> Optional[Tuple]:
    """Wheel-only: 210-wheel filter, uniform δ."""
    from wheel_residues import is_admissible, next_admissible
    
    tested = 0
    delta = 0
    max_delta = 0
    
    while tested < max_candidates:
        for sign in [1, -1]:
            candidate = sqrt_N + sign * delta
            if candidate <= 1:
                continue
            
            if not is_admissible(candidate):
                continue
            
            if N % candidate == 0:
                return (candidate, N // candidate, tested, max_delta)
            
            tested += 1
            max_delta = max(max_delta, abs(delta))
            
            if tested >= max_candidates:
                break
        
        delta += 1
    
    return None


def z5d_only_search(N: int, sqrt_N: int, max_candidates: int) -> Optional[Tuple]:
    """Z5D-only: Z5D stepping, no wheel."""
    from z5d_api import prioritize_delta_bands, adaptive_step_size
    
    bands = prioritize_delta_bands(sqrt_N, delta_max=100000, num_bands=10)
    tested = 0
    max_delta = 0
    
    for band in bands:
        delta_start = band['delta_start']
        delta_end = band['delta_end']
        density = band['density']
        step = adaptive_step_size(density, base_step=1)
        
        current_delta = delta_start
        while current_delta <= delta_end and tested < max_candidates:
            for sign in [1, -1]:
                candidate = sqrt_N + sign * current_delta
                if candidate <= 1:
                    continue
                
                if N % candidate == 0:
                    return (candidate, N // candidate, tested, max_delta)
                
                tested += 1
                max_delta = max(max_delta, abs(current_delta))
                
                if tested >= max_candidates:
                    break
            
            current_delta += step
    
    return None


def full_z5d_search(N: int, sqrt_N: int, max_candidates: int) -> Optional[Tuple]:
    """Full Z5D: wheel + Z5D stepping + GVA."""
    tested = 0
    max_delta = 0
    
    for cand_data in generate_z5d_candidates(
        N, sqrt_N, delta_max=100000, num_bands=10, k_value=0.35
    ):
        candidate = cand_data['candidate']
        delta = abs(cand_data['delta'])
        
        if N % candidate == 0:
            return (candidate, N // candidate, tested, max_delta)
        
        tested += 1
        max_delta = max(max_delta, delta)
        
        if tested >= max_candidates:
            break
    
    return None


def run_variant(variant_name: str, 
               variant_fn,
               N: int, 
               sqrt_N: int,
               budget: int) -> Dict:
    """
    Run a single variant with given budget.
    
    Returns:
        Dict with metrics
    """
    start_time = time.time()
    result = variant_fn(N, sqrt_N, budget)
    elapsed = time.time() - start_time
    
    if result:
        p, q, samples, delta_span = result
        success = True
    else:
        success = False
        p, q, samples, delta_span = None, None, budget, 0
    
    # Compute coverage metric
    log_sqrt_N = log(float(sqrt_N))
    
    if variant_name in ['wheel-only', 'full-z5d']:
        wheel_factor = WHEEL_SIZE / WHEEL_MODULUS
    else:
        wheel_factor = 1.0
    
    coverage = (delta_span * wheel_factor) / log_sqrt_N if log_sqrt_N > 0 else 0
    
    return {
        'variant': variant_name,
        'success': success,
        'p': str(p) if p else None,
        'q': str(q) if q else None,
        'samples_tested': samples,
        'delta_span': delta_span,
        'coverage': coverage,
        'time_seconds': elapsed
    }


def rehearse_bitlength(bit_length: int) -> List[Dict]:
    """
    Rehearse all variants on a single bit-length.
    
    Args:
        bit_length: Target bit-length
        
    Returns:
        List of result dicts
    """
    print(f"\n{'=' * 70}")
    print(f"Rehearsing {bit_length}-bit semiprime")
    print('=' * 70)
    
    # Generate test case
    N, p_true, q_true = generate_balanced_semiprime(bit_length)
    sqrt_N = isqrt(N)
    
    print(f"N = {N}")
    print(f"p = {p_true}")
    print(f"q = {q_true}")
    print(f"√N = {sqrt_N}")
    print()
    
    variants = [
        ('baseline', baseline_search),
        ('wheel-only', wheel_only_search),
        ('z5d-only', z5d_only_search),
        ('full-z5d', full_z5d_search),
    ]
    
    budgets = [10**4, 10**5, 10**6]
    results = []
    
    for budget in budgets:
        print(f"Budget: {budget}")
        
        for variant_name, variant_fn in variants:
            print(f"  Running {variant_name}...", end=' ', flush=True)
            
            result = run_variant(variant_name, variant_fn, N, sqrt_N, budget)
            result['bit_length'] = bit_length
            result['N'] = str(N)
            result['budget'] = budget
            
            status = "SUCCESS" if result['success'] else "FAILED"
            print(f"{status} ({result['samples_tested']} samples, "
                  f"{result['time_seconds']:.2f}s, C={result['coverage']:.2f})")
            
            results.append(result)
        
        print()
    
    return results


def rehearse_all() -> Dict:
    """
    Run full rehearsal across all bit-lengths.
    
    Returns:
        Dict with all results
    """
    print("=" * 70)
    print("Z5D Rehearsal: 60-96 bit Semiprimes")
    print("=" * 70)
    
    bit_lengths = [60, 70, 80, 90, 96]
    all_results = []
    
    for bl in bit_lengths:
        results = rehearse_bitlength(bl)
        all_results.extend(results)
    
    # Analyze success rates by variant
    print("\n" + "=" * 70)
    print("Rehearsal Summary")
    print("=" * 70)
    print()
    
    variants = ['baseline', 'wheel-only', 'z5d-only', 'full-z5d']
    
    for variant in variants:
        variant_results = [r for r in all_results if r['variant'] == variant]
        successes = sum(1 for r in variant_results if r['success'])
        total = len(variant_results)
        success_rate = successes / total if total > 0 else 0
        
        print(f"{variant:12s}: {successes}/{total} = {success_rate:.1%}")
    
    print()
    
    # Coverage analysis
    print("Coverage metrics (successful runs only):")
    for variant in variants:
        successful = [r for r in all_results 
                     if r['variant'] == variant and r['success']]
        if successful:
            coverages = [r['coverage'] for r in successful]
            avg_coverage = sum(coverages) / len(coverages)
            min_coverage = min(coverages)
            max_coverage = max(coverages)
            print(f"  {variant:12s}: C_avg={avg_coverage:.2f}, "
                  f"C_range=[{min_coverage:.2f}, {max_coverage:.2f}]")
    
    print()
    
    return {
        'results': all_results,
        'summary': {
            'variants': variants,
            'bit_lengths': bit_lengths,
            'budgets': [10**4, 10**5, 10**6]
        }
    }


def main():
    """Run rehearsal and export results."""
    rehearsal_data = rehearse_all()
    
    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__), 
        'rehearsal_results.json'
    )
    
    with open(output_path, 'w') as f:
        json.dump(rehearsal_data, f, indent=2)
    
    print("=" * 70)
    print(f"Rehearsal complete. Results saved to:")
    print(f"  {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
