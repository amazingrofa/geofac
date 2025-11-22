"""
Main comparison experiment for deeper recursion hypothesis.

Runs all three methods (baseline, 2-stage, 3-stage) on the 110-bit
test case and compares results.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import json
import time
from typing import Dict, List, Any
from baseline_gva import baseline_gva
from two_stage_prototype import two_stage_gva
from three_stage_prototype import three_stage_gva


def run_comparison_experiment(N: int, verbose: bool = True) -> Dict[str, Any]:
    """
    Run all three methods and compare results.
    
    Args:
        N: Semiprime to factor
        verbose: Enable detailed logging
        
    Returns:
        Dictionary with comparison results
    """
    print(f"\n{'='*70}")
    print(f"Deeper Recursion Hypothesis - Comparison Experiment")
    print(f"{'='*70}")
    print(f"\nTest Case: N = {N}")
    print(f"Bit length: {N.bit_length()}")
    print(f"Expected factors: 36000000000000013 × 36000000000000091")
    print(f"\n{'='*70}")
    
    results = {}
    
    # Run baseline GVA
    print(f"\n{'='*70}")
    print(f"[1/3] Running Baseline GVA...")
    print(f"{'='*70}")
    try:
        baseline_result = baseline_gva(N, verbose=verbose)
        results['baseline'] = baseline_result
    except Exception as e:
        print(f"✗ Baseline failed: {e}")
        results['baseline'] = {'success': False, 'error': str(e)}
    
    # Run 2-stage
    print(f"\n{'='*70}")
    print(f"[2/3] Running 2-Stage GVA (PR #92 simulation)...")
    print(f"{'='*70}")
    try:
        two_stage_result = two_stage_gva(N, segments=32, top_k=16, verbose=verbose)
        results['two_stage'] = two_stage_result
    except Exception as e:
        print(f"✗ 2-stage failed: {e}")
        results['two_stage'] = {'success': False, 'error': str(e)}
    
    # Run 3-stage
    print(f"\n{'='*70}")
    print(f"[3/3] Running 3-Stage GVA (Hypothesis Test)...")
    print(f"{'='*70}")
    try:
        three_stage_result = three_stage_gva(
            N,
            stage1_segments=8,
            stage1_top_k=4,
            stage2_subsegments=4,
            stage2_top_k=2,
            stage2_threshold=0.7,
            early_exit=True,
            verbose=verbose
        )
        results['three_stage'] = three_stage_result
    except Exception as e:
        print(f"✗ 3-stage failed: {e}")
        results['three_stage'] = {'success': False, 'error': str(e)}
    
    # Print comparison summary
    print(f"\n{'='*70}")
    print(f"COMPARISON SUMMARY")
    print(f"{'='*70}")
    
    # Verify all methods found correct factors
    expected_p = 36000000000000013
    expected_q = 36000000000000091
    
    print(f"\n--- Correctness Check ---")
    for method, result in results.items():
        if result.get('success'):
            p, q = result['factors']
            correct = (p == expected_p and q == expected_q) or (p == expected_q and q == expected_p)
            print(f"{method:15s}: {'✓ CORRECT' if correct else '✗ INCORRECT'} ({p} × {q})")
        else:
            print(f"{method:15s}: ✗ FAILED")
    
    print(f"\n--- Runtime Comparison ---")
    baseline_time = results.get('baseline', {}).get('runtime', 0.0)
    
    print(f"{'Method':<15s} {'Runtime':>10s} {'vs Baseline':>15s} {'Speedup':>10s}")
    print(f"{'-'*60}")
    
    for method, result in results.items():
        runtime = result.get('runtime', 0.0)
        if baseline_time > 0:
            speedup = baseline_time / runtime if runtime > 0 else 0.0
            vs_baseline = f"{runtime - baseline_time:+.3f}s"
        else:
            speedup = 0.0
            vs_baseline = "N/A"
        
        print(f"{method:<15s} {runtime:>10.3f}s {vs_baseline:>15s} {speedup:>10.2f}x")
    
    print(f"\n--- Candidate Efficiency ---")
    print(f"{'Method':<15s} {'Total Candidates':>18s} {'Coverage':>10s}")
    print(f"{'-'*60}")
    
    for method, result in results.items():
        total_cands = result.get('total_candidates', result.get('candidates_tested', 0))
        coverage = result.get('coverage', 0.0)
        print(f"{method:<15s} {total_cands:>18d} {coverage:>9.1f}%")
    
    # Hypothesis verdict
    print(f"\n{'='*70}")
    print(f"HYPOTHESIS VERDICT")
    print(f"{'='*70}")
    
    three_stage_success = results.get('three_stage', {}).get('success', False)
    three_stage_runtime = results.get('three_stage', {}).get('runtime', float('inf'))
    baseline_runtime = results.get('baseline', {}).get('runtime', 0.0)
    two_stage_runtime = results.get('two_stage', {}).get('runtime', float('inf'))
    
    print(f"\nHypothesis: 3-stage recursion with dynamic thresholds can reduce")
    print(f"            runtime below baseline (< {baseline_runtime:.3f}s) on 110-bit semiprimes.")
    
    if three_stage_success and three_stage_runtime < baseline_runtime:
        print(f"\n✓✓✓ HYPOTHESIS SUPPORTED ✓✓✓")
        print(f"\n3-stage runtime ({three_stage_runtime:.3f}s) < baseline ({baseline_runtime:.3f}s)")
        print(f"Speedup: {baseline_runtime / three_stage_runtime:.2f}x")
        print(f"Factors recovered correctly ✓")
        verdict = "SUPPORTED"
    elif not three_stage_success:
        print(f"\n✗✗✗ HYPOTHESIS FALSIFIED ✗✗✗")
        print(f"\n3-stage failed to recover factors")
        print(f"Early exit: {results.get('three_stage', {}).get('early_exited', False)}")
        verdict = "FALSIFIED_CORRECTNESS"
    elif three_stage_runtime >= baseline_runtime:
        print(f"\n✗✗✗ HYPOTHESIS FALSIFIED ✗✗✗")
        print(f"\n3-stage runtime ({three_stage_runtime:.3f}s) ≥ baseline ({baseline_runtime:.3f}s)")
        print(f"No runtime improvement achieved")
        if three_stage_runtime < two_stage_runtime:
            print(f"Note: 3-stage is faster than 2-stage ({two_stage_runtime:.3f}s)")
        verdict = "FALSIFIED_RUNTIME"
    else:
        print(f"\n⚠ INCONCLUSIVE")
        verdict = "INCONCLUSIVE"
    
    # Package experiment results
    experiment_output = {
        'test_case': {
            'N': str(N),
            'bit_length': N.bit_length(),
            'expected_p': expected_p,
            'expected_q': expected_q
        },
        'results': results,
        'verdict': verdict,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return experiment_output


def save_results(experiment_data: Dict[str, Any], filename: str = "experiment_results.json"):
    """Save experiment results to JSON file."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    # Convert non-serializable types
    serializable_data = {}
    for key, value in experiment_data.items():
        if key == 'results':
            serializable_data[key] = {}
            for method, result in value.items():
                serializable_data[key][method] = {}
                for rkey, rvalue in result.items():
                    if rkey == 'factors' and rvalue is not None:
                        serializable_data[key][method][rkey] = [int(rvalue[0]), int(rvalue[1])]
                    else:
                        serializable_data[key][method][rkey] = rvalue
        else:
            serializable_data[key] = value
    
    with open(filepath, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    print(f"\nResults saved to {filepath}")


if __name__ == "__main__":
    # Run experiment on the 110-bit test case
    N = 1296000000000003744000000000001183
    
    experiment_data = run_comparison_experiment(N, verbose=True)
    
    # Save results
    save_results(experiment_data)
    
    print(f"\n{'='*70}")
    print(f"Experiment complete. See EXPERIMENT_SUMMARY.md for full analysis.")
    print(f"{'='*70}")
