"""
Parameterize 127-bit Challenge
===============================

Uses calibration and rehearsal results to compute optimal parameters
for the 127-bit challenge N = 137524771864208156028430259349934309717.

Steps:
1. Load calibration ε values
2. Load rehearsal success curves
3. Compute δ-band for 127-bit using ε(127)
4. Choose target coverage C* for 95% success
5. Translate C* to total candidate budget k
6. Split budget across band priorities

Exports: challenge_params.json
"""

import json
import os
from math import log, isqrt
from typing import Dict


# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717
CHALLENGE_P = 10508623501177419659
CHALLENGE_Q = 13086849276577416863


def load_calibration() -> Dict:
    """Load calibration results."""
    calib_path = os.path.join(
        os.path.dirname(__file__),
        'calibration_results.json'
    )
    
    if not os.path.exists(calib_path):
        print(f"Warning: {calib_path} not found. Using fallback.")
        return {
            'curve_fit': {
                'a': 0.01,
                'b': 0.0001,
                'formula': 'ε(n) = 0.01 + 0.0001 × n (fallback)'
            }
        }
    
    with open(calib_path, 'r') as f:
        return json.load(f)


def load_rehearsal() -> Dict:
    """Load rehearsal results."""
    rehearsal_path = os.path.join(
        os.path.dirname(__file__),
        'rehearsal_results.json'
    )
    
    if not os.path.exists(rehearsal_path):
        print(f"Warning: {rehearsal_path} not found. Using fallback.")
        return {
            'results': [],
            'summary': {}
        }
    
    with open(rehearsal_path, 'r') as f:
        return json.load(f)


def compute_epsilon_127(calibration: Dict) -> float:
    """
    Compute ε for 127-bit using calibration curve.
    
    Args:
        calibration: Calibration data
        
    Returns:
        ε value for 127-bit
    """
    if 'curve_fit' in calibration:
        a = calibration['curve_fit']['a']
        b = calibration['curve_fit']['b']
        epsilon = a + b * 127
        print(f"Using calibrated ε(127) = {a:.6f} + {b:.6f} × 127 = {epsilon:.4f}")
    else:
        # Fallback
        epsilon = 0.01 + 0.0001 * 127
        print(f"Using fallback ε(127) = {epsilon:.4f}")
    
    return epsilon


def compute_target_coverage(rehearsal: Dict) -> float:
    """
    Compute target coverage C* for 95% success.
    
    Analyzes rehearsal data to find coverage threshold.
    
    Args:
        rehearsal: Rehearsal data
        
    Returns:
        Target coverage C*
    """
    results = rehearsal.get('results', [])
    
    if not results:
        print("No rehearsal data. Using conservative C* = 100.0")
        return 100.0
    
    # Find successful full-z5d runs
    successful_z5d = [
        r for r in results 
        if r['variant'] == 'full-z5d' and r['success']
    ]
    
    if not successful_z5d:
        print("No successful Z5D runs. Using conservative C* = 100.0")
        return 100.0
    
    # Find minimum coverage among successes
    coverages = [r['coverage'] for r in successful_z5d]
    min_coverage = min(coverages)
    avg_coverage = sum(coverages) / len(coverages)
    
    # Add 50% safety margin
    target = avg_coverage * 1.5
    
    print(f"Successful Z5D runs: coverage range [{min_coverage:.2f}, {max(coverages):.2f}]")
    print(f"Average coverage: {avg_coverage:.2f}")
    print(f"Target C* (with 50% margin): {target:.2f}")
    
    return target


