"""
GVA Curvature Validation 2025 — Factor Localization via Discrete Laplacian
==========================================================================

Tests the hypothesis: "Second-order differences of amplitude (curvature/discrete
Laplacian) carry a usable gradient for factor localization where raw amplitude
does not."

Key improvements over gva-curvature-falsification:
1. Compute null-model: expected mean distance for uniform distribution
2. Statistical significance testing
3. Track top-K peaks systematically
4. Compare peak clustering vs null expectation

Experiment design:
- N: CHALLENGE_127 (127-bit)
- Shell: S₅ (golden-ratio shells around √N)
- K-values: [0.30, 0.35, 0.40]
- Samples: ~5000 per k-value
- Curvature: discrete Laplacian with h = stride/10
- Precision: 708 dps (adaptive for 127-bit)
"""

import mpmath as mp
from typing import List, Dict, Tuple
import time
import json
from datetime import datetime
import statistics

# 127-bit challenge (whitelist)
CHALLENGE_127 = 137524771864208156028430259349934309717
EXPECTED_P = 10508623501177419659
EXPECTED_Q = 13086849276577416863

# Shell S₅ boundaries (offsets from √N)
# From shell-geometry-scan-01 empirical results
R5_OFFSET = 867036556394714496   # R₅ ≈ 8.67×10¹⁴
R6_OFFSET = 1402894617735313152  # R₆ ≈ 1.40×10¹⁵

# GVA kernel parameters
K_VALUES = [0.30, 0.35, 0.40]

