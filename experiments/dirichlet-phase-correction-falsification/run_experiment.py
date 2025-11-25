"""
Dirichlet Phase Correction Falsification — Gate 2 Analysis
===========================================================

Tests whether the Dirichlet-kernel phase correction is blocking resonance lock
in Gate 2 attempts by analyzing residual phase curvature and applying global
phase shift correction.

Gate 2: N = 1152921470247108503 (60-bit semiprime)
Expected factors: p = 1073741789, q = 1073741827

Hypothesis: Residual phase Δφ shows systematic curvature correctable by
φ_shift = α × ln(N)/e²

Acceptance criteria:
- |a| (curvature coefficient) drops by ≥5× after correction
- Residual RMS drops by ≥2× after correction
"""

import mpmath as mp
import math
import json
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configure seed for reproducibility
SEED = 42
np.random.seed(SEED)

# Gate 2 parameters
GATE_2_N = 1152921470247108503
EXPECTED_P = 1073741789
EXPECTED_Q = 1073741827

# Phase correction sweep parameters
ALPHA_RANGE_INITIAL = (-0.5, 0.5)
ALPHA_RANGE_EXTENDED = (-2.0, 2.0)
ALPHA_STEPS = 101  # Number of α values to test

# Sampling parameters
SAMPLE_WINDOW = 1000  # ±1000 around sqrt(N)

# Precomputed constants for efficiency
E_SQUARED = math.e ** 2


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bitLength() × 4 + 200)
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def wrap_to_pi(angle: float) -> float:
    """
    Wrap angle to [-π, π] range.
    
    Args:
        angle: Angle in radians
        
    Returns:
        Angle wrapped to [-π, π]
    """
    return (angle + math.pi) % (2 * math.pi) - math.pi


def embed_torus_geodesic(n: int, k: float = 0.35, dimensions: int = 7) -> List[mp.mpf]:
    """
    Embed integer n into a 7D torus using golden ratio geodesic mapping.
    
    Args:
        n: Integer to embed
        k: Geodesic exponent (default 0.35)
        dimensions: Torus dimensions (default 7)
        
    Returns:
        List of coordinates in 7D torus [0,1)^7
    """
    phi = mp.mpf(1 + mp.sqrt(5)) / 2  # Golden ratio
    
    coords = []
    for d in range(dimensions):
        phi_power = phi ** (d + 1)
        coord = mp.fmod(n * phi_power, 1)
        if abs(k - 1.0) > 1e-15:  # Use tolerance for float comparison
            coord = mp.power(coord, k)
            coord = mp.fmod(coord, 1)
        coords.append(coord)
    
    return coords


def compute_phase_from_embedding(coords: List[mp.mpf]) -> float:
    """
    Compute phase angle from 7D torus embedding.
    
    The phase is derived from the first two coordinates mapped to a 2D angle.
    This captures the primary angular structure of the embedding.
    
    Args:
        coords: 7D torus coordinates
        
    Returns:
        Phase angle in radians
    """
    # Use first two coordinates to compute primary phase
    x = float(coords[0])
    y = float(coords[1])
    
    # Map [0,1) to [-1,1) and compute angle
    x_centered = 2 * x - 1
    y_centered = 2 * y - 1
    
    phase = math.atan2(y_centered, x_centered)
    return phase


def compute_predicted_phase(m: int, N: int, sqrt_N: int) -> float:
    """
    Compute the predicted phase based on a linear position-to-phase mapping.
    
    Maps the candidate's position relative to sqrt(N) to a predicted phase angle.
    This linear mapping serves as a baseline: if the embedding phase followed
    position linearly, residuals would be zero. Deviations indicate geometric
    structure in the embedding.
    
    Args:
        m: Candidate factor
        N: Semiprime to factor
        sqrt_N: Integer square root of N
        
    Returns:
        Predicted phase in radians [-π, π]
    """
    # Normalized offset from sqrt(N) in range [-1, 1]
    delta = m - sqrt_N
    normalized_delta = delta / SAMPLE_WINDOW
    
    # Linear position-to-phase mapping: delta ∈ [-1, 1] → phase ∈ [-π, π]
    predicted_phase = normalized_delta * math.pi
    
    return predicted_phase


