#!/usr/bin/env python3
"""
Hash-Bounds Predictor v1
========================

Implements the v1 Hash-Bounds predictor to test the hypothesis:

    Z5D prime structure + √p fractional parts can be turned into a 
    probabilistic band on frac(√d) (or d/√N) for a factor d of semiprime N.

Hypothesis parameters:
- mean relative error ≈ 22,126 ppm
- average fractional error ≈ 0.237
- width factor ≈ 0.155 giving ≈ 51.5% coverage in older experiments
- plus curvature terms like κ(n) if we add them

This is NOT a deterministic bound; it gives a prior window that 
allegedly hits factors in ~50-80% of cases.

Usage:
    predictor = HashBoundsPredictor(width=0.155)
    band = predictor.predict_band(N)
    is_hit = predictor.check_factor_in_band(N, factor, strategy='fracSqrt')
"""

import mpmath as mp
from mpmath import mpf, sqrt, log, floor, frac
from typing import Tuple, Dict, Optional, NamedTuple
from dataclasses import dataclass
import json
import datetime


class PredictedBand(NamedTuple):
    """Predicted fractional band [lower, upper] in [0,1)."""
    center: mpf
    lower: mpf
    upper: mpf
    width: mpf
    p_pred: mpf      # Predicted prime location
    f_pred: mpf      # Predicted fractional part
    m_approx: mpf    # Prime index approximation


@dataclass
class BandCheckResult:
    """Result of checking if a factor is in the predicted band."""
    in_band: bool
    factor_value: mpf       # The computed g(d) value
    band_center: mpf
    band_lower: mpf
    band_upper: mpf
    distance_from_center: mpf
    strategy: str


def set_precision(N: int) -> int:
    """
    Set mpmath precision based on bit-length of N.
    
    Formula: max(configured, N.bitLength() × 4 + 200)
    
    Args:
        N: The semiprime
        
    Returns:
        The precision in decimal places (mp.dps)
    """
    bit_length = N.bit_length()
    required_dps = max(100, bit_length * 4 + 200)
    mp.dps = required_dps
    return required_dps


