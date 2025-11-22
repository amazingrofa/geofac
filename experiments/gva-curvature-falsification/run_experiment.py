"""
GVA Curvature Falsification — Minimal Probe for Distant-Factor Signal
======================================================================

Tests whether curvature (second-order differences) of GVA amplitude reveals
structure where raw amplitude is flat. Fixed to Shell S₅ and CHALLENGE_127.

Key change from shell-geometry-scan-01: compute curvature instead of raw amplitude.
Everything else (shell, N, k-values, precision) kept identical for controlled comparison.
"""

import mpmath as mp
from typing import List, Dict, Tuple
import time
import json
from datetime import datetime

import statistics

# Configure high precision


# 127-bit challenge (whitelist)
CHALLENGE_127 = 137524771864208156028430259349934309717
EXPECTED_P = 10508623501177419659
EXPECTED_Q = 13086849276577416863

# Shell S₅ boundaries (from shell-geometry-scan-01 results)
R5 = 867036556394714496
R6 = 1402894617735313152

# GVA kernel parameters (unchanged from previous experiment)
K_VALUES = [0.30, 0.35, 0.40]


# Sampling parameters
SAMPLES_TARGET = 10000  # Target number of samples across S₅
CURVATURE_H_DIVISOR = 10  # h = stride / this value


def adaptive_precision(N: int) -> int:
    """Compute adaptive precision: max(50, bitLength × 4 + 200)"""
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """Embed integer n into 7D torus using golden ratio geodesic mapping."""
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
    """Compute Riemannian geodesic distance on 7D torus with periodic boundaries."""
    dist_sq = mp.mpf(0)
    for x, y in zip(p1, p2):
        diff = abs(x - y)
        torus_diff = min(diff, 1 - diff)
        dist_sq += torus_diff**2
    return mp.sqrt(dist_sq)


def compute_amplitude(N_coords: List[mp.mpf], candidate: int, k: float) -> mp.mpf:
    """Compute GVA amplitude for a candidate (inverse distance)."""
    cand_coords = embed_torus_geodesic(candidate, k)
    dist = riemannian_distance(N_coords, cand_coords)
    amplitude = mp.mpf(1) / (mp.mpf(1) + dist)
    return amplitude


def compute_curvature(
    N_coords: List[mp.mpf], candidate: int, k: float, h: int
) -> Tuple[float, float, float, float]:
    """
    Compute discrete curvature (second-order difference) of amplitude.

    Returns: (curvature, A_minus, A_center, A_plus)

    curvature = (A_plus - 2*A_center + A_minus) / h²

    This is the discrete Laplacian: measures local concavity/convexity.
    High |curvature| indicates rapid change in gradient → potential signal.
    """
    c_minus = max(1, candidate - h)
    c_plus = candidate + h

    A_minus = compute_amplitude(N_coords, c_minus, k)
    A_center = compute_amplitude(N_coords, candidate, k)
    A_plus = compute_amplitude(N_coords, c_plus, k)

    # Second-order central difference
    curvature = (A_plus - 2 * A_center + A_minus) / (h * h)

    return curvature, A_minus, A_center, A_plus


