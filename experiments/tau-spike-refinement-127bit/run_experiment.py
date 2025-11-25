#!/usr/bin/env python3
"""
τ''' Spike Refinement Experiment for 127-bit Challenge
=======================================================

Follow-up to PR #131's unbalanced-left-edge-127bit experiment.

Problem Statement:
PR #131 detected the correct scale region via τ''' spike at b=63.28,
aligning with actual factor bit lengths (p ≈ 2^63.19, q ≈ 2^63.50),
but failed factor recovery due to insufficient narrowing of the
candidate space within 100k tests.

Root Causes Identified:
1. Mapping offset: Center from b=63.28 is ≈1.119×10^19, but actual p is
   ≈1.051×10^19 — offset of ~6.9×10^17, exceeding inner search windows.
2. Sampling inefficiency: Inner dense search covers negligible fraction
   of range; outer sampling yields hit probability <10^{-13}.
3. Precision limits: Finite differences may introduce spike location error.

Improvements Tested:
1. Richardson extrapolation for sub-bit spike localization accuracy.
2. Sobol QMC sampling focused around refined spike (80% budget ±0.1 bit).
3. Increased candidate budget (1M candidates vs 100k).

Target: N = 137524771864208156028430259349934309717 (127-bit challenge)

Constraints:
- No prior knowledge of factors used in algorithm
- No classical fallbacks (Pollard, ECM, trial division, sieves)
- Deterministic/quasi-deterministic methods only (Sobol sequences)
- Explicit adaptive precision
"""

import time
import json
import sys
from datetime import datetime
from math import log2
from typing import List, Tuple, Optional, Dict, Any

try:
    import mpmath as mp
except ImportError:
    print("ERROR: mpmath required. Install with: pip install mpmath")
    sys.exit(1)

# Constant to prevent division by zero in confidence calculation
MIN_ERROR_THRESHOLD = 1e-30

# Sobol sequence for QMC sampling
try:
    from scipy.stats.qmc import Sobol
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy.stats.qmc not available. Using deterministic grid.")

# Challenge constant
CHALLENGE_127 = 137524771864208156028430259349934309717


def adaptive_precision(N: int) -> int:
    """Compute adaptive precision: max(configured, N.bit_length() × 4 + 200)."""
    return max(50, N.bit_length() * 4 + 200)


def set_precision(N: int) -> int:
    """Set mpmath precision and return the value used."""
    precision = adaptive_precision(N)
    mp.mp.dps = precision
    return precision


def compute_tau(N: int, b: mp.mpf, phi: mp.mpf) -> mp.mpf:
    """
    Compute τ(b): a log-folded geometric score at scale parameter b.
    
    See PR #131 for original design. τ measures geometric resonance
    at a given scale, combining modular resonance and phase alignment.
    """
    scale = mp.power(2, b)
    sqrt_N = mp.sqrt(N)
    
    if scale < 1:
        return mp.mpf(0)
    
    ratio = scale / sqrt_N
    if ratio <= 0:
        return mp.mpf(0)
    
    log_ratio = mp.log(ratio)
    
    # Modular resonance
    scale_int = int(mp.floor(scale))
    if scale_int < 2:
        mod_resonance = mp.mpf(0)
    else:
        remainder = N % scale_int
        mod_normalized = min(remainder, scale_int - remainder) / scale_int
        mod_resonance = 1 - mod_normalized
    
    # Phase alignment with golden ratio
    phase = mp.fmod(scale * phi, 1)
    phase_alignment = mp.mpf(1) - mp.power(mp.sin(mp.pi * phase), 2)
    
    geometric_score = 0.5 * phase_alignment + 0.5 * mod_resonance
    decay = mp.exp(-abs(log_ratio) * 0.5)
    
    return mp.log(1 + geometric_score * decay)