def sample_phase_data(N: int, sqrt_N: int, k: float = 0.35, 
                      verbose: bool = True) -> Dict:
    """
    Sample phase measurements across candidates around sqrt(N).
    
    Args:
        N: Semiprime to factor
        sqrt_N: Integer square root of N
        k: Geodesic exponent for embedding
        verbose: Print progress
        
    Returns:
        Dictionary with phase data and statistics
    """
    data = {
        "candidates": [],
        "normalized_x": [],  # m/N
        "phi_meas": [],
        "phi_pred": [],
        "dphi": [],  # residual phase
    }
    
    # Sample around sqrt(N)
    start = sqrt_N - SAMPLE_WINDOW
    end = sqrt_N + SAMPLE_WINDOW + 1
    
    if verbose:
        print(f"Sampling phase data from m = {start:,} to {end:,}")
        print(f"Using k = {k}, dimensions = 7")
    
    for m in range(start, end):
        if m <= 1 or m >= N:
            continue
        
        # Embed candidate in 7D torus
        coords = embed_torus_geodesic(m, k)
        
        # Compute measured phase from embedding
        phi_meas = compute_phase_from_embedding(coords)
        
        # Compute predicted phase from geometric model
        phi_pred = compute_predicted_phase(m, N, sqrt_N)
        
        # Compute residual phase
        dphi = wrap_to_pi(phi_meas - phi_pred)
        
        # Store data
        data["candidates"].append(m)
        data["normalized_x"].append(m / N)
        data["phi_meas"].append(phi_meas)
        data["phi_pred"].append(phi_pred)
        data["dphi"].append(dphi)
    
    if verbose:
        print(f"Collected {len(data['candidates'])} samples")
    
    return data


def fit_quadratic(x: List[float], y: List[float]) -> Tuple[float, float, float, float]:
    """
    Fit quadratic curve y = ax² + bx + c.
    
    Args:
        x: Independent variable values
        y: Dependent variable values
        
    Returns:
        Tuple (a, b, c, r_squared)
    """
    x_arr = np.array(x)
    y_arr = np.array(y)
    
    # Center x for numerical stability
    x_mean = np.mean(x_arr)
    x_centered = x_arr - x_mean
    
    # Fit polynomial with error handling for numerical instability
    try:
        coeffs = np.polyfit(x_centered, y_arr, 2)
        a, b, c = coeffs
        
        # Compute R²
        y_pred = np.polyval(coeffs, x_centered)
        ss_res = np.sum((y_arr - y_pred) ** 2)
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    except (np.linalg.LinAlgError, ValueError):
        # Return zeros if fitting fails due to numerical issues
        return 0.0, 0.0, float(np.mean(y_arr)), 0.0
    
    return float(a), float(b), float(c), float(r_squared)


def compute_rms(values: List[float]) -> float:
    """Compute root mean square of values."""
    if not values:
        return 0.0
    arr = np.array(values)
    return float(np.sqrt(np.mean(arr ** 2)))


def calculate_improvement_ratio(baseline: float, optimized: float) -> float:
    """
    Calculate improvement ratio of baseline over optimized value.
    
    Args:
        baseline: Baseline metric value
        optimized: Optimized metric value
        
    Returns:
        Ratio baseline/optimized, or infinity if optimized is zero
    """
    if optimized > 0:
        return baseline / optimized
    return float('inf')


