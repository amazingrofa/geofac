#!/usr/bin/env python3
"""
Test and Falsification Logic for 127-bit Parameter Optimization
================================================================

Implements the falsification tests for the parameter optimization hypothesis.
Tests whether proposed parameters improve 127-bit factorization.
"""

import os
import sys
import json
import time
import subprocess
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from math import log, sqrt, isqrt, floor

# High-precision math
try:
    import mpmath
    # Note: Precision is set within functions that need it (not at module level)
except ImportError:
    print("Warning: mpmath not available, using standard math")
    mpmath = None


# ============================================================================
# Constants
# ============================================================================

# 127-bit Challenge (Whitelisted)
CHALLENGE_127 = 137524771864208156028430259349934309717
CHALLENGE_127_P = 10508623501177419659
CHALLENGE_127_Q = 13086849276577416863

# Validate challenge constants at import time
assert CHALLENGE_127_P * CHALLENGE_127_Q == CHALLENGE_127, \
    "Challenge factor verification failed: p * q != N"

# Gate 1 (30-bit)
GATE_1_N = 1073217479
GATE_1_P = 32749
GATE_1_Q = 32771

# Gate 2 (60-bit)
GATE_2_N = 1152921470247108503
GATE_2_P = 1073741789
GATE_2_Q = 1073741827

# Baseline bit-length for scaling
BASELINE_BIT_LENGTH = 30.0

# Search radius constants
LARGE_N_DIVISOR = 10**15       # Divisor for sqrt_N when computing search radius for large N
DEFAULT_SEARCH_FRACTION = 0.001  # Default fraction of p0 for search radius
MAX_SEARCH_RADIUS = 10000      # Maximum search radius for small/medium N
LARGE_N_MIN_RADIUS = 10        # Minimum radius for large N

# Threshold analysis constants
FALSE_POSITIVE_HIGH_THRESHOLD = 0.5   # Pass rate above this indicates HIGH risk
FALSE_POSITIVE_MODERATE_THRESHOLD = 0.1  # Pass rate above this indicates MODERATE risk
EXCESSIVE_FALSE_POSITIVE_MULTIPLIER = 2  # Multiplier for comparing candidate pass rates


# ============================================================================
# Scale-Adaptive Parameter Calculations (mirrors ScaleAdaptiveParams.java)
# ============================================================================

def adaptive_samples(N: int, base_samples: int) -> int:
    """Compute scale-adaptive samples count."""
    bit_length = N.bit_length()
    scale_factor = (bit_length / BASELINE_BIT_LENGTH) ** 1.5
    return int(base_samples * scale_factor)


def adaptive_m_span(N: int, base_m_span: int) -> int:
    """Compute scale-adaptive m-span."""
    bit_length = N.bit_length()
    scale_factor = bit_length / BASELINE_BIT_LENGTH
    return int(base_m_span * scale_factor)


def adaptive_threshold(N: int, base_threshold: float, attenuation: float) -> float:
    """Compute scale-adaptive threshold."""
    bit_length = N.bit_length()
    scale_factor = log(bit_length / BASELINE_BIT_LENGTH) / log(2)
    adapted = base_threshold - (scale_factor * attenuation)
    return max(0.5, min(1.0, adapted))


def adaptive_k_range(N: int, k_lo: float, k_hi: float) -> Tuple[float, float]:
    """Compute scale-adaptive k-range."""
    bit_length = N.bit_length()
    center = (k_lo + k_hi) / 2.0
    base_width = (k_hi - k_lo) / 2.0
    scale_factor = sqrt(bit_length / BASELINE_BIT_LENGTH)
    adapted_width = base_width / scale_factor
    return (center - adapted_width, center + adapted_width)


def adaptive_timeout(N: int, base_timeout: int) -> int:
    """Compute scale-adaptive timeout (ms)."""
    bit_length = N.bit_length()
    scale_factor = (bit_length / BASELINE_BIT_LENGTH) ** 2.0
    return int(base_timeout * scale_factor)


# ============================================================================
# Parameter Configurations
# ============================================================================