class HashBoundsPredictor:
    """
    v1 Hash-Bounds Predictor implementation.
    
    Prediction pipeline:
    1. Choose predictor input: x = N or x = floor(sqrt(N))
    2. Map to prime index scale: m ≈ x / ln(x) 
    3. Compute predicted prime location: p_pred ≈ m × ln(m)
    4. Compute fractional part: f_pred = frac(sqrt(p_pred))
    5. Build band with configurable width
    
    Strategies for checking factors:
    - 'fracSqrt': g(d) = frac(√d) 
    - 'dOverSqrtN': g(d) = frac(d / √N)
    """
    
    DEFAULT_WIDTH = mpf('0.155')
    
    def __init__(self, 
                 width: float = 0.155, 
                 use_sqrt_N: bool = True,
                 bit_length_scaling: bool = True):
        """
        Initialize the predictor.
        
        Args:
            width: Band width factor (default 0.155 from hypothesis)
            use_sqrt_N: If True, use x=floor(√N) as input; else use x=N
            bit_length_scaling: If True, adjust width based on bit-length
        """
        self.width = mpf(str(width))
        self.use_sqrt_N = use_sqrt_N
        self.bit_length_scaling = bit_length_scaling
        self._precision = None
    
    def _compute_prime_index_approx(self, x: mpf) -> mpf:
        """
        Map x to prime index scale.
        
        m ≈ x / ln(x) (simple Prime Number Theorem approximation)
        
        This is a proxy for Z5D prime index structure.
        """
        if x <= 1:
            return mpf('1')
        ln_x = log(x)
        if ln_x <= 0:
            return mpf('1')
        return x / ln_x
    
    def _compute_predicted_prime(self, m: mpf) -> mpf:
        """
        Compute predicted prime location.
        
        p_pred ≈ m × ln(m) (inverse of prime counting function)
        
        The m-th prime is approximately m × ln(m).
        """
        if m <= 1:
            return mpf('2')
        ln_m = log(m)
        if ln_m <= 0:
            return mpf('2')
        return m * ln_m
    
    def _fractional_part(self, x: mpf) -> mpf:
        """
        Compute fractional part frac(x) = x - floor(x).
        
        Result is in [0, 1).
        """
        return frac(x)
    
    def _wrap_band(self, center: mpf, half_width: mpf) -> Tuple[mpf, mpf]:
        """
        Build band [lower, upper] with wrap-around in [0,1).
        
        Args:
            center: Band center in [0,1)
            half_width: Half of band width
            
        Returns:
            Tuple (lower, upper) with wrap-around handled
        """
        lower = center - half_width
        upper = center + half_width
        
        # Normalize to [0, 1) using fractional part arithmetic
        # Adding 1 ensures the value is positive before taking frac(),
        # since frac(x) = frac(x + n) for any integer n
        lower = self._fractional_part(lower + 1)
        upper = self._fractional_part(upper)
        
        return lower, upper
    
    def _adjust_width_for_bit_length(self, bit_length: int) -> mpf:
        """
        Optionally adjust width based on bit-length.
        
        The hypothesis suggests width might need scaling for different scales.
        This is a simple linear adjustment based on empirical observations.
        """
        if not self.bit_length_scaling:
            return self.width
        
        # Base width at 60 bits, slight increase for larger numbers
        # This is speculative and part of the falsification test
        base_bits = 60
        if bit_length > base_bits:
            # Increase width by 0.5% per 10 bits above 60
            scale_factor = 1 + 0.005 * (bit_length - base_bits) / 10
            return self.width * mpf(str(scale_factor))
        return self.width
    
    def predict_band(self, N: int) -> PredictedBand:
        """
        Predict the fractional band for a semiprime N.
        
        Args:
            N: The semiprime to predict band for
            
        Returns:
            PredictedBand with center, lower, upper, and diagnostic info
        """
        # Set precision
        self._precision = set_precision(N)
        
        N_mpf = mpf(str(N))
        bit_length = N.bit_length()
        
        # Step 1: Choose predictor input
        if self.use_sqrt_N:
            x = floor(sqrt(N_mpf))
        else:
            x = N_mpf
        
        # Step 2: Map to prime index scale
        m = self._compute_prime_index_approx(x)
        
        # Step 3: Compute predicted prime location
        p_pred = self._compute_predicted_prime(m)
        
        # Step 4: Compute fractional part
        f_pred = self._fractional_part(sqrt(p_pred))
        
        # Step 5: Build band
        width = self._adjust_width_for_bit_length(bit_length)
        half_width = width / 2
        lower, upper = self._wrap_band(f_pred, half_width)
        
        return PredictedBand(
            center=f_pred,
            lower=lower,
            upper=upper,
            width=width,
            p_pred=p_pred,
            f_pred=f_pred,
            m_approx=m
        )
    
    def _in_band(self, value: mpf, band: PredictedBand) -> bool:
        """
        Check if value is in the band, handling wrap-around.
        
        For bands that wrap around 0 (e.g., lower=0.9, upper=0.1),
        a value is in-band if value >= lower OR value <= upper.
        """
        lower = band.lower
        upper = band.upper
        
        if lower <= upper:
            # Normal case: band doesn't wrap
            return lower <= value <= upper
        else:
            # Wrap-around case: band crosses 0
            return value >= lower or value <= upper
    
    def check_factor_in_band(self, 
                             N: int, 
                             factor: int, 
                             strategy: str = 'fracSqrt') -> BandCheckResult:
        """
        Check if a factor d of N falls in the predicted band.
        
        Args:
            N: The semiprime
            factor: A factor d of N (must divide N)
            strategy: 'fracSqrt' for g(d)=frac(√d) or 'dOverSqrtN' for g(d)=frac(d/√N)
            
        Returns:
            BandCheckResult with all diagnostic information
        """
        # Ensure precision is set
        if self._precision is None:
            self._precision = set_precision(N)
        
        N_mpf = mpf(str(N))
        d_mpf = mpf(str(factor))
        
        # Get the predicted band
        band = self.predict_band(N)
        
        # Compute g(d) based on strategy
        if strategy == 'fracSqrt':
            g_d = self._fractional_part(sqrt(d_mpf))
        elif strategy == 'dOverSqrtN':
            sqrt_N = sqrt(N_mpf)
            g_d = self._fractional_part(d_mpf / sqrt_N)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Check if in band
        in_band = self._in_band(g_d, band)
        
        # Distance from center (handling wrap-around)
        dist = abs(float(g_d) - float(band.center))
        if dist > 0.5:
            dist = 1 - dist  # wrap-around distance
        
        return BandCheckResult(
            in_band=in_band,
            factor_value=g_d,
            band_center=band.center,
            band_lower=band.lower,
            band_upper=band.upper,
            distance_from_center=mpf(str(dist)),
            strategy=strategy
        )
    
    def get_config(self) -> Dict:
        """Return predictor configuration as a dictionary."""
        return {
            'width': float(self.width),
            'use_sqrt_N': self.use_sqrt_N,
            'bit_length_scaling': self.bit_length_scaling,
            'precision': self._precision
        }


