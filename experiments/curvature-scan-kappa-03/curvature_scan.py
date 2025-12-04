#!/usr/bin/env python3
"""
Narrow-Band Curvature Scan around κ ≈ 0.3
==========================================

High-resolution curvature sweep to test if Dirichlet-kernel peaks at κ ≈ 0.3
are stable and gateworthy before scaling to Gate-4.

Scan parameters:
- Center: κ₀ = 0.3000
- Half-width: Δκ = 0.0100 (scan 0.2900 → 0.3100)
- Resolution: δκ = 1e-5 (≈ 2,001 points)
- Dirichlet orders: J ∈ {257, 513, 1025}
- Sample count: M = 1e6 (or standard), fixed seed = 1729

Acceptance gates:
- Peak persistence: Same primary peak location κ* stays within ±3δκ when changing J
- Width: Primary peak FWHM ≤ 40δκ
- SNR: Peak amplitude at least 8× the local median absolute deviation
- Rank stability: Jaccard(top-100 at κ₀, top-100 at κ₀±5δκ) ≥ 0.75
- Skew test: On a skewed semiprime, still observe a primary peak within ±0.002 of κ₀

Validation gates:
- Gate 3 (127-bit challenge): N = 137524771864208156028430259349934309717
- Gate 4 (10^14 - 10^18): Operational range
"""

import mpmath as mp
from typing import List, Dict, Tuple, Optional, Set
import time
import json
import hashlib
import os
import platform
import sys
from datetime import datetime
from dataclasses import dataclass, asdict


# =============================================================================
# Validation Constants
# =============================================================================
CHALLENGE_127 = 137524771864208156028430259349934309717
EXPECTED_P = 10508623501177419659
EXPECTED_Q = 13086849276577416863

# Gate-3/near-balanced test case (127-bit)
GATE_3_N = CHALLENGE_127
GATE_3_P = EXPECTED_P
GATE_3_Q = EXPECTED_Q

# Operational range
RANGE_MIN = 10**14
RANGE_MAX = 10**18

# Numerical constants
KAPPA_EQUALITY_TOLERANCE = 1e-15  # Tolerance for kappa ≈ 1.0 or 0.0 comparisons