def sample_shell_curvature(
    N: int, sqrt_N: int, k: float, samples_target: int, verbose: bool = True
) -> Dict:
    """
    Sample Shell S₅ uniformly and compute curvature at each point.

    Returns metrics dict with curvature statistics.
    """
    metrics = {
        "k": k,
        "samples_collected": 0,
        "curvature_min": float("inf"),
        "curvature_max": float("-inf"),
        "curvature_values": [],
        "amplitude_min": float("inf"),
        "amplitude_max": float("-inf"),
        "amplitude_values": [],
        "peak_locations": [],  # (candidate, curvature, amplitude)
        "factor_p_offset": EXPECTED_P - sqrt_N,
        "factor_q_offset": EXPECTED_Q - sqrt_N,
    }

    # Embed N once
    N_coords = embed_torus_geodesic(N, k)

    # Sample positive delta region: [sqrt_N + R5, sqrt_N + R6]
    start = sqrt_N + R5
    end = sqrt_N + R6
    width = end - start

    # Stride to get approximately samples_target samples
    stride = max(1, width // samples_target)
    h = max(1, stride // CURVATURE_H_DIVISOR)

    metrics["stride"] = stride
    metrics["curvature_h"] = h

    if verbose:
        print(f"\nk={k}: Sampling Shell S₅ positive region")
        print(f"  Range: [{start:,}, {end:,}]")
        print(f"  Width: {width:,}")
        print(f"  Stride: {stride:,}")
        print(f"  Curvature h: {h:,}")

    samples_collected = 0
    for candidate in range(start, end, stride):
        if candidate <= 1 or candidate >= N:
            continue
        if N % 2 == 1 and candidate % 2 == 0:
            continue

        curvature, A_minus, A_center, A_plus = compute_curvature(
            N_coords, candidate, k, h
        )

        metrics["curvature_values"].append(curvature)
        metrics["amplitude_values"].append(A_center)

        if curvature < metrics["curvature_min"]:
            metrics["curvature_min"] = curvature
        if curvature > metrics["curvature_max"]:
            metrics["curvature_max"] = curvature

        if A_center < metrics["amplitude_min"]:
            metrics["amplitude_min"] = A_center
        if A_center > metrics["amplitude_max"]:
            metrics["amplitude_max"] = A_center

        samples_collected += 1
        metrics["candidates"].append(candidate)

        if verbose and samples_collected % 1000 == 0:
            print(
                f"  Samples: {samples_collected}, curvature range: [{metrics['curvature_min']:.2e}, {metrics['curvature_max']:.2e}]"
            )

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

        # Find top 100 peaks (highest |curvature|)
        curv_with_idx = [
            (abs(c), i, metrics["curvature_values"][i])
            for i, c in enumerate(metrics["curvature_values"])
        ]
        curv_with_idx.sort(reverse=True)

        for abs_curv, idx, curv in curv_with_idx[:100]:
            candidate = start + idx * stride
            delta = candidate - sqrt_N
            # Distance to nearest factor (in delta space)
            dist_to_p = abs(delta - metrics["factor_p_offset"])
            dist_to_q = abs(delta - metrics["factor_q_offset"])
            dist_to_nearest = min(dist_to_p, dist_to_q)

            metrics["peak_locations"].append(
                {
                    "candidate": candidate,
                    "delta": delta,
                    "curvature": curv,
                    "amplitude": metrics["amplitude_values"][idx],
                    "distance_to_nearest_factor": dist_to_nearest,
                }
            )

    return metrics


def run_experiment(verbose: bool = True) -> Dict:
    """
    Run the curvature falsification experiment.

    Tests whether curvature metric shows structure where amplitude is flat.
    """
    N = CHALLENGE_127
    sqrt_N = int(mp.sqrt(N))

    # Set adaptive precision
    required_dps = adaptive_precision(N)
    with mp.workdps(required_dps):
        if verbose:
            print("=" * 70)
            print("GVA Curvature Falsification — Shell S₅ Probe")
            print("=" * 70)
            print(f"N = {N}")
            print(f"sqrt(N) = {sqrt_N:,}")
            print(f"Expected p = {EXPECTED_P:,}")
            print(f"Expected q = {EXPECTED_Q:,}")
            print(f"Shell S₅: R₅={R5:,}, R₆={R6:,}")
            print(f"Adaptive precision: {required_dps} dps")
            print(f"Target samples: {SAMPLES_TARGET}")

        start_time = time.time()

        results = {
            "experiment": "gva-curvature-falsification",
            "timestamp": datetime.now().isoformat(),
            "N": N,
            "sqrt_N": sqrt_N,
            "expected_p": EXPECTED_P,
            "expected_q": EXPECTED_Q,
            "shell_R5": R5,
            "shell_R6": R6,
            "k_values": K_VALUES,
            "samples_target": SAMPLES_TARGET,
            "precision_dps": required_dps,
            "per_k_metrics": [],
        }

        # Test each k value
        for k in K_VALUES:
            metrics = sample_shell_curvature(N, sqrt_N, k, SAMPLES_TARGET, verbose)
            results["per_k_metrics"].append(metrics)

        elapsed = time.time() - start_time
        results["elapsed_seconds"] = elapsed

        if verbose:
            print(f"\n{'=' * 70}")
            print(f"Experiment complete in {elapsed:.2f} seconds")
            print(f"{'=' * 70}")

            # Summary
            print("\nSUMMARY:")
            for m in results["per_k_metrics"]:
                print(f"\nk={m['k']}:")
                print(f"  Samples: {m['samples_collected']}")
                print(
                    f"  Curvature range: [{m['curvature_min']:.2e}, {m['curvature_max']:.2e}]"
                )
                print(f"  Curvature std: {m['curvature_std']:.2e}")
                print(
                    f"  Amplitude range: [{m['amplitude_min']:.6f}, {m['amplitude_max']:.6f}]"
                )
                print(f"  Amplitude std: {m['amplitude_std']:.6f}")

        return results


if __name__ == "__main__":
    print("Starting GVA Curvature Falsification experiment...")
    print("This will sample Shell S₅ and compute curvature metrics.\n")

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
    print("1. Review results.json for raw metrics")
    print("2. Analyze curvature distribution and peak locations")
    print("3. Check for spatial clustering near factors")
    print("4. Compare curvature range vs amplitude range")