def apply_phase_correction(phi_meas: List[float], phi_pred: List[float], 
                           alpha: float, N: int) -> List[float]:
    """
    Apply global phase shift correction.
    
    φ_shift = α × ln(N) / e²
    Δφ_corrected = wrap_to_pi((φ_meas + φ_shift) - φ_pred)
    
    Args:
        phi_meas: Measured phase values
        phi_pred: Predicted phase values
        alpha: Phase correction coefficient
        N: Semiprime value
        
    Returns:
        Corrected residual phase values
    """
    phi_shift = alpha * math.log(N) / E_SQUARED
    
    dphi_corrected = []
    for pm, pp in zip(phi_meas, phi_pred):
        corrected = wrap_to_pi((pm + phi_shift) - pp)
        dphi_corrected.append(corrected)
    
    return dphi_corrected


def sweep_alpha(data: Dict, N: int, alpha_range: Tuple[float, float],
                num_steps: int, verbose: bool = True) -> List[Dict]:
    """
    Sweep α values and compute metrics for each.
    
    Args:
        data: Phase data from sample_phase_data
        N: Semiprime value
        alpha_range: (min_alpha, max_alpha) tuple
        num_steps: Number of α values to test
        verbose: Print progress
        
    Returns:
        List of metrics dictionaries for each α value
    """
    alpha_min, alpha_max = alpha_range
    alpha_values = np.linspace(alpha_min, alpha_max, num_steps)
    
    results = []
    
    if verbose:
        print(f"\nSweeping α from {alpha_min} to {alpha_max} ({num_steps} steps)")
    
    for i, alpha in enumerate(alpha_values):
        # Apply phase correction
        dphi_corrected = apply_phase_correction(
            data["phi_meas"], data["phi_pred"], alpha, N
        )
        
        # Fit quadratic to corrected residuals
        a, b, c, r_sq = fit_quadratic(data["normalized_x"], dphi_corrected)
        
        # Compute RMS
        rms = compute_rms(dphi_corrected)
        
        results.append({
            "alpha": float(alpha),
            "curvature_a": float(a),
            "linear_b": float(b),
            "constant_c": float(c),
            "r_squared": float(r_sq),
            "rms": float(rms),
            "abs_curvature": abs(float(a)),
        })
        
        if verbose and (i % 20 == 0 or i == num_steps - 1):
            print(f"  α={alpha:.3f}: |a|={abs(a):.6e}, RMS={rms:.6e}")
    
    return results


def find_optimal_alpha(sweep_results: List[Dict]) -> Dict:
    """
    Find the α value that minimizes |curvature|.
    
    Args:
        sweep_results: Results from sweep_alpha
        
    Returns:
        Dictionary with optimal α and its metrics
    """
    min_curvature = float('inf')
    optimal = None
    
    for result in sweep_results:
        if result["abs_curvature"] < min_curvature:
            min_curvature = result["abs_curvature"]
            optimal = result
    
    return optimal


