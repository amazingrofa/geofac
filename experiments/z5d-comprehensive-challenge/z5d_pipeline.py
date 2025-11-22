"""
Z5D-Enhanced Candidate Pipeline
=================================

Implements the Z5D-guided candidate generation pipeline:
1. 210-wheel as hard filter
2. Z5D-based δ-band prioritization
3. Z5D-based adaptive step sizing
4. FR-GVA amplitude for ranking within stream

This pipeline uses Z5D as a STEPPING oracle, not just a score term.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'z5d-informed-gva'))

from wheel_residues import (
    is_admissible, next_admissible, WHEEL_MODULUS, WHEEL_SIZE
)
from z5d_api import (
    prioritize_delta_bands, adaptive_step_size, density_in_range,
    local_prime_density
)
import mpmath as mp
from typing import List, Tuple, Optional, Dict, Iterator
from math import log, isqrt


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


def compute_gva_amplitude(candidate: int, 
                         sqrt_N_embedding: List[mp.mpf],
                         k_value: float) -> float:
    """
    Compute FR-GVA amplitude for a candidate.
    
    This is used for RANKING within the Z5D-filtered stream,
    not for density estimation.
    
    Args:
        candidate: Candidate value
        sqrt_N_embedding: Pre-computed embedding of √N
        k_value: Geodesic exponent
        
    Returns:
        Amplitude (smaller = better)
    """
    cand_embedding = embed_torus_geodesic(candidate, k_value)
    distance = riemannian_distance(cand_embedding, sqrt_N_embedding)
    return float(distance)


def generate_z5d_candidates(N: int,
                            sqrt_N: int,
                            delta_max: int,
                            num_bands: int,
                            k_value: float = 0.35,
                            verbose: bool = False) -> Iterator[Dict]:
    """
    Generate candidates using Z5D pipeline.
    
    Yields candidates in priority order:
    1. High-density Z5D bands first
    2. Within bands: wheel-filtered
    3. Adaptive stepping based on local density
    4. Each candidate tagged with metadata
    
    Args:
        N: Semiprime to factor
        sqrt_N: Floor of square root
        delta_max: Maximum δ-offset
        num_bands: Number of δ-bands
        k_value: GVA exponent
        verbose: Logging flag
        
    Yields:
        Dict with keys: candidate, delta, residue, density, amplitude, band_id
    """
    required_dps = adaptive_precision(N)
    
    with mp.workdps(required_dps):
        # Pre-compute √N embedding for GVA amplitude
        sqrt_N_embedding = embed_torus_geodesic(sqrt_N, k_value)
        
        # Get prioritized bands from Z5D
        bands = prioritize_delta_bands(sqrt_N, delta_max, num_bands)
        
        if verbose:
            print(f"Z5D Pipeline: {len(bands)} bands, δ_max={delta_max}")
            print(f"Top 3 bands:")
            for i, band in enumerate(bands[:3]):
                print(f"  {i+1}. δ=[{band['delta_start']}, {band['delta_end']}], "
                      f"density={band['density']:.6e}")
            print()
        
        # Iterate through bands in priority order
        for band_idx, band in enumerate(bands):
            delta_start = band['delta_start']
            delta_end = band['delta_end']
            density = band['density']
            
            # Determine step size for this band
            step = adaptive_step_size(density, base_step=1)
            
            # Scan this band
            current_delta = delta_start
            while current_delta <= delta_end:
                # Candidate = √N + δ
                candidate = sqrt_N + current_delta
                
                # Apply wheel filter
                if not is_admissible(candidate):
                    # Jump to next admissible
                    candidate = next_admissible(candidate)
                    current_delta = candidate - sqrt_N
                    
                    # Check if we've exceeded band
                    if current_delta > delta_end:
                        break
                
                # Compute GVA amplitude for ranking
                amplitude = compute_gva_amplitude(
                    candidate, sqrt_N_embedding, k_value
                )
                
                # Yield candidate with metadata
                yield {
                    'candidate': candidate,
                    'delta': current_delta,
                    'residue': candidate % WHEEL_MODULUS,
                    'density': density,
                    'amplitude': amplitude,
                    'band_id': band_idx,
                    'step': step
                }
                
                # Advance by adaptive step
                current_delta += step
                
                # Also try negative δ
                if current_delta <= delta_max:
                    neg_candidate = sqrt_N - current_delta
                    if neg_candidate > 1 and is_admissible(neg_candidate):
                        neg_amplitude = compute_gva_amplitude(
                            neg_candidate, sqrt_N_embedding, k_value
                        )
                        yield {
                            'candidate': neg_candidate,
                            'delta': -current_delta,
                            'residue': neg_candidate % WHEEL_MODULUS,
                            'density': density,
                            'amplitude': neg_amplitude,
                            'band_id': band_idx,
                            'step': step
                        }


def z5d_pipeline_search(N: int,
                       max_candidates: int = 100000,
                       delta_max: int = 100000,
                       num_bands: int = 10,
                       k_value: float = 0.35,
                       verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Full Z5D pipeline search.
    
    Args:
        N: Semiprime to factor
        max_candidates: Budget limit
        delta_max: Maximum δ-offset
        num_bands: Number of δ-bands
        k_value: GVA exponent
        verbose: Logging flag
        
    Returns:
        Tuple (p, q) if factors found, None otherwise
    """
    sqrt_N = isqrt(N)
    
    if verbose:
        print("=" * 70)
        print("Z5D Pipeline Search")
        print("=" * 70)
        print(f"N = {N}")
        print(f"√N = {sqrt_N}")
        print(f"Max candidates: {max_candidates}")
        print(f"δ_max: {delta_max}")
        print(f"Bands: {num_bands}")
        print()
    
    tested = 0
    for cand_data in generate_z5d_candidates(
        N, sqrt_N, delta_max, num_bands, k_value, verbose
    ):
        candidate = cand_data['candidate']
        
        # Test divisibility
        if N % candidate == 0:
            p = candidate
            q = N // p
            if verbose:
                print(f"\n*** FACTOR FOUND ***")
                print(f"p = {p}")
                print(f"q = {q}")
                print(f"N = {N}")
                print(f"Verified: {p * q == N}")
                print(f"Candidates tested: {tested + 1}")
            return (p, q)
        
        tested += 1
        if tested >= max_candidates:
            break
        
        # Progress logging
        if verbose and tested % 10000 == 0:
            print(f"  Tested {tested} candidates, δ={cand_data['delta']}, "
                  f"band={cand_data['band_id']}, amp={cand_data['amplitude']:.4f}")
    
    if verbose:
        print(f"\nSearch exhausted after {tested} candidates")
    
    return None


if __name__ == "__main__":
    # Quick test
    print("Testing Z5D Pipeline on small semiprime...")
    
    # 60-bit test case
    p = next_prime(2**29 + 1)
    q = next_prime(2**29 + 1000)
    N = p * q
    
    print(f"Test: N = {N}")
    print(f"True factors: p = {p}, q = {q}")
    print()
    
    result = z5d_pipeline_search(
        N,
        max_candidates=10000,
        delta_max=50000,
        num_bands=5,
        verbose=True
    )
    
    if result:
        print("\nSUCCESS!")
    else:
        print("\nFailed to find factors")


def next_prime(n: int) -> int:
    """Find next prime >= n (for testing)."""
    if n <= 2:
        return 2
    if n % 2 == 0:
        n += 1
    while not miller_rabin(n):
        n += 2
    return n


def miller_rabin(n: int, k: int = 10) -> bool:
    """Miller-Rabin primality test."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    def check_witness(a):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return True
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                return True
        return False
    witnesses = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    for a in witnesses[:k]:
        if a >= n:
            continue
        if not check_witness(a):
            return False
    return True