def richardson_extrapolation_third_derivative(
    N: int,
    b: mp.mpf,
    phi: mp.mpf,
    h_base: mp.mpf
) -> Tuple[mp.mpf, mp.mpf]:
    """
    Compute τ'''(b) using Richardson extrapolation for improved accuracy.
    
    Richardson extrapolation combines estimates at different step sizes
    to eliminate leading error terms. For third derivative:
    
    D_h = (τ(b+2h) - 2τ(b+h) + 2τ(b-h) - τ(b-2h)) / (2h³)
    
    Using h and h/2:
    D_refined = (4*D_{h/2} - D_h) / 3
    
    Returns:
        (refined_derivative, estimated_error)
    """
    h = h_base
    h2 = h / 2
    
    # Coarse estimate with step h
    tau_p2h = compute_tau(N, b + 2*h, phi)
    tau_ph = compute_tau(N, b + h, phi)
    tau_mh = compute_tau(N, b - h, phi)
    tau_m2h = compute_tau(N, b - 2*h, phi)
    
    D_h = (tau_p2h - 2*tau_ph + 2*tau_mh - tau_m2h) / (2 * h**3)
    
    # Fine estimate with step h/2
    tau_p2h2 = compute_tau(N, b + 2*h2, phi)
    tau_ph2 = compute_tau(N, b + h2, phi)
    tau_mh2 = compute_tau(N, b - h2, phi)
    tau_m2h2 = compute_tau(N, b - 2*h2, phi)
    
    D_h2 = (tau_p2h2 - 2*tau_ph2 + 2*tau_mh2 - tau_m2h2) / (2 * h2**3)
    
    # Richardson extrapolation: eliminate O(h²) error
    # Coefficient = (h/(h/2))² = 2² = 4 for third derivative with O(h²) error
    D_refined = (4 * D_h2 - D_h) / 3
    
    # Error estimate from difference between estimates
    error_estimate = abs(D_refined - D_h2)
    
    return D_refined, error_estimate


def compute_tau_profile_richardson(
    N: int,
    b_start: float,
    b_end: float,
    num_points: int,
    phi: mp.mpf
) -> Tuple[List[float], List[mp.mpf], List[mp.mpf], List[mp.mpf]]:
    """
    Compute τ and τ''' across [b_start, b_end] using Richardson extrapolation.
    
    Returns:
        (b_values, tau_values, tau_triple_prime, error_estimates)
    """
    h = mp.mpf(b_end - b_start) / (num_points - 1)
    
    b_values = []
    tau_values = []
    tau_triple_prime = []
    error_estimates = []
    
    for i in range(num_points):
        b = mp.mpf(b_start) + i * h
        b_values.append(float(b))
        
        tau = compute_tau(N, b, phi)
        tau_values.append(tau)
        
        # Richardson extrapolation for third derivative
        d3, err = richardson_extrapolation_third_derivative(N, b, phi, h)
        tau_triple_prime.append(d3)
        error_estimates.append(err)
    
    return b_values, tau_values, tau_triple_prime, error_estimates