def run_diagnostic(N: int, p: int, q: int, predictor: HashBoundsPredictor = None) -> Dict:
    """
    Run diagnostic on a known semiprime with factors.
    
    Args:
        N: The semiprime
        p: First factor
        q: Second factor (N = p × q)
        predictor: Optional predictor instance
        
    Returns:
        Dictionary with diagnostic results
    """
    if predictor is None:
        predictor = HashBoundsPredictor()
    
    # Verify N = p × q
    assert N == p * q, f"Invalid factors: {p} × {q} ≠ {N}"
    
    # Get band prediction
    band = predictor.predict_band(N)
    
    # Check both factors with both strategies
    results = {
        'N': str(N),
        'N_bit_length': N.bit_length(),
        'p': str(p),
        'q': str(q),
        'band': {
            'center': float(band.center),
            'lower': float(band.lower),
            'upper': float(band.upper),
            'width': float(band.width),
            'm_approx': float(band.m_approx),
            'p_pred': float(band.p_pred)
        },
        'checks': {},
        'precision_dps': predictor._precision,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    
    for factor_name, factor in [('p', p), ('q', q)]:
        for strategy in ['fracSqrt', 'dOverSqrtN']:
            check = predictor.check_factor_in_band(N, factor, strategy)
            key = f"{factor_name}_{strategy}"
            results['checks'][key] = {
                'in_band': check.in_band,
                'factor_value': float(check.factor_value),
                'distance_from_center': float(check.distance_from_center)
            }
    
    # Summary
    hits = sum(1 for c in results['checks'].values() if c['in_band'])
    results['summary'] = {
        'total_checks': len(results['checks']),
        'hits': hits,
        'hit_rate': hits / len(results['checks'])
    }
    
    return results


if __name__ == "__main__":
    # Quick test with 127-bit challenge
    CHALLENGE_127 = 137524771864208156028430259349934309717
    P_127 = 10508623501177419659
    Q_127 = 13086849276577416863
    
    print("Hash-Bounds Predictor v1 - Diagnostic")
    print("=" * 70)
    
    predictor = HashBoundsPredictor()
    results = run_diagnostic(CHALLENGE_127, P_127, Q_127, predictor)
    
    print(f"N = {results['N']}")
    print(f"N bit-length = {results['N_bit_length']}")
    print(f"Precision (dps) = {results['precision_dps']}")
    print()
    print("Predicted Band:")
    print(f"  center = {results['band']['center']:.6f}")
    print(f"  lower  = {results['band']['lower']:.6f}")
    print(f"  upper  = {results['band']['upper']:.6f}")
    print(f"  width  = {results['band']['width']:.6f}")
    print()
    print("Factor Checks:")
    for key, check in results['checks'].items():
        status = "✓ IN BAND" if check['in_band'] else "✗ OUT OF BAND"
        print(f"  {key}: {check['factor_value']:.6f} - {status} (dist: {check['distance_from_center']:.6f})")
    print()
    print(f"Summary: {results['summary']['hits']}/{results['summary']['total_checks']} hits "
          f"({results['summary']['hit_rate']:.1%})")
    print("=" * 70)
