"""
Hash-Bounds Partition Sampling
==============================

Implements boundary-focused sampling based on fractional square roots
of seed primes (2, 3, 5, 7, 11, 13).

Hypothesis: Factors preferentially cluster near boundaries at n × frac(√p),
and concentrating Sobol/Halton points near these boundaries improves
factor detection vs. uniform sampling.

Validation range: [10^14, 10^18] per VALIDATION_GATES.md
Whitelist: 127-bit CHALLENGE_127 = 137524771864208156028430259349934309717
"""

import mpmath as mp
from typing import List, Tuple, Optional, Dict
import time
from math import log, sqrt, isqrt

# Configure high precision for computations
# Precision should be set explicitly in functions using mp.workdps()

# Validation gates
GATE_1_30BIT = 1073217479  # 32749 × 32771
GATE_2_60BIT = 1152921470247108503  # 1073741789 × 1073741827
CHALLENGE_127 = 137524771864208156028430259349934309717  # 10508623501177419659 × 13086849276577416863

# Operational range
RANGE_MIN = 10**14
RANGE_MAX = 10**18

# Seed primes for fractional square root boundaries
SEED_PRIMES = [2, 3, 5, 7, 11, 13]


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bitLength() × 4 + 200)
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def compute_fractional_sqrt(p: int, precision: int = 100) -> mp.mpf:
    """
    Compute fractional part of √p with specified precision.
    
    frac(√p) = √p - floor(√p)
    
    Args:
        p: Prime number
        precision: Decimal precision (dps)
        
    Returns:
        Fractional part as mpmath.mpf
    """
    with mp.workdps(precision):
        sqrt_p = mp.sqrt(p)
        frac_part = sqrt_p - mp.floor(sqrt_p)
        return frac_part


def get_all_fractional_roots(precision: int = 100) -> Dict[int, mp.mpf]:
    """
    Compute fractional parts of √p for all seed primes.
    
    Args:
        precision: Decimal precision
        
    Returns:
        Dict mapping prime p -> frac(√p)
    """
    result = {}
    with mp.workdps(precision):
        for p in SEED_PRIMES:
            result[p] = compute_fractional_sqrt(p, precision)
    return result


def compute_boundary_centers(sqrt_N: int, frac_sqrt: mp.mpf, 
                            window: int = 100000) -> List[int]:
    """
    Compute boundary centers near √N for a given fractional root.
    
    Boundaries occur at offsets δ where δ × frac(√p) is close to an integer,
    i.e., where (δ × frac(√p)) mod 1 ≈ 0.
    
    For frac(√p) = α, boundaries are approximately at δ = k/α for integers k.
    
    Args:
        sqrt_N: Integer square root of N
        frac_sqrt: Fractional part of √p
        window: Search window ±window around sqrt_N
        
    Returns:
        List of boundary center positions (as offsets from sqrt_N)
    """
    boundaries = []
    frac_float = float(frac_sqrt)
    
    if frac_float <= 0:
        return boundaries
    
    # Boundaries occur at positions δ where δ × frac(√p) ≈ integer
    # This happens at δ ≈ k / frac(√p) for integers k
    # The spacing between boundaries is approximately 1/frac(√p)
    
    boundary_spacing = 1.0 / frac_float
    
    # Find all boundaries within the window
    # Start from k=0 and go both directions
    k = 0
    while True:
        boundary_pos = int(k * boundary_spacing)
        
        if boundary_pos > window:
            break
        
        boundaries.append(boundary_pos)
        if boundary_pos > 0:
            boundaries.append(-boundary_pos)
        
        k += 1
        
        # Safety limit only for extreme cases (e.g. millions of boundaries)
        # 2000 was too small and truncated the search window
        if len(boundaries) > 2000000:
            break
    
    return sorted(set(boundaries))


