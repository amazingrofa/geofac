"""
Z5D-Informed GVA Comparison Experiment
=======================================

Compare baseline FR-GVA vs. Z5D-enhanced FR-GVA to test the hypothesis.

Hypothesis: Z5D Prime Predictor insights (density prior, wheel filtering,
gap rules, variable stepping) improve FR-GVA performance on 127-bit challenge.

Falsification criteria:
1. Z5D enhancements don't change segment selection meaningfully
2. No correlation between Z5D density and kernel amplitude
3. No reduction in sample counts or improved convergence
4. All improvements attributable to wheel filter alone (Z5D prior redundant)

This experiment runs controlled comparisons and ablation studies.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from baseline_fr_gva import baseline_fr_gva
from z5d_enhanced_fr_gva import z5d_enhanced_fr_gva
from wheel_residues import WHEEL_SIZE, WHEEL_MODULUS
from math import log, isqrt
import time

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717
EXPECTED_P = 10508623501177419659
EXPECTED_Q = 13086849276577416863


def run_baseline_experiment(max_candidates: int = 50000, 
                           delta_window: int = 500000,
                           verbose: bool = True):
    """
    Run baseline FR-GVA (no Z5D enhancements).
    
    Returns:
        Dict with results and metrics
    """
    print("=" * 70)
    print("EXPERIMENT 1: Baseline FR-GVA")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    result = baseline_fr_gva(
        CHALLENGE_127,
        k_value=0.35,
        max_candidates=max_candidates,
        delta_window=delta_window,
        verbose=verbose
    )
    
    elapsed = time.time() - start_time
    
    success = result is not None
    if success:
        p, q = result
        verified = (p * q == CHALLENGE_127)
    else:
        p, q = None, None
        verified = False
    
    metrics = {
        'name': 'Baseline FR-GVA',
        'success': success,
        'verified': verified,
        'elapsed': elapsed,
        'p': p,
        'q': q,
        'max_candidates': max_candidates,
        'delta_window': delta_window,
        'wheel_filter': False,
        'z5d_prior': False,
        'z5d_stepping': False,
    }
    
    print_summary(metrics)
    
    return metrics


def run_wheel_only_experiment(max_candidates: int = 50000,
                              delta_window: int = 500000,
                              verbose: bool = True):
    """
    Run FR-GVA with ONLY wheel filtering (no Z5D prior or stepping).
    
    This tests if wheel filter alone accounts for improvements.
    
    Returns:
        Dict with results and metrics
    """
    print("=" * 70)
    print("EXPERIMENT 2: Wheel Filter Only")
    print("=" * 70)
    print()
    
    density_file = os.path.join(os.path.dirname(__file__), "z5d_density_histogram.csv")
    
    start_time = time.time()
    
    result = z5d_enhanced_fr_gva(
        CHALLENGE_127,
        z5d_density_file=None,  # No Z5D density
        k_value=0.35,
        max_candidates=max_candidates,
        delta_window=delta_window,
        z5d_weight_beta=0.0,  # No Z5D weight
        use_wheel_filter=True,  # Wheel ON
        use_z5d_stepping=False,  # Z5D stepping OFF
        verbose=verbose
    )
    
    elapsed = time.time() - start_time
    
    success = result is not None
    if success:
        p, q = result
        verified = (p * q == CHALLENGE_127)
    else:
        p, q = None, None
        verified = False
    
    metrics = {
        'name': 'Wheel Filter Only',
        'success': success,
        'verified': verified,
        'elapsed': elapsed,
        'p': p,
        'q': q,
        'max_candidates': max_candidates,
        'delta_window': delta_window,
        'wheel_filter': True,
        'z5d_prior': False,
        'z5d_stepping': False,
    }
    
    print_summary(metrics)
    
    return metrics


def run_z5d_prior_only_experiment(max_candidates: int = 50000,
                                  delta_window: int = 500000,
                                  z5d_weight_beta: float = 0.1,
                                  verbose: bool = True):
    """
    Run FR-GVA with ONLY Z5D density prior (no wheel filter or stepping).
    
    This isolates the effect of Z5D density weighting.
    
    Returns:
        Dict with results and metrics
    """
    print("=" * 70)
    print("EXPERIMENT 3: Z5D Prior Only")
    print("=" * 70)
    print()
    
    density_file = os.path.join(os.path.dirname(__file__), "z5d_density_histogram.csv")
    
    start_time = time.time()
    
    result = z5d_enhanced_fr_gva(
        CHALLENGE_127,
        z5d_density_file=density_file,  # Z5D density ON
        k_value=0.35,
        max_candidates=max_candidates,
        delta_window=delta_window,
        z5d_weight_beta=z5d_weight_beta,  # Z5D weight ON
        use_wheel_filter=False,  # Wheel OFF
        use_z5d_stepping=False,  # Z5D stepping OFF
        verbose=verbose
    )
    
    elapsed = time.time() - start_time
    
    success = result is not None
    if success:
        p, q = result
        verified = (p * q == CHALLENGE_127)
    else:
        p, q = None, None
        verified = False
    
    metrics = {
        'name': f'Z5D Prior Only (β={z5d_weight_beta})',
        'success': success,
        'verified': verified,
        'elapsed': elapsed,
        'p': p,
        'q': q,
        'max_candidates': max_candidates,
        'delta_window': delta_window,
        'wheel_filter': False,
        'z5d_prior': True,
        'z5d_stepping': False,
        'z5d_weight_beta': z5d_weight_beta,
    }
    
    print_summary(metrics)
    
    return metrics


def run_full_z5d_experiment(max_candidates: int = 50000,
                            delta_window: int = 500000,
                            z5d_weight_beta: float = 0.1,
                            verbose: bool = True):
    """
    Run FR-GVA with ALL Z5D enhancements.
    
    This tests the full hypothesis: Z5D prior + wheel + stepping.
    
    Returns:
        Dict with results and metrics
    """
    print("=" * 70)
    print("EXPERIMENT 4: Full Z5D Enhancement")
    print("=" * 70)
    print()
    
    density_file = os.path.join(os.path.dirname(__file__), "z5d_density_histogram.csv")
    
    start_time = time.time()
    
    result = z5d_enhanced_fr_gva(
        CHALLENGE_127,
        z5d_density_file=density_file,
        k_value=0.35,
        max_candidates=max_candidates,
        delta_window=delta_window,
        z5d_weight_beta=z5d_weight_beta,
        use_wheel_filter=True,
        use_z5d_stepping=True,
        verbose=verbose
    )
    
    elapsed = time.time() - start_time
    
    success = result is not None
    if success:
        p, q = result
        verified = (p * q == CHALLENGE_127)
    else:
        p, q = None, None
        verified = False
    
    metrics = {
        'name': f'Full Z5D (β={z5d_weight_beta})',
        'success': success,
        'verified': verified,
        'elapsed': elapsed,
        'p': p,
        'q': q,
        'max_candidates': max_candidates,
        'delta_window': delta_window,
        'wheel_filter': True,
        'z5d_prior': True,
        'z5d_stepping': True,
        'z5d_weight_beta': z5d_weight_beta,
    }
    
    print_summary(metrics)
    
    return metrics


def print_summary(metrics: dict):
    """Print experiment summary."""
    print()
    print("-" * 70)
    print(f"Experiment: {metrics['name']}")
    print("-" * 70)
    print(f"Success: {metrics['success']}")
    if metrics['success']:
        print(f"  p = {metrics['p']}")
        print(f"  q = {metrics['q']}")
        print(f"  Verified: {metrics['verified']}")
    print(f"Elapsed: {metrics['elapsed']:.3f}s")
    print(f"Max candidates: {metrics['max_candidates']}")
    print(f"Delta window: ±{metrics['delta_window']}")
    print(f"Wheel filter: {metrics['wheel_filter']}")
    print(f"Z5D prior: {metrics['z5d_prior']}")
    print(f"Z5D stepping: {metrics['z5d_stepping']}")
    print("-" * 70)
    print()


def print_comparison_table(all_metrics: list):
    """Print comparison table of all experiments."""
    print()
    print("=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print()
    
    # Table header
    print(f"{'Experiment':<30} {'Success':<10} {'Time (s)':<12} {'Wheel':<8} {'Z5D':<8}")
    print("-" * 70)
    
    # Table rows
    for m in all_metrics:
        success_str = "✓" if m['success'] else "✗"
        time_str = f"{m['elapsed']:.2f}"
        wheel_str = "Yes" if m['wheel_filter'] else "No"
        z5d_str = "Yes" if m['z5d_prior'] else "No"
        
        print(f"{m['name']:<30} {success_str:<10} {time_str:<12} {wheel_str:<8} {z5d_str:<8}")
    
    print("-" * 70)
    print()
    
    # Analysis
    print("ANALYSIS:")
    print()
    
    # Check hypothesis falsification criteria
    baseline = next((m for m in all_metrics if m['name'] == 'Baseline FR-GVA'), None)
    full_z5d = next((m for m in all_metrics if 'Full Z5D' in m['name']), None)
    wheel_only = next((m for m in all_metrics if m['name'] == 'Wheel Filter Only'), None)
    z5d_only = next((m for m in all_metrics if 'Z5D Prior Only' in m['name']), None)
    
    if baseline and full_z5d:
        if baseline['success'] and full_z5d['success']:
            speedup = baseline['elapsed'] / full_z5d['elapsed']
            print(f"Baseline vs Full Z5D speedup: {speedup:.2f}x")
        elif not baseline['success'] and full_z5d['success']:
            print("Full Z5D succeeded where baseline failed ✓")
        elif baseline['success'] and not full_z5d['success']:
            print("Baseline succeeded where Full Z5D failed ✗")
    
    # Wheel filter contribution
    if baseline and wheel_only:
        if wheel_only['success'] and not baseline['success']:
            print("Wheel filter alone enables success ✓")
        elif baseline['success'] and wheel_only['success']:
            if wheel_only['elapsed'] < baseline['elapsed']:
                wheel_speedup = baseline['elapsed'] / wheel_only['elapsed']
                print(f"Wheel filter speedup: {wheel_speedup:.2f}x")
    
    # Z5D prior contribution
    if baseline and z5d_only:
        if z5d_only['success'] and not baseline['success']:
            print("Z5D prior alone enables success ✓")
        elif baseline['success'] and z5d_only['success']:
            if z5d_only['elapsed'] < baseline['elapsed']:
                z5d_speedup = baseline['elapsed'] / z5d_only['elapsed']
                print(f"Z5D prior speedup: {z5d_speedup:.2f}x")
    
    print()


def main():
    """Run full comparison experiment."""
    print("=" * 70)
    print("Z5D-Informed GVA Comparison Experiment")
    print("=" * 70)
    print()
    print(f"Target: N = {CHALLENGE_127}")
    print(f"Expected factors: p = {EXPECTED_P}, q = {EXPECTED_Q}")
    print(f"√N ≈ {isqrt(CHALLENGE_127)}")
    print(f"Expected gap: ḡ ≈ {log(float(isqrt(CHALLENGE_127))):.2f}")
    print()
    print("Running 4 experiments:")
    print("  1. Baseline FR-GVA (no enhancements)")
    print("  2. Wheel filter only")
    print("  3. Z5D prior only")
    print("  4. Full Z5D (all enhancements)")
    print()
    
    # Check for non-interactive mode
    import os
    if os.environ.get('CI') or os.environ.get('NON_INTERACTIVE'):
        print("Running in non-interactive mode...")
    else:
        input("Press Enter to start experiments...")
    print()
    
    # Reduced budget for faster testing
    # In production, use max_candidates=50000+
    MAX_CANDIDATES = 20000
    DELTA_WINDOW = 500000
    Z5D_BETA = 0.1
    
    all_metrics = []
    
    # Experiment 1: Baseline
    m1 = run_baseline_experiment(
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        verbose=False  # Reduced verbosity for comparison
    )
    all_metrics.append(m1)
    
    # Experiment 2: Wheel only
    m2 = run_wheel_only_experiment(
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        verbose=False
    )
    all_metrics.append(m2)
    
    # Experiment 3: Z5D prior only
    m3 = run_z5d_prior_only_experiment(
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        z5d_weight_beta=Z5D_BETA,
        verbose=False
    )
    all_metrics.append(m3)
    
    # Experiment 4: Full Z5D
    m4 = run_full_z5d_experiment(
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        z5d_weight_beta=Z5D_BETA,
        verbose=False
    )
    all_metrics.append(m4)
    
    # Print comparison
    print_comparison_table(all_metrics)
    
    # Export results
    import json
    results_file = os.path.join(os.path.dirname(__file__), "comparison_results.json")
    with open(results_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"Results exported to: {results_file}")
    print()
    
    print("=" * 70)
    print("Experiment complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
