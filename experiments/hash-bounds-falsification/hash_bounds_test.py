"""
Hash-Bounds Falsification Experiment
=====================================

Objective: Falsify the hypothesis that hash-bounds derived from bounded fractional
parts {√p} can predict useful bounds for locating factor d in semiprime N = p × q.

Hypothesis Claims to Test:
1. SHA-256-like constants derived from {√p} can predict bounds for factor d
2. Z5D prime predictions establish geometric bounds on fractional parts {√p}
3. Calibrated metrics: mean relative error ~22,126 ppm, avg fractional errors ~0.237,
   width factor 0.155 yields ~51.5% coverage
4. θ'(n,k) = φ·((n mod φ)/φ)^k with k=0.3 approximates Z5D predictions

Key Claims from Issue:
- Actual {√p} ≈ 0.228200298... for p=10508623501177419659 (CHALLENGE_127 smaller factor)
- Mock Z5D prediction {√(m·ln(m))} ≈ 0.878727625... where m ≈ p/ln(p)
- Bound interval [0.801, 0.956] with width=0.155 should capture factor ~50% of time

Falsification Criteria:
1. The proposed bounds systematically miss the actual factor's fractional part
2. Coverage rates < 30% (significantly below claimed 51.5%)
3. The method provides no predictive signal vs random baseline

Reproducibility:
- Fixed seed: 42
- mpmath precision: adaptive (max(configured, N.bit_length() × 4 + 200))
- Deterministic computations
- All parameters logged with timestamps
"""

import mpmath as mp
from mpmath import mpf, sqrt, log, floor
from typing import Dict, Any, Tuple
from datetime import datetime
import json

# Golden ratio
PHI = (1 + mp.sqrt(5)) / 2

# Parts per million multiplier for relative error reporting
PPM_MULTIPLIER = 1e6


def compute_adaptive_precision(n: int, min_precision: int = 50) -> int:
    """
    Compute adaptive precision following geofac convention:
    precision = max(configured, N.bit_length() × 4 + 200)
    
    Args:
        n: The number being analyzed
        min_precision: Minimum precision floor
        
    Returns:
        Computed precision in decimal places
    """
    bit_length = n.bit_length()
    adaptive = bit_length * 4 + 200
    return max(min_precision, adaptive)


def fractional_part(x: mpf) -> mpf:
    """
    Compute the fractional part of x: {x} = x - floor(x)
    
    Args:
        x: Input value
        
    Returns:
        Fractional part in [0, 1)
    """
    return x - floor(x)


def theta_prime(n: int, k: float = 0.3) -> mpf:
    """
    Geometric prime-density mapping: θ'(n,k) = φ·((n mod φ)/φ)^k
    
    This is the Z5D approximation function from the hypothesis.
    
    Args:
        n: Integer parameter
        k: Geodesic exponent (default 0.3)
        
    Returns:
        Geodesic-transformed value
    """
    n_mod_phi = mpf(n) % PHI
    ratio = n_mod_phi / PHI
    result = PHI * (ratio ** mpf(k))
    return result


def compute_mock_z5d_prediction(p: int) -> mpf:
    """
    Compute mock Z5D prediction for fractional part based on hypothesis.
    
    Formula: {√(m·ln(m))} where m ≈ p/ln(p)
    
    This represents the claimed Z5D prime density prediction mechanism.
    
    Args:
        p: Prime factor
        
    Returns:
        Predicted fractional part
    """
    ln_p = log(mpf(p))
    m = mpf(p) / ln_p
    m_ln_m = m * log(m)
    sqrt_m_ln_m = sqrt(m_ln_m)
    return fractional_part(sqrt_m_ln_m)


def compute_hash_bounds(center: mpf, width: float = 0.155) -> Tuple[mpf, mpf]:
    """
    Compute hash-bounds interval centered on prediction.
    
    The hypothesis claims width factor 0.155 yields ~51.5% coverage.
    
    Args:
        center: Center of the bound interval (predicted {√p})
        width: Width factor (default 0.155 from hypothesis)
        
    Returns:
        Tuple (lower_bound, upper_bound)
    """
    half_width = mpf(width) / 2
    lower = center - half_width
    upper = center + half_width
    return (lower, upper)


def is_in_bounds(value: mpf, lower: mpf, upper: mpf) -> bool:
    """
    Check if value falls within bounds.
    
    Handles wraparound for fractional parts (e.g., if bounds cross 0 or 1).
    
    Args:
        value: Value to check
        lower: Lower bound
        upper: Upper bound
        
    Returns:
        True if value is within bounds
    """
    # Handle wraparound cases
    if lower < 0:
        # Bounds wrap around 0: [lower+1, 1) ∪ [0, upper]
        return value >= lower + 1 or value <= upper
    elif upper > 1:
        # Bounds wrap around 1: [lower, 1) ∪ [0, upper-1]
        return value >= lower or value <= upper - 1
    else:
        # Normal case
        return lower <= value <= upper