@dataclass
class ParameterConfig:
    """Configuration for a factorization attempt."""
    name: str
    samples: int
    m_span: int
    threshold: float
    k_lo: float
    k_hi: float
    timeout_ms: int
    precision: int = 708  # N.bitLength() * 4 + 200 for 127-bit
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "samples": self.samples,
            "m_span": self.m_span,
            "threshold": self.threshold,
            "k_lo": self.k_lo,
            "k_hi": self.k_hi,
            "timeout_ms": self.timeout_ms,
            "precision": self.precision,
            "description": self.description
        }


def get_scale_adaptive_defaults(N: int) -> ParameterConfig:
    """Get current scale-adaptive defaults for given N."""
    # Base values from application.yml
    base_samples = 2000
    base_m_span = 180
    base_threshold = 0.95
    base_k_lo = 0.25
    base_k_hi = 0.45
    base_timeout = 1200000  # 20 minutes
    attenuation = 0.05
    
    k_lo, k_hi = adaptive_k_range(N, base_k_lo, base_k_hi)
    
    return ParameterConfig(
        name="scale_adaptive_defaults",
        samples=adaptive_samples(N, base_samples),
        m_span=adaptive_m_span(N, base_m_span),
        threshold=adaptive_threshold(N, base_threshold, attenuation),
        k_lo=k_lo,
        k_hi=k_hi,
        timeout_ms=adaptive_timeout(N, base_timeout),
        precision=max(240, N.bit_length() * 4 + 200),
        description="Current scale-adaptive defaults from ScaleAdaptiveParams.java"
    )


def get_proposed_params(N: int) -> ParameterConfig:
    """
    Get the proposed parameter values from the hypothesis.
    
    Note on parameter interpretation:
    - The hypothesis specifies k.min=2, k.max=17 (integer values)
    - The current Java implementation uses fractional k in [0.25, 0.45]
    - We interpret the integer range [2, 17] as requiring a wider fractional range
    - Mapping: [0.1, 0.9] covers most of the fractional k-space
    
    - The hypothesis specifies m.resolution=200 which we interpret as m_span=200
    - m_span controls the half-width of the Dirichlet kernel sweep over m
    """
    return ParameterConfig(
        name="proposed_hypothesis",
        samples=50000,  # Fixed, not scaled (hypothesis value)
        m_span=200,     # Interpreted from "m.resolution=200" as sweep half-width
        threshold=0.15,  # Much lower threshold (hypothesis value)
        k_lo=0.1,       # Wide k-range to capture hypothesis intent of k.min=2
        k_hi=0.9,       # Wide k-range to capture hypothesis intent of k.max=17
        timeout_ms=1800000,  # 30 minutes as per hypothesis constraint
        precision=max(240, N.bit_length() * 4 + 200),
        description="Proposed parameters from the hypothesis"
    )


def get_ablation_configs(N: int) -> List[ParameterConfig]:
    """Get ablation configurations to test individual claims."""
    defaults = get_scale_adaptive_defaults(N)
    
    # Ablation 1: Default + lower threshold only
    ablation1 = ParameterConfig(
        name="ablation_lower_threshold",
        samples=defaults.samples,
        m_span=defaults.m_span,
        threshold=0.15,  # Lower threshold from hypothesis
        k_lo=defaults.k_lo,
        k_hi=defaults.k_hi,
        timeout_ms=defaults.timeout_ms,
        precision=defaults.precision,
        description="Default + lower threshold (0.15) only"
    )
    
    # Ablation 2: Default + wider k-range only
    ablation2 = ParameterConfig(
        name="ablation_wider_k_range",
        samples=defaults.samples,
        m_span=defaults.m_span,
        threshold=defaults.threshold,
        k_lo=0.1,  # Wider range
        k_hi=0.9,
        timeout_ms=defaults.timeout_ms,
        precision=defaults.precision,
        description="Default + wider k-range [0.1, 0.9] only"
    )
    
    # Ablation 3: Default + higher samples only
    ablation3 = ParameterConfig(
        name="ablation_higher_samples",
        samples=50000,  # Higher samples from hypothesis
        m_span=defaults.m_span,
        threshold=defaults.threshold,
        k_lo=defaults.k_lo,
        k_hi=defaults.k_hi,
        timeout_ms=defaults.timeout_ms,
        precision=defaults.precision,
        description="Default + higher samples (50000) only"
    )
    
    return [ablation1, ablation2, ablation3]


