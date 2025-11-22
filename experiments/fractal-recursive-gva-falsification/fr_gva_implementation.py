"""
Fractal-Recursive GVA (FR-GVA) Implementation
==============================================

Implements segment-based FR-GVA with well-informed candidate generation:

Key features:
- Segment-based approach: Mandelbrot assigns interest scores to coarse segments
  of the search window (not exact candidates)
- Hard prefilters: Parity checks, small prime divisibility (first 100 primes),
  and factor band restrictions eliminate invalid candidates early
- Monotone mapping: Preserves locality in segment-to-complex-plane mapping
- Metrics tracking: segments_scored, segments_searched, candidates_tested,
  window_coverage_pct

This replaces arbitrary modulo mapping with deterministic, well-informed
candidate generation that respects number-theoretic constraints.

Validation range: [10^14, 10^18] per VALIDATION_GATES.md
Whitelist: 127-bit CHALLENGE_127
"""

import mpmath as mp
from typing import Tuple, Optional, List, Dict
import time
from math import log, e

# Configure high precision
mp.mp.dps = 50

# Validation gates (from gva_factorization.py)
GATE_1_30BIT = 1073217479  # 32749 × 32771
GATE_2_60BIT = 1152921470247108503  # 1073741789 × 1073741827
CHALLENGE_127 = 137524771864208156028430259349934309717
RANGE_MIN = 10**14
RANGE_MAX = 10**18


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bitLength() × 4 + 200)
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def compute_kappa(n: int) -> float:
    """
    Compute kappa curvature metric as described in hypothesis.
    κ(n) = d(n) · ln(n+1) / e²
    
    where d(n) is the divisor count.
    
    Note: For large semiprimes, computing full divisor count is expensive.
    We use an approximation based on expected divisor patterns.
    """
    # For a semiprime p*q, d(n) = 4 (divisors: 1, p, q, pq)
    # For testing purposes, we approximate based on small divisors
    d_n = 2  # Minimum divisors: 1 and n
    
    # Check small divisors (deterministic, limited scope)
    for divisor in [2, 3, 5, 7, 11, 13]:
        if n % divisor == 0:
            d_n += 1
    
    kappa = d_n * log(n + 1) / (e ** 2)
    return kappa


# Small primes for prefiltering (first 100 primes)
SMALL_PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151,
    157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233,
    239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317,
    331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419,
    421, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509,
    521, 523, 541
]