def run_experiment(verbose: bool = True) -> Dict:
    """
    Run the Dirichlet phase correction falsification experiment.
    
    Tests whether phase correction reduces curvature and RMS in residual phase.
    
    Args:
        verbose: Print detailed output
        
    Returns:
        Complete experiment results dictionary
    """
    N = GATE_2_N
    sqrt_N = int(math.isqrt(N))
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    mp.mp.dps = required_dps
    
    if verbose:
        print("=" * 70)
        print("Dirichlet Phase Correction Falsification — Gate 2 Analysis")
        print("=" * 70)
        print(f"N = {N:,}")
        print(f"sqrt(N) = {sqrt_N:,}")
        print(f"Expected p = {EXPECTED_P:,}")
        print(f"Expected q = {EXPECTED_Q:,}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Adaptive precision: {required_dps} dps")
        print(f"Seed: {SEED}")
        print(f"Sample window: ±{SAMPLE_WINDOW}")
        print()
    
    start_time = time.time()
    
    # Initialize results structure
    results = {
        "experiment": "dirichlet-phase-correction-falsification",
        "timestamp": datetime.now().isoformat(),
        "seed": SEED,
        "gate": "Gate 2 (60-bit)",
        "N": N,
        "sqrt_N": sqrt_N,
        "expected_p": EXPECTED_P,
        "expected_q": EXPECTED_Q,
        "bit_length": N.bit_length(),
        "precision_dps": required_dps,
        "sample_window": SAMPLE_WINDOW,
        "alpha_range_initial": list(ALPHA_RANGE_INITIAL),
        "alpha_range_extended": list(ALPHA_RANGE_EXTENDED),
        "alpha_steps": ALPHA_STEPS,
    }
    
    # Step 1: Sample phase data
    if verbose:
        print("Step 1: Sampling phase data")
        print("-" * 40)
    
    phase_data = sample_phase_data(N, sqrt_N, k=0.35, verbose=verbose)
    results["samples_collected"] = len(phase_data["candidates"])
    
    # Step 2: Compute baseline metrics (α = 0)
    if verbose:
        print("\nStep 2: Computing baseline metrics (α = 0)")
        print("-" * 40)
    
    baseline_a, baseline_b, baseline_c, baseline_r2 = fit_quadratic(
        phase_data["normalized_x"], phase_data["dphi"]
    )
    baseline_rms = compute_rms(phase_data["dphi"])
    
    results["baseline"] = {
        "curvature_a": float(baseline_a),
        "linear_b": float(baseline_b),
        "constant_c": float(baseline_c),
        "r_squared": float(baseline_r2),
        "rms": float(baseline_rms),
        "abs_curvature": float(abs(baseline_a)),
    }
    
    if verbose:
        print(f"Baseline curvature (a): {baseline_a:.6e}")
        print(f"Baseline linear (b): {baseline_b:.6e}")
        print(f"Baseline constant (c): {baseline_c:.6e}")
        print(f"Baseline R²: {baseline_r2:.6f}")
        print(f"Baseline RMS: {baseline_rms:.6e}")
    
    # Step 3: Sweep α in initial range
    if verbose:
        print("\nStep 3: Sweeping α in initial range [-0.5, 0.5]")
        print("-" * 40)
    
    initial_sweep = sweep_alpha(
        phase_data, N, ALPHA_RANGE_INITIAL, ALPHA_STEPS, verbose
    )
    results["initial_sweep"] = initial_sweep
    
    # Find optimal α from initial sweep
    optimal_initial = find_optimal_alpha(initial_sweep)
    results["optimal_initial"] = optimal_initial
    
    if verbose:
        print(f"\nOptimal α (initial): {optimal_initial['alpha']:.6f}")
        print(f"Optimal |a|: {optimal_initial['abs_curvature']:.6e}")
        print(f"Optimal RMS: {optimal_initial['rms']:.6e}")
    
    # Step 4: Check if acceptance criteria met
    curvature_improvement = calculate_improvement_ratio(
        abs(baseline_a), optimal_initial['abs_curvature']
    )
    rms_improvement = calculate_improvement_ratio(
        baseline_rms, optimal_initial['rms']
    )
    
    results["initial_improvement"] = {
        "curvature_ratio": float(curvature_improvement),
        "rms_ratio": float(rms_improvement),
        "curvature_target_met": curvature_improvement >= 5.0,
        "rms_target_met": rms_improvement >= 2.0,
    }
    
    if verbose:
        print(f"\nCurvature improvement: {curvature_improvement:.2f}× (target: ≥5×)")
        print(f"RMS improvement: {rms_improvement:.2f}× (target: ≥2×)")
    
    # Step 5: If not met, try extended range
    if not (results["initial_improvement"]["curvature_target_met"] and 
            results["initial_improvement"]["rms_target_met"]):
        if verbose:
            print("\nStep 5: Acceptance criteria not met, trying extended range [-2, 2]")
            print("-" * 40)
        
        extended_sweep = sweep_alpha(
            phase_data, N, ALPHA_RANGE_EXTENDED, ALPHA_STEPS, verbose
        )
        results["extended_sweep"] = extended_sweep
        
        optimal_extended = find_optimal_alpha(extended_sweep)
        results["optimal_extended"] = optimal_extended
        
        # Recompute improvements with extended optimal
        curvature_improvement_ext = calculate_improvement_ratio(
            abs(baseline_a), optimal_extended['abs_curvature']
        )
        rms_improvement_ext = calculate_improvement_ratio(
            baseline_rms, optimal_extended['rms']
        )
        
        results["extended_improvement"] = {
            "curvature_ratio": float(curvature_improvement_ext),
            "rms_ratio": float(rms_improvement_ext),
            "curvature_target_met": curvature_improvement_ext >= 5.0,
            "rms_target_met": rms_improvement_ext >= 2.0,
        }
        
        if verbose:
            print(f"\nOptimal α (extended): {optimal_extended['alpha']:.6f}")
            print(f"Optimal |a|: {optimal_extended['abs_curvature']:.6e}")
            print(f"Optimal RMS: {optimal_extended['rms']:.6e}")
            print(f"Curvature improvement: {curvature_improvement_ext:.2f}× (target: ≥5×)")
            print(f"RMS improvement: {rms_improvement_ext:.2f}× (target: ≥2×)")
    
    # Step 6: Determine verdict
    elapsed = time.time() - start_time
    results["elapsed_seconds"] = elapsed
    
    # Determine final improvement metrics:
    # Use extended results if extended sweep was performed, otherwise use initial
    extended_sweep_performed = "extended_sweep" in results
    if extended_sweep_performed:
        final_improvement = results["extended_improvement"]
    else:
        final_improvement = results["initial_improvement"]
    
    hypothesis_validated = (final_improvement["curvature_target_met"] and 
                           final_improvement["rms_target_met"])
    
    results["verdict"] = {
        "hypothesis_validated": hypothesis_validated,
        "curvature_target_met": final_improvement["curvature_target_met"],
        "rms_target_met": final_improvement["rms_target_met"],
        "final_curvature_ratio": final_improvement["curvature_ratio"],
        "final_rms_ratio": final_improvement["rms_ratio"],
        "extended_sweep_performed": extended_sweep_performed,
    }
    
    if verbose:
        print("\n" + "=" * 70)
        print("VERDICT")
        print("=" * 70)
        if hypothesis_validated:
            print("HYPOTHESIS VALIDATED")
            print("Phase correction successfully reduces curvature and RMS.")
        else:
            print("HYPOTHESIS FALSIFIED")
            print("Phase correction does NOT significantly improve residual metrics.")
        print(f"\nExperiment completed in {elapsed:.2f} seconds")
    
    return results