# ============================================================================
# Simple Dirichlet Kernel Implementation
# ============================================================================

def dirichlet_amplitude(theta: float, J: int) -> float:
    """
    Compute normalized Dirichlet kernel amplitude.
    D_J(θ) = sin((2J+1)θ/2) / sin(θ/2)
    Normalized: |D_J(θ)| / (2J+1)
    """
    if abs(theta) < 1e-10:
        return 1.0  # Limit as θ → 0
    
    half_theta = theta / 2.0
    numerator = abs(sin((2 * J + 1) * half_theta))
    denominator = abs(sin(half_theta))
    
    if denominator < 1e-10:
        return 1.0
    
    raw = numerator / denominator
    return raw / (2 * J + 1)  # Normalize


def sin(x: float) -> float:
    """Sine function using mpmath if available."""
    if mpmath:
        return float(mpmath.sin(x))
    return math.sin(x)


def cos(x: float) -> float:
    """Cosine function using mpmath if available."""
    if mpmath:
        return float(mpmath.cos(x))
    return math.cos(x)


# ============================================================================
# Test Results
# ============================================================================

@dataclass
class TestResult:
    """Result from a single test run."""
    config_name: str
    N: int
    success: bool
    p: Optional[int] = None
    q: Optional[int] = None
    duration_ms: int = 0
    candidates_tested: int = 0
    candidates_passed_threshold: int = 0
    peak_amplitude: float = 0.0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_name": self.config_name,
            "N": str(self.N),
            "N_bits": self.N.bit_length(),
            "success": self.success,
            "p": str(self.p) if self.p else None,
            "q": str(self.q) if self.q else None,
            "duration_ms": self.duration_ms,
            "candidates_tested": self.candidates_tested,
            "candidates_passed_threshold": self.candidates_passed_threshold,
            "peak_amplitude": self.peak_amplitude,
            "error_message": self.error_message
        }


# ============================================================================
# Python-based Geometric Resonance Search (Simplified)
# ============================================================================