def is_valid_candidate(candidate: int, N: int, sqrt_N: int) -> bool:
    """
    Hard prefilter for candidate validity.
    
    Checks:
    1. Parity: Candidate must match N's parity structure
    2. Small prime divisibility: Not divisible by first 100 primes (unless factor)
    3. Factor band: Within reasonable distance from sqrt(N)
    
    Args:
        candidate: Candidate factor to validate
        N: Semiprime to factor
        sqrt_N: Integer square root of N
        
    Returns:
        True if candidate passes all prefilters, False otherwise
    """
    # Basic range check
    if candidate <= 1 or candidate >= N:
        return False
    
    # Parity check: if N is odd, candidate must be odd
    if N % 2 == 1 and candidate % 2 == 0:
        return False
    
    # Small prime divisibility check (skip if N has that prime factor)
    for prime in SMALL_PRIMES:
        if prime >= candidate:
            break
        # Skip if N is divisible by this prime (candidate might be this prime)
        if N % prime == 0:
            continue
        # Reject if candidate is divisible by small prime
        if candidate % prime == 0:
            return False
    
    # Factor band check: candidate should be within reasonable range of sqrt(N)
    # For balanced semiprimes, factors are near sqrt(N)
    # Allow up to 10x deviation for unbalanced cases
    max_deviation = max(sqrt_N // 10, 1000)
    if abs(candidate - sqrt_N) > max_deviation and candidate < sqrt_N:
        return False
    
    return True


def score_segment_with_mandelbrot(segment_start: int, segment_end: int, 
                                   N: int, kappa: float,
                                   max_iterations: int = 100,
                                   escape_radius: float = 2.0) -> float:
    """
    Compute Mandelbrot-based interest score for a segment.
    
    Instead of generating exact candidates, use Mandelbrot to assess
    the "interestingness" of a coarse segment of the search space.
    
    Uses monotone mapping that preserves locality: segment position
    maps to a specific region in the complex plane, and escape behavior
    indicates potential factor density.
    
    Args:
        segment_start: Start of segment
        segment_end: End of segment
        N: Semiprime to factor
        kappa: Curvature metric
        max_iterations: Maximum fractal iterations
        escape_radius: Escape threshold
        
    Returns:
        Interest score in [0, 1], higher = more promising
    """
    # Monotone mapping: segment position to complex parameter
    # Map segment relative position [0, 1] to a scaled complex offset
    sqrt_N = int(mp.sqrt(N))
    segment_center = (segment_start + segment_end) // 2
    
    # Normalized position relative to sqrt(N): [-1, 1]
    relative_pos = (segment_center - sqrt_N) / sqrt_N if sqrt_N > 0 else 0
    
    # Map to complex plane with kappa influence
    # Use relative position to create a stable, monotone mapping
    c = complex(kappa + relative_pos * 0.1, log(N) * 1e-20)
    
    z = 0j
    escape_count = 0
    total_magnitude = 0.0
    
    # Run Mandelbrot iterations
    for iteration in range(max_iterations):
        z = z**2 + c
        magnitude = abs(z)
        total_magnitude += magnitude
        
        if magnitude > escape_radius:
            escape_count += 1
            # Dampen after escape to continue exploration
            z = z / (magnitude / escape_radius)
    
    # Score based on escape dynamics
    # More escapes and larger magnitudes suggest more "interesting" regions
    avg_magnitude = total_magnitude / max_iterations
    escape_ratio = escape_count / max_iterations
    
    # Combine metrics: balance escape behavior with magnitude
    score = (escape_ratio * 0.6 + min(avg_magnitude / 10.0, 1.0) * 0.4)
    
    return min(score, 1.0)





def recursive_window_subdivision(N: int, window_start: int, window_end: int,
                                 depth: int, max_depth: int, kappa_threshold: float,
                                 metrics: Dict, verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Recursively subdivide search window using segment-based Mandelbrot scoring.
    
    Key changes from original:
    - Segments are scored with Mandelbrot (not exact candidate generation)
    - Top-K segments are searched using standard GVA candidate testing
    - Hard prefilters eliminate invalid candidates early
    - Metrics track segments_scored, segments_searched, candidates_tested
    
    Args:
        N: Semiprime to factor
        window_start: Start of search window
        window_end: End of search window
        depth: Current recursion depth
        max_depth: Maximum recursion depth
        kappa_threshold: Threshold for geodesic density
        metrics: Dictionary to track metrics
        verbose: Enable detailed logging
        
    Returns:
        Tuple (p, q) if factors found, None otherwise
    """
    if depth > max_depth:
        # Base case: exhausted recursion depth
        if verbose:
            print(f"  Depth {depth}: Max depth reached, terminating search")
        return None
    
    # Compute kappa for current window
    kappa = compute_kappa(N)
    sqrt_N = int(mp.sqrt(N))
    
    if kappa > kappa_threshold:
        if verbose:
            print(f"  Depth {depth}: κ={kappa:.4f} > threshold, using segment-based search")
        
        # Divide window into coarse segments
        segment_size = max((window_end - window_start) // 20, 1000)
        segments = []
        
        current = window_start
        while current < window_end:
            seg_end = min(current + segment_size, window_end)
            segments.append((current, seg_end))
            current = seg_end
        
        if verbose:
            print(f"    Created {len(segments)} segments of size ~{segment_size}")
        
        # Score each segment with Mandelbrot
        segment_scores = []
        for seg_start, seg_end in segments:
            score = score_segment_with_mandelbrot(seg_start, seg_end, N, kappa)
            segment_scores.append((score, seg_start, seg_end))
            metrics['segments_scored'] += 1
        
        # Sort by score (descending) and select top-K
        segment_scores.sort(reverse=True, key=lambda x: x[0])
        top_k = min(5, len(segment_scores))  # Search top 5 segments
        
        if verbose:
            print(f"    Top-{top_k} segments by score:")
            for i, (score, start, end) in enumerate(segment_scores[:top_k]):
                print(f"      {i+1}. [{start}, {end}] score={score:.4f}")
        
        # Search top-K segments with GVA-style candidate testing
        for score, seg_start, seg_end in segment_scores[:top_k]:
            metrics['segments_searched'] += 1
            
            if verbose:
                print(f"    Searching segment [{seg_start}, {seg_end}] (score={score:.4f})")
            
            # Generate candidates in this segment with stride
            # Use deterministic stride based on segment size
            stride = max((seg_end - seg_start) // 100, 1)
            
            for candidate in range(seg_start, seg_end, stride):
                # Apply hard prefilters
                if not is_valid_candidate(candidate, N, sqrt_N):
                    continue
                
                metrics['candidates_tested'] += 1
                
                # Test candidate
                if N % candidate == 0:
                    if verbose:
                        print(f"    ✓ Factor found: {candidate}")
                    return (candidate, N // candidate)
        
        # Update window coverage
        covered = sum(end - start for _, start, end in segment_scores[:top_k])
        total = window_end - window_start
        metrics['window_coverage_pct'] = (covered / total * 100) if total > 0 else 0
    
    # Recursive subdivision
    mid = (window_start + window_end) // 2
    
    # Search left half
    result = recursive_window_subdivision(N, window_start, mid, depth + 1, 
                                         max_depth, kappa_threshold, metrics, verbose)
    if result:
        return result
    
    # Search right half
    result = recursive_window_subdivision(N, mid + 1, window_end, depth + 1,
                                         max_depth, kappa_threshold, metrics, verbose)
    if result:
        return result
    
    return None


def fr_gva_factor_search(N: int, max_depth: int = 5, kappa_threshold: float = 0.525,
                         max_candidates: int = 10000, verbose: bool = False,
                         allow_any_range: bool = False) -> Optional[Tuple[int, int]]:
    """
    Factor semiprime N using Fractal-Recursive GVA (FR-GVA).
    
    Implements segment-based Mandelbrot scoring with hard prefilters:
    1. Segment-based approach: Mandelbrot scores coarse segments (not exact candidates)
    2. Hard prefilters: Parity, small primes (first 100), factor band restrictions
    3. Monotone mapping: Preserves locality in segment scoring
    4. Metrics: segments_scored, segments_searched, candidates_tested, window_coverage_pct
    
    Args:
        N: Semiprime to factor
        max_depth: Maximum recursion depth
        kappa_threshold: Threshold for geodesic density gating
        max_candidates: Maximum candidates to test (for comparison)
        verbose: Enable detailed logging
        allow_any_range: Allow N outside operational range (for testing)
        
    Returns:
        Tuple (p, q) if factors found, None otherwise
        
    Metrics tracked:
        - segments_scored: Number of segments scored with Mandelbrot
        - segments_searched: Number of top-K segments actually searched
        - candidates_tested: Number of candidates passing prefilters and tested
        - window_coverage_pct: Percentage of window covered by searched segments
    """
    # Validate input range
    if not allow_any_range and N != CHALLENGE_127 and not (RANGE_MIN <= N <= RANGE_MAX):
        raise ValueError(f"N must be in [{RANGE_MIN}, {RANGE_MAX}] or CHALLENGE_127. Use allow_any_range=True for testing.")
    
    # Quick check for even numbers
    if N % 2 == 0:
        return (2, N // 2)
    
    # Initialize metrics
    metrics = {
        'segments_scored': 0,
        'segments_searched': 0,
        'candidates_tested': 0,
        'window_coverage_pct': 0.0
    }
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    with mp.workdps(required_dps):
        if verbose:
            print(f"FR-GVA Factorization (Segment-Based)")
            print(f"N = {N}")
            print(f"Bit length: {N.bit_length()}")
            print(f"Adaptive precision: {required_dps} dps")
            print(f"Max depth: {max_depth}")
            print(f"κ threshold: {kappa_threshold}")
            print(f"Prefilters: parity, first {len(SMALL_PRIMES)} primes, factor band")
        
        start_time = time.time()
        
        # Compute search window around sqrt(N)
        sqrt_N = int(mp.sqrt(N))
        bit_length = N.bit_length()
        
        # Adaptive window sizing (matching GVA baseline)
        if bit_length <= 40:
            window = max(1000, sqrt_N // 1000)
        elif bit_length <= 60:
            window = max(10000, sqrt_N // 5000)
        elif bit_length <= 85:
            window = max(100000, sqrt_N // 1000)
        else:
            window = max(200000, sqrt_N // 500)
        
        window_start = max(2, sqrt_N - window)
        window_end = min(N - 1, sqrt_N + window)
        
        if verbose:
            print(f"Search window: [{window_start}, {window_end}] (±{window} around sqrt(N)={sqrt_N})")
        
        # Execute FR-GVA with segment-based subdivision
        result = recursive_window_subdivision(N, window_start, window_end, 
                                             depth=0, max_depth=max_depth,
                                             kappa_threshold=kappa_threshold,
                                             metrics=metrics,
                                             verbose=verbose)
        
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"\nMetrics:")
            print(f"  Segments scored: {metrics['segments_scored']}")
            print(f"  Segments searched: {metrics['segments_searched']}")
            print(f"  Candidates tested: {metrics['candidates_tested']}")
            print(f"  Window coverage: {metrics['window_coverage_pct']:.2f}%")
        
        if result:
            p, q = result
            if verbose:
                print(f"\n✓ Factor found: {N} = {p} × {q}")
                print(f"  Time: {elapsed:.3f}s")
            return result
        else:
            if verbose:
                print(f"\n✗ No factors found")
                print(f"  Time: {elapsed:.3f}s")
            return None


def main():
    """
    Quick validation of FR-GVA implementation.
    """
    print("="*60)
    print("FR-GVA Quick Validation")
    print("="*60)
    
    # Test small example from hypothesis
    print("\n1. Small example (N=899 = 29×31):")
    result = fr_gva_factor_search(899, max_depth=3, verbose=True, allow_any_range=True)
    if result:
        print(f"✓ Success: {result}")
    else:
        print("✗ Failed")
    
    # Test Gate 1 (30-bit) - outside operational range, requires allow_any_range
    print("\n2. Gate 1 validation (30-bit, outside range):")
    print("   Note: 30-bit is < 10^14, testing with allow_any_range=True")
    result = fr_gva_factor_search(GATE_1_30BIT, max_depth=5, verbose=True, allow_any_range=True)
    if result:
        p, q = result
        print(f"✓ Success: {GATE_1_30BIT} = {p} × {q}")
        print(f"  Verification: {p * q == GATE_1_30BIT}")
    else:
        print("✗ Failed")


if __name__ == "__main__":
    main()