def compute_all_boundaries(sqrt_N: int, precision: int = 100, 
                          window: int = 100000) -> Dict[int, List[int]]:
    """
    Compute boundary centers for all seed primes.
    
    Args:
        sqrt_N: Integer square root of N
        precision: Decimal precision
        window: Search window
        
    Returns:
        Dict mapping prime p -> list of boundary offsets
    """
    frac_roots = get_all_fractional_roots(precision)
    all_boundaries = {}
    
    for p, frac_sqrt in frac_roots.items():
        all_boundaries[p] = compute_boundary_centers(sqrt_N, frac_sqrt, window)
    
    return all_boundaries


def distance_to_nearest_boundary(offset: int, boundaries: List[int]) -> int:
    """
    Compute minimum distance from offset to any boundary.
    
    Args:
        offset: Offset from √N
        boundaries: List of boundary positions
        
    Returns:
        Minimum distance to any boundary
    """
    if not boundaries:
        return abs(offset)
    
    min_dist = float('inf')
    for b in boundaries:
        dist = abs(offset - b)
        if dist < min_dist:
            min_dist = dist
    
    return int(min_dist)


def boundary_proximity_score(offset: int, all_boundaries: Dict[int, List[int]],
                            decay_scale: float = 100.0) -> float:
    """
    Compute boundary proximity score for a candidate offset.
    
    Higher score means closer to boundaries.
    Uses exponential decay from boundaries.
    
    Args:
        offset: Offset from √N
        all_boundaries: Dict mapping prime -> boundary offsets
        decay_scale: Distance scale for exponential decay
        
    Returns:
        Proximity score in [0, 1] range (higher = closer to boundaries)
    """
    total_score = 0.0
    
    for p, boundaries in all_boundaries.items():
        dist = distance_to_nearest_boundary(offset, boundaries)
        # Exponential decay from boundaries
        score = mp.exp(-dist / decay_scale)
        total_score += float(score)
    
    # Normalize by number of seed primes
    return total_score / len(SEED_PRIMES)


def generate_boundary_focused_samples(sqrt_N: int, 
                                      n_samples: int,
                                      window: int = 100000,
                                      boundary_weight: float = 0.7,
                                      seed: int = 42) -> List[int]:
    """
    Generate samples focused near hash boundaries.
    
    Uses mixture of boundary-focused and uniform sampling.
    
    Args:
        sqrt_N: Integer square root of N
        n_samples: Number of samples to generate
        window: Search window ±window
        boundary_weight: Fraction of samples near boundaries (0-1)
        seed: Random seed for reproducibility
        
    Returns:
        List of candidate offsets from sqrt_N
    """
    precision = adaptive_precision(sqrt_N ** 2)
    all_boundaries = compute_all_boundaries(sqrt_N, precision, window)
    
    # Collect all boundary points
    all_boundary_points = set()
    for boundaries in all_boundaries.values():
        all_boundary_points.update(boundaries)
    all_boundary_points = sorted(all_boundary_points)
    
    samples = []
    
    # Golden ratio for quasi-random uniform coverage
    phi_inv = (sqrt(5) - 1) / 2
    
    # Number of boundary-focused vs uniform samples
    n_boundary = int(n_samples * boundary_weight)
    n_uniform = n_samples - n_boundary
    
    # Generate boundary-focused samples using Sobol-like sequence
    # Samples clustered near boundary points with local QMC
    for i in range(n_boundary):
        if not all_boundary_points:
            break
            
        # Select boundary point using golden ratio sequence
        idx = int((i * phi_inv) % 1.0 * len(all_boundary_points))
        boundary_center = all_boundary_points[idx % len(all_boundary_points)]
        
        # Local offset using golden ratio within boundary region
        local_width = max(10, int(log(sqrt_N)))  # Scale with N
        alpha = ((i * phi_inv * phi_inv) % 1.0) * 2 - 1  # Range [-1, 1]
        local_offset = int(alpha * local_width)
        
        sample = boundary_center + local_offset
        if -window <= sample <= window:
            samples.append(sample)
    
    # Generate uniform samples using golden ratio QMC
    for i in range(n_uniform):
        alpha = ((seed + i) * phi_inv) % 1.0
        offset = int(alpha * 2 * window - window)
        if offset not in samples:  # Avoid duplicates
            samples.append(offset)
    
    return samples


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """
    Embed integer n into 7D torus using geodesic mapping.
    
    Uses golden ratio powers for quasi-periodic embedding.
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
    Compute Riemannian geodesic distance on 7D torus.
    """
    dist_sq = mp.mpf(0)
    for c1, c2 in zip(p1, p2):
        diff = abs(c1 - c2)
        wrap_diff = mp.mpf(1) - diff
        min_diff = min(diff, wrap_diff)
        dist_sq += min_diff * min_diff
    return mp.sqrt(dist_sq)