def geometric_resonance_search(
    N: int,
    config: ParameterConfig,
    verbose: bool = False
) -> TestResult:
    """
    Python implementation of geometric resonance search.
    Simplified version for parameter testing.
    
    This uses the same core algorithm as the Java FactorizerService:
    1. QMC sampling in k-space
    2. Dirichlet kernel amplitude filtering
    3. Phase-corrected snap to candidate
    4. Expanding ring search around candidates
    """
    start_time = time.time()
    
    sqrt_N = isqrt(N)
    two_pi = 2 * 3.141592653589793
    J = 6  # Dirichlet kernel order
    
    # Use mpmath for high-precision log if available
    if mpmath:
        mpmath.mp.dps = max(100, N.bit_length() * 4 + 200)
        ln_N = float(mpmath.log(N))
    else:
        ln_N = log(N) if N > 0 else 0
    
    candidates_tested = 0
    candidates_passed = 0
    peak_amplitude = 0.0
    
    # Generate k-samples using golden ratio (quasi-random, deterministic)
    phi_inv = (sqrt(5) - 1) / 2
    k_samples = []
    for i in range(config.samples):
        u = (i * phi_inv) % 1.0
        k = config.k_lo + u * (config.k_hi - config.k_lo)
        k_samples.append(k)
    
    if verbose:
        print(f"Testing {len(k_samples)} k-samples in [{config.k_lo:.4f}, {config.k_hi:.4f}]")
        print(f"Threshold: {config.threshold}, M-span: {config.m_span}")
    
    # Test each k-sample with m-scan
    for k_idx, k in enumerate(k_samples):
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Timeout check
        if elapsed_ms >= config.timeout_ms:
            if verbose:
                print(f"Timeout after {elapsed_ms}ms at k-sample {k_idx}/{len(k_samples)}")
            return TestResult(
                config_name=config.name,
                N=N,
                success=False,
                duration_ms=elapsed_ms,
                candidates_tested=candidates_tested,
                candidates_passed_threshold=candidates_passed,
                peak_amplitude=peak_amplitude,
                error_message=f"Timeout after {elapsed_ms}ms"
            )
        
        # M-scan for this k
        for dm in range(-config.m_span, config.m_span + 1):
            m = dm
            if k > 0:
                theta = two_pi * m / k
            else:
                theta = 0
            
            # Dirichlet kernel filtering
            amplitude = dirichlet_amplitude(theta, J)
            peak_amplitude = max(peak_amplitude, amplitude)
            candidates_tested += 1
            
            if amplitude > config.threshold:
                candidates_passed += 1
                
                # Phase-corrected snap using high-precision arithmetic
                # For large N, we need to use mpmath to avoid overflow
                try:
                    if mpmath and abs(theta) > 0.001:
                        # Use mpmath for large exponents (precision already set at function start)
                        p0_mp = mpmath.exp(mpmath.mpf(ln_N) / 2 + mpmath.mpf(theta))
                        p0 = int(mpmath.nint(p0_mp))
                    elif abs(theta) < 0.001:
                        # For small theta, use sqrt_N directly
                        p0 = sqrt_N
                    else:
                        # Fallback: clamp to sqrt_N neighborhood
                        # exp(ln_N/2 + theta) = sqrt_N * exp(theta)
                        if abs(theta) < 50:  # Safe range for exp
                            p0 = int(round(sqrt_N * math.exp(theta)))
                        else:
                            # Theta too large, skip this candidate
                            continue
                except (OverflowError, ValueError):
                    # Skip candidates that cause overflow
                    continue
                
                # Guard: reject invalid p0
                if p0 <= 1 or p0 >= N:
                    continue
                
                # Test candidate and neighbors (expanding ring)
                # Scale search radius based on N's magnitude
                if N.bit_length() > 60:
                    search_radius = min(MAX_SEARCH_RADIUS, max(LARGE_N_MIN_RADIUS, int(sqrt_N / LARGE_N_DIVISOR)))
                else:
                    search_radius = min(MAX_SEARCH_RADIUS, int(p0 * DEFAULT_SEARCH_FRACTION))
                
                for d in range(-search_radius, search_radius + 1):
                    candidate = p0 + d
                    if candidate <= 1 or candidate >= N:
                        continue
                    
                    if N % candidate == 0:
                        q = N // candidate
                        duration_ms = int((time.time() - start_time) * 1000)
                        return TestResult(
                            config_name=config.name,
                            N=N,
                            success=True,
                            p=min(candidate, q),
                            q=max(candidate, q),
                            duration_ms=duration_ms,
                            candidates_tested=candidates_tested,
                            candidates_passed_threshold=candidates_passed,
                            peak_amplitude=peak_amplitude
                        )
    
    duration_ms = int((time.time() - start_time) * 1000)
    return TestResult(
        config_name=config.name,
        N=N,
        success=False,
        duration_ms=duration_ms,
        candidates_tested=candidates_tested,
        candidates_passed_threshold=candidates_passed,
        peak_amplitude=peak_amplitude,
        error_message="No factors found within budget"
    )


def exp(x: float) -> float:
    """Exponential function using mpmath if available."""
    if mpmath:
        return float(mpmath.exp(x))
    return math.exp(x)


# ============================================================================
# Falsification Tests
# ============================================================================

def test_gate1_regression(config: ParameterConfig, verbose: bool = False) -> TestResult:
    """Test that parameters don't regress on Gate 1 (30-bit)."""
    if verbose:
        print(f"\n=== Gate 1 Regression Test: {config.name} ===")
    
    # Scale config for 30-bit
    scaled_config = ParameterConfig(
        name=config.name,
        samples=min(config.samples, 1000),  # Don't need as many for 30-bit
        m_span=min(config.m_span, 100),
        threshold=config.threshold,
        k_lo=config.k_lo,
        k_hi=config.k_hi,
        timeout_ms=60000,  # 1 minute max for 30-bit
        precision=320,
        description=f"{config.name} (scaled for 30-bit)"
    )
    
    result = geometric_resonance_search(GATE_1_N, scaled_config, verbose)
    
    if result.success:
        if result.p == GATE_1_P and result.q == GATE_1_Q:
            if verbose:
                print(f"✓ Gate 1 passed: found correct factors")
        else:
            result.success = False
            result.error_message = f"Wrong factors: {result.p} × {result.q}"
    
    return result


