"""
Geodesic Signal Decay Analysis
================================

Phase 1.1: Measure geodesic distance signal-to-noise ratio (SNR) across bit-length gradient.

Tests hypothesis: SNR decays exponentially as bit-length increases, explaining
why GVA succeeds on Gate 1 (30-bit) but fails in operational range [10^14, 10^18].

Methodology:
- Generate balanced RSA-style semiprimes from 20-bit to 50-bit (10 samples per bit length)
- For each N, compute geodesic distances at true factor locations vs random candidates
- Calculate SNR = (min_distance_at_factors) / (avg_distance_over_candidates)
- Export data and visualize decay curve

Validation gates: All N are in form p × q where p, q are primes near sqrt(N)
No classical fallbacks: Uses only GVA geodesic distance metric
Precision: Adaptive per N, logged for each test
"""

import mpmath as mp
import json
import time
import random
from typing import List, Tuple, Dict
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from gva_factorization import embed_torus_geodesic, riemannian_distance, adaptive_precision


def generate_balanced_semiprime(bit_length: int, seed: int) -> Tuple[int, int, int]:
    """
    Generate a balanced semiprime at target bit length.
    
    Args:
        bit_length: Target bit length for N
        seed: Random seed for reproducibility
        
    Returns:
        Tuple (N, p, q) where N = p × q, p and q are primes near sqrt(N)
    """
    random.seed(seed)
    mp.mp.dps = 50
    
    # Target: p and q are each approximately (bit_length / 2) bits
    # So N ≈ 2^bit_length
    target_N = 2 ** bit_length
    target_p = int(mp.sqrt(target_N))
    
    # Search for primes near target_p
    # Simple prime generation: find next prime after target_p
    def is_prime_simple(n: int) -> bool:
        """Simple primality test for small numbers"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    # Find p near target_p
    p = target_p
    offset = random.randint(-1000, 1000)
    p += offset
    while not is_prime_simple(p):
        p += 2 if p % 2 == 1 else 1
    
    # Find q near target_p to keep balanced
    q = target_p
    offset = random.randint(-1000, 1000)
    q += offset
    while not is_prime_simple(q) or q == p:
        q += 2 if q % 2 == 1 else 1
    
    N = p * q
    
    return (N, p, q)


def measure_geodesic_snr(N: int, p: int, q: int, k: float = 0.35,
                        num_random_candidates: int = 1000) -> Dict:
    """
    Measure geodesic signal-to-noise ratio for a semiprime.
    
    Args:
        N: Semiprime
        p, q: True factors (p × q = N)
        k: Geodesic exponent
        num_random_candidates: Number of random candidates to sample for noise baseline
        
    Returns:
        Dictionary with SNR measurements
    """
    bit_length = N.bit_length()
    required_dps = adaptive_precision(N)
    
    with mp.workdps(required_dps):
        # Embed N
        N_coords = embed_torus_geodesic(N, k)
        
        # Compute distances at true factors
        p_coords = embed_torus_geodesic(p, k)
        q_coords = embed_torus_geodesic(q, k)
        
        dist_p = riemannian_distance(N_coords, p_coords)
        dist_q = riemannian_distance(N_coords, q_coords)
        min_factor_distance = float(min(dist_p, dist_q))
        
        # Sample random candidates near sqrt(N)
        sqrt_N = int(mp.sqrt(N))
        window = max(10000, sqrt_N // 100)
        
        random_distances = []
        for _ in range(num_random_candidates):
            offset = random.randint(-window, window)
            candidate = sqrt_N + offset
            
            if candidate <= 1 or candidate >= N:
                continue
            if N % candidate == 0:  # Skip actual factors
                continue
            
            candidate_coords = embed_torus_geodesic(candidate, k)
            dist = riemannian_distance(N_coords, candidate_coords)
            random_distances.append(float(dist))
        
        if not random_distances:
            return None
        
        avg_random_distance = sum(random_distances) / len(random_distances)
        snr = min_factor_distance / avg_random_distance if avg_random_distance > 0 else 0.0
        
        return {
            'N': N,
            'p': p,
            'q': q,
            'bit_length': bit_length,
            'precision_dps': required_dps,
            'k': k,
            'min_factor_distance': min_factor_distance,
            'avg_random_distance': avg_random_distance,
            'snr': snr,
            'num_samples': len(random_distances)
        }


def run_signal_decay_analysis():
    """
    Run complete signal decay analysis across bit-length gradient.
    """
    print("=" * 80)
    print("GVA Root-Cause Analysis: Phase 1.1 - Geodesic Signal Decay")
    print("=" * 80)
    print()
    
    output_dir = Path(__file__).parent
    
    # Configuration
    bit_lengths = range(20, 51)  # 20 to 50 bits
    samples_per_bit_length = 10
    k = 0.35  # Standard GVA parameter
    random_candidates = 1000
    
    print(f"Configuration:")
    print(f"  Bit length range: {min(bit_lengths)} to {max(bit_lengths)}")
    print(f"  Samples per bit length: {samples_per_bit_length}")
    print(f"  Geodesic exponent k: {k}")
    print(f"  Random candidates per test: {random_candidates}")
    print()
    
    results = []
    start_time = time.time()
    
    for bit_length in bit_lengths:
        print(f"Testing {bit_length}-bit semiprimes...")
        
        for sample_idx in range(samples_per_bit_length):
            seed = bit_length * 1000 + sample_idx  # Deterministic seed
            
            try:
                N, p, q = generate_balanced_semiprime(bit_length, seed)
                
                # Verify N is in expected range
                actual_bits = N.bit_length()
                if actual_bits != bit_length:
                    print(f"  Warning: Generated {actual_bits}-bit N instead of {bit_length}-bit")
                
                result = measure_geodesic_snr(N, p, q, k, random_candidates)
                
                if result:
                    results.append(result)
                    print(f"  Sample {sample_idx + 1}: N={N}, SNR={result['snr']:.6f}")
            
            except Exception as e:
                print(f"  Error on sample {sample_idx + 1}: {e}")
                continue
    
    elapsed = time.time() - start_time
    
    print()
    print(f"Analysis complete. Total time: {elapsed:.2f}s")
    print(f"Total measurements: {len(results)}")
    print()
    
    # Export data
    output_file = output_dir / "signal_decay_data.json"
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'experiment': 'geodesic_signal_decay',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'bit_length_range': [min(bit_lengths), max(bit_lengths)],
                'samples_per_bit_length': samples_per_bit_length,
                'k': k,
                'random_candidates': random_candidates,
                'total_runtime_seconds': elapsed
            },
            'results': results
        }, f, indent=2)
    
    print(f"Data exported to: {output_file}")
    
    # Generate summary statistics
    print()
    print("Summary Statistics:")
    print("-" * 80)
    
    # Group by bit length
    from collections import defaultdict
    by_bit_length = defaultdict(list)
    for r in results:
        by_bit_length[r['bit_length']].append(r['snr'])
    
    for bit_length in sorted(by_bit_length.keys()):
        snrs = by_bit_length[bit_length]
        avg_snr = sum(snrs) / len(snrs)
        min_snr = min(snrs)
        max_snr = max(snrs)
        print(f"  {bit_length:2d} bits: avg SNR = {avg_snr:.6f}, min = {min_snr:.6f}, max = {max_snr:.6f}")
    
    print()
    print("Next step: Run generate_visualizations.py to create plots")
    
    return results


if __name__ == '__main__':
    random.seed(42)  # Global seed for reproducibility
    run_signal_decay_analysis()