def hash_bounds_factor_search(N: int,
                              k_value: float = 0.35,
                              max_candidates: int = 10000,
                              delta_window: int = 100000,
                              boundary_weight: float = 0.7,
                              boundary_proximity_weight: float = 0.1,
                              seed: int = 42,
                              verbose: bool = False,
                              allow_any_range: bool = False) -> Optional[Tuple[int, int]]:
    """
    Factor semiprime N using hash-bounds focused sampling.
    
    Integrates:
    1. Fractional square root boundary computation
    2. Boundary-focused Sobol sampling
    3. GVA 7D torus embedding
    4. Combined scoring: geodesic distance + boundary proximity
    
    Args:
        N: Semiprime to factor
        k_value: Geodesic exponent for torus embedding
        max_candidates: Maximum candidates to test
        delta_window: Half-width of δ-search window around √N
        boundary_weight: Fraction of samples near boundaries (0-1)
        boundary_proximity_weight: Weight for boundary proximity in scoring
        seed: Random seed for reproducibility
        verbose: Enable detailed logging
        allow_any_range: Allow N outside operational range (for testing)
        
    Returns:
        Tuple (p, q) if factors found, None otherwise
    """
    # Validate input range
    if not allow_any_range and N != CHALLENGE_127 and not (RANGE_MIN <= N <= RANGE_MAX):
        raise ValueError(f"N must be in [{RANGE_MIN}, {RANGE_MAX}] or CHALLENGE_127. "
                        "Use allow_any_range=True for testing.")
    
    # Quick check for even numbers
    if N % 2 == 0:
        return (2, N // 2)
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    
    # Always log precision for reproducibility
    if verbose:
        print("=" * 70)
        print("Hash-Bounds Partition Factor Search")
        print("=" * 70)
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Precision: {required_dps} dps")
    else:
        # Log precision even in non-verbose mode if this is a significant run
        # For now, we assume non-verbose might still want minimal audit trail if logging is configured
        # But adhering to the specific review: "always logging the precision regardless of verbose flag"
        # We print it to stdout as a minimal log line.
        print(f"[INFO] Hash-Bounds Search: N={N} (bits={N.bit_length()}), Precision={required_dps} dps")

    with mp.workdps(required_dps):
        if verbose:
            print(f"k = {k_value}")
            print(f"Max candidates: {max_candidates}")
            print(f"Delta window: ±{delta_window}")
            print(f"Boundary weight: {boundary_weight}")
            print(f"Boundary proximity weight: {boundary_proximity_weight}")
            print(f"Seed: {seed}")
            print()
        
        sqrt_N = isqrt(N)
        
        if verbose:
            print(f"√N = {sqrt_N}")
            print()
        
        # Compute all boundaries
        if verbose:
            print("Computing fractional sqrt boundaries...")
        
        frac_roots = get_all_fractional_roots(required_dps)
        all_boundaries = compute_all_boundaries(sqrt_N, required_dps, delta_window)
        
        if verbose:
            print("Fractional roots:")
            for p, frac in frac_roots.items():
                print(f"  frac(√{p}) = {float(frac):.10f}")
            print()
            print("Boundary counts per seed prime:")
            for p, bounds in all_boundaries.items():
                print(f"  √{p}: {len(bounds)} boundaries")
            print()
        
        # Generate boundary-focused samples
        if verbose:
            print(f"Generating {max_candidates} boundary-focused samples...")
        
        sample_offsets = generate_boundary_focused_samples(
            sqrt_N, max_candidates, delta_window, boundary_weight, seed
        )
        
        if verbose:
            print(f"  Generated {len(sample_offsets)} unique samples")
            print()
        
        # Embed N in 7D torus
        N_coords = embed_torus_geodesic(N, k_value)
        
        start_time = time.time()
        
        # Score all candidates
        candidates_with_scores = []
        
        if verbose:
            print("Phase 1: Scoring candidates...")
        
        for offset in sample_offsets:
            candidate = sqrt_N + offset
            
            # Skip trivial cases
            if candidate <= 1 or candidate >= N:
                continue
            if candidate % 2 == 0:
                continue
            
            # Compute geodesic distance
            cand_coords = embed_torus_geodesic(candidate, k_value)
            geo_dist = riemannian_distance(N_coords, cand_coords)
            
            # Compute boundary proximity
            prox = boundary_proximity_score(offset, all_boundaries)
            
            # Combined score (lower is better for distance, higher for proximity)
            # Negate distance so higher score is better overall
            combined_score = (1.0 - boundary_proximity_weight) * (-float(geo_dist)) + \
                            boundary_proximity_weight * prox
            
            candidates_with_scores.append((candidate, combined_score, offset, float(geo_dist), prox))
        
        if verbose:
            print(f"  Scored {len(candidates_with_scores)} candidates")
            print()
        
        # Sort by combined score (descending - higher is better)
        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        if verbose:
            print("Top 10 candidates by combined score:")
            for i, (cand, score, offset, geo, prox) in enumerate(candidates_with_scores[:10]):
                print(f"  {i+1}. offset={offset}, score={score:.6f}, "
                      f"geo_dist={geo:.6e}, boundary_prox={prox:.4f}")
            print()
        
        # Test candidates in order of score
        if verbose:
            print("Phase 2: Testing candidates...")
        
        tested = 0
        for candidate, score, offset, geo_dist, prox in candidates_with_scores:
            tested += 1
            
            if N % candidate == 0:
                p = candidate
                q = N // candidate
                
                elapsed = time.time() - start_time
                
                if verbose:
                    print()
                    print("✓ FACTOR FOUND!")
                    print(f"  p = {p}")
                    print(f"  q = {q}")
                    print(f"  δ = {offset}")
                    print(f"  Geodesic distance = {geo_dist:.6e}")
                    print(f"  Boundary proximity = {prox:.4f}")
                    print(f"  Combined score = {score:.6f}")
                    print(f"  Candidates tested: {tested}")
                    print(f"  Elapsed: {elapsed:.3f}s")
                    print()
                
                return (p, q)
        
        elapsed = time.time() - start_time
        
        if verbose:
            print()
            print("✗ No factors found")
            print(f"  Candidates tested: {tested}")
            print(f"  Elapsed: {elapsed:.3f}s")
            print()
        
        return None


if __name__ == "__main__":
    print("Hash-Bounds Partition Sampling")
    print("=" * 70)
    print()
    
    # Display fractional roots
    print("Fractional square roots of seed primes:")
    frac_roots = get_all_fractional_roots(50)
    for p, frac in frac_roots.items():
        print(f"  frac(√{p}) = {float(frac):.15f}")
    print()
    
    # Test on 60-bit semiprime (Gate 2)
    print("Testing on 60-bit semiprime (Gate 2):")
    N = GATE_2_60BIT
    print(f"N = {N}")
    print(f"Expected: 1073741789 × 1073741827")
    print()
    
    result = hash_bounds_factor_search(
        N,
        k_value=0.35,
        max_candidates=5000,
        delta_window=50000,
        boundary_weight=0.7,
        boundary_proximity_weight=0.1,
        seed=42,
        verbose=True,
        allow_any_range=True
    )
    
    if result:
        p, q = result
        print("=" * 70)
        print("SUCCESS!")
        print(f"  p = {p}")
        print(f"  q = {q}")
        print(f"  Verify: {p * q == N}")
    else:
        print("=" * 70)
        print("FAILURE: No factors found within budget")