def test_gate2_regression(config: ParameterConfig, verbose: bool = False) -> TestResult:
    """Test that parameters don't regress on Gate 2 (60-bit)."""
    if verbose:
        print(f"\n=== Gate 2 Regression Test: {config.name} ===")
    
    # Scale config for 60-bit
    scaled_config = ParameterConfig(
        name=config.name,
        samples=min(config.samples, 5000),
        m_span=min(config.m_span, 300),
        threshold=config.threshold,
        k_lo=config.k_lo,
        k_hi=config.k_hi,
        timeout_ms=300000,  # 5 minutes max for 60-bit
        precision=440,
        description=f"{config.name} (scaled for 60-bit)"
    )
    
    result = geometric_resonance_search(GATE_2_N, scaled_config, verbose)
    
    if result.success:
        if result.p == GATE_2_P and result.q == GATE_2_Q:
            if verbose:
                print(f"✓ Gate 2 passed: found correct factors")
        else:
            result.success = False
            result.error_message = f"Wrong factors: {result.p} × {result.q}"
    
    return result


def test_127bit_challenge(config: ParameterConfig, verbose: bool = False) -> TestResult:
    """Test 127-bit challenge with given configuration."""
    if verbose:
        print(f"\n=== 127-bit Challenge Test: {config.name} ===")
        print(f"N = {CHALLENGE_127}")
        print(f"Parameters: samples={config.samples}, m_span={config.m_span}, threshold={config.threshold}")
        print(f"k-range: [{config.k_lo:.4f}, {config.k_hi:.4f}]")
        print(f"Timeout: {config.timeout_ms}ms ({config.timeout_ms/60000:.1f} min)")
    
    result = geometric_resonance_search(CHALLENGE_127, config, verbose)
    
    if result.success:
        if result.p == CHALLENGE_127_P and result.q == CHALLENGE_127_Q:
            if verbose:
                print(f"✓ 127-bit challenge passed: found correct factors in {result.duration_ms}ms")
        else:
            result.success = False
            result.error_message = f"Wrong factors: {result.p} × {result.q}"
    
    return result


