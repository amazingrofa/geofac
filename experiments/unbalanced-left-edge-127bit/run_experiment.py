#!/usr/bin/env python3
"""
Unbalanced Left-Edge Geometry Experiment for 127-bit Challenge
================================================================

Hypothesis: For unbalanced semiprimes, there exists a "left-edge cliff" in
τ-space where the small factor lives. This cliff can be detected via the
third derivative of τ with respect to a scale parameter.

Target: N = 137524771864208156028430259349934309717 (127-bit challenge)

Method:
1. Define τ(b) as a log-folded geometric score over scan parameter b (scale/bit index)
2. Compute τ'(b), τ''(b), τ'''(b) via finite differences
3. Detect τ''' spike (the left-edge cliff signature)
4. Map spike location b* to candidate factor region
5. Test candidates with N % candidate == 0

NO prior knowledge of factors is used in the algorithm.
NO classical fallbacks (Pollard, ECM, trial division as primary method).
Only the final divisibility check N % candidate == 0 is used for validation.
"""

import time
import json
import sys
from datetime import datetime
from math import log, exp, sqrt, floor, ceil
from typing import List, Tuple, Optional

# Add mpmath for high precision
try:
    import mpmath as mp
except ImportError:
    print("ERROR: mpmath required. Install with: pip install mpmath")
    sys.exit(1)

# Challenge constant - NO factors stored in the algorithm
CHALLENGE_127 = 137524771864208156028430259349934309717


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bit_length() * 4 + 200)
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def set_precision(N: int) -> int:
    """Set mpmath precision and return the value used."""
    precision = adaptive_precision(N)
    mp.mp.dps = precision
    return precision


def compute_tau(N: int, b: float, phi: mp.mpf) -> mp.mpf:
    """
    Compute τ(b): a log-folded geometric score at scale parameter b.
    
    The τ-function measures geometric resonance at a given scale.
    For unbalanced semiprimes, there should be a sharp transition
    at the scale corresponding to the smaller factor.
    
    τ(b) = log(1 + resonance_score)
    
    where resonance_score involves:
    - Distance from 2^b to sqrt(N) (geometric scale alignment)
    - Modular relationship between N and the scale
    - Golden ratio phase alignment
    
    Args:
        N: The semiprime to factor
        b: Scale parameter (bit index, typically 1 to N.bit_length())
        phi: Golden ratio (pre-computed for efficiency)
    
    Returns:
        τ(b) as mpf
    """
    # Compute the scale at bit index b
    # scale = 2^b represents the candidate factor magnitude
    scale = mp.power(2, b)
    
    # Compute sqrt(N) for reference
    sqrt_N = mp.sqrt(N)
    
    # Distance metric: how far is this scale from sqrt(N)?
    # Normalized by sqrt(N) for numerical stability
    if scale < 1:
        return mp.mpf(0)
    
    # Geometric distance ratio (log-folded for stability)
    ratio = scale / sqrt_N
    if ratio <= 0:
        return mp.mpf(0)
    
    log_ratio = mp.log(ratio)
    
    # Resonance component: modular structure
    # For a true factor p, N mod p = 0
    # Near a factor, N mod scale should show structure
    scale_int = int(mp.floor(scale))
    if scale_int < 2:
        mod_resonance = mp.mpf(0)
    else:
        remainder = N % scale_int
        # Normalize: closer to 0 or scale means higher resonance
        mod_normalized = min(remainder, scale_int - remainder) / scale_int
        mod_resonance = 1 - mod_normalized  # Higher = closer to divisibility
    
    # Phase alignment with golden ratio
    # Factors show characteristic phase relationships when scale aligns with factor structure
    # Using sin² creates period-0.5 oscillation: max alignment at phase = 0, 0.5, 1
    # This detects scale values where N's multiplicative structure resonates with φ
    phase = mp.fmod(scale * phi, 1)
    phase_alignment = mp.mpf(1) - mp.power(mp.sin(mp.pi * phase), 2)
    
    # Combined geometric score
    # Weight modular resonance heavily - it's the key signal
    geometric_score = (
        0.5 * phase_alignment +  # Phase component
        0.5 * mod_resonance      # Modular component (divisibility signal)
    )
    
    # Apply exponential decay based on distance from sqrt(N)
    # This focuses the signal near plausible factor locations
    decay = mp.exp(-abs(log_ratio) * 0.5)
    
    # Final τ: log-folded for numerical stability
    tau = mp.log(1 + geometric_score * decay)
    
    return tau