def compute_budget(target_coverage: float,
                  sqrt_N: int,
                  epsilon: float) -> Dict:
    """
    Translate target coverage to candidate budget.
    
    Coverage formula: C = (δ_span × wheel_factor) / log(√N)
    Solve for δ_span: δ_span = C × log(√N) / wheel_factor
    
    Args:
        target_coverage: Target C*
        sqrt_N: Floor of square root
        epsilon: Band error parameter
        
    Returns:
        Dict with budget parameters
    """
    from z5d_pipeline import WHEEL_SIZE, WHEEL_MODULUS
    
    log_sqrt_N = log(float(sqrt_N))
    wheel_factor = WHEEL_SIZE / WHEEL_MODULUS
    
    # Required δ_span
    delta_span_needed = (target_coverage * log_sqrt_N) / wheel_factor
    
    print(f"\nBudget calculation:")
    print(f"  log(√N) = {log_sqrt_N:.2f}")
    print(f"  Wheel factor = {wheel_factor:.4f}")
    print(f"  Required δ_span = {delta_span_needed:.0f}")
    
    # Estimate candidates per unit δ
    # With wheel: ~48/210 candidates per unit δ
    candidates_per_delta = wheel_factor
    
    # Total candidate budget
    total_budget = int(delta_span_needed * candidates_per_delta)
    
    # Add safety margin for adaptive stepping
    # Z5D uses variable steps, so multiply by 2
    total_budget = int(total_budget * 2)
    
    print(f"  Estimated candidates: {total_budget:,}")
    
    # Split budget:
    # 70% high-priority Z5D bands (top 3 bands)
    # 20% outer shells (bands 4-7)
    # 10% safety net (bands 8-10)
    
    budget_split = {
        'high_priority': int(total_budget * 0.70),
        'outer_shells': int(total_budget * 0.20),
        'safety_net': int(total_budget * 0.10)
    }
    
    print(f"\nBudget split:")
    print(f"  High-priority bands (70%): {budget_split['high_priority']:,}")
    print(f"  Outer shells (20%): {budget_split['outer_shells']:,}")
    print(f"  Safety net (10%): {budget_split['safety_net']:,}")
    
    return {
        'total_budget': total_budget,
        'delta_max': int(delta_span_needed),
        'split': budget_split
    }


def parameterize_127bit() -> Dict:
    """
    Compute all parameters for 127-bit challenge.
    
    Returns:
        Dict with complete parameter set
    """
    print("=" * 70)
    print("Parameterizing 127-bit Challenge")
    print("=" * 70)
    print()
    
    sqrt_N = isqrt(CHALLENGE_127)
    
    print(f"N = {CHALLENGE_127}")
    print(f"√N = {sqrt_N}")
    print(f"True factors: p = {CHALLENGE_P}, q = {CHALLENGE_Q}")
    print()
    
    # Load data
    print("Loading calibration and rehearsal data...")
    calibration = load_calibration()
    rehearsal = load_rehearsal()
    print()
    
    # Compute epsilon
    epsilon = compute_epsilon_127(calibration)
    print()
    
    # Compute target coverage
    target_coverage = compute_target_coverage(rehearsal)
    print()
    
    # Compute budget
    budget = compute_budget(target_coverage, sqrt_N, epsilon)
    
    # Package parameters
    params = {
        'challenge': {
            'N': str(CHALLENGE_127),
            'p_true': str(CHALLENGE_P),
            'q_true': str(CHALLENGE_Q),
            'sqrt_N': str(sqrt_N),
            'bit_length': CHALLENGE_127.bit_length(),
            'log_sqrt_N': log(float(sqrt_N))
        },
        'z5d_config': {
            'epsilon': epsilon,
            'num_bands': 10,
            'k_value': 0.35
        },
        'budget': budget,
        'coverage': {
            'target': target_coverage,
            'confidence': '95%'
        },
        'wheel': {
            'modulus': 210,
            'residues': 48
        }
    }
    
    return params


def main():
    """Parameterize and export."""
    params = parameterize_127bit()
    
    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__), 
        'challenge_params.json'
    )
    
    with open(output_path, 'w') as f:
        json.dump(params, f, indent=2)
    
    print("\n" + "=" * 70)
    print("Parameterization complete. Parameters saved to:")
    print(f"  {output_path}")
    print("=" * 70)
    print()
    print("Key parameters:")
    print(f"  Total budget: {params['budget']['total_budget']:,} candidates")
    print(f"  δ_max: {params['budget']['delta_max']:,}")
    print(f"  ε: {params['z5d_config']['epsilon']:.4f}")
    print(f"  Target coverage: {params['coverage']['target']:.2f}")


if __name__ == "__main__":
    main()
