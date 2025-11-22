"""
Geometric Resonance Factorization Pipeline
==========================================

Complete implementation of geometric resonance factorization for the 127-bit
challenge number using Python and mpmath.

This module implements:
1. Z-framework forms: Z = A(B/c) from cornerstone_invariant.py
2. Discrete structures: Z = n(Δₙ/Δₘₐₓ) where Δₙ = d(n)·ln(n+1)/e²
3. Geometric prime-density mapping: θ′(n,k)=φ·((n mod φ)/φ)^k with k≈0.3
4. Dirichlet kernel resonance detection
5. Golden-ratio QMC sampling with deterministic seeds
6. Scale-adaptive parameter tuning

VALIDATION GATE:
- Primary target: N = 137524771864208156028430259349934309717 (127-bit challenge)
- Expected factors: p = 10508623501177419659, q = 13086849276577416863
- Precision: min(704) = N.bitLength() × 4 + 200 decimal digits

CRITICAL REQUIREMENTS:
- No classical fallbacks (no Pollard's Rho, ECM, trial division)
- Deterministic/quasi-deterministic only
- Explicit precision with mp.dps set and logged
- Pin seeds, log all parameters with timestamps
"""

import mpmath as mp
from mpmath import mpf, pi, log, sin, sqrt, ln, e
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import time


# Constants
CHALLENGE_127 = 137524771864208156028430259349934309717
CHALLENGE_127_P = 10508623501177419659
CHALLENGE_127_Q = 13086849276577416863

# Golden ratio (high precision)
PHI = (1 + sqrt(5)) / 2

# e² for discrete invariant
E_SQUARED = e**2


class ScaleAdaptiveParams:
    """
    Scale-adaptive parameter tuning based on bit-length analysis.
    
    Implements empirical scaling laws from Z5D prime predictor research:
    - Number-theoretic patterns exhibit scale-dependent behavior
    - Parameters must adapt to mathematical scale
    """
    
    BASELINE_BIT_LENGTH = 30.0
    MIN_THRESHOLD = 0.5
    MAX_THRESHOLD = 1.0
    
    @staticmethod
    def bit_length(n: int) -> int:
        """Compute bit length of integer."""
        return n.bit_length()
    
    @staticmethod
    def adaptive_samples(n: int, base_samples: int) -> int:
        """
        Compute scale-adaptive samples count.
        Formula: base × (bitLength / 30)^1.5
        """
        bit_len = ScaleAdaptiveParams.bit_length(n)
        scale_factor = (bit_len / ScaleAdaptiveParams.BASELINE_BIT_LENGTH) ** 1.5
        return int(base_samples * scale_factor)
    
    @staticmethod
    def adaptive_m_span(n: int, base_m_span: int) -> int:
        """
        Compute scale-adaptive m-span.
        Formula: base × (bitLength / 30)
        """
        bit_len = ScaleAdaptiveParams.bit_length(n)
        scale_factor = bit_len / ScaleAdaptiveParams.BASELINE_BIT_LENGTH
        return int(base_m_span * scale_factor)
    
    @staticmethod
    def adaptive_threshold(n: int, base_threshold: float, attenuation: float) -> float:
        """
        Compute scale-adaptive threshold.
        Formula: base - (log₂(bitLength / 30) × attenuation)
        """
        bit_len = ScaleAdaptiveParams.bit_length(n)
        scale_factor = mp.log(bit_len / ScaleAdaptiveParams.BASELINE_BIT_LENGTH, 2)
        adapted = base_threshold - (float(scale_factor) * attenuation)
        return max(ScaleAdaptiveParams.MIN_THRESHOLD, 
                   min(ScaleAdaptiveParams.MAX_THRESHOLD, adapted))
    
    @staticmethod
    def adaptive_k_range(n: int, k_lo: float, k_hi: float) -> Tuple[float, float]:
        """
        Compute scale-adaptive k-range bounds.
        Formula: Center around 0.35 with narrowing window.
        """
        bit_len = ScaleAdaptiveParams.bit_length(n)
        center = (k_lo + k_hi) / 2.0
        base_width = (k_hi - k_lo) / 2.0
        
        scale_factor = mp.sqrt(bit_len / ScaleAdaptiveParams.BASELINE_BIT_LENGTH)
        adapted_width = base_width / float(scale_factor)
        
        return (center - adapted_width, center + adapted_width)
    
    @staticmethod
    def adaptive_timeout(n: int, base_timeout: float) -> float:
        """
        Compute scale-adaptive timeout in seconds.
        Formula: base × (bitLength / 30)^2
        """
        bit_len = ScaleAdaptiveParams.bit_length(n)
        scale_factor = (bit_len / ScaleAdaptiveParams.BASELINE_BIT_LENGTH) ** 2.0
        return base_timeout * scale_factor


