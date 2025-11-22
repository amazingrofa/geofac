"""
Z5D Prime Density Generator
============================

Generates an empirical prime density histogram around √N₁₂₇ for use as a 
prior in Z5D-informed FR-GVA.

Since we don't have direct access to z5d-prime-predictor, we simulate its
behavior by:
1. Computing √N₁₂₇
2. Enumerating actual primes in a window around √N (using segmented sieve)
3. Building a density histogram with δ = p - √N
4. Exporting to CSV for import into FR-GVA

This represents the "offline on Apple silicon" step mentioned in the problem
statement, adapted for our validation environment.

Validation range: [10^14, 10^18] per VALIDATION_GATES.md
Whitelist: 127-bit CHALLENGE_127
"""

import mpmath as mp
from math import log, sqrt, isqrt
from typing import List, Tuple, Dict
import csv
import random

# Configure precision
mp.mp.dps = 100

# 127-bit challenge number
CHALLENGE_127 = 137524771864208156028430259349934309717

# Analysis window parameters
DELTA_WINDOW = 10**6  # ±1 million around √N
BIN_WIDTH = 1000      # Histogram bin width in δ-space


def compute_sqrt_n(N: int) -> int:
    """
    Compute floor(√N) with exact integer arithmetic.
    
    Args:
        N: Integer to find square root of
        
    Returns:
        floor(√N)
    """
    return isqrt(N)


def segmented_sieve(start: int, end: int) -> List[int]:
    """
    Generate all primes in [start, end] using segmented sieve.
    
    For the 127-bit challenge scale (~10^19), we need to:
    1. Handle very large numbers
    2. Work in segments to manage memory
    3. Use wheel factorization for efficiency
    
    Args:
        start: Start of range (inclusive)
        end: End of range (inclusive)
        
    Returns:
        List of primes in [start, end]
    """
    # For a window this large (~2×10^6), we use trial division
    # with wheel mod 30 for first pass, then primality test
    
    # Wheel mod 30: skip multiples of 2, 3, 5
    # Residues: 1, 7, 11, 13, 17, 19, 23, 29
    wheel_30 = [1, 7, 11, 13, 17, 19, 23, 29]
    
    primes = []
    
    # Adjust start to first valid residue
    start_val = start
    if start_val % 2 == 0:
        start_val += 1
    
    for n in range(start_val, end + 1, 2):
        if is_prime_trial(n):
            primes.append(n)
    
    return primes


def is_prime_trial(n: int, limit: int = 10000) -> bool:
    """
    Primality test using trial division up to sqrt(n) or limit.
    
    For numbers near √N₁₂₇ ≈ 1.17×10^19, we only need to check divisors
    up to √(√N₁₂₇) ≈ 3.4×10^9. However, for practical purposes and since
    we're in the [10^14, 10^18] operational range, we use a reasonable limit.
    
    Args:
        n: Number to test
        limit: Maximum trial divisor
        
    Returns:
        True if n is probably prime (no divisors found up to limit)
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    if n == 3:
        return True
    if n % 3 == 0:
        return False
    
    # Check 6k±1 up to min(sqrt(n), limit)
    i = 5
    sqrt_n = isqrt(n)
    max_check = min(sqrt_n, limit)
    
    while i <= max_check:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    
    return True


def miller_rabin(n: int, k: int = 20) -> bool:
    """
    Miller-Rabin primality test.
    
    For very large numbers, use probabilistic test.
    k rounds gives error probability ≤ 4^(-k).
    
    Args:
        n: Number to test
        k: Number of test rounds
        
    Returns:
        True if n is probably prime
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    # Witness loop
    random.seed(42)  # Deterministic for reproducibility
    
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    return True


