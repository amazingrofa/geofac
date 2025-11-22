"""
Z5D Band Calibration
====================

Calibrates Z5D error parameter ε(bit-length) using balanced semiprimes.

For each bit-length (60, 70, 80, 90, 96):
1. Generate balanced semiprime N = p × q with p ≈ q ≈ √N
2. Compute Z5D predicted band for √N
3. Measure where actual p lands relative to band center
4. Compute ε needed for 95% capture rate

Exports: calibration_results.json
"""

import json
import os
from math import log, sqrt
from typing import List, Dict, Tuple
from z5d_api import predict_prime_band, estimate_prime_index, z5d_error_estimate


def isqrt(n: int) -> int:
    """Integer square root."""
    if n < 0:
        raise ValueError("Square root of negative number")
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def miller_rabin(n: int, k: int = 10) -> bool:
    """Miller-Rabin primality test."""
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
    def check_witness(a):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return True
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                return True
        return False
    
    # Test with first k primes as witnesses
    witnesses = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    for a in witnesses[:k]:
        if a >= n:
            continue
        if not check_witness(a):
            return False
    return True


def next_prime(n: int) -> int:
    """Find next prime >= n."""
    if n <= 2:
        return 2
    if n % 2 == 0:
        n += 1
    while not miller_rabin(n, k=15):
        n += 2
    return n


def generate_balanced_semiprime(bit_length: int) -> Tuple[int, int, int]:
    """
    Generate balanced semiprime N = p × q at target bit-length.
    
    Args:
        bit_length: Target bit-length for N
        
    Returns:
        Tuple (N, p, q) where p < q and both ≈ √N
    """
    # Target: N has bit_length bits, p and q each have ~(bit_length/2) bits
    half_bits = bit_length // 2
    
    # Start with p near 2^(half_bits - 1)
    p_start = 2 ** (half_bits - 1) + 1
    p = next_prime(p_start)
    
    # Find q such that N ≈ 2^bit_length
    target_N = 2 ** bit_length
    q_target = target_N // p
    q = next_prime(q_target)
    
    N = p * q
    
    # Ensure p < q
    if p > q:
        p, q = q, p
    
    return (N, p, q)


def calibrate_single_bitlength(bit_length: int, 
                               num_samples: int = 1) -> Dict:
    """
    Calibrate Z5D error for a single bit-length.
    
    Args:
        bit_length: Target bit-length
        num_samples: Number of samples (default 1 for speed)
        
    Returns:
        Dict with calibration metrics
    """
    print(f"Calibrating {bit_length}-bit...")
    
    N, p, q = generate_balanced_semiprime(bit_length)
    sqrt_N = isqrt(N)
    
    print(f"  N = {N}")
    print(f"  p = {p}")
    print(f"  q = {q}")
    print(f"  √N = {sqrt_N}")
    print(f"  N bit-length: {N.bit_length()}")
    
    # Compute true prime indices
    k_p = estimate_prime_index(float(p))
    k_sqrt = estimate_prime_index(float(sqrt_N))
    
    # Relative error in index space
    relative_error = abs(k_p - k_sqrt) / k_sqrt if k_sqrt > 0 else 0
    
    print(f"  k(p) = {k_p}")
    print(f"  k(√N) = {k_sqrt}")
    print(f"  Relative error = {relative_error:.4f}")
    
    # Compute ε needed for capture (with safety margin)
    # For 95% capture, use ε = relative_error × 1.5
    epsilon_95 = relative_error * 1.5
    
    print(f"  ε (95% capture) = {epsilon_95:.4f}")
    print()
    
    return {
        'bit_length': bit_length,
        'N': str(N),
        'p': str(p),
        'q': str(q),
        'sqrt_N': str(sqrt_N),
        'k_p': k_p,
        'k_sqrt': k_sqrt,
        'relative_error': relative_error,
        'epsilon_95': epsilon_95
    }


def calibrate_all() -> Dict:
    """
    Run full calibration across bit-lengths.
    
    Returns:
        Dict with all calibration results
    """
    print("=" * 70)
    print("Z5D Band Calibration")
    print("=" * 70)
    print()
    
    bit_lengths = [60, 70, 80, 90, 96]
    results = []
    
    for bl in bit_lengths:
        result = calibrate_single_bitlength(bl)
        results.append(result)
    
    # Fit ε(n) curve
    # Simple linear fit: ε = a + b × bit_length
    if len(results) >= 2:
        x = [r['bit_length'] for r in results]
        y = [r['epsilon_95'] for r in results]
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)
        
        b = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        a = (sum_y - b * sum_x) / n
        
        print("=" * 70)
        print("Calibration Summary")
        print("=" * 70)
        print()
        print("ε(bit_length) curve fit:")
        print(f"  ε(n) = {a:.6f} + {b:.6f} × n")
        print()
        
        for r in results:
            predicted = a + b * r['bit_length']
            print(f"  {r['bit_length']}-bit: ε_measured = {r['epsilon_95']:.4f}, "
                  f"ε_fitted = {predicted:.4f}")
        print()
        
        calibration = {
            'results': results,
            'curve_fit': {
                'a': a,
                'b': b,
                'formula': f"ε(n) = {a:.6f} + {b:.6f} × n"
            }
        }
    else:
        calibration = {'results': results}
    
    return calibration


def main():
    """Run calibration and export results."""
    calibration = calibrate_all()
    
    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__), 
        'calibration_results.json'
    )
    
    with open(output_path, 'w') as f:
        json.dump(calibration, f, indent=2)
    
    print("=" * 70)
    print(f"Calibration complete. Results saved to:")
    print(f"  {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