class DirichletKernel:
    """
    Normalized Dirichlet kernel for geometric resonance detection.
    Returns amplitude normalized to (2J+1) for consistent thresholding.
    """
    
    @staticmethod
    def normalized_amplitude(theta: mpf, J: int, precision_eps: mpf) -> mpf:
        """
        Compute normalized Dirichlet kernel amplitude.
        A(θ) = |sin((2J+1)θ/2) / ((2J+1) sin(θ/2))|
        
        Args:
            theta: Angular parameter θ
            J: Half-width of Dirichlet kernel
            precision_eps: Epsilon for singularity guard
            
        Returns:
            Normalized amplitude in [0, 1]
        """
        # Reduce to [-π, π] for stability
        t = principal_angle(theta)
        
        th2 = t / 2  # θ/2
        sin_th2 = sin(th2)
        
        # Singularity guard
        if abs(sin_th2) < precision_eps:
            return mpf(1)
        
        two_j_plus_1 = mpf(2 * J + 1)
        num = sin(th2 * two_j_plus_1)
        den = sin_th2 * two_j_plus_1
        
        amplitude = abs(num / den)
        return amplitude


def principal_angle(theta: mpf) -> mpf:
    """
    Reduce angle to [-π, π] for numerical stability.
    Uses modular arithmetic for efficiency.
    """
    two_pi = 2 * pi
    # Reduce to [-π, π] using modular arithmetic
    t = ((theta + pi) % two_pi) - pi
    return t


def compute_discrete_delta(n: int) -> mpf:
    """
    Compute discrete frame shift: Δₙ = d(n)·ln(n+1)/e²
    
    Uses log(n) as simplified approximation for d(n) (divisor count),
    consistent with z_baseline implementation. This is an average-order
    approximation; individual divisor counts vary but the approximation
    provides adequate accuracy for frame shift calculations.
    
    Args:
        n: Integer for divisor computation
        
    Returns:
        Frame shift value
    """
    if n < 1:
        return mpf(0)
    
    # Approximate divisor count: d(n) ≈ log(n) (average order approximation)
    d_n = log(n) if n > 1 else mpf(1)
    ln_term = log(n + 1)
    
    delta_n = (d_n * ln_term) / E_SQUARED
    return delta_n


def compute_geodesic_transform(n: int, k: float) -> mpf:
    """
    Compute geometric prime-density mapping: θ′(n,k) = φ·((n mod φ)/φ)^k
    
    This function implements one of the Z-framework domain-specific forms
    and is provided for completeness and future extensions. The current
    factorization algorithm uses the standard phase formula θ = 2π*m/k
    (see line 389 in factor() method).
    
    Note: Taking modulo of integer n by irrational φ is intentional for the
    geodesic mapping. This computes the fractional position of n relative to
    the golden ratio scale, which is part of the geometric prime-density
    transformation framework.
    
    Args:
        n: Integer parameter
        k: Geodesic exponent (typically ~0.3)
        
    Returns:
        Geodesic-transformed value
    """
    # Guard against zero division
    if PHI == 0:
        return mpf(0)
    
    # Compute (n mod φ) / φ - fractional position on golden ratio scale
    n_mod_phi = mpf(n) % PHI
    ratio = n_mod_phi / PHI
    
    # Apply geodesic transformation: φ · ratio^k
    result = PHI * (ratio ** mpf(k))
    return result


def golden_ratio_qmc_sample(index: int, seed: int = 0) -> mpf:
    """
    Golden-ratio quasi-Monte Carlo sampling (deterministic).
    
    Args:
        index: Sample index
        seed: Deterministic seed for reproducibility
        
    Returns:
        QMC sample value in [0, 1]
    """
    # Deterministic golden ratio sequence
    alpha = PHI - 1  # 1/φ ≈ 0.618
    return mpf((seed + index * alpha) % 1)