if __name__ == "__main__":
    print("Starting Dirichlet Phase Correction Falsification experiment...")
    print("This will analyze residual phase curvature for Gate 2.\n")
    
    results = run_experiment(verbose=True)
    
    # Save results
    output_file = "results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Gate: {results['gate']}")
    print(f"N: {results['N']:,}")
    print(f"Samples: {results['samples_collected']}")
    print(f"Baseline curvature |a|: {results['baseline']['abs_curvature']:.6e}")
    print(f"Baseline RMS: {results['baseline']['rms']:.6e}")
    
    optimal = results.get("optimal_extended", results["optimal_initial"])
    print(f"Optimal α: {optimal['alpha']:.6f}")
    print(f"Optimal curvature |a|: {optimal['abs_curvature']:.6e}")
    print(f"Optimal RMS: {optimal['rms']:.6e}")
    
    verdict = results["verdict"]
    print(f"\nCurvature improvement: {verdict['final_curvature_ratio']:.2f}× (target: ≥5×)")
    print(f"RMS improvement: {verdict['final_rms_ratio']:.2f}× (target: ≥2×)")
    print(f"\nVerdict: {'HYPOTHESIS VALIDATED' if verdict['hypothesis_validated'] else 'HYPOTHESIS FALSIFIED'}")
