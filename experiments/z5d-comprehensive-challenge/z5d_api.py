"""
Z5D API Adapter
===============

Provides Z5D oracle interface using PNT-based approximation.

Since we don't have the actual Z5D predictor library, this adapter
simulates Z5D functionality using Prime Number Theorem estimations.

Key functions:
- Predict prime index band [k₋, k₊] given x ≈ √N
- Return local density estimates for δ-ranges
- Provide stepping oracle for search prioritization
"""

from math import log, exp, sqrt
from typing import Tuple, Dict, List
import mpmath as mp


def prime_counting_function(x: float) -> int:
    """
    Approximate π(x) using logarithmic integral li(x).
    
    For large x: π(x) ≈ x / log(x)
    Better approximation: π(x) ≈ li(x) = ∫₂ˣ dt/log(t)
    
    Args:
        x: Upper bound
        
    Returns:
        Estimated π(x)
    """
    if x < 2:
        return 0
    # Use PNT approximation: π(x) ≈ x / log(x) with correction term
    return int(x / log(x) * (1 + 1/log(x) + 2/log(x)**2))


def estimate_prime_index(p: float) -> int:
    """
    Estimate the prime index k such that p ≈ p_k (the k-th prime).
    
    By PNT: p_k ≈ k × log(k)
    Inverting: k ≈ p / log(p)
    
    Args:
        p: Prime (or value near a prime)
        
    Returns:
        Estimated prime index k
    """
    if p < 2:
        return 0
    return prime_counting_function(p)


def predict_prime_band(sqrt_N: int, epsilon: float = 0.02) -> Tuple[int, int]:
    """
    Predict prime index band [k₋, k₊] for factors of N.
    
    Given N = p × q with p, q both near √N, the Z5D oracle predicts
    which prime indices k contain p and q.
    
    Args:
        sqrt_N: Floor of square root of N
        epsilon: Relative error margin (default 2% = calibrated from rehearsal)
        
    Returns:
        Tuple (k_minus, k_plus) defining the band
    """
    # Estimate central index
    k_center = estimate_prime_index(float(sqrt_N))
    
    # Compute band width based on epsilon
    k_width = int(epsilon * k_center)
    
    k_minus = max(1, k_center - k_width)
    k_plus = k_center + k_width
    
    return (k_minus, k_plus)


def local_prime_density(x: float) -> float:
    """
    Estimate local prime density near x.
    
    By PNT: ρ(x) ≈ 1/log(x)
    
    Args:
        x: Location
        
    Returns:
        Estimated density (primes per unit)
    """
    if x < 2:
        return 0.0
    return 1.0 / log(x)


def density_in_range(center: int, delta: int) -> float:
    """
    Estimate average prime density in [center - delta, center + delta].
    
    Args:
        center: Center of range
        delta: Half-width
        
    Returns:
        Average density in range
    """
    # Sample density at 3 points for better estimate
    rho_low = local_prime_density(float(center - delta))
    rho_mid = local_prime_density(float(center))
    rho_high = local_prime_density(float(center + delta))
    
    # Weighted average
    return (rho_low + 4*rho_mid + rho_high) / 6.0


def prioritize_delta_bands(sqrt_N: int, 
                           delta_max: int,
                           num_bands: int = 10) -> List[Dict]:
    """
    Create prioritized list of δ-bands to search.
    
    Z5D oracle guides which regions around √N are most likely to contain
    factors based on local density.
    
    Args:
        sqrt_N: Floor of square root of N
        delta_max: Maximum δ-offset to consider
        num_bands: Number of bands to create
        
    Returns:
        List of dicts with keys: center, delta_start, delta_end, density, priority
    """
    bands = []
    band_width = delta_max // num_bands
    
    for i in range(num_bands):
        delta_start = i * band_width
        delta_end = min((i + 1) * band_width, delta_max)
        center_offset = (delta_start + delta_end) // 2
        
        # Estimate density in this band
        density = density_in_range(sqrt_N + center_offset, band_width // 2)
        
        band = {
            'center': sqrt_N + center_offset,
            'delta_start': delta_start,
            'delta_end': delta_end,
            'density': density,
            'priority': i  # Will be re-sorted by density
        }
        bands.append(band)
    
    # Sort by density (descending) - search dense regions first
    bands.sort(key=lambda b: b['density'], reverse=True)
    
    # Update priorities after sorting
    for i, band in enumerate(bands):
        band['priority'] = i
    
    return bands


def adaptive_step_size(density: float, base_step: int = 1) -> int:
    """
    Compute adaptive step size based on local density.
    
    In dense regions (high ρ), use small steps.
    In sparse regions (low ρ), use large steps.
    
    Args:
        density: Local prime density
        base_step: Base step size
        
    Returns:
        Adaptive step size
    """
    if density <= 0:
        return base_step * 10
    
    # Step size inversely proportional to density
    # High density → step = 1, Low density → step = 5-10
    step = max(1, int(base_step / (density * 50)))
    return min(step, 10)  # Cap at 10x base


def z5d_error_estimate(bit_length: int) -> float:
    """
    Estimate Z5D prediction error ε as function of bit-length.
    
    This is a placeholder using empirical scaling law:
    ε(n) ≈ 0.01 + 0.0001 × n
    
    Will be refined by calibration step.
    
    Args:
        bit_length: Bit length of N
        
    Returns:
        Estimated relative error
    """
    return 0.01 + 0.0001 * bit_length


def expected_gap(x: float) -> float:
    """
    Expected prime gap near x.
    
    By PNT: average gap ≈ log(x)
    
    Args:
        x: Location
        
    Returns:
        Expected gap
    """
    return log(x)


# Diagnostic function
def print_z5d_summary(sqrt_N: int, epsilon: float = 0.02):
    """Print Z5D predictions for given √N."""
    print("Z5D API Summary")
    print("=" * 70)
    print(f"√N = {sqrt_N}")
    print(f"log(√N) = {log(float(sqrt_N)):.2f}")
    print(f"Base density = {local_prime_density(float(sqrt_N)):.6e}")
    print()
    
    k_minus, k_plus = predict_prime_band(sqrt_N, epsilon)
    print(f"Prime index band [k₋, k₊]: [{k_minus}, {k_plus}]")
    print(f"Band width: {k_plus - k_minus}")
    print(f"Error margin ε = {epsilon:.2%}")
    print()
    
    print("Sample δ-bands (top 5):")
    bands = prioritize_delta_bands(sqrt_N, delta_max=100000, num_bands=10)
    for i, band in enumerate(bands[:5]):
        print(f"  {i+1}. δ=[{band['delta_start']}, {band['delta_end']}], "
              f"density={band['density']:.6e}")
    print("=" * 70)


if __name__ == "__main__":
    # Test with 127-bit challenge
    CHALLENGE_127 = 137524771864208156028430259349934309717
    
    def isqrt(n):
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
    
    sqrt_N = isqrt(CHALLENGE_127)
    print_z5d_summary(sqrt_N, epsilon=0.02)