def analyze_threshold_false_positives(config: ParameterConfig, verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze whether low threshold causes excessive false positives.
    Returns statistics on amplitude distribution and threshold pass rate.
    """
    if verbose:
        print(f"\n=== Threshold Analysis: {config.name} ===")
    
    sqrt_N = isqrt(CHALLENGE_127)
    J = 6
    two_pi = 2 * 3.141592653589793
    
    amplitudes = []
    passed_count = 0
    
    # Sample amplitudes across k and m space
    sample_size = min(1000, config.samples)
    phi_inv = (sqrt(5) - 1) / 2
    
    for i in range(sample_size):
        u = (i * phi_inv) % 1.0
        k = config.k_lo + u * (config.k_hi - config.k_lo)
        
        for dm in range(-10, 11):  # Sample subset of m-span
            m = dm
            if k > 0:
                theta = two_pi * m / k
            else:
                theta = 0
            
            amplitude = dirichlet_amplitude(theta, J)
            amplitudes.append(amplitude)
            
            if amplitude > config.threshold:
                passed_count += 1
    
    total_samples = len(amplitudes)
    pass_rate = passed_count / total_samples if total_samples > 0 else 0
    
    amplitudes.sort()
    min_amp = amplitudes[0] if amplitudes else 0
    max_amp = amplitudes[-1] if amplitudes else 0
    median_amp = amplitudes[len(amplitudes)//2] if amplitudes else 0
    mean_amp = sum(amplitudes) / len(amplitudes) if amplitudes else 0
    
    # Count how many are above various thresholds
    count_above_015 = sum(1 for a in amplitudes if a > 0.15)
    count_above_050 = sum(1 for a in amplitudes if a > 0.50)
    count_above_082 = sum(1 for a in amplitudes if a > 0.82)
    
    # Determine false positive risk based on pass rate
    if pass_rate > FALSE_POSITIVE_HIGH_THRESHOLD:
        fp_risk = "HIGH"
    elif pass_rate > FALSE_POSITIVE_MODERATE_THRESHOLD:
        fp_risk = "MODERATE"
    else:
        fp_risk = "LOW"
    
    result = {
        "config_name": config.name,
        "threshold": config.threshold,
        "total_samples": total_samples,
        "passed_count": passed_count,
        "pass_rate": pass_rate,
        "min_amplitude": min_amp,
        "max_amplitude": max_amp,
        "median_amplitude": median_amp,
        "mean_amplitude": mean_amp,
        "count_above_015": count_above_015,
        "count_above_050": count_above_050,
        "count_above_082": count_above_082,
        "false_positive_risk": fp_risk
    }
    
    if verbose:
        print(f"Total samples: {total_samples}")
        print(f"Passed threshold ({config.threshold}): {passed_count} ({pass_rate*100:.1f}%)")
        print(f"Amplitude range: [{min_amp:.4f}, {max_amp:.4f}]")
        print(f"Mean amplitude: {mean_amp:.4f}")
        print(f"False positive risk: {result['false_positive_risk']}")
    
    return result


# ============================================================================
# Main Falsification Entry Point
# ============================================================================

def run_falsification_tests(verbose: bool = True) -> Dict[str, Any]:
    """
    Run complete falsification test suite.
    
    Returns a dictionary with:
    - hypothesis_supported: bool
    - falsification_reasons: list of strings if falsified
    - test_results: dict of all test results
    """
    results = {
        "hypothesis_supported": False,
        "falsification_reasons": [],
        "test_results": {},
        "threshold_analysis": {},
        "summary": {}
    }
    
    # Get configurations
    defaults = get_scale_adaptive_defaults(CHALLENGE_127)
    proposed = get_proposed_params(CHALLENGE_127)
    ablations = get_ablation_configs(CHALLENGE_127)
    
    if verbose:
        print("=" * 70)
        print("PARAMETER OPTIMIZATION 127-BIT FALSIFICATION EXPERIMENT")
        print("=" * 70)
        print()
        print("Hypothesis: Proposed parameters improve 127-bit factorization")
        print()
        print("Control (Scale-Adaptive Defaults):")
        print(f"  samples={defaults.samples}, m_span={defaults.m_span}")
        print(f"  threshold={defaults.threshold:.4f}, k=[{defaults.k_lo:.4f}, {defaults.k_hi:.4f}]")
        print()
        print("Proposed Parameters:")
        print(f"  samples={proposed.samples}, m_span={proposed.m_span}")
        print(f"  threshold={proposed.threshold:.4f}, k=[{proposed.k_lo:.4f}, {proposed.k_hi:.4f}]")
        print()
    
    # Test 1: Gate 1 regression check
    if verbose:
        print("\n" + "=" * 70)
        print("TEST 1: Gate 1 (30-bit) Regression Check")
        print("=" * 70)
    
    gate1_defaults = test_gate1_regression(defaults, verbose)
    gate1_proposed = test_gate1_regression(proposed, verbose)
    
    results["test_results"]["gate1_defaults"] = gate1_defaults.to_dict()
    results["test_results"]["gate1_proposed"] = gate1_proposed.to_dict()
    
    if not gate1_proposed.success and gate1_defaults.success:
        results["falsification_reasons"].append(
            "Proposed parameters cause Gate 1 (30-bit) regression"
        )
    
    # Test 2: Gate 2 regression check
    if verbose:
        print("\n" + "=" * 70)
        print("TEST 2: Gate 2 (60-bit) Regression Check")
        print("=" * 70)
    
    gate2_defaults = test_gate2_regression(defaults, verbose)
    gate2_proposed = test_gate2_regression(proposed, verbose)
    
    results["test_results"]["gate2_defaults"] = gate2_defaults.to_dict()
    results["test_results"]["gate2_proposed"] = gate2_proposed.to_dict()
    
    if not gate2_proposed.success and gate2_defaults.success:
        results["falsification_reasons"].append(
            "Proposed parameters cause Gate 2 (60-bit) regression"
        )
    
    # Test 3: Threshold analysis
    if verbose:
        print("\n" + "=" * 70)
        print("TEST 3: Threshold False Positive Analysis")
        print("=" * 70)
    
    threshold_defaults = analyze_threshold_false_positives(defaults, verbose)
    threshold_proposed = analyze_threshold_false_positives(proposed, verbose)
    
    results["threshold_analysis"]["defaults"] = threshold_defaults
    results["threshold_analysis"]["proposed"] = threshold_proposed
    
    if threshold_proposed["false_positive_risk"] == "HIGH":
        results["falsification_reasons"].append(
            f"Lower threshold (0.15) causes high false positive risk: {threshold_proposed['pass_rate']*100:.1f}% pass rate"
        )
    
    # Test 4: 127-bit challenge (limited time for experiment)
    if verbose:
        print("\n" + "=" * 70)
        print("TEST 4: 127-bit Challenge (Limited Budget)")
        print("=" * 70)
        print("Note: Full 127-bit test requires longer runtime.")
        print("Running with reduced budget for comparison...")
    
    # Use reduced timeout for experiment (5 minutes each)
    experiment_timeout = 300000  # 5 minutes
    
    defaults_127 = ParameterConfig(
        name="defaults_127bit",
        samples=min(defaults.samples, 5000),
        m_span=min(defaults.m_span, 200),
        threshold=defaults.threshold,
        k_lo=defaults.k_lo,
        k_hi=defaults.k_hi,
        timeout_ms=experiment_timeout,
        precision=defaults.precision,
        description="Scale-adaptive defaults (reduced budget)"
    )
    
    proposed_127 = ParameterConfig(
        name="proposed_127bit",
        samples=min(proposed.samples, 5000),
        m_span=min(proposed.m_span, 200),
        threshold=proposed.threshold,
        k_lo=proposed.k_lo,
        k_hi=proposed.k_hi,
        timeout_ms=experiment_timeout,
        precision=proposed.precision,
        description="Proposed parameters (reduced budget)"
    )
    
    challenge_defaults = test_127bit_challenge(defaults_127, verbose)
    challenge_proposed = test_127bit_challenge(proposed_127, verbose)
    
    results["test_results"]["challenge_defaults"] = challenge_defaults.to_dict()
    results["test_results"]["challenge_proposed"] = challenge_proposed.to_dict()
    
    # Compare results
    if verbose:
        print("\n" + "=" * 70)
        print("COMPARISON SUMMARY")
        print("=" * 70)
    
    # Determine if hypothesis is supported
    proposed_better = False
    
    if challenge_proposed.success and not challenge_defaults.success:
        proposed_better = True
        if verbose:
            print("Proposed parameters found factors when defaults did not")
    elif challenge_proposed.success and challenge_defaults.success:
        if challenge_proposed.duration_ms < challenge_defaults.duration_ms:
            proposed_better = True
            if verbose:
                print(f"Proposed faster: {challenge_proposed.duration_ms}ms vs {challenge_defaults.duration_ms}ms")
    elif not challenge_proposed.success and not challenge_defaults.success:
        # Compare candidates tested - significantly more false positives indicates wasted effort
        if challenge_proposed.candidates_passed_threshold > challenge_defaults.candidates_passed_threshold * EXCESSIVE_FALSE_POSITIVE_MULTIPLIER:
            results["falsification_reasons"].append(
                "Lower threshold generates too many false candidates without finding factors"
            )
    
    # Final verdict
    if not results["falsification_reasons"] and proposed_better:
        results["hypothesis_supported"] = True
    
    results["summary"] = {
        "defaults_gate1_success": gate1_defaults.success,
        "proposed_gate1_success": gate1_proposed.success,
        "defaults_gate2_success": gate2_defaults.success,
        "proposed_gate2_success": gate2_proposed.success,
        "defaults_127bit_success": challenge_defaults.success,
        "proposed_127bit_success": challenge_proposed.success,
        "proposed_better_than_defaults": proposed_better,
        "falsification_count": len(results["falsification_reasons"])
    }
    
    return results


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    results = run_falsification_tests(verbose=verbose)
    
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    
    if results["hypothesis_supported"]:
        print("\n✓ HYPOTHESIS SUPPORTED")
        print("The proposed parameters show improvement over defaults.")
    else:
        print("\n✗ HYPOTHESIS FALSIFIED")
        print("\nReasons:")
        for reason in results["falsification_reasons"]:
            print(f"  - {reason}")
    
    # Save results
    output_path = os.path.join(os.path.dirname(__file__), "test_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")