def compute_tau_derivative_profile(
    N: int,
    b_start: float,
    b_end: float,
    num_points: int,
    phi: mp.mpf
) -> Tuple[List[float], List[mp.mpf], List[mp.mpf], List[mp.mpf], List[mp.mpf]]:
    """
    Compute τ and its derivatives across the scale range [b_start, b_end].
    
    Uses finite differences for derivatives:
    τ'(b)   ≈ (τ(b+h) - τ(b-h)) / (2h)
    τ''(b)  ≈ (τ(b+h) - 2τ(b) + τ(b-h)) / h²
    τ'''(b) ≈ (τ(b+2h) - 2τ(b+h) + 2τ(b-h) - τ(b-2h)) / (2h³)
    
    Returns:
        Tuple of (b_values, tau_values, tau_prime, tau_double_prime, tau_triple_prime)
    """
    # Step size for finite differences
    h = (b_end - b_start) / (num_points - 1)
    
    # Pre-compute τ values with padding for derivative computation
    b_extended_start = b_start - 2 * h
    b_extended_end = b_end + 2 * h
    extended_points = num_points + 4
    extended_h = (b_extended_end - b_extended_start) / (extended_points - 1)
    
    tau_extended = []
    b_extended = []
    
    for i in range(extended_points):
        b = b_extended_start + i * extended_h
        b_extended.append(b)
        tau_extended.append(compute_tau(N, b, phi))
    
    # Extract the main range values
    b_values = []
    tau_values = []
    tau_prime = []
    tau_double_prime = []
    tau_triple_prime = []
    
    for i in range(2, extended_points - 2):
        b = b_extended[i]
        b_values.append(float(b))
        
        tau_curr = tau_extended[i]
        tau_values.append(tau_curr)
        
        # First derivative: (τ[i+1] - τ[i-1]) / (2h)
        d1 = (tau_extended[i + 1] - tau_extended[i - 1]) / (2 * extended_h)
        tau_prime.append(d1)
        
        # Second derivative: (τ[i+1] - 2τ[i] + τ[i-1]) / h²
        d2 = (tau_extended[i + 1] - 2 * tau_curr + tau_extended[i - 1]) / (extended_h ** 2)
        tau_double_prime.append(d2)
        
        # Third derivative: (τ[i+2] - 2τ[i+1] + 2τ[i-1] - τ[i-2]) / (2h³)
        d3 = (tau_extended[i + 2] - 2 * tau_extended[i + 1] + 
              2 * tau_extended[i - 1] - tau_extended[i - 2]) / (2 * extended_h ** 3)
        tau_triple_prime.append(d3)
    
    return b_values, tau_values, tau_prime, tau_double_prime, tau_triple_prime


def find_tau_triple_spikes(
    b_values: List[float],
    tau_triple_prime: List[mp.mpf],
    threshold_factor: float = 2.0
) -> List[Tuple[int, float, mp.mpf]]:
    """
    Find spikes in τ'''(b) that indicate left-edge cliff signatures.
    
    A spike is defined as a point where |τ'''(b)| exceeds threshold_factor
    times the mean absolute value.
    
    Args:
        b_values: Scale parameter values
        tau_triple_prime: Third derivative values
        threshold_factor: How many times above mean to count as spike
    
    Returns:
        List of (index, b_value, spike_magnitude) sorted by magnitude descending
    """
    # Compute mean absolute value
    abs_values = [abs(float(d3)) for d3 in tau_triple_prime]
    mean_abs = sum(abs_values) / len(abs_values) if abs_values else 1.0
    
    # Find points exceeding threshold
    spikes = []
    threshold = mean_abs * threshold_factor
    
    for i, (b, d3) in enumerate(zip(b_values, tau_triple_prime)):
        magnitude = abs(float(d3))
        if magnitude > threshold:
            spikes.append((i, b, d3))
    
    # Sort by magnitude descending
    spikes.sort(key=lambda x: abs(float(x[2])), reverse=True)
    
    return spikes


