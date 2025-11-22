"""
Baseline FR-GVA Implementation
================================

Minimal Fractal-Recursive GVA for comparison baseline.

This implements the core FR-GVA concept from the falsification experiment
but without Z5D enhancements. It provides the baseline for measuring Z5D impact.

Key components:
1. Fractal candidate generation (simplified Mandelbrot-inspired)
2. Recursive window subdivision
3. Geodesic distance computation
4. Uniform δ-sampling (no Z5D density weighting)

This is NOT the full FR-GVA from the previous experiment (which was falsified).
This is a minimal working version for this experiment's baseline.
"""

import mpmath as mp
from typing import List, Tuple, Optional, Dict
import time
from math import log, sqrt, isqrt

# Configure precision
mp.mp.dps = 100

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717


def adaptive_precision(N: int) -> int:
    """Compute adaptive precision: max(100, N.bitLength() × 4 + 200)"""
    return max(100, N.bit_length() * 4 + 200)


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """Embed integer n into 7D torus using geodesic mapping."""
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
    """Compute Riemannian geodesic distance on 7D torus."""
    dist_sq = mp.mpf(0)
    for c1, c2 in zip(p1, p2):
        diff = abs(c1 - c2)
        wrap_diff = mp.mpf(1) - diff
        min_diff = min(diff, wrap_diff)
        dist_sq += min_diff * min_diff
    return mp.sqrt(dist_sq)


def baseline_fr_gva(N: int, 
                    k_value: float = 0.35,
                    max_candidates: int = 10000,
                    delta_window: int = 100000,
                    verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Baseline FR-GVA: geodesic-guided search WITHOUT Z5D enhancements.
    
    Args:
        N: Semiprime to factor
        k_value: Geodesic exponent
        max_candidates: Maximum candidates to test
        delta_window: Half-width of δ-search window around √N
        verbose: Enable detailed logging
        
    Returns:
        Tuple (p, q) if factors found, None otherwise
    """
    required_dps = adaptive_precision(N)
    with mp.workdps(required_dps):
        if verbose:
            print("=" * 70)
            print("Baseline FR-GVA (without Z5D enhancements)")
            print("=" * 70)
            print(f"N = {N}")
            print(f"Bit length: {N.bit_length()}")
            print(f"Precision: {required_dps} dps")
            print(f"k = {k_value}")
            print(f"Max candidates: {max_candidates}")
            print(f"Delta window: ±{delta_window}")
            print()
        
        sqrt_N = isqrt(N)
        
        if verbose:
            print(f"√N = {sqrt_N}")
            print(f"Expected prime gap: ḡ ≈ log(√N) ≈ {log(float(sqrt_N)):.2f}")
            print()
        
        # Embed N in 7D torus
        N_coords = embed_torus_geodesic(N, k_value)
        
        start_time = time.time()
        
        # Sample candidates uniformly in δ-space
        # Use golden ratio sampling (QMC) for better coverage
        phi = (1 + sqrt(5)) / 2
        phi_inv = 1 / phi
        
        candidates_with_scores = []
        
        if verbose:
            print("Phase 1: Sampling candidates and computing distances...")
        
        for i in range(max_candidates):
            # Golden ratio QMC sequence for δ
            # Map [0, 1) to [-delta_window, +delta_window]
            alpha = (i * phi_inv) % 1.0
            delta = int(alpha * 2 * delta_window - delta_window)
            
            candidate = sqrt_N + delta
            
            # Skip trivial cases
            if candidate <= 1 or candidate >= N:
                continue
            if candidate % 2 == 0:
                continue
            
            # Compute geodesic distance
            cand_coords = embed_torus_geodesic(candidate, k_value)
            distance = riemannian_distance(N_coords, cand_coords)
            
            candidates_with_scores.append((candidate, distance, delta))
        
        if verbose:
            print(f"  Generated {len(candidates_with_scores)} candidates")
            print()
        
        # Sort by distance (ascending)
        candidates_with_scores.sort(key=lambda x: x[1])
        
        if verbose:
            print("Phase 2: Testing top candidates...")
            print(f"  Top 10 distances: {[float(d) for _, d, _ in candidates_with_scores[:10]]}")
            print()
        
        # Test candidates in order of ascending distance
        tested = 0
        for candidate, distance, delta in candidates_with_scores:
            tested += 1
            
            if N % candidate == 0:
                p = candidate
                q = N // candidate
                
                elapsed = time.time() - start_time
                
                if verbose:
                    print("✓ FACTOR FOUND!")
                    print(f"  p = {p}")
                    print(f"  q = {q}")
                    print(f"  δ = {delta}")
                    print(f"  Distance = {float(distance):.6e}")
                    print(f"  Candidates tested: {tested}")
                    print(f"  Elapsed: {elapsed:.3f}s")
                    print()
                
                return (p, q)
        
        elapsed = time.time() - start_time
        
        if verbose:
            print("✗ No factors found")
            print(f"  Candidates tested: {tested}")
            print(f"  Elapsed: {elapsed:.3f}s")
            print()
        
        return None


def main():
    """Test baseline FR-GVA on 127-bit challenge."""
    print("Testing Baseline FR-GVA on 127-bit Challenge")
    print("=" * 70)
    print()
    
    # Known factors for verification
    p_expected = 10508623501177419659
    q_expected = 13086849276577416863
    
    print(f"N = {CHALLENGE_127}")
    print(f"Expected factors:")
    print(f"  p = {p_expected}")
    print(f"  q = {q_expected}")
    print(f"  p × q = {p_expected * q_expected}")
    print(f"  Verify: {p_expected * q_expected == CHALLENGE_127}")
    print()
    
    # Run baseline
    result = baseline_fr_gva(
        CHALLENGE_127,
        k_value=0.35,
        max_candidates=50000,  # Larger budget for 127-bit
        delta_window=500000,   # Larger window for 127-bit
        verbose=True
    )
    
    if result:
        p, q = result
        print("=" * 70)
        print("SUCCESS: Factors found!")
        print(f"  p = {p}")
        print(f"  q = {q}")
        print(f"  p × q = {p * q}")
        print(f"  Verify: {p * q == CHALLENGE_127}")
    else:
        print("=" * 70)
        print("FAILURE: No factors found within budget")


if __name__ == "__main__":
    main()