def compute_random_baseline_coverage(
    width: float, num_samples: int = 10000, seed: int = 42
) -> float:
    """
    Compute expected random baseline coverage for given width.
    
    For uniformly distributed values in [0, 1), an interval of width w
    should capture a fraction w of values.
    
    Args:
        width: Width of the interval
        num_samples: Number of samples for Monte Carlo estimation
        seed: Random seed
        
    Returns:
        Expected coverage rate for random baseline
    """
    # For uniform distribution, expected coverage = width (up to 1.0)
    return min(width, 1.0)


def analyze_validation_gate(
    gate_name: str,
    n: int,
    p: int,
    q: int,
    width_factor: float = 0.155,
    k_value: float = 0.3,
) -> Dict[str, Any]:
    """
    Analyze a single validation gate against hash-bounds hypothesis.
    
    Args:
        gate_name: Name of the validation gate
        n: Semiprime N = p × q
        p: Smaller prime factor
        q: Larger prime factor  
        width_factor: Width of hash-bounds interval
        k_value: Parameter k for θ'(n,k)
        
    Returns:
        Dict with analysis results
    """
    # Set adaptive precision
    precision = compute_adaptive_precision(n)
    mp.dps = precision
    
    # Verify inputs
    assert p * q == n, f"p × q != N: {p} × {q} = {p * q} != {n}"
    assert p < q, f"Expected p < q, got p={p}, q={q}"
    
    # Compute actual fractional parts
    sqrt_p = sqrt(mpf(p))
    sqrt_q = sqrt(mpf(q))
    actual_frac_p = fractional_part(sqrt_p)
    actual_frac_q = fractional_part(sqrt_q)
    
    # Compute Z5D predictions
    z5d_pred_p = compute_mock_z5d_prediction(p)
    z5d_pred_q = compute_mock_z5d_prediction(q)
    
    # Compute θ'(n,k) predictions
    sqrt_n = sqrt(mpf(n))
    sqrt_n_floor = int(floor(sqrt_n))
    theta_val = theta_prime(sqrt_n_floor, k_value)
    theta_pred_frac = fractional_part(theta_val)
    
    # Compute hash-bounds for both factors
    bounds_p = compute_hash_bounds(z5d_pred_p, width_factor)
    bounds_q = compute_hash_bounds(z5d_pred_q, width_factor)
    
    # Check if actual values fall within bounds
    p_in_bounds = is_in_bounds(actual_frac_p, bounds_p[0], bounds_p[1])
    q_in_bounds = is_in_bounds(actual_frac_q, bounds_q[0], bounds_q[1])
    
    # Compute prediction errors
    error_p = abs(float(actual_frac_p - z5d_pred_p))
    error_q = abs(float(actual_frac_q - z5d_pred_q))
    
    # Relative error (in ppm)
    rel_error_p = error_p * PPM_MULTIPLIER if actual_frac_p != 0 else float('inf')
    rel_error_q = error_q * PPM_MULTIPLIER if actual_frac_q != 0 else float('inf')
    
    # Random baseline comparison
    random_coverage = compute_random_baseline_coverage(width_factor)
    
    results = {
        "gate_name": gate_name,
        "n": str(n),
        "p": str(p),
        "q": str(q),
        "n_bit_length": n.bit_length(),
        "precision_dps": precision,
        
        # Actual fractional parts
        "actual_frac_p": float(actual_frac_p),
        "actual_frac_q": float(actual_frac_q),
        
        # Z5D predictions
        "z5d_pred_p": float(z5d_pred_p),
        "z5d_pred_q": float(z5d_pred_q),
        
        # θ'(n,k) prediction
        "theta_prime_value": float(theta_val),
        "theta_pred_frac": float(theta_pred_frac),
        
        # Hash-bounds
        "bounds_p_lower": float(bounds_p[0]),
        "bounds_p_upper": float(bounds_p[1]),
        "bounds_q_lower": float(bounds_q[0]),
        "bounds_q_upper": float(bounds_q[1]),
        "width_factor": width_factor,
        
        # Coverage results
        "p_in_bounds": p_in_bounds,
        "q_in_bounds": q_in_bounds,
        
        # Prediction errors
        "error_p": error_p,
        "error_q": error_q,
        "rel_error_p_ppm": rel_error_p,
        "rel_error_q_ppm": rel_error_q,
        
        # Random baseline
        "random_baseline_coverage": random_coverage,
    }
    
    return results