# =============================================================================
# Scan Configuration
# =============================================================================
@dataclass
class ScanConfig:
    """Configuration for the curvature scan."""
    # Target semiprime
    N: int
    
    # Curvature band
    kappa_center: float = 0.3000
    kappa_half_width: float = 0.0100
    kappa_resolution: float = 1e-5
    
    # Dirichlet orders
    J_values: Tuple[int, ...] = (257, 513, 1025)
    
    # Sampling
    sample_count: int = 100000  # Reduced from 1e6 for practical runtime
    seed: int = 1729
    
    # Top-K for rank stability
    top_K_values: Tuple[int, ...] = (10, 100, 1000)
    
    # Precision
    precision_dps: int = 0  # Will be computed adaptively
    
    def __post_init__(self):
        """Compute derived values."""
        if self.precision_dps == 0:
            self.precision_dps = adaptive_precision(self.N)
    
    def kappa_range(self) -> Tuple[float, float]:
        """Return (kappa_min, kappa_max)."""
        return (
            self.kappa_center - self.kappa_half_width,
            self.kappa_center + self.kappa_half_width
        )
    
    def num_kappa_points(self) -> int:
        """Number of kappa values to scan."""
        return int(2 * self.kappa_half_width / self.kappa_resolution) + 1
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary."""
        d = asdict(self)
        d['N'] = str(self.N)  # Handle large integers
        return d


# =============================================================================
# Precision Utilities
# =============================================================================
def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision: max(50, N.bitLength() × 4 + 200).
    
    For 127-bit N: 127 * 4 + 200 = 708 dps
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


# =============================================================================
# Sobol Sequence Generator (Quasi-random sampling)
# =============================================================================
class SobolSequence:
    """
    Simple Sobol sequence generator for quasi-random sampling.
    Uses direction numbers for 1D sequence generation.
    """
    
    def __init__(self, seed: int = 1729):
        """Initialize with seed for reproducibility."""
        self.seed = seed
        # Direction numbers for dimension 1 (primitive polynomial x + 1)
        self.direction_numbers = [1 << (31 - i) for i in range(32)]
        self.index = seed % (2**20)  # Start index based on seed
    
    def next(self) -> float:
        """Generate next quasi-random value in [0, 1)."""
        self.index += 1
        result = 0
        i = self.index
        for j in range(32):
            if i & 1:
                result ^= self.direction_numbers[j]
            i >>= 1
            if i == 0:
                break
        return result / (2**32)
    
    def generate(self, n: int) -> List[float]:
        """Generate n quasi-random values."""
        return [self.next() for _ in range(n)]


# =============================================================================
# Dirichlet Kernel Implementation
# =============================================================================
def dirichlet_kernel(omega: mp.mpf, J: int) -> mp.mpf:
    """
    Compute Dirichlet kernel amplitude.
    
    D_J(ω) = sin((2J+1)ω/2) / ((2J+1)sin(ω/2))
    
    Normalized to [0, 1] with peak at ω = 0.
    
    Args:
        omega: Angular frequency
        J: Kernel order (half-width)
        
    Returns:
        Normalized amplitude in [0, 1]
    """
    two_j_plus_1 = 2 * J + 1
    half_omega = omega / 2
    
    sin_half = mp.sin(half_omega)
    
    # Singularity guard at ω ≈ 0
    # Use 10 decimal places margin from machine precision for numerical stability
    SINGULARITY_MARGIN = 10
    eps = mp.mpf(10) ** (-mp.mp.dps + SINGULARITY_MARGIN)
    if abs(sin_half) < eps:
        return mp.mpf(1)
    
    numerator = mp.sin(half_omega * two_j_plus_1)
    denominator = sin_half * two_j_plus_1
    
    return abs(numerator / denominator)


def hamming_window(n: int, N: int) -> float:
    """
    Hamming window function for sidelobe reduction.
    
    w(n) = 0.54 - 0.46 * cos(2πn / (N-1))
    
    Args:
        n: Sample index [0, N-1]
        N: Total samples
        
    Returns:
        Window weight in [0.08, 1.0]
    """
    import math
    if N <= 1:
        return 1.0
    return 0.54 - 0.46 * math.cos(2 * math.pi * n / (N - 1))


# =============================================================================
# Geometric Signal Construction
# =============================================================================
def embed_torus_geodesic(n: int, kappa: float, dimensions: int = 7) -> List[mp.mpf]:
    """
    Embed integer n into a 7D torus using golden ratio geodesic mapping.
    
    The embedding uses powers of the golden ratio φ for quasi-periodic structure.
    The curvature parameter κ (kappa) warps the density distribution.
    
    Args:
        n: Integer to embed
        kappa: Curvature parameter (geodesic exponent)
        dimensions: Torus dimensions (default 7)
        
    Returns:
        List of coordinates in [0,1)^7
    """
    phi = mp.mpf(1 + mp.sqrt(5)) / 2  # Golden ratio
    
    coords = []
    for d in range(dimensions):
        phi_power = phi ** (d + 1)
        coord = mp.fmod(n * phi_power, 1)
        
        # Apply curvature warping (skip for kappa near 1.0 or 0.0 to avoid degeneracy)
        if abs(kappa - 1.0) > KAPPA_EQUALITY_TOLERANCE and abs(kappa) > KAPPA_EQUALITY_TOLERANCE and coord > 0:
            coord = mp.power(coord, kappa)
            coord = mp.fmod(coord, 1)
        
        coords.append(coord)
    
    return coords


def riemannian_distance(p1: List[mp.mpf], p2: List[mp.mpf]) -> mp.mpf:
    """
    Compute Riemannian geodesic distance on flat torus.
    
    Distance accounts for periodic wrapping: d(x,y) = min(|x-y|, 1-|x-y|)
    
    Args:
        p1: First point coordinates
        p2: Second point coordinates
        
    Returns:
        Geodesic distance
    """
    dist_sq = mp.mpf(0)
    for c1, c2 in zip(p1, p2):
        diff = abs(c1 - c2)
        torus_diff = min(diff, mp.mpf(1) - diff)
        dist_sq += torus_diff ** 2
    return mp.sqrt(dist_sq)


def build_geometric_signal(
    N: int, 
    kappa: float, 
    sample_indices: List[int],
    N_coords: List[mp.mpf]
) -> List[Tuple[int, mp.mpf]]:
    """
    Build geometric signal s_κ(m) for a set of candidate samples.
    
    s_κ(m) = 1 / (1 + distance(N, m))
    
    Higher values indicate candidates closer to N in torus embedding.
    
    Args:
        N: Target semiprime
        kappa: Curvature parameter
        sample_indices: List of candidate integers to evaluate
        N_coords: Pre-computed embedding of N
        
    Returns:
        List of (sample_index, signal_value) pairs
    """
    signals = []
    
    for m in sample_indices:
        m_coords = embed_torus_geodesic(m, kappa)
        dist = riemannian_distance(N_coords, m_coords)
        signal = mp.mpf(1) / (mp.mpf(1) + dist)
        signals.append((m, signal))
    
    return signals


# =============================================================================
# Amplitude and Peak Analysis
# =============================================================================
@dataclass
class PeakInfo:
    """Information about a detected peak."""
    kappa: float
    amplitude: float
    peak_freq: float
    fwhm: float
    snr: float
    J: int


def compute_dirichlet_amplitude(
    signals: List[Tuple[int, mp.mpf]], 
    J: int,
    apply_hamming: bool = False
) -> Tuple[mp.mpf, float]:
    """
    Compute maximum Dirichlet amplitude from geometric signal.
    
    A(κ) = max_ω |D_J(ω; s_κ)|
    
    Optimized: Uses sparse frequency sampling (32 frequencies) instead of 
    J*2 frequencies to reduce computation time while preserving peak detection.
    
    Args:
        signals: List of (index, signal_value) pairs
        J: Dirichlet kernel order
        apply_hamming: Apply Hamming window for sidelobe reduction
        
    Returns:
        Tuple of (max_amplitude, peak_frequency)
    """
    if not signals:
        return mp.mpf(0), 0.0
    
    N_signals = len(signals)
    
    # Apply optional Hamming window
    if apply_hamming:
        weighted_signals = [
            (idx, sig * hamming_window(i, N_signals)) 
            for i, (idx, sig) in enumerate(signals)
        ]
    else:
        weighted_signals = signals
    
    # Compute Dirichlet response at sparse frequencies (optimization)
    # Use 32 frequency samples instead of J*2 for efficiency
    max_amp = mp.mpf(0)
    peak_freq = 0.0
    
    # Sparse frequency sampling for efficiency
    num_freq_samples = min(32, N_signals)
    
    for f_idx in range(num_freq_samples):
        omega = mp.mpf(2 * mp.pi * f_idx) / num_freq_samples
        
        # Compute DFT-like sum weighted by Dirichlet kernel
        kernel_amp = dirichlet_kernel(omega, J)
        
        # Modulate signals by frequency
        real_sum = mp.mpf(0)
        imag_sum = mp.mpf(0)
        
        for i, (_, sig) in enumerate(weighted_signals):
            phase = omega * i
            real_sum += sig * mp.cos(phase)
            imag_sum += sig * mp.sin(phase)
        
        total_amp = mp.sqrt(real_sum**2 + imag_sum**2) * kernel_amp / N_signals
        
        if total_amp > max_amp:
            max_amp = total_amp
            peak_freq = float(omega)
    
    return max_amp, peak_freq


def compute_fwhm(amplitudes: List[float], kappa_values: List[float], peak_idx: int) -> float:
    """
    Compute Full Width at Half Maximum (FWHM) of a peak.
    
    Args:
        amplitudes: List of amplitude values
        kappa_values: Corresponding kappa values
        peak_idx: Index of the peak
        
    Returns:
        FWHM in kappa units
    """
    if peak_idx < 0 or peak_idx >= len(amplitudes):
        return 0.0
    
    peak_amp = amplitudes[peak_idx]
    half_max = peak_amp / 2
    
    # Find left edge
    left_idx = peak_idx
    while left_idx > 0 and amplitudes[left_idx] > half_max:
        left_idx -= 1
    
    # Find right edge
    right_idx = peak_idx
    while right_idx < len(amplitudes) - 1 and amplitudes[right_idx] > half_max:
        right_idx += 1
    
    if left_idx >= len(kappa_values) or right_idx >= len(kappa_values):
        return 0.0
    
    return kappa_values[right_idx] - kappa_values[left_idx]


def compute_snr(amplitude: float, amplitudes: List[float]) -> float:
    """
    Compute Signal-to-Noise Ratio using Median Absolute Deviation.
    
    SNR = peak_amplitude / (1.4826 * MAD)
    
    Args:
        amplitude: Peak amplitude
        amplitudes: All amplitude values
        
    Returns:
        SNR value
    """
    if not amplitudes:
        return 0.0
    
    median = sorted(amplitudes)[len(amplitudes) // 2]
    deviations = [abs(a - median) for a in amplitudes]
    mad = sorted(deviations)[len(deviations) // 2]
    
    # 1.4826 is the consistency constant for normal distribution
    if mad == 0:
        return float('inf') if amplitude > 0 else 0.0
    
    return amplitude / (1.4826 * mad)


def find_peaks(amplitudes: List[float], kappa_values: List[float]) -> List[int]:
    """
    Find local maxima in amplitude array.
    
    Args:
        amplitudes: List of amplitude values
        kappa_values: Corresponding kappa values
        
    Returns:
        List of indices of local maxima
    """
    peaks = []
    
    for i in range(1, len(amplitudes) - 1):
        if amplitudes[i] > amplitudes[i-1] and amplitudes[i] > amplitudes[i+1]:
            peaks.append(i)
    
    return peaks


# =============================================================================
# Rank Stability Analysis
# =============================================================================
def jaccard_index(set1: Set[int], set2: Set[int]) -> float:
    """
    Compute Jaccard similarity index between two sets.
    
    J(A, B) = |A ∩ B| / |A ∪ B|
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        Jaccard index in [0, 1]
    """
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def compute_top_k_hash(signals: List[Tuple[int, mp.mpf]], K: int) -> str:
    """
    Compute hash of top-K candidate indices for reproducibility verification.
    
    Args:
        signals: List of (index, signal_value) pairs
        K: Number of top candidates
        
    Returns:
        SHA-256 hash of top-K indices
    """
    sorted_signals = sorted(signals, key=lambda x: float(x[1]), reverse=True)
    top_k_indices = [idx for idx, _ in sorted_signals[:K]]
    
    indices_str = ','.join(map(str, top_k_indices))
    return hashlib.sha256(indices_str.encode()).hexdigest()[:16]


def get_top_k_set(signals: List[Tuple[int, mp.mpf]], K: int) -> Set[int]:
    """
    Get set of top-K candidate indices.
    
    Args:
        signals: List of (index, signal_value) pairs
        K: Number of top candidates
        
    Returns:
        Set of top-K indices
    """
    sorted_signals = sorted(signals, key=lambda x: float(x[1]), reverse=True)
    return {idx for idx, _ in sorted_signals[:K]}


# =============================================================================
# Main Scan Functions
# =============================================================================
def generate_candidate_lattice(
    N: int, 
    sample_count: int, 
    seed: int
) -> Tuple[List[int], str]:
    """
    Generate deterministic candidate lattice using Sobol sequence.
    
    Candidates are distributed around sqrt(N) using quasi-random sampling.
    
    Args:
        N: Target semiprime
        sample_count: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (candidate_indices, lattice_hash)
    """
    sqrt_N = int(mp.sqrt(N))
    
    # Use Sobol sequence for quasi-random sampling
    sobol = SobolSequence(seed)
    
    # Generate candidates in a window around sqrt(N)
    # Window size scales with sqrt(N) magnitude
    window_size = max(10000, sqrt_N // 10000)
    
    candidates = []
    seen = set()
    
    for _ in range(sample_count):
        # Map quasi-random value to candidate position
        u = sobol.next()
        offset = int((2 * u - 1) * window_size)
        candidate = sqrt_N + offset
        
        # Skip invalid or duplicate candidates
        # Note: candidate < N is correct since any factor must be < N
        # For skewed semiprimes, the larger factor may be outside the window
        if candidate <= 1 or candidate >= N or candidate in seen:
            continue
        
        # Skip even candidates for odd N
        if N % 2 == 1 and candidate % 2 == 0:
            continue
        
        candidates.append(candidate)
        seen.add(candidate)
    
    # Compute hash for verification
    candidates_str = ','.join(map(str, sorted(candidates)))
    lattice_hash = hashlib.sha256(candidates_str.encode()).hexdigest()[:16]
    
    return candidates, lattice_hash


def run_kappa_scan(
    config: ScanConfig,
    verbose: bool = True
) -> Dict:
    """
    Run the curvature scan across the specified kappa range.
    
    Args:
        config: Scan configuration
        verbose: Enable detailed logging
        
    Returns:
        Dictionary with scan results
    """
    start_time = time.time()
    
    # Set precision
    mp.mp.dps = config.precision_dps
    
    N = config.N
    sqrt_N = int(mp.sqrt(N))
    
    if verbose:
        print("=" * 70)
        print("Narrow-Band Curvature Scan around κ ≈ 0.3")
        print("=" * 70)
        print(f"N = {N}")
        print(f"sqrt(N) = {sqrt_N:,}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Precision: {config.precision_dps} dps")
        print(f"Kappa range: [{config.kappa_center - config.kappa_half_width:.4f}, "
              f"{config.kappa_center + config.kappa_half_width:.4f}]")
        print(f"Kappa resolution: {config.kappa_resolution}")
        print(f"Kappa points: {config.num_kappa_points()}")
        print(f"Dirichlet orders (J): {config.J_values}")
        print(f"Sample count: {config.sample_count}")
        print(f"Seed: {config.seed}")
        print()
    
    # Generate candidate lattice (same for all kappa values)
    if verbose:
        print("Generating candidate lattice...")
    
    candidates, lattice_hash = generate_candidate_lattice(
        N, config.sample_count, config.seed
    )
    
    if verbose:
        print(f"  Generated {len(candidates)} candidates")
        print(f"  Lattice hash: {lattice_hash}")
        print()
    
    # Initialize results
    results = {
        'config': config.to_dict(),
        'lattice_hash': lattice_hash,
        'candidates_count': len(candidates),
        'per_J_results': {},
        'kappa_values': [],
        'raw_amplitudes': {},
        'tapered_amplitudes': {},
        'peak_analysis': {},
        'rank_stability': {},
    }
    
    # Generate kappa values
    kappa_min, kappa_max = config.kappa_range()
    num_points = config.num_kappa_points()
    kappa_values = [kappa_min + i * config.kappa_resolution for i in range(num_points)]
    results['kappa_values'] = kappa_values
    
    # Scan each J value
    for J in config.J_values:
        if verbose:
            print(f"Scanning J = {J}...")
        
        J_results = {
            'amplitudes': [],
            'peak_freqs': [],
            'tapered_amplitudes': [],
            'top_K_hashes': {K: [] for K in config.top_K_values},
            'top_K_sets': {K: [] for K in config.top_K_values},
        }
        
        J_start = time.time()
        
        for i, kappa in enumerate(kappa_values):
            # Embed N for this kappa
            N_coords = embed_torus_geodesic(N, kappa)
            
            # Build geometric signal
            signals = build_geometric_signal(N, kappa, candidates, N_coords)
            
            # Compute raw amplitude
            amp_raw, peak_freq = compute_dirichlet_amplitude(signals, J, apply_hamming=False)
            J_results['amplitudes'].append(float(amp_raw))
            J_results['peak_freqs'].append(peak_freq)
            
            # Compute tapered amplitude
            amp_tapered, _ = compute_dirichlet_amplitude(signals, J, apply_hamming=True)
            J_results['tapered_amplitudes'].append(float(amp_tapered))
            
            # Compute top-K for rank stability
            for K in config.top_K_values:
                top_k_hash = compute_top_k_hash(signals, K)
                J_results['top_K_hashes'][K].append(top_k_hash)
                J_results['top_K_sets'][K].append(get_top_k_set(signals, K))
            
            # Progress logging
            if verbose and (i + 1) % 100 == 0:
                elapsed = time.time() - J_start
                rate = (i + 1) / elapsed
                print(f"    κ = {kappa:.5f} ({i+1}/{num_points}), rate: {rate:.1f} pts/s")
        
        J_elapsed = time.time() - J_start
        
        # Find peaks
        peaks_idx = find_peaks(J_results['amplitudes'], kappa_values)
        
        # Analyze primary peak
        if peaks_idx:
            primary_idx = max(peaks_idx, key=lambda i: J_results['amplitudes'][i])
            primary_kappa = kappa_values[primary_idx]
            primary_amp = J_results['amplitudes'][primary_idx]
            primary_fwhm = compute_fwhm(J_results['amplitudes'], kappa_values, primary_idx)
            primary_snr = compute_snr(primary_amp, J_results['amplitudes'])
            
            J_results['primary_peak'] = {
                'kappa': primary_kappa,
                'amplitude': primary_amp,
                'index': primary_idx,
                'fwhm': primary_fwhm,
                'snr': primary_snr,
            }
        else:
            J_results['primary_peak'] = None
        
        J_results['peaks_count'] = len(peaks_idx)
        J_results['elapsed_seconds'] = J_elapsed
        
        results['per_J_results'][J] = J_results
        
        if verbose:
            print(f"    Completed in {J_elapsed:.1f}s, {len(peaks_idx)} peaks found")
            if J_results['primary_peak']:
                pp = J_results['primary_peak']
                print(f"    Primary peak: κ* = {pp['kappa']:.5f}, A = {pp['amplitude']:.6f}, "
                      f"FWHM = {pp['fwhm']:.6f}, SNR = {pp['snr']:.2f}")
            print()
    
    # Compute rank stability (Jaccard indices)
    if verbose:
        print("Computing rank stability metrics...")
    
    center_idx = num_points // 2
    delta_5 = 5  # ±5δκ offset for stability comparison
    
    for K in config.top_K_values:
        stability = {}
        
        # Get center top-K set from first J value
        J_base = config.J_values[0]
        if center_idx < len(results['per_J_results'][J_base]['top_K_sets'][K]):
            center_set = results['per_J_results'][J_base]['top_K_sets'][K][center_idx]
            
            # Compute Jaccard vs κ₀±5δκ
            left_idx = max(0, center_idx - delta_5)
            right_idx = min(num_points - 1, center_idx + delta_5)
            
            left_set = results['per_J_results'][J_base]['top_K_sets'][K][left_idx]
            right_set = results['per_J_results'][J_base]['top_K_sets'][K][right_idx]
            
            stability['jaccard_left'] = jaccard_index(center_set, left_set)
            stability['jaccard_right'] = jaccard_index(center_set, right_set)
            stability['jaccard_mean'] = (stability['jaccard_left'] + stability['jaccard_right']) / 2
        else:
            stability['jaccard_left'] = 0.0
            stability['jaccard_right'] = 0.0
            stability['jaccard_mean'] = 0.0
        
        results['rank_stability'][K] = stability
    
    if verbose:
        for K, stab in results['rank_stability'].items():
            print(f"  K={K}: Jaccard mean = {stab['jaccard_mean']:.4f}")
    
    # Check acceptance gates
    if verbose:
        print("\nChecking acceptance gates...")
    
    gates = check_acceptance_gates(results, config)
    results['acceptance_gates'] = gates
    
    if verbose:
        for gate_name, gate_result in gates.items():
            status = "✓ PASS" if gate_result['passed'] else "✗ FAIL"
            print(f"  {gate_name}: {status} - {gate_result.get('message', '')}")
    
    elapsed_total = time.time() - start_time
    results['elapsed_seconds'] = elapsed_total
    
    if verbose:
        print(f"\nTotal elapsed time: {elapsed_total:.1f}s")
    
    return results


def check_acceptance_gates(results: Dict, config: ScanConfig) -> Dict:
    """
    Check all acceptance gates.
    
    Args:
        results: Scan results dictionary
        config: Scan configuration
        
    Returns:
        Dictionary of gate results
    """
    gates = {}
    delta_kappa = config.kappa_resolution
    
    # Gate 1: Peak persistence across J values
    primary_peaks = []
    for J in config.J_values:
        peak = results['per_J_results'][J].get('primary_peak')
        if peak:
            primary_peaks.append((J, peak['kappa']))
    
    if len(primary_peaks) >= 2:
        kappas = [k for _, k in primary_peaks]
        max_diff = max(kappas) - min(kappas)
        threshold = 3 * delta_kappa
        passed = max_diff <= threshold
        gates['peak_persistence'] = {
            'passed': passed,
            'max_diff': max_diff,
            'threshold': threshold,
            'message': f"max Δκ* = {max_diff:.6f} (threshold: ≤{threshold:.6f})"
        }
    else:
        gates['peak_persistence'] = {
            'passed': False,
            'message': "Not enough peaks found across J values"
        }
    
    # Gate 2: FWHM ≤ 40δκ
    # Use middle J value, or first if only one
    J_base = config.J_values[len(config.J_values) // 2] if len(config.J_values) > 1 else config.J_values[0]
    peak = results['per_J_results'][J_base].get('primary_peak')
    if peak:
        fwhm = peak['fwhm']
        threshold = 40 * delta_kappa
        passed = fwhm <= threshold
        gates['fwhm_width'] = {
            'passed': passed,
            'fwhm': fwhm,
            'threshold': threshold,
            'message': f"FWHM = {fwhm:.6f} (threshold: ≤{threshold:.6f})"
        }
    else:
        gates['fwhm_width'] = {
            'passed': False,
            'message': "No primary peak found"
        }
    
    # Gate 3: SNR ≥ 8
    if peak:
        snr = peak['snr']
        passed = snr >= 8.0
        gates['snr'] = {
            'passed': passed,
            'snr': snr,
            'threshold': 8.0,
            'message': f"SNR = {snr:.2f} (threshold: ≥8.0)"
        }
    else:
        gates['snr'] = {
            'passed': False,
            'message': "No primary peak found"
        }
    
    # Gate 4: Rank stability (Jaccard ≥ 0.75 for K=100, or highest available K)
    # Prefer K=100, but fall back to largest available K if 100 not in config
    if 100 in config.top_K_values:
        K = 100
    else:
        K = max(config.top_K_values) if config.top_K_values else 0
    
    if K > 0 and K in results['rank_stability']:
        jaccard_mean = results['rank_stability'][K]['jaccard_mean']
        passed = jaccard_mean >= 0.75
        gates['rank_stability'] = {
            'passed': passed,
            'jaccard_mean': jaccard_mean,
            'K': K,
            'threshold': 0.75,
            'message': f"Jaccard(top-{K}) = {jaccard_mean:.4f} (threshold: ≥0.75)"
        }
    else:
        gates['rank_stability'] = {
            'passed': False,
            'message': "Rank stability not computed"
        }
    
    return gates


def run_skew_test(config: ScanConfig, verbose: bool = True) -> Dict:
    """
    Run skew test on an unbalanced semiprime.
    
    Args:
        config: Scan configuration (N will be replaced)
        verbose: Enable logging
        
    Returns:
        Dictionary with skew test results
    """
    # Use a skewed semiprime of similar scale
    # For 127-bit challenge, we can create a test case with more imbalanced factors
    # Using a synthetic semiprime in the 10^14-10^18 range
    
    # Example: p ≈ 10^9, q ≈ 10^8 gives N ≈ 10^17
    skew_p = 1000000007  # ~10^9
    skew_q = 100000007   # ~10^8
    skew_N = skew_p * skew_q
    
    if verbose:
        print("=" * 70)
        print("Skew Test: Running on unbalanced semiprime")
        print("=" * 70)
        print(f"N = {skew_N}")
        print(f"p = {skew_p}")
        print(f"q = {skew_q}")
        print(f"p/q ratio = {skew_p/skew_q:.2f}")
        print()
    
    # Create modified config
    skew_config = ScanConfig(
        N=skew_N,
        kappa_center=config.kappa_center,
        kappa_half_width=config.kappa_half_width,
        kappa_resolution=config.kappa_resolution,
        J_values=config.J_values,
        sample_count=config.sample_count // 10,  # Reduced for speed
        seed=config.seed,
        top_K_values=config.top_K_values,
    )
    
    # Run scan
    skew_results = run_kappa_scan(skew_config, verbose=verbose)
    
    # Check if primary peak is within ±0.002 of κ₀
    # Use middle J value from skew_config, or first if only one
    J_base = skew_config.J_values[len(skew_config.J_values) // 2] if len(skew_config.J_values) > 1 else skew_config.J_values[0]
    peak = skew_results['per_J_results'][J_base].get('primary_peak')
    
    if peak:
        kappa_diff = abs(peak['kappa'] - config.kappa_center)
        passed = kappa_diff <= 0.002
        
        skew_results['skew_gate'] = {
            'passed': passed,
            'kappa_diff': kappa_diff,
            'threshold': 0.002,
            'message': f"Δκ = {kappa_diff:.6f} (threshold: ≤0.002)"
        }
    else:
        skew_results['skew_gate'] = {
            'passed': False,
            'message': "No primary peak found in skew test"
        }
    
    return skew_results


# =============================================================================
# Output Functions
# =============================================================================
def save_results(results: Dict, output_dir: str):
    """
    Save all results and artifacts.
    
    Args:
        results: Scan results dictionary
        output_dir: Output directory path
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Save config
    config_path = os.path.join(output_dir, 'scan_config.json')
    with open(config_path, 'w') as f:
        json.dump(results['config'], f, indent=2)
    
    # Save main results CSV
    csv_path = os.path.join(output_dir, 'curvature_scan.csv')
    with open(csv_path, 'w') as f:
        # Header
        headers = ['kappa', 'J', 'amplitude', 'peak_freq', 'fwhm', 'snr', 'topK_hash']
        f.write(','.join(headers) + '\n')
        
        # Data rows
        kappa_values = results['kappa_values']
        for J, J_results in results['per_J_results'].items():
            for i, kappa in enumerate(kappa_values):
                # Check array bounds before access
                if i >= len(J_results['amplitudes']) or i >= len(J_results['peak_freqs']):
                    continue
                    
                # Get top-K hash if available (use K=100 if present, else first available K)
                topk_hash = ""
                if 100 in J_results['top_K_hashes']:
                    if i < len(J_results['top_K_hashes'][100]):
                        topk_hash = J_results['top_K_hashes'][100][i]
                elif J_results['top_K_hashes']:
                    first_K = list(J_results['top_K_hashes'].keys())[0]
                    if i < len(J_results['top_K_hashes'][first_K]):
                        topk_hash = J_results['top_K_hashes'][first_K][i]
                
                row = [
                    f"{kappa:.6f}",
                    str(J),
                    f"{J_results['amplitudes'][i]:.8f}",
                    f"{J_results['peak_freqs'][i]:.6f}",
                    "",  # FWHM is per-peak, not per-point
                    "",  # SNR is per-peak
                    topk_hash
                ]
                f.write(','.join(row) + '\n')
    
    # Save top-K JSON files
    topk_dir = os.path.join(output_dir, 'topK')
    os.makedirs(topk_dir, exist_ok=True)
    
    J_base = list(results['per_J_results'].keys())[0]
    for K in results['config'].get('top_K_values', [10, 100, 1000]):
        for i, kappa in enumerate(results['kappa_values'][:10]):  # First 10 for brevity
            if K in results['per_J_results'][J_base]['top_K_sets']:
                top_k_sets = results['per_J_results'][J_base]['top_K_sets'][K]
                if i < len(top_k_sets):
                    top_k_set = top_k_sets[i]
                    topk_path = os.path.join(topk_dir, f'kappa_{kappa:.5f}_K{K}.json')
                    with open(topk_path, 'w') as f:
                        json.dump({'kappa': kappa, 'K': K, 'indices': list(top_k_set)}, f)
    
    # Save environment info
    env_path = os.path.join(output_dir, 'env.txt')
    with open(env_path, 'w') as f:
        f.write(f"Python version: {sys.version}\n")
        f.write(f"Platform: {platform.platform()}\n")
        f.write(f"CPU: {platform.processor()}\n")
        f.write(f"mpmath version: {mp.__version__}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Save log
    log_path = os.path.join(output_dir, 'log.txt')
    with open(log_path, 'w') as f:
        f.write(f"Curvature Scan Log\n")
        f.write(f"==================\n\n")
        f.write(f"Start time: {datetime.now().isoformat()}\n")
        f.write(f"N: {results['config']['N']}\n")
        f.write(f"Lattice hash: {results['lattice_hash']}\n")
        f.write(f"Candidates: {results['candidates_count']}\n")
        f.write(f"Total elapsed: {results['elapsed_seconds']:.1f}s\n\n")
        f.write("Acceptance Gates:\n")
        for gate_name, gate_result in results.get('acceptance_gates', {}).items():
            status = "PASS" if gate_result['passed'] else "FAIL"
            f.write(f"  {gate_name}: {status} - {gate_result.get('message', '')}\n")
    
    # Save full results JSON
    results_path = os.path.join(output_dir, 'results.json')
    
    # Convert sets to lists for JSON serialization
    results_json = json.loads(json.dumps(results, default=lambda x: list(x) if isinstance(x, set) else str(x)))
    
    with open(results_path, 'w') as f:
        json.dump(results_json, f, indent=2)


# =============================================================================
# Main Entry Point
# =============================================================================
def main():
    """Main entry point for the curvature scan experiment."""
    print("=" * 70)
    print("Narrow-Band Curvature Scan around κ ≈ 0.3")
    print("Testing Dirichlet-kernel peak stability for Gate-4 scaling")
    print("=" * 70)
    print()
    
    # Use Gate-3 challenge as primary target
    config = ScanConfig(
        N=GATE_3_N,
        kappa_center=0.3000,
        kappa_half_width=0.0100,
        kappa_resolution=5e-5,  # Start with coarser resolution for practical runtime
        J_values=(257, 513, 1025),
        sample_count=50000,  # Reduced for practical runtime
        seed=1729,
        top_K_values=(10, 100, 1000),
    )
    
    print("Phase 1: Primary scan on Gate-3 (127-bit challenge)")
    print("-" * 70)
    results = run_kappa_scan(config, verbose=True)
    
    # Save results
    output_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(output_dir, 'results')
    save_results(results, results_dir)
    print(f"\nResults saved to: {results_dir}")
    
    # Run skew test
    print("\n")
    print("Phase 2: Skew test on unbalanced semiprime")
    print("-" * 70)
    skew_results = run_skew_test(config, verbose=True)
    
    # Save skew results
    skew_dir = os.path.join(output_dir, 'results_skew')
    save_results(skew_results, skew_dir)
    print(f"\nSkew results saved to: {skew_dir}")
    
    # Print summary
    print("\n")
    print("=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)
    
    all_gates_passed = all(
        g['passed'] for g in results.get('acceptance_gates', {}).values()
    )
    
    print("\nPrimary Scan (Gate-3):")
    for gate_name, gate_result in results.get('acceptance_gates', {}).items():
        status = "✓ PASS" if gate_result['passed'] else "✗ FAIL"
        print(f"  {gate_name}: {status}")
    
    print("\nSkew Test:")
    if 'skew_gate' in skew_results:
        status = "✓ PASS" if skew_results['skew_gate']['passed'] else "✗ FAIL"
        print(f"  skew_test: {status} - {skew_results['skew_gate'].get('message', '')}")
    
    print("\n" + "=" * 70)
    if all_gates_passed:
        print("VERDICT: SCALE TO GATE-4")
        print("All acceptance gates passed. Proceed with Gate-4 validation.")
    else:
        print("VERDICT: HOLD")
        print("Not all acceptance gates passed. Further investigation needed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