def generate_prime_density_data(N: int, window: int, bin_width: int) -> Tuple[int, List[Tuple[int, int]], Dict[int, int]]:
    """
    Generate prime density histogram around √N.
    
    Args:
        N: Target semiprime
        window: Half-width of search window (±window)
        bin_width: Histogram bin width
        
    Returns:
        Tuple of (sqrt_N, [(p, delta)], {bin_center: count})
    """
    sqrt_N = compute_sqrt_n(N)
    
    print(f"N = {N}")
    print(f"√N = {sqrt_N}")
    print(f"√N ≈ {float(sqrt_N):.6e}")
    print(f"log(√N) ≈ {log(float(sqrt_N)):.2f}")
    print()
    
    start = sqrt_N - window
    end = sqrt_N + window
    
    print(f"Searching for primes in [{start}, {end}]")
    print(f"Window span: {2 * window:,}")
    print()
    
    # For very large numbers near 10^19, we need a more sophisticated approach
    # Since we're in simulation mode, we'll use a simplified model:
    # Generate representative primes using primality testing
    
    print("Generating prime density profile...")
    print("(Using Miller-Rabin primality testing for large numbers)")
    print()
    
    primes_and_deltas = []
    
    # Sample candidates from the range
    # Use wheel mod 210 (residues coprime to 2,3,5,7) for efficiency
    wheel_210 = [
        1, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
        53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103,
        107, 109, 113, 121, 127, 131, 137, 139, 143, 149, 151,
        157, 163, 167, 169, 173, 179, 181, 187, 191, 193, 197,
        199, 209
    ]
    
    # Scan the range using wheel
    candidate_count = 0
    prime_count = 0
    
    # Find starting point aligned to wheel
    base = (start // 210) * 210
    
    for offset in range(base - 210, end + 210, 210):
        for residue in wheel_210:
            candidate = offset + residue
            
            if candidate < start:
                continue
            if candidate > end:
                break
            
            candidate_count += 1
            
            # Test primality
            if miller_rabin(candidate, k=20):
                delta = candidate - sqrt_N
                primes_and_deltas.append((candidate, delta))
                prime_count += 1
            
            if candidate_count % 10000 == 0:
                print(f"  Tested {candidate_count:,} candidates, found {prime_count:,} primes")
    
    print(f"\nTotal: {prime_count:,} primes found in window")
    print(f"Prime density: {prime_count / (2 * window):.2e} primes per unit")
    print()
    
    # Build histogram
    histogram = {}
    for p, delta in primes_and_deltas:
        bin_center = (delta // bin_width) * bin_width
        histogram[bin_center] = histogram.get(bin_center, 0) + 1
    
    print(f"Histogram bins: {len(histogram)}")
    
    return sqrt_N, primes_and_deltas, histogram


def export_to_csv(sqrt_N: int, primes_and_deltas: List[Tuple[int, int]], 
                  histogram: Dict[int, int], filename: str):
    """
    Export prime density data to CSV files.
    
    Creates two files:
    1. {filename}_primes.csv: Individual primes and deltas
    2. {filename}_histogram.csv: Histogram (bin_center, count, density)
    
    Args:
        sqrt_N: Floor of square root of N
        primes_and_deltas: List of (prime, delta) tuples
        histogram: Histogram dict {bin_center: count}
        filename: Base filename (without .csv)
    """
    # Individual primes
    primes_file = f"{filename}_primes.csv"
    with open(primes_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['prime', 'delta', 'sqrt_N'])
        for p, delta in primes_and_deltas:
            writer.writerow([p, delta, sqrt_N])
    
    print(f"Exported {len(primes_and_deltas)} primes to {primes_file}")
    
    # Histogram
    histogram_file = f"{filename}_histogram.csv"
    with open(histogram_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['bin_center', 'count', 'density'])
        
        # Sort by bin_center
        for bin_center in sorted(histogram.keys()):
            count = histogram[bin_center]
            density = count / BIN_WIDTH  # primes per unit in this bin
            writer.writerow([bin_center, count, density])
    
    print(f"Exported {len(histogram)} histogram bins to {histogram_file}")


def main():
    """
    Main entry point: generate Z5D prime density data for 127-bit challenge.
    """
    print("=" * 70)
    print("Z5D Prime Density Generator")
    print("=" * 70)
    print()
    
    # Generate density data
    sqrt_N, primes_and_deltas, histogram = generate_prime_density_data(
        CHALLENGE_127, 
        DELTA_WINDOW, 
        BIN_WIDTH
    )
    
    # Export to CSV
    export_to_csv(sqrt_N, primes_and_deltas, histogram, 
                  "/home/runner/work/geofac/geofac/experiments/z5d-informed-gva/z5d_density")
    
    print()
    print("=" * 70)
    print("Generation complete")
    print("=" * 70)
    print()
    print("Expected prime gap near √N: ḡ ≈ log(√N) ≈", log(float(sqrt_N)))
    print()
    
    # Summary statistics
    if primes_and_deltas:
        deltas = [d for _, d in primes_and_deltas]
        print(f"Delta range: [{min(deltas)}, {max(deltas)}]")
        print(f"Total primes: {len(primes_and_deltas)}")
        print(f"Avg spacing: {(max(deltas) - min(deltas)) / max(1, len(primes_and_deltas) - 1):.2f}")


if __name__ == "__main__":
    main()