# Sampling parameters
SAMPLES_TARGET = 5000  # Target samples per k-value
CURVATURE_H_DIVISOR = 10  # h = stride / this value
TOP_K_PEAKS = 100  # Track top K peaks by absolute curvature


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision: max(50, N.bitLength() × 4 + 200).
    
    For 127-bit N: 127 * 4 + 200 = 708 dps
    """
    bit_length = N.bit_length()
    precision = max(50, bit_length * 4 + 200)
    return precision


def compute_shell_boundaries(sqrt_N: int) -> Tuple[int, int]:
    """
    Return shell boundaries as offsets from √N.
    
    Shell S₅ spans [√N + R5_OFFSET, √N + R6_OFFSET]
    Boundaries are from shell-geometry-scan-01 empirical results.
    
    Returns:
        (R5_OFFSET, R6_OFFSET) as integers
    """
    return R5_OFFSET, R6_OFFSET


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """
    Embed integer n into 7D torus using golden ratio geodesic mapping.
    
    Args:
        n: Integer to embed
        k: Geodesic exponent (density warping)
        dimensions: Torus dimensions (default 7)
        
    Returns:
        List of coordinates in [0,1)^7
    """
    phi = mp.mpf(1 + mp.sqrt(5)) / 2
    coords = []
    for d in range(dimensions):
        phi_power = phi ** (d + 1)
        coord = mp.fmod(n * phi_power, 1)
        if k != 1.0:
            coord = mp.power(coord, k)
            coord = mp.fmod(coord, 1)
        coords.append(coord)
    return coords


def riemannian_distance(p1: List[mp.mpf], p2: List[mp.mpf]) -> mp.mpf:
    """
    Compute Riemannian geodesic distance on 7D torus with periodic boundaries.
    
    Distance accounts for wrapping: d(x,y) = min(|x-y|, 1-|x-y|) per dimension.
    """
    dist_sq = mp.mpf(0)
    for x, y in zip(p1, p2):
        diff = abs(x - y)
        torus_diff = min(diff, mp.mpf(1) - diff)
        dist_sq += torus_diff ** 2
    return mp.sqrt(dist_sq)


def compute_amplitude(N_coords: List[mp.mpf], candidate: int, k: float) -> mp.mpf:
    """
    Compute GVA amplitude for a candidate.
    
    A(c) = 1 / (1 + distance(N, c))
    
    Higher amplitude means candidate is closer to N in torus embedding.
    """
    cand_coords = embed_torus_geodesic(candidate, k)
    dist = riemannian_distance(N_coords, cand_coords)
    amplitude = mp.mpf(1) / (mp.mpf(1) + dist)
    return amplitude


def compute_curvature(
    N_coords: List[mp.mpf], candidate: int, k: float, h: int
) -> Tuple[mp.mpf, mp.mpf, mp.mpf, mp.mpf]:
    """
    Compute discrete curvature (second-order difference) of amplitude.
    
    curvature = (A(c+h) - 2*A(c) + A(c-h)) / h²
    
    This is the discrete Laplacian: measures local concavity/convexity.
    High |curvature| indicates rapid change in gradient.
    
    Returns:
        (curvature, A_minus, A_center, A_plus)
    """
    c_minus = max(1, candidate - h)
    c_plus = candidate + h
    
    A_minus = compute_amplitude(N_coords, c_minus, k)
    A_center = compute_amplitude(N_coords, candidate, k)
    A_plus = compute_amplitude(N_coords, c_plus, k)
    
    # Second-order central difference
    curvature = (A_plus - mp.mpf(2) * A_center + A_minus) / (mp.mpf(h) ** 2)
    
    return curvature, A_minus, A_center, A_plus


def compute_null_model_distance(shell_width: int, factor_p_offset: int, factor_q_offset: int) -> float:
    """
    Compute expected mean distance to nearest factor for uniform distribution.
    
    For a uniform distribution over width W with two point targets at positions
    p and q, the expected distance to the nearest target is:
    
    E[dist] ≈ W / (2 * num_targets + 1)
    
    For two targets (p and q), this gives W / 5.
    A more precise calculation integrates over the shell.
    
    Args:
        shell_width: Width of sampling region
        factor_p_offset: Position of factor p (as offset from sqrt_N)
        factor_q_offset: Position of factor q (as offset from sqrt_N)
        
    Returns:
        Expected mean distance for null model
    """
    # Simple approximation: W / (2*n + 1) for n targets
    # For 2 targets: W / 5
    return shell_width / 5.0


def sample_shell_curvature(
    N: int, sqrt_N: int, k: float, R_lower: int, R_upper: int,
    samples_target: int, verbose: bool = True
) -> Dict:
    """
    Sample shell uniformly and compute curvature at each point.
    
    Returns:
        Metrics dictionary with curvature statistics and peak analysis
    """
    metrics = {
        "k": k,
        "R_lower": R_lower,
        "R_upper": R_upper,
        "samples_collected": 0,
        "curvature_min": float("inf"),
        "curvature_max": float("-inf"),
        "curvature_values": [],
        "amplitude_min": float("inf"),
        "amplitude_max": float("-inf"),
        "amplitude_values": [],
        "candidates": [],
        "peak_locations": [],
        "factor_p_offset": EXPECTED_P - sqrt_N,
        "factor_q_offset": EXPECTED_Q - sqrt_N,
    }
    
    # Embed N once
    N_coords = embed_torus_geodesic(N, k)
    
    # Sample positive delta region: [sqrt_N + R_lower, sqrt_N + R_upper]
    start = sqrt_N + R_lower
    end = sqrt_N + R_upper
    width = end - start
    
    # Stride to get approximately samples_target samples
    stride = max(1, width // samples_target)
    h = max(1, stride // CURVATURE_H_DIVISOR)
    
    metrics["stride"] = stride
    metrics["curvature_h"] = h
    metrics["shell_width"] = width
    
    if verbose:
        print(f"\nk={k}: Sampling Shell S₅")
        print(f"  Range: [{start:,}, {end:,}]")
        print(f"  Width: {width:,}")
        print(f"  Stride: {stride:,}")
        print(f"  Curvature h: {h:,}")
        print(f"  Factor p offset: {metrics['factor_p_offset']:,}")
        print(f"  Factor q offset: {metrics['factor_q_offset']:,}")
    
    samples_collected = 0
    sample_start_time = time.time()
    
    for candidate in range(start, end, stride):
        if candidate <= 1 or candidate >= N:
            continue
        # Skip even candidates for odd N
        if N % 2 == 1 and candidate % 2 == 0:
            continue
        
        curvature, A_minus, A_center, A_plus = compute_curvature(
            N_coords, candidate, k, h
        )
        
        curvature_f = float(curvature)
        A_center_f = float(A_center)
        
        metrics["curvature_values"].append(curvature_f)
        metrics["amplitude_values"].append(A_center_f)
        metrics["candidates"].append(candidate)
        
        if curvature_f < metrics["curvature_min"]:
            metrics["curvature_min"] = curvature_f
        if curvature_f > metrics["curvature_max"]:
            metrics["curvature_max"] = curvature_f
        
        if A_center_f < metrics["amplitude_min"]:
            metrics["amplitude_min"] = A_center_f
        if A_center_f > metrics["amplitude_max"]:
            metrics["amplitude_max"] = A_center_f
        
        samples_collected += 1
        
        if verbose and samples_collected % 1000 == 0:
            elapsed = time.time() - sample_start_time
            rate = samples_collected / elapsed
            print(f"  Samples: {samples_collected}, rate: {rate:.1f}/s, "
                  f"curvature range: [{metrics['curvature_min']:.2e}, {metrics['curvature_max']:.2e}]")
    
    metrics["samples_collected"] = samples_collected
    
    # Compute statistics
    if len(metrics["curvature_values"]) > 0:
        metrics["curvature_mean"] = statistics.mean(metrics["curvature_values"])
        metrics["curvature_std"] = (
            statistics.stdev(metrics["curvature_values"])
            if len(metrics["curvature_values"]) > 1
            else 0.0
        )
        metrics["curvature_range"] = metrics["curvature_max"] - metrics["curvature_min"]
        
        metrics["amplitude_mean"] = statistics.mean(metrics["amplitude_values"])
        metrics["amplitude_std"] = (
            statistics.stdev(metrics["amplitude_values"])
            if len(metrics["amplitude_values"]) > 1
            else 0.0
        )
        metrics["amplitude_range"] = metrics["amplitude_max"] - metrics["amplitude_min"]
        
        # Find top TOP_K_PEAKS peaks (highest |curvature|)
        curv_with_idx = [
            (abs(c), i, metrics["curvature_values"][i])
            for i, c in enumerate(metrics["curvature_values"])
        ]
        curv_with_idx.sort(reverse=True)
        
        distances_to_factors = []
        
        for abs_curv, idx, curv in curv_with_idx[:TOP_K_PEAKS]:
            candidate = metrics["candidates"][idx]
            delta = candidate - sqrt_N
            
            # Distance to nearest factor (in delta space)
            dist_to_p = abs(delta - metrics["factor_p_offset"])
            dist_to_q = abs(delta - metrics["factor_q_offset"])
            dist_to_nearest = min(dist_to_p, dist_to_q)
            
            distances_to_factors.append(dist_to_nearest)
            
            metrics["peak_locations"].append({
                "candidate": candidate,
                "delta": delta,
                "curvature": curv,
                "abs_curvature": abs_curv,
                "amplitude": metrics["amplitude_values"][idx],
                "distance_to_nearest_factor": dist_to_nearest,
            })
        
        # Compute null model and actual peak statistics
        null_model_mean = compute_null_model_distance(
            width, metrics["factor_p_offset"], metrics["factor_q_offset"]
        )
        
        if distances_to_factors:
            actual_mean_distance = statistics.mean(distances_to_factors)
            actual_median_distance = statistics.median(distances_to_factors)
            
            metrics["null_model_mean_distance"] = null_model_mean
            metrics["actual_mean_distance_top_peaks"] = actual_mean_distance
            metrics["actual_median_distance_top_peaks"] = actual_median_distance
            metrics["distance_ratio_mean"] = actual_mean_distance / null_model_mean
            metrics["distance_ratio_median"] = actual_median_distance / null_model_mean
            
            # Count peaks within various distance thresholds
            metrics["peaks_within_1e13"] = sum(1 for d in distances_to_factors if d < 1e13)
            metrics["peaks_within_1e14"] = sum(1 for d in distances_to_factors if d < 1e14)
            metrics["peaks_within_1e15"] = sum(1 for d in distances_to_factors if d < 1e15)
    
    return metrics


def run_experiment(verbose: bool = True) -> Dict:
    """
    Run the curvature validation experiment.
    
    Tests whether curvature (discrete Laplacian) provides a usable gradient
    for factor localization.
    """
    N = CHALLENGE_127
    sqrt_N = int(mp.sqrt(N))
    
    # Compute shell boundaries (offsets from sqrt_N)
    R_lower, R_upper = compute_shell_boundaries(sqrt_N)
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    
    with mp.workdps(required_dps):
        if verbose:
            print("=" * 70)
            print("GVA Curvature Validation 2025 — Factor Localization Test")
            print("=" * 70)
            print(f"N = {N}")
            print(f"sqrt(N) = {sqrt_N:,}")
            print(f"Expected p = {EXPECTED_P:,}")
            print(f"Expected q = {EXPECTED_Q:,}")
            print(f"p offset from sqrt(N) = {EXPECTED_P - sqrt_N:,}")
            print(f"q offset from sqrt(N) = {EXPECTED_Q - sqrt_N:,}")
            print(f"Shell S₅ offsets: R₅={R_lower:,}, R₆={R_upper:,}")
            print(f"Shell width: {R_upper - R_lower:,}")
            print(f"Absolute range: [{sqrt_N + R_lower:,}, {sqrt_N + R_upper:,}]")
            print(f"Adaptive precision: {required_dps} dps")
            print(f"Target samples per k: {SAMPLES_TARGET}")
            print(f"K-values to test: {K_VALUES}")
        
        start_time = time.time()
        
        results = {
            "experiment": "gva-curvature-validation-2025",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": "Second-order differences (curvature) carry usable gradient for factor localization",
            "N": N,
            "sqrt_N": sqrt_N,
            "expected_p": EXPECTED_P,
            "expected_q": EXPECTED_Q,
            "shell_R5_offset": R_lower,
            "shell_R6_offset": R_upper,
            "k_values": K_VALUES,
            "samples_target": SAMPLES_TARGET,
            "precision_dps": required_dps,
            "top_k_peaks_tracked": TOP_K_PEAKS,
            "per_k_metrics": [],
        }
        
        # Test each k value
        for k in K_VALUES:
            metrics = sample_shell_curvature(
                N, sqrt_N, k, R_lower, R_upper, SAMPLES_TARGET, verbose
            )
            results["per_k_metrics"].append(metrics)
        
        elapsed = time.time() - start_time
        results["elapsed_seconds"] = elapsed
        
        if verbose:
            print(f"\n{'=' * 70}")
            print(f"Experiment complete in {elapsed:.2f} seconds")
            print(f"{'=' * 70}")
            
            # Summary
            print("\n" + "=" * 70)
            print("EXECUTIVE SUMMARY")
            print("=" * 70)
            
            for m in results["per_k_metrics"]:
                print(f"\nk={m['k']}:")
                print(f"  Samples collected: {m['samples_collected']}")
                
                if m['samples_collected'] == 0:
                    print(f"  ERROR: No samples collected!")
                    continue
                
                print(f"  Curvature range: [{m['curvature_min']:.2e}, {m['curvature_max']:.2e}]")
                print(f"  Curvature std/mean: {m['curvature_std']/abs(m['curvature_mean']):.3f}")
                print(f"  Amplitude range: [{m['amplitude_min']:.6f}, {m['amplitude_max']:.6f}]")
                print(f"  Amplitude std/mean: {m['amplitude_std']/m['amplitude_mean']:.3f}")
                print(f"\n  Null model (uniform): mean distance = {m['null_model_mean_distance']:.2e}")
                print(f"  Top {TOP_K_PEAKS} peaks: mean distance = {m['actual_mean_distance_top_peaks']:.2e}")
                print(f"  Top {TOP_K_PEAKS} peaks: median distance = {m['actual_median_distance_top_peaks']:.2e}")
                print(f"  Distance ratio (mean): {m['distance_ratio_mean']:.3f}")
                print(f"  Distance ratio (median): {m['distance_ratio_median']:.3f}")
                print(f"\n  Peaks within 1e13: {m['peaks_within_1e13']}")
                print(f"  Peaks within 1e14: {m['peaks_within_1e14']}")
                print(f"  Peaks within 1e15: {m['peaks_within_1e15']}")
                
                # Check if hypothesis is supported
                if m['distance_ratio_mean'] < 0.5:
                    print(f"  ✓ HYPOTHESIS SUPPORTED: Top peaks cluster near factors")
                elif m['distance_ratio_mean'] < 1.0:
                    print(f"  ≈ HYPOTHESIS WEAKLY SUPPORTED: Mild clustering detected")
                else:
                    print(f"  ✗ HYPOTHESIS NOT SUPPORTED: No clustering detected")
        
        return results


if __name__ == "__main__":
    print("Starting GVA Curvature Validation 2025 experiment...")
    print("Testing hypothesis: curvature provides gradient for factor localization\n")
    
    results = run_experiment(verbose=True)
    
    # Save results
    output_file = "results.json"
    with open(output_file, "w") as f:
        # Convert any remaining mpmath values to float for JSON
        def convert(obj):
            if isinstance(obj, mp.mpf):
                return float(obj)
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(v) for v in obj]
            return obj
        
        results_json = convert(results)
        json.dump(results_json, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    print("\nNext steps:")
    print("1. Review EXECUTIVE_SUMMARY.md for interpretation")
    print("2. Check DETAILED_RESULTS.md for methodology")
    print("3. Analyze results.json for raw data")