def map_spike_to_candidates(
    N: int,
    b_spike: float,
    search_radius_bits: float = 2.0,
    max_candidates: int = 10000
) -> List[int]:
    """
    Map a spike location b* to candidate factor values.
    
    The spike at b* suggests the small factor is near 2^b*.
    We search a region around this scale.
    
    Args:
        N: The semiprime
        b_spike: Spike location in bit space
        search_radius_bits: How many bits around b_spike to search
        max_candidates: Maximum number of candidates to generate
    
    Returns:
        List of candidate factor values to test
    """
    # Central estimate: 2^b_spike
    center = int(mp.power(2, b_spike))
    
    # Search range: [2^(b_spike - radius), 2^(b_spike + radius)]
    low = int(mp.power(2, b_spike - search_radius_bits))
    high = int(mp.power(2, b_spike + search_radius_bits))
    
    # Ensure valid range
    low = max(2, low)
    high = min(N - 1, high)
    
    # If range is too large, sample around center
    range_size = high - low
    
    if range_size > max_candidates:
        # Dense sampling around center, sparser farther out
        candidates = []
        
        # Inner region: step 1 (minimum radius of 1 to avoid empty search)
        inner_radius = max(1, min(range_size // 4, max_candidates // 2))
        for offset in range(-inner_radius, inner_radius + 1):
            c = center + offset
            if low <= c <= high and c > 1:
                candidates.append(c)
        
        # Outer region: logarithmic sampling with exponential offset growth
        # OUTER_GROWTH_RATE controls sampling density: 1.1 gives ~10% increase per step
        # Higher values = sparser outer sampling, lower values = denser but slower
        OUTER_GROWTH_RATE = 1.1
        remaining = max_candidates - len(candidates)
        if remaining > 0:
            # Sample outward from inner region
            for i in range(remaining // 2):
                # Exponentially increasing offsets
                offset = inner_radius + int(OUTER_GROWTH_RATE ** i)
                if offset > range_size // 2:
                    break
                
                c_plus = center + offset
                c_minus = center - offset
                
                if low <= c_plus <= high and c_plus not in candidates:
                    candidates.append(c_plus)
                if low <= c_minus <= high and c_minus > 1 and c_minus not in candidates:
                    candidates.append(c_minus)
        
        return sorted(set(candidates))
    else:
        # Range is small enough: enumerate all
        return list(range(low, high + 1))


def test_candidates(N: int, candidates: List[int], verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Test candidate factors for divisibility.
    
    This is the ONLY divisibility check used - purely for validation,
    not as a search strategy.
    
    Args:
        N: The semiprime
        candidates: List of candidate factors to test
        verbose: Print progress
    
    Returns:
        (p, q) if factor found, None otherwise
    """
    tested = 0
    for c in candidates:
        if c <= 1 or c >= N:
            continue
        
        tested += 1
        
        if N % c == 0:
            p = c
            q = N // c
            if verbose:
                print(f"  Factor found after testing {tested} candidates")
                print(f"  p = {p}")
                print(f"  q = {q}")
            return (min(p, q), max(p, q))
    
    if verbose:
        print(f"  No factor found after testing {tested} candidates")
    
    return None


def run_left_edge_experiment(
    N: int = CHALLENGE_127,
    num_scan_points: int = 500,
    spike_threshold_factor: float = 2.0,
    max_spikes_to_test: int = 20,
    search_radius_bits: float = 3.0,
    candidates_per_spike: int = 5000,
    verbose: bool = True
) -> dict:
    """
    Run the unbalanced left-edge geometry experiment.
    
    Args:
        N: Semiprime to factor (default: 127-bit challenge)
        num_scan_points: Number of points in τ scan
        spike_threshold_factor: Threshold for spike detection
        max_spikes_to_test: Maximum number of spikes to investigate
        search_radius_bits: Search radius around spike in bits
        candidates_per_spike: Max candidates to test per spike
        verbose: Enable detailed output
    
    Returns:
        Experiment results dictionary
    """
    start_time = time.time()
    
    # Set precision
    precision = set_precision(N)
    
    # Initialize results
    results = {
        "timestamp": datetime.now().isoformat(),
        "N": str(N),
        "N_bit_length": N.bit_length(),
        "mode": "UNBALANCED_LEFT_EDGE",
        "precision_dps": precision,
        "num_scan_points": num_scan_points,
        "spike_threshold_factor": spike_threshold_factor,
        "max_spikes_to_test": max_spikes_to_test,
        "search_radius_bits": search_radius_bits,
        "candidates_per_spike": candidates_per_spike,
        "candidate_factor_found": None,
        "cofactor": None,
        "verified": False,
        "elapsed_ms": 0,
        "spikes_detected": [],
        "spikes_tested": 0,
        "total_candidates_tested": 0,
    }
    
    if verbose:
        print("=" * 70)
        print("UNBALANCED LEFT-EDGE GEOMETRY EXPERIMENT")
        print("=" * 70)
        print(f"N = {N}")
        print(f"N_bit_length = {N.bit_length()}")
        print(f"mode = UNBALANCED_LEFT_EDGE")
        print(f"precision_dps = {precision}")
        print(f"num_scan_points = {num_scan_points}")
        print(f"spike_threshold_factor = {spike_threshold_factor}")
        print("=" * 70)
    
    # Define scan range: from small factors (bit 1) to sqrt(N) region
    # For unbalanced semiprimes, the small factor is well below sqrt(N)
    sqrt_N = mp.sqrt(N)
    sqrt_N_bits = float(mp.log(sqrt_N, 2))
    
    # Scan from bit 1 to sqrt(N) bits + some margin
    b_start = 1.0
    b_end = sqrt_N_bits + 2.0  # Go slightly beyond sqrt(N)
    
    results["tau_scan_range"] = [b_start, b_end]
    
    if verbose:
        print(f"\nτ scan range: [{b_start:.2f}, {b_end:.2f}] bits")
        print(f"sqrt(N) ≈ 2^{sqrt_N_bits:.2f}")
        print("-" * 70)
    
    # Compute τ and derivatives
    if verbose:
        print("\nPhase 1: Computing τ(b) and derivatives...")
    
    phi = (1 + mp.sqrt(5)) / 2  # Golden ratio
    
    b_values, tau_values, tau_prime, tau_double_prime, tau_triple_prime = \
        compute_tau_derivative_profile(N, b_start, b_end, num_scan_points, phi)
    
    if verbose:
        print(f"  Computed {len(b_values)} τ values")
        
        # Show τ statistics
        tau_floats = [float(t) for t in tau_values]
        print(f"  τ range: [{min(tau_floats):.6f}, {max(tau_floats):.6f}]")
        
        d3_floats = [float(d) for d in tau_triple_prime]
        print(f"  τ''' range: [{min(d3_floats):.6e}, {max(d3_floats):.6e}]")
    
    # Find spikes in τ'''
    if verbose:
        print("\nPhase 2: Detecting τ''' spikes (left-edge signatures)...")
    
    spikes = find_tau_triple_spikes(b_values, tau_triple_prime, spike_threshold_factor)
    
    results["spikes_detected"] = [
        {"index": s[0], "b": s[1], "magnitude": float(s[2])}
        for s in spikes[:max_spikes_to_test * 2]  # Store more for analysis
    ]
    
    if verbose:
        print(f"  Found {len(spikes)} spikes above threshold")
        if spikes:
            print(f"  Top 5 spikes by magnitude:")
            for i, (idx, b, mag) in enumerate(spikes[:5]):
                print(f"    {i+1}. b = {b:.4f} (2^b ≈ {int(2**b):,}), |τ'''| = {abs(float(mag)):.6e}")
    
    # Test spikes as potential factor locations
    if verbose:
        print("\nPhase 3: Testing spike locations for factors...")
    
    total_candidates_tested = 0
    spikes_tested = 0
    
    for spike_idx, (idx, b_spike, magnitude) in enumerate(spikes[:max_spikes_to_test]):
        spikes_tested += 1
        
        if verbose:
            print(f"\n  Testing spike {spikes_tested}/{min(len(spikes), max_spikes_to_test)}:")
            print(f"    b* = {b_spike:.4f}")
            print(f"    Candidate scale: 2^{b_spike:.2f} ≈ {int(2**b_spike):,}")
        
        # Generate candidates around this spike
        candidates = map_spike_to_candidates(
            N, b_spike, search_radius_bits, candidates_per_spike
        )
        
        if verbose:
            print(f"    Generated {len(candidates)} candidates")
        
        # Test candidates
        factor_result = test_candidates(N, candidates, verbose=verbose)
        total_candidates_tested += len(candidates)
        
        if factor_result:
            p, q = factor_result
            results["candidate_factor_found"] = str(p)
            results["cofactor"] = str(q)
            results["verified"] = (p * q == N)
            results["tau_third_derivative_spike_at"] = b_spike
            results["spikes_tested"] = spikes_tested
            results["total_candidates_tested"] = total_candidates_tested
            
            elapsed = (time.time() - start_time) * 1000
            results["elapsed_ms"] = elapsed
            
            if verbose:
                print("\n" + "=" * 70)
                print("SUCCESS - FACTOR FOUND")
                print("=" * 70)
                print(f"candidate_factor_found = {p}")
                print(f"cofactor = {q}")
                print(f"verified = {results['verified']}")
                print(f"tau_third_derivative_spike_at = {b_spike:.4f}")
                print(f"spikes_tested = {spikes_tested}")
                print(f"total_candidates_tested = {total_candidates_tested}")
                print(f"elapsed_ms = {elapsed:.2f}")
            
            return results
    
    # No factor found
    results["spikes_tested"] = spikes_tested
    results["total_candidates_tested"] = total_candidates_tested
    results["tau_third_derivative_spike_at"] = None
    
    elapsed = (time.time() - start_time) * 1000
    results["elapsed_ms"] = elapsed
    
    if verbose:
        print("\n" + "=" * 70)
        print("NO FACTOR FOUND")
        print("=" * 70)
        print(f"spikes_tested = {spikes_tested}")
        print(f"total_candidates_tested = {total_candidates_tested}")
        print(f"elapsed_ms = {elapsed:.2f}")
    
    return results


def main():
    """Main entry point."""
    print("=" * 70)
    print("UNBALANCED LEFT-EDGE GEOMETRY EXPERIMENT")
    print("127-bit Challenge Factorization Attempt")
    print("=" * 70)
    print()
    print("Target: N = 137524771864208156028430259349934309717")
    print("Hypothesis: Left-edge cliff in τ-space reveals small factor location")
    print("Method: τ'''(b) spike detection + candidate testing")
    print()
    print("CONSTRAINTS:")
    print("  - No prior knowledge of factors used")
    print("  - No classical fallbacks (Pollard, ECM, etc.)")
    print("  - Only divisibility check is final validation: N % candidate == 0")
    print()
    
    # Run experiment with default parameters
    results = run_left_edge_experiment(
        N=CHALLENGE_127,
        num_scan_points=500,
        spike_threshold_factor=2.0,
        max_spikes_to_test=20,
        search_radius_bits=3.0,
        candidates_per_spike=5000,
        verbose=True
    )
    
    # Output structured results
    print("\n" + "=" * 70)
    print("STRUCTURED OUTPUT")
    print("=" * 70)
    print(f"N = {results['N']}")
    print(f"mode = {results['mode']}")
    print(f"tau_scan_range = {results['tau_scan_range']}")
    print(f"tau_third_derivative_spike_at = {results.get('tau_third_derivative_spike_at', 'None')}")
    print(f"candidate_factor_found = {results['candidate_factor_found']}")
    print(f"cofactor = {results['cofactor']}")
    print(f"verified = {results['verified']}")
    print(f"elapsed_ms = {results['elapsed_ms']:.2f}")
    
    # Save JSON results
    json_path = "experiment_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {json_path}")
    
    return 0 if results['verified'] else 1


if __name__ == "__main__":
    sys.exit(main())