def find_refined_spike(
    b_values: List[float],
    tau_triple_prime: List[mp.mpf],
    error_estimates: List[mp.mpf],
    threshold_factor: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Find τ''' spikes with refined localization using error estimates.
    
    Returns sorted list of spike info dictionaries.
    """
    abs_values = [abs(float(d3)) for d3 in tau_triple_prime]
    mean_abs = sum(abs_values) / len(abs_values) if abs_values else 1.0
    threshold = mean_abs * threshold_factor
    
    spikes = []
    for i, (b, d3, err) in enumerate(zip(b_values, tau_triple_prime, error_estimates)):
        magnitude = abs(float(d3))
        if magnitude > threshold:
            spikes.append({
                "index": i,
                "b": b,
                "magnitude": float(d3),
                "abs_magnitude": magnitude,
                "error_estimate": float(err),
                "confidence": magnitude / (float(err) + MIN_ERROR_THRESHOLD),  # signal/noise ratio
            })
    
    # Sort by confidence (signal/noise ratio)
    spikes.sort(key=lambda x: x["confidence"], reverse=True)
    
    return spikes


def sobol_qmc_candidates(
    center: int,
    radius_bits: float,
    total_candidates: int,
    inner_fraction: float = 0.8,
    inner_radius_bits: float = 0.1,
    seed: int = 42
) -> List[int]:
    """
    Generate candidates using Sobol QMC sequence with focused inner region.
    
    Strategy:
    - inner_fraction (80%) of budget goes to ±inner_radius_bits around center
    - Remaining (20%) spread across wider radius_bits region
    
    Args:
        center: Central candidate value (2^b*)
        radius_bits: Outer search radius in bits
        total_candidates: Total number of candidates to generate
        inner_fraction: Fraction of budget for inner region (default 0.8)
        inner_radius_bits: Inner region radius in bits (default 0.1)
        seed: Random seed for reproducibility
    
    Returns:
        Sorted list of unique candidate integers
    """
    inner_count = int(total_candidates * inner_fraction)
    outer_count = total_candidates - inner_count
    
    candidates = set()
    
    # Inner region: ±inner_radius_bits (e.g., ±0.1 bit = factor of ~1.07)
    inner_low = int(center / (2 ** inner_radius_bits))
    inner_high = int(center * (2 ** inner_radius_bits))
    inner_low = max(2, inner_low)
    
    if HAS_SCIPY and inner_high > inner_low:
        # Use Sobol sequence for quasi-random sampling
        sampler = Sobol(d=1, scramble=True, seed=seed)
        samples = sampler.random(inner_count)
        for s in samples:
            c = int(inner_low + s[0] * (inner_high - inner_low))
            if c > 1:
                candidates.add(c)
    else:
        # Fallback: deterministic grid
        step = max(1, (inner_high - inner_low) // inner_count)
        for i in range(inner_count):
            c = inner_low + i * step
            if c <= inner_high and c > 1:
                candidates.add(c)
    
    # Outer region: ±radius_bits excluding inner
    outer_low = int(center / (2 ** radius_bits))
    outer_high = int(center * (2 ** radius_bits))
    outer_low = max(2, outer_low)
    
    if HAS_SCIPY and outer_high > outer_low:
        sampler = Sobol(d=1, scramble=True, seed=seed + 1)
        samples = sampler.random(outer_count)
        for s in samples:
            c = int(outer_low + s[0] * (outer_high - outer_low))
            # Exclude inner region
            if c > 1 and (c < inner_low or c > inner_high):
                candidates.add(c)
    else:
        # Logarithmic sampling for outer region
        if outer_high > outer_low and outer_count > 0:
            # Handle edge case: single sample uses midpoint
            divisor = outer_count - 1 if outer_count > 1 else 1
            for i in range(outer_count):
                # Exponentially spaced
                t = i / divisor if outer_count > 1 else 0.5
                log_low = log2(max(1, outer_low))
                log_high = log2(max(1, outer_high))
                c = int(2 ** (log_low + t * (log_high - log_low)))
                if c > 1 and (c < inner_low or c > inner_high):
                    candidates.add(c)
    
    return sorted(candidates)


def test_candidates(N: int, candidates: List[int]) -> Optional[Tuple[int, int]]:
    """Test candidate factors. Returns (p, q) if found, None otherwise."""
    for c in candidates:
        if c <= 1 or c >= N:
            continue
        if N % c == 0:
            p, q = c, N // c
            return (min(p, q), max(p, q))
    return None


def run_refinement_experiment(
    N: int = CHALLENGE_127,
    num_scan_points: int = 1000,
    spike_threshold_factor: float = 2.0,
    max_spikes_to_test: int = 10,
    outer_radius_bits: float = 2.0,
    inner_radius_bits: float = 0.1,
    inner_fraction: float = 0.8,
    candidates_per_spike: int = 100000,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run the τ''' spike refinement experiment.
    
    Key improvements over PR #131:
    1. Richardson extrapolation for spike localization
    2. Sobol QMC sampling with 80% budget in ±0.1 bit inner region
    3. Increased candidate budget (configurable, default 100k per spike)
    """
    start_time = time.time()
    
    precision = set_precision(N)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "experiment": "tau-spike-refinement-127bit",
        "N": str(N),
        "N_bit_length": N.bit_length(),
        "precision_dps": precision,
        "num_scan_points": num_scan_points,
        "spike_threshold_factor": spike_threshold_factor,
        "max_spikes_to_test": max_spikes_to_test,
        "outer_radius_bits": outer_radius_bits,
        "inner_radius_bits": inner_radius_bits,
        "inner_fraction": inner_fraction,
        "candidates_per_spike": candidates_per_spike,
        "has_scipy_sobol": HAS_SCIPY,
        "richardson_extrapolation": True,
        "factor_found": None,
        "cofactor": None,
        "verified": False,
        "spikes_detected": [],
        "spikes_tested": 0,
        "total_candidates_tested": 0,
        "elapsed_ms": 0,
    }
    
    if verbose:
        print("=" * 70)
        print("τ''' SPIKE REFINEMENT EXPERIMENT")
        print("Follow-up to PR #131 (unbalanced-left-edge-127bit)")
        print("=" * 70)
        print(f"N = {N}")
        print(f"N_bit_length = {N.bit_length()}")
        print(f"precision_dps = {precision}")
        print(f"num_scan_points = {num_scan_points}")
        print(f"candidates_per_spike = {candidates_per_spike}")
        print(f"Sobol QMC available: {HAS_SCIPY}")
        print(f"Richardson extrapolation: ENABLED")
        print("=" * 70)
    
    # Scan range
    sqrt_N = mp.sqrt(N)
    sqrt_N_bits = float(mp.log(sqrt_N, 2))
    
    b_start = 1.0
    b_end = sqrt_N_bits + 2.0
    
    results["tau_scan_range"] = [b_start, b_end]
    
    if verbose:
        print(f"\nPhase 1: Computing τ(b) with Richardson extrapolation...")
        print(f"  Scan range: [{b_start:.2f}, {b_end:.2f}] bits")
        print(f"  sqrt(N) ≈ 2^{sqrt_N_bits:.4f}")
    
    phi = (1 + mp.sqrt(5)) / 2
    
    b_values, tau_values, tau_triple_prime, error_estimates = \
        compute_tau_profile_richardson(N, b_start, b_end, num_scan_points, phi)
    
    if verbose:
        print(f"  Computed {len(b_values)} τ values")
        
        d3_floats = [float(d) for d in tau_triple_prime]
        err_floats = [float(e) for e in error_estimates]
        print(f"  τ''' range: [{min(d3_floats):.4e}, {max(d3_floats):.4e}]")
        print(f"  Error estimate range: [{min(err_floats):.4e}, {max(err_floats):.4e}]")
    
    # Find spikes
    if verbose:
        print("\nPhase 2: Detecting τ''' spikes with confidence ranking...")
    
    spikes = find_refined_spike(b_values, tau_triple_prime, error_estimates, spike_threshold_factor)
    
    results["spikes_detected"] = spikes[:max_spikes_to_test * 2]
    
    if verbose:
        print(f"  Found {len(spikes)} spikes above threshold")
        if spikes:
            print(f"  Top 5 spikes by confidence (signal/noise):")
            for i, spike in enumerate(spikes[:5]):
                center_int = int(2 ** spike["b"])
                print(f"    {i+1}. b={spike['b']:.4f} (2^b≈{center_int:.3e})")
                print(f"       |τ'''|={spike['abs_magnitude']:.4e}, err={spike['error_estimate']:.4e}")
                print(f"       confidence={spike['confidence']:.2f}")
    
    # Test spikes
    if verbose:
        print("\nPhase 3: Testing spike locations with Sobol QMC sampling...")
    
    total_candidates_tested = 0
    spikes_tested = 0
    
    for spike_idx, spike in enumerate(spikes[:max_spikes_to_test]):
        spikes_tested += 1
        b_spike = spike["b"]
        center = int(2 ** b_spike)
        
        if verbose:
            print(f"\n  Testing spike {spikes_tested}/{min(len(spikes), max_spikes_to_test)}:")
            print(f"    b* = {b_spike:.6f}")
            print(f"    Center: 2^{b_spike:.4f} ≈ {center:,}")
            print(f"    Confidence: {spike['confidence']:.2f}")
        
        # Generate candidates with QMC
        candidates = sobol_qmc_candidates(
            center=center,
            radius_bits=outer_radius_bits,
            total_candidates=candidates_per_spike,
            inner_fraction=inner_fraction,
            inner_radius_bits=inner_radius_bits,
            seed=42 + spike_idx
        )
        
        if verbose:
            print(f"    Generated {len(candidates):,} unique candidates")
            if candidates:
                print(f"    Range: [{min(candidates):,}, {max(candidates):,}]")
        
        # Test candidates
        factor_result = test_candidates(N, candidates)
        total_candidates_tested += len(candidates)
        
        if factor_result:
            p, q = factor_result
            results["factor_found"] = str(p)
            results["cofactor"] = str(q)
            results["verified"] = (p * q == N)
            results["spike_that_found_factor"] = spike
            results["spikes_tested"] = spikes_tested
            results["total_candidates_tested"] = total_candidates_tested
            
            elapsed = (time.time() - start_time) * 1000
            results["elapsed_ms"] = elapsed
            
            if verbose:
                print("\n" + "=" * 70)
                print("SUCCESS - FACTOR FOUND")
                print("=" * 70)
                print(f"factor_found = {p}")
                print(f"cofactor = {q}")
                print(f"verified = {results['verified']}")
                print(f"spike_b* = {b_spike:.6f}")
                print(f"spikes_tested = {spikes_tested}")
                print(f"total_candidates_tested = {total_candidates_tested:,}")
                print(f"elapsed_ms = {elapsed:.2f}")
            
            return results
        
        if verbose:
            print(f"    No factor found in this spike region")
    
    # No factor found
    results["spikes_tested"] = spikes_tested
    results["total_candidates_tested"] = total_candidates_tested
    
    elapsed = (time.time() - start_time) * 1000
    results["elapsed_ms"] = elapsed
    
    if verbose:
        print("\n" + "=" * 70)
        print("HYPOTHESIS NOT VALIDATED - NO FACTOR FOUND")
        print("=" * 70)
        print(f"spikes_tested = {spikes_tested}")
        print(f"total_candidates_tested = {total_candidates_tested:,}")
        print(f"elapsed_ms = {elapsed:.2f}")
    
    return results


def analyze_distance_to_actual_factors(
    spikes: List[Dict[str, Any]],
    actual_p: int = 10508623501177419659,
    actual_q: int = 13086849276577416863,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Post-hoc analysis: compute distance from spike centers to actual factors.
    
    NOTE: This is for validation/falsification analysis ONLY.
    The actual factors are NOT used in the algorithm.
    """
    actual_p_bits = log2(actual_p)
    actual_q_bits = log2(actual_q)
    
    analysis = {
        "actual_p": actual_p,
        "actual_q": actual_q,
        "actual_p_bits": actual_p_bits,
        "actual_q_bits": actual_q_bits,
        "spike_analysis": [],
    }
    
    if verbose:
        print("\n" + "=" * 70)
        print("POST-HOC ANALYSIS (for falsification documentation only)")
        print("=" * 70)
        print(f"Actual p = {actual_p} ≈ 2^{actual_p_bits:.4f}")
        print(f"Actual q = {actual_q} ≈ 2^{actual_q_bits:.4f}")
        print()
    
    for i, spike in enumerate(spikes[:10]):
        b_spike = spike["b"]
        center = int(2 ** b_spike)
        
        dist_to_p = abs(center - actual_p)
        dist_to_q = abs(center - actual_q)
        bit_dist_to_p = abs(b_spike - actual_p_bits)
        bit_dist_to_q = abs(b_spike - actual_q_bits)
        
        closest = "p" if dist_to_p < dist_to_q else "q"
        closest_dist = min(dist_to_p, dist_to_q)
        closest_bit_dist = min(bit_dist_to_p, bit_dist_to_q)
        
        spike_analysis = {
            "rank": i + 1,
            "b": b_spike,
            "center": center,
            "dist_to_p": dist_to_p,
            "dist_to_q": dist_to_q,
            "bit_dist_to_p": bit_dist_to_p,
            "bit_dist_to_q": bit_dist_to_q,
            "closest_factor": closest,
            "closest_distance": closest_dist,
            "closest_bit_distance": closest_bit_dist,
        }
        analysis["spike_analysis"].append(spike_analysis)
        
        if verbose:
            print(f"Spike #{i+1}: b*={b_spike:.4f}")
            print(f"  Center: {center:,}")
            print(f"  Distance to p: {dist_to_p:.3e} ({bit_dist_to_p:.4f} bits)")
            print(f"  Distance to q: {dist_to_q:.3e} ({bit_dist_to_q:.4f} bits)")
            print(f"  Closest factor: {closest}, distance: {closest_dist:.3e}")
            print()
    
    return analysis


def main():
    """Main entry point."""
    print("=" * 70)
    print("τ''' SPIKE REFINEMENT EXPERIMENT")
    print("127-bit Challenge Factorization Attempt")
    print("Follow-up to PR #131 (unbalanced-left-edge-127bit)")
    print("=" * 70)
    print()
    print("Target: N = 137524771864208156028430259349934309717")
    print()
    print("IMPROVEMENTS OVER PR #131:")
    print("  1. Richardson extrapolation for sub-bit spike accuracy")
    print("  2. Sobol QMC sampling (80% budget in ±0.1 bit inner region)")
    print("  3. Increased candidate budget (100k per spike, 1M total)")
    print()
    print("HYPOTHESIS: Improved localization + smarter sampling")
    print("            can achieve factor recovery")
    print()
    print("CONSTRAINTS:")
    print("  - No prior knowledge of factors used in algorithm")
    print("  - No classical fallbacks (Pollard, ECM, etc.)")
    print("  - Deterministic/quasi-deterministic methods only")
    print()
    
    # Run with parameters designed to test the hypothesis
    results = run_refinement_experiment(
        N=CHALLENGE_127,
        num_scan_points=1000,        # 2x PR #131 for finer resolution
        spike_threshold_factor=2.0,
        max_spikes_to_test=10,       # Focus on top 10 spikes
        outer_radius_bits=2.0,       # ±4x in outer region
        inner_radius_bits=0.1,       # ±7% in inner region
        inner_fraction=0.8,          # 80% budget in inner region
        candidates_per_spike=100000, # 100k per spike (1M total budget)
        verbose=True
    )
    
    # Post-hoc analysis for falsification documentation
    if results["spikes_detected"]:
        analysis = analyze_distance_to_actual_factors(
            results["spikes_detected"],
            verbose=True
        )
        results["post_hoc_analysis"] = analysis
    
    # Structured output
    print("\n" + "=" * 70)
    print("STRUCTURED OUTPUT")
    print("=" * 70)
    print(f"N = {results['N']}")
    print(f"experiment = {results['experiment']}")
    print(f"richardson_extrapolation = {results['richardson_extrapolation']}")
    print(f"has_scipy_sobol = {results['has_scipy_sobol']}")
    print(f"tau_scan_range = {results['tau_scan_range']}")
    print(f"factor_found = {results['factor_found']}")
    print(f"cofactor = {results['cofactor']}")
    print(f"verified = {results['verified']}")
    print(f"spikes_tested = {results['spikes_tested']}")
    print(f"total_candidates_tested = {results['total_candidates_tested']:,}")
    print(f"elapsed_ms = {results['elapsed_ms']:.2f}")
    
    # Save results
    json_path = "experiment_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {json_path}")
    
    return 0 if results["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