class GeometricResonanceFactorizer:
    """
    Complete geometric resonance factorization implementation.
    """
    
    def __init__(
        self,
        samples: int = 3000,
        m_span: int = 180,
        J: int = 10,
        threshold: float = 0.92,
        k_lo: float = 0.25,
        k_hi: float = 0.45,
        timeout_seconds: float = 600.0,
        attenuation: float = 0.05,
        enable_scale_adaptive: bool = True,
        seed: int = 42
    ):
        """
        Initialize geometric resonance factorizer.
        
        Args:
            samples: Base number of QMC samples
            m_span: Base resonance sweep width
            J: Dirichlet kernel half-width
            threshold: Base resonance detection threshold
            k_lo: Lower bound of k-range
            k_hi: Upper bound of k-range
            timeout_seconds: Base timeout in seconds
            attenuation: Threshold attenuation factor
            enable_scale_adaptive: Enable scale-adaptive parameter tuning
            seed: Deterministic seed for reproducibility
        """
        self.base_samples = samples
        self.base_m_span = m_span
        self.J = J
        self.base_threshold = threshold
        self.base_k_lo = k_lo
        self.base_k_hi = k_hi
        self.base_timeout = timeout_seconds
        self.attenuation = attenuation
        self.enable_scale_adaptive = enable_scale_adaptive
        self.seed = seed
    
    def factor(self, N: int) -> Optional[Tuple[int, int]]:
        """
        Factor semiprime N into p × q using geometric resonance.
        
        Args:
            N: Semiprime to factor (must be 127-bit challenge or in [10^14, 10^18])
            
        Returns:
            Tuple (p, q) if successful, None otherwise
        """
        # Validation gate check
        if N != CHALLENGE_127:
            # Check if in operational range [10^14, 10^18]
            if not (10**14 <= N <= 10**18):
                raise ValueError(
                    f"N={N} violates validation gates. "
                    f"Must be 127-bit challenge or in [10^14, 10^18]"
                )
        
        # Set precision: max(configured, N.bitLength() × 4 + 200)
        bit_length = N.bit_length()
        precision_dps = max(100, bit_length * 4 + 200)
        mp.dps = precision_dps
        
        print(f"=== Geometric Resonance Factorization ===")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"N = {N} ({bit_length} bits)")
        print(f"Precision: {mp.dps} decimal digits")
        print(f"Seed: {self.seed}")
        
        # Apply scale-adaptive parameters
        if self.enable_scale_adaptive:
            samples = ScaleAdaptiveParams.adaptive_samples(N, self.base_samples)
            m_span = ScaleAdaptiveParams.adaptive_m_span(N, self.base_m_span)
            threshold = ScaleAdaptiveParams.adaptive_threshold(
                N, self.base_threshold, self.attenuation
            )
            k_lo, k_hi = ScaleAdaptiveParams.adaptive_k_range(
                N, self.base_k_lo, self.base_k_hi
            )
            timeout = ScaleAdaptiveParams.adaptive_timeout(N, self.base_timeout)
        else:
            samples = self.base_samples
            m_span = self.base_m_span
            threshold = self.base_threshold
            k_lo = self.base_k_lo
            k_hi = self.base_k_hi
            timeout = self.base_timeout
        
        print(f"=== Scale-Adaptive Parameters ===")
        print(f"Samples: {samples}")
        print(f"M-span: {m_span}")
        print(f"J: {self.J}")
        print(f"Threshold: {threshold:.4f}")
        print(f"K-range: [{k_lo:.4f}, {k_hi:.4f}]")
        print(f"Timeout: {timeout:.1f} seconds ({timeout/60:.1f} minutes)")
        print(f"================================")
        
        # Epsilon for singularity guards (adaptive based on precision)
        eps_scale = precision_dps // 2
        precision_eps = mpf(10) ** (-eps_scale)
        print(f"Singularity epsilon: 1e-{eps_scale}")
        
        # Convert N to mpmath
        N_mp = mpf(N)
        ln_N = log(N_mp)
        two_pi = 2 * pi
        
        # Start search
        start_time = time.time()
        print(f"\nStarting resonance search...")
        
        # QMC sampling loop
        k_width = k_hi - k_lo
        progress_interval = max(1, samples // 10)
        
        for n in range(samples):
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                print(f"\nTimeout reached after {elapsed:.1f} seconds")
                return None
            
            # Progress reporting
            if n > 0 and n % progress_interval == 0:
                print(f"Progress: {n}/{samples} samples ({100*n//samples}%), "
                      f"elapsed: {elapsed:.1f}s")
            
            # Golden-ratio QMC sample for u in [0, 1]
            u = golden_ratio_qmc_sample(n, self.seed)
            
            # Map u to k-range
            k = k_lo + float(u) * k_width
            
            # Sweep over m-span for resonance detection
            # m = 0 assumption (balanced semiprime)
            for m in range(-m_span, m_span + 1):
                # Guard against division by zero (k should never be 0 from QMC, but defensive)
                if abs(k) < 1e-10:
                    continue
                    
                # Compute phase angle: θ = 2π*m/k
                # NOTE: This is the standard formula, not using geodesic transform
                theta = two_pi * mpf(m) / mpf(k)
                
                # Dirichlet kernel amplitude
                amplitude = DirichletKernel.normalized_amplitude(
                    theta, self.J, precision_eps
                )
                
                # Resonance detection
                if amplitude >= mpf(threshold):
                    # Potential factor candidate using phase-corrected snap
                    # Formula: p̂ = exp((ln(N) - θ')/2) where θ' is principal angle
                    
                    # Reduce theta to principal angle for stability
                    theta_principal = principal_angle(theta)
                    
                    # Phase-corrected snap: p̂ = exp((ln(N) - θ')/2)
                    expo = (ln_N - theta_principal) / 2
                    p_hat = mp.exp(expo)
                    
                    # Round to nearest integer (use floor as in Java SnapKernel)
                    candidate = int(mp.floor(p_hat))
                    
                    # Guard: candidate must be in valid range (1, N)
                    if candidate <= 1 or candidate >= N:
                        continue
                    
                    # Verify candidate
                    if N % candidate == 0:
                        p = candidate
                        q = N // p
                        
                        # Order factors
                        if p > q:
                            p, q = q, p
                        
                        elapsed = time.time() - start_time
                        print(f"\n=== SUCCESS ===")
                        print(f"Factor found at sample {n}, m={m}")
                        print(f"k = {k:.6f}")
                        print(f"Amplitude = {amplitude:.6f}")
                        print(f"Theta (principal) = {float(theta_principal):.6f}")
                        print(f"p = {p}")
                        print(f"q = {q}")
                        print(f"Time: {elapsed:.3f} seconds")
                        
                        # Verification
                        if p * q == N:
                            print(f"Verification: p × q = N ✓")
                            return (p, q)
                        else:
                            print(f"Verification FAILED: p × q ≠ N")
                            continue
        
        # No factor found
        elapsed = time.time() - start_time
        print(f"\nNo factor found after {samples} samples, {elapsed:.1f} seconds")
        return None


def factor_127_bit_challenge() -> Optional[Tuple[int, int]]:
    """
    Factor the 127-bit challenge number with scale-adaptive parameters.
    
    Returns:
        Tuple (p, q) if successful, None otherwise
    """
    factorizer = GeometricResonanceFactorizer(
        samples=3000,
        m_span=180,
        J=10,
        threshold=0.92,
        k_lo=0.25,
        k_hi=0.45,
        timeout_seconds=600.0,
        attenuation=0.05,
        enable_scale_adaptive=True,
        seed=42
    )
    
    result = factorizer.factor(CHALLENGE_127)
    
    if result:
        p, q = result
        # Final verification
        if p * q == CHALLENGE_127:
            print(f"\n{'='*50}")
            print(f"127-BIT CHALLENGE SOLVED")
            print(f"{'='*50}")
            print(f"N = {CHALLENGE_127}")
            print(f"p = {p}")
            print(f"q = {q}")
            print(f"Verification: {p} × {q} = {p * q}")
            print(f"Match: {p * q == CHALLENGE_127}")
            return (p, q)
    
    return None


if __name__ == "__main__":
    # Run the 127-bit challenge factorization
    result = factor_127_bit_challenge()
    
    if result is None:
        print("\nFACTORIZATION FAILED")
        exit(1)
    else:
        print("\nFACTORIZATION SUCCEEDED")
        exit(0)