def run_experiment(seed: int = 42) -> Dict[str, Any]:
    """
    Run the complete hash-bounds falsification experiment.
    
    Tests three validation gates:
    1. Gate 1 (30-bit): Quick sanity check
    2. Gate 2 (60-bit): Scaling validation  
    3. Gate 3 (127-bit): Challenge verification
    
    Args:
        seed: Random seed for reproducibility
        
    Returns:
        Complete experiment results
    """
    print("=" * 80)
    print("HASH-BOUNDS FALSIFICATION EXPERIMENT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Seed: {seed}")
    print()
    
    # Define validation gates
    validation_gates = [
        {
            "name": "Gate 1 (30-bit)",
            "n": 1073217479,
            "p": 32749,
            "q": 32771,
        },
        {
            "name": "Gate 2 (60-bit)",
            "n": 1152921470247108503,
            "p": 1073741789,
            "q": 1073741827,
        },
        {
            "name": "Gate 3 (127-bit CHALLENGE)",
            "n": 137524771864208156028430259349934309717,
            "p": 10508623501177419659,
            "q": 13086849276577416863,
        },
    ]
    
    # Run analysis on each gate
    gate_results = []
    
    for gate in validation_gates:
        print(f"Analyzing {gate['name']}...")
        precision = compute_adaptive_precision(gate['n'])
        print(f"  N = {gate['n']}")
        print(f"  p = {gate['p']}, q = {gate['q']}")
        print(f"  Bit length: {gate['n'].bit_length()}")
        print(f"  Adaptive precision: {precision} dps")
        
        result = analyze_validation_gate(
            gate_name=gate['name'],
            n=gate['n'],
            p=gate['p'],
            q=gate['q'],
        )
        
        gate_results.append(result)
        
        # Display key findings
        print(f"  Actual {{√p}} = {result['actual_frac_p']:.12f}")
        print(f"  Z5D prediction = {result['z5d_pred_p']:.12f}")
        print(f"  Bounds: [{result['bounds_p_lower']:.3f}, {result['bounds_p_upper']:.3f}]")
        print(f"  p in bounds: {result['p_in_bounds']}")
        print(f"  Error: {result['error_p']:.6f}")
        print()
    
    # Compute aggregate statistics
    total_gates = len(gate_results)
    p_coverage_count = sum(1 for r in gate_results if r['p_in_bounds'])
    q_coverage_count = sum(1 for r in gate_results if r['q_in_bounds'])
    total_factor_coverage = (p_coverage_count + q_coverage_count) / (2 * total_gates)
    
    avg_error_p = sum(r['error_p'] for r in gate_results) / total_gates
    avg_error_q = sum(r['error_q'] for r in gate_results) / total_gates
    avg_error = (avg_error_p + avg_error_q) / 2
    
    avg_rel_error_ppm = sum(
        r['rel_error_p_ppm'] + r['rel_error_q_ppm'] 
        for r in gate_results
    ) / (2 * total_gates)
    
    # Determine verdict
    claimed_coverage = 0.515  # 51.5% from hypothesis
    claimed_error_ppm = 22126  # From hypothesis
    
    # Falsification criteria
    coverage_threshold = 0.30  # 30% threshold
    
    is_falsified = (
        total_factor_coverage < coverage_threshold or
        p_coverage_count == 0  # Zero coverage on p factors
    )
    
    verdict = "FALSIFIED" if is_falsified else "INCONCLUSIVE"
    if total_factor_coverage >= claimed_coverage:
        verdict = "SUPPORTED"
    
    # Summary statistics
    summary = {
        "total_gates": total_gates,
        "p_coverage_count": p_coverage_count,
        "q_coverage_count": q_coverage_count,
        "total_factors_tested": 2 * total_gates,
        "factors_in_bounds": p_coverage_count + q_coverage_count,
        "coverage_rate": total_factor_coverage,
        "claimed_coverage": claimed_coverage,
        "coverage_threshold_for_falsification": coverage_threshold,
        "avg_absolute_error": avg_error,
        "avg_relative_error_ppm": avg_rel_error_ppm,
        "claimed_error_ppm": claimed_error_ppm,
        "random_baseline_coverage": 0.155,  # Width factor
        "verdict": verdict,
    }
    
    # Display summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Factors tested: {summary['total_factors_tested']}")
    print(f"Factors in bounds: {summary['factors_in_bounds']}")
    print(f"Coverage rate: {summary['coverage_rate'] * 100:.1f}%")
    print(f"Claimed coverage: {summary['claimed_coverage'] * 100:.1f}%")
    print(f"Random baseline: {summary['random_baseline_coverage'] * 100:.1f}%")
    print(f"Average absolute error: {summary['avg_absolute_error']:.6f}")
    print()
    print(f"VERDICT: {verdict}")
    print()
    
    # Compile experiment output
    experiment_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "seed": seed,
            "hypothesis": "Hash-bounds from Z5D fractional part predictions",
            "width_factor": 0.155,
            "k_value": 0.3,
        },
        "validation_gates": validation_gates,
        "gate_results": gate_results,
        "summary": summary,
    }
    
    return experiment_results


def save_results(results: Dict[str, Any], output_path: str):
    """Save experiment results to JSON file."""
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    # Run experiment
    results = run_experiment(seed=42)
    
    # Save results
    output_path = "results.json"
    save_results(results, output_path)
    
    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)
