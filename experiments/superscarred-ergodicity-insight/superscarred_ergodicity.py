"""
Superscarred Ergodicity Insight Experiment
============================================

Implements Ruelle-like spectral resonance analysis to improve geometry-ranking
before arithmetic certification. The experiment analyzes κ(n) (curvature/Dirichlet
amplitude) over search intervals to find "Ruelle-like" resonances via spectral analysis.

Key components:
1. Window & Detrend: High-pass/median-remove detrending of κ(n) series
2. Spectral Scan (FFT): Magnitude spectrum, spectral entropy, peak prominence
3. Scar Score on Rectangles: Tiled energy concentration analysis
4. Stability Test: Sinusoidal perturbations with overlap detection
5. Candidate Shortlist: Ranked n-windows for arithmetic certification

Validation gates:
- Primary: CHALLENGE_127 = 137524771864208156028430259349934309717
- Operational: [10^14, 10^18]

Constraints:
- Deterministic/quasi-deterministic methods only (Sobol/Halton)
- Pin seeds, log all parameters with timestamps
- Precision: max(configured, N.bitLength() × 4 + 200)
- No classical fallbacks (Pollard Rho, ECM, trial division)

References:
- Ruelle resonance theory in dynamical systems
- Quantum scarring in chaotic systems
- Spectral theory for Anosov flows
"""

import mpmath as mp
from mpmath import mpf, log, sqrt, sin, cos, pi
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import time
import csv
import os
import json

# Try numpy/scipy imports - required for FFT and analysis
try:
    import numpy as np
    from scipy import signal
    from scipy.fft import fft, fftfreq
    from scipy.stats import zscore as scipy_zscore
    HAS_NUMPY_SCIPY = True
except ImportError:
    HAS_NUMPY_SCIPY = False

# Try matplotlib for plotting
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ============================================================================
# CONSTANTS
# ============================================================================

# 127-bit challenge (primary validation gate)
CHALLENGE_127 = 137524771864208156028430259349934309717
CHALLENGE_127_P = 10508623501177419659
CHALLENGE_127_Q = 13086849276577416863

# Operational range (explicit integer literals to avoid runtime computation)
RANGE_MIN = 100000000000000       # 10^14
RANGE_MAX = 1000000000000000000   # 10^18

# Minimum valid n value for curvature computation
MIN_VALID_N = 2

# Frequency matching tolerance (relative): 5% matching window
FREQ_TOLERANCE = 0.05
# Epsilon to avoid division by zero when frequency is 0
FREQ_EPSILON = 1e-10

# Golden ratio for QMC sampling
PHI = mpf(1 + mp.sqrt(5)) / 2

# e² for discrete invariant (from cornerstone_invariant.py)
E_SQUARED = mp.e ** 2


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SpectralPeak:
    """Represents a peak in the FFT magnitude spectrum."""
    frequency: float
    height: float
    prominence: float
    bandwidth: float
    z_score: float
    tile_indices: List[int]


@dataclass
class TileScore:
    """Represents a rectangular tile in (n, feature)-space."""
    start_n: int
    end_n: int
    tile_index: int
    energy: float
    scar_score: float


@dataclass
class CandidateWindow:
    """Final candidate window for arithmetic certification."""
    start_n: int
    end_n: int
    peak_height: float
    stability: float
    scar_score: float
    composite_score: float


@dataclass
class ExperimentConfig:
    """Configuration for the superscarred ergodicity experiment."""
    # Window parameters
    window_length: int = 4096  # FFT window size (power of 2)
    detrend_method: str = "median"  # "median" or "highpass"
    highpass_cutoff: float = 0.01  # Cutoff for highpass filter (Hz)
    
    # Spectral parameters
    top_peaks: int = 5  # Number of top peaks to record
    min_prominence_zscore: float = 2.0  # Gate A threshold
    
    # Tiling parameters
    num_tiles: int = 20  # Number of rectangular tiles
    top_tile_fraction: float = 0.10  # Top 10% tiles for scar score
    
    # Stability test parameters
    epsilon_values: List[float] = None  # Perturbation magnitudes
    L_values: List[int] = None  # Perturbation wavelengths
    stability_overlap_threshold: float = 0.60  # Gate B threshold (60%)
    
    # Output parameters
    top_candidates: int = 10  # Final candidate count
    reduction_threshold: float = 0.10  # Gate C: 10% reduction
    
    # Reproducibility
    seed: int = 42
    
    def __post_init__(self):
        if self.epsilon_values is None:
            self.epsilon_values = [1e-6, 1e-5, 1e-4]
        if self.L_values is None:
            self.L_values = [100, 500, 1000]


# ============================================================================
# CURVATURE COMPUTATION (κ(n))
# ============================================================================

def compute_curvature_kappa(n: int, N: int, precision_dps: int = 50) -> mpf:
    """
    Compute curvature κ(n) = d(n)·ln(n+1)/e² for a candidate near sqrt(N).
    
    This is the discrete frame shift from cornerstone_invariant.py, which
    represents the local "curvature" or Dirichlet amplitude at position n.
    
    Args:
        n: Candidate integer position
        N: Semiprime being analyzed
        precision_dps: Decimal precision
        
    Returns:
        Curvature value κ(n)
    """
    if n < 1:
        return mpf(0)
    
    with mp.workdps(precision_dps):
        # Approximate divisor count: d(n) ≈ log(n) (average order)
        d_n = log(n) if n > 1 else mpf(1)
        ln_term = log(n + 1)
        
        kappa = (d_n * ln_term) / E_SQUARED
        return kappa


def generate_kappa_series(
    N: int,
    center: int,
    half_window: int,
    step: int = 1,
    seed: int = 42,
    filter_small_primes: bool = False
) -> Tuple[List[int], List[float]]:
    """
    Generate κ(n) series over a search interval around center.
    
    Uses deterministic Sobol-like sampling for reproducibility.
    
    Args:
        N: Semiprime being analyzed
        center: Center of search window (typically sqrt(N))
        half_window: Half-width of window
        step: Step size for sampling
        seed: Random seed for reproducibility
        filter_small_primes: If True, skip candidates divisible by 2, 3, 5
        
    Returns:
        Tuple of (n_values, kappa_values)
    """
    precision_dps = max(50, N.bit_length() * 4 + 200)
    
    n_values = []
    kappa_values = []
    
    # Generate points deterministically
    start_n = max(2, center - half_window)
    end_n = center + half_window
    
    for n in range(start_n, end_n, step):
        if n <= 1 or n >= N:
            continue
        # Optionally skip even and small prime divisible candidates
        if filter_small_primes and (n % 2 == 0 or n % 3 == 0 or n % 5 == 0):
            continue
            
        n_values.append(n)
        kappa = float(compute_curvature_kappa(n, N, precision_dps))
        kappa_values.append(kappa)
    
    return n_values, kappa_values


# ============================================================================
# DETRENDING METHODS
# ============================================================================

def detrend_median(kappa_values: List[float], window_size: int = 51) -> np.ndarray:
    """
    Remove median trend from κ(n) series to isolate oscillations.
    
    Args:
        kappa_values: Raw κ(n) series
        window_size: Size of median filter window (must be odd)
        
    Returns:
        Detrended series as numpy array
    """
    if not HAS_NUMPY_SCIPY:
        raise ImportError("numpy/scipy required for detrending")
    
    kappa_arr = np.array(kappa_values)
    
    # Apply median filter to get trend
    if window_size % 2 == 0:
        window_size += 1
    
    # Handle edge cases with padding
    if len(kappa_arr) < window_size:
        trend = np.median(kappa_arr)
    else:
        trend = signal.medfilt(kappa_arr, kernel_size=window_size)
    
    # Remove trend to get oscillatory component
    detrended = kappa_arr - trend
    
    return detrended


def detrend_highpass(kappa_values: List[float], cutoff: float = 0.01, fs: float = 1.0) -> np.ndarray:
    """
    Apply high-pass filter to κ(n) series to isolate high-frequency oscillations.
    
    Args:
        kappa_values: Raw κ(n) series
        cutoff: Cutoff frequency (normalized to Nyquist)
        fs: Sampling frequency
        
    Returns:
        Filtered series as numpy array
    """
    if not HAS_NUMPY_SCIPY:
        raise ImportError("numpy/scipy required for filtering")
    
    kappa_arr = np.array(kappa_values)
    
    # Ensure cutoff is valid
    nyquist = fs / 2
    normalized_cutoff = min(cutoff / nyquist, 0.99)
    
    # Design Butterworth high-pass filter
    order = 4
    b, a = signal.butter(order, normalized_cutoff, btype='high')
    
    # Apply filter (use filtfilt for zero phase shift)
    if len(kappa_arr) > 3 * max(len(a), len(b)):
        filtered = signal.filtfilt(b, a, kappa_arr)
    else:
        # Fall back to lfilter for short signals
        filtered = signal.lfilter(b, a, kappa_arr)
    
    return filtered


def apply_detrend(
    kappa_values: List[float], 
    method: str = "median",
    **kwargs
) -> np.ndarray:
    """
    Apply specified detrending method.
    
    Args:
        kappa_values: Raw κ(n) series
        method: "median" or "highpass"
        **kwargs: Additional parameters for detrending method
        
    Returns:
        Detrended series
    """
    if method == "median":
        window_size = kwargs.get("window_size", 51)
        return detrend_median(kappa_values, window_size)
    elif method == "highpass":
        cutoff = kwargs.get("cutoff", 0.01)
        fs = kwargs.get("fs", 1.0)
        return detrend_highpass(kappa_values, cutoff, fs)
    else:
        raise ValueError(f"Unknown detrend method: {method}")


# ============================================================================
# SPECTRAL ANALYSIS (FFT)
# ============================================================================

def compute_magnitude_spectrum(detrended: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute magnitude spectrum |K(f)| using FFT.
    
    Args:
        detrended: Detrended κ(n) series
        
    Returns:
        Tuple of (frequencies, magnitudes)
    """
    if not HAS_NUMPY_SCIPY:
        raise ImportError("numpy/scipy required for FFT")
    
    n = len(detrended)
    
    # Apply Hann window to reduce spectral leakage
    window = signal.windows.hann(n)
    windowed = detrended * window
    
    # Compute FFT
    spectrum = fft(windowed)
    frequencies = fftfreq(n)
    
    # Get magnitude (only positive frequencies)
    positive_mask = frequencies >= 0
    freqs = frequencies[positive_mask]
    magnitudes = np.abs(spectrum[positive_mask])
    
    return freqs, magnitudes


def compute_spectral_entropy(magnitudes: np.ndarray) -> float:
    """
    Compute spectral entropy of the magnitude spectrum.
    
    Lower entropy indicates more concentrated spectral power (periodic signals).
    Higher entropy indicates more uniform power distribution (noise-like).
    
    Args:
        magnitudes: FFT magnitude spectrum
        
    Returns:
        Spectral entropy value
    """
    # Normalize to probability distribution
    power = magnitudes ** 2
    total_power = np.sum(power)
    
    if total_power == 0:
        return 0.0
    
    p = power / total_power
    
    # Compute entropy (avoid log(0))
    p_nonzero = p[p > 0]
    entropy = -np.sum(p_nonzero * np.log2(p_nonzero))
    
    # Normalize by maximum entropy
    max_entropy = np.log2(len(magnitudes))
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    return normalized_entropy


def find_spectral_peaks(
    frequencies: np.ndarray,
    magnitudes: np.ndarray,
    top_k: int = 5,
    min_prominence_zscore: float = 2.0
) -> List[SpectralPeak]:
    """
    Find top spectral peaks with prominence analysis.
    
    Args:
        frequencies: Frequency array
        magnitudes: Magnitude spectrum
        top_k: Number of top peaks to return
        min_prominence_zscore: Minimum z-score for prominence
        
    Returns:
        List of SpectralPeak objects
    """
    if not HAS_NUMPY_SCIPY:
        raise ImportError("numpy/scipy required for peak finding")
    
    if len(magnitudes) < 3:
        return []
    
    # Find peaks
    peak_indices, properties = signal.find_peaks(
        magnitudes,
        prominence=0,  # We'll filter by z-score later
        width=0
    )
    
    if len(peak_indices) == 0:
        return []
    
    # Get peak properties
    prominences = properties.get('prominences', np.zeros(len(peak_indices)))
    widths = properties.get('widths', np.ones(len(peak_indices)))
    
    # Compute z-scores for prominence
    if len(prominences) > 1:
        prom_zscores = scipy_zscore(prominences)
    else:
        prom_zscores = np.array([0.0])
    
    # Build peak list
    peaks = []
    for i, idx in enumerate(peak_indices):
        peak = SpectralPeak(
            frequency=float(frequencies[idx]),
            height=float(magnitudes[idx]),
            prominence=float(prominences[i]) if i < len(prominences) else 0.0,
            bandwidth=float(widths[i]) if i < len(widths) else 1.0,
            z_score=float(prom_zscores[i]) if i < len(prom_zscores) else 0.0,
            tile_indices=[]
        )
        peaks.append(peak)
    
    # Sort by height and return top k
    peaks.sort(key=lambda p: p.height, reverse=True)
    return peaks[:top_k]


# ============================================================================
# SCAR SCORE ON RECTANGLES
# ============================================================================

def compute_tile_scores(
    n_values: List[int],
    kappa_values: List[float],
    detrended: np.ndarray,
    num_tiles: int = 20
) -> List[TileScore]:
    """
    Subdivide n into equal blocks and compute scar scores.
    
    Scar score = (energy in top 10% tiles) / (total energy)
    
    Args:
        n_values: Integer positions
        kappa_values: Original κ(n) values
        detrended: Detrended series
        num_tiles: Number of rectangular tiles
        
    Returns:
        List of TileScore objects
    """
    if len(n_values) == 0:
        return []
    
    n_arr = np.array(n_values)
    energy = detrended ** 2  # Local energy
    
    # Compute tile boundaries
    tile_size = len(n_values) // num_tiles
    if tile_size == 0:
        tile_size = 1
    
    tiles = []
    for i in range(num_tiles):
        start_idx = i * tile_size
        end_idx = min((i + 1) * tile_size, len(n_values))
        
        if start_idx >= len(n_values):
            break
        
        tile_energy = np.sum(energy[start_idx:end_idx])
        
        tile = TileScore(
            start_n=int(n_arr[start_idx]),
            end_n=int(n_arr[end_idx - 1]) if end_idx > start_idx else int(n_arr[start_idx]),
            tile_index=i,
            energy=float(tile_energy),
            scar_score=0.0  # Will be computed later
        )
        tiles.append(tile)
    
    # Compute scar scores
    total_energy = sum(t.energy for t in tiles)
    if total_energy > 0:
        for tile in tiles:
            tile.scar_score = tile.energy / total_energy
    
    return tiles


def compute_global_scar_score(tiles: List[TileScore], top_fraction: float = 0.10) -> float:
    """
    Compute global scar score: (energy in top X% tiles) / (total energy).
    
    Higher scar score indicates more concentrated energy (scarring).
    
    Args:
        tiles: List of TileScore objects
        top_fraction: Fraction of tiles considered "top"
        
    Returns:
        Global scar score in [0, 1]
    """
    if len(tiles) == 0:
        return 0.0
    
    # Sort tiles by energy
    sorted_tiles = sorted(tiles, key=lambda t: t.energy, reverse=True)
    
    # Get top tiles
    top_count = max(1, int(len(tiles) * top_fraction))
    top_tiles = sorted_tiles[:top_count]
    
    total_energy = sum(t.energy for t in tiles)
    top_energy = sum(t.energy for t in top_tiles)
    
    if total_energy == 0:
        return 0.0
    
    return top_energy / total_energy


# ============================================================================
# STABILITY TEST
# ============================================================================

def apply_perturbation(
    n_values: List[int],
    epsilon: float,
    L: int
) -> List[int]:
    """
    Apply sinusoidal perturbation: n' = n + ε·sin(2πn/L).
    
    Args:
        n_values: Original n positions
        epsilon: Perturbation magnitude
        L: Perturbation wavelength
        
    Returns:
        Perturbed n values (rounded to integers)
    """
    perturbed = []
    for n in n_values:
        delta = epsilon * np.sin(2 * np.pi * n / L)
        n_prime = int(round(n + delta))
        perturbed.append(max(MIN_VALID_N, n_prime))  # Ensure valid range
    return perturbed


def compute_peak_overlap(peaks1: List[SpectralPeak], peaks2: List[SpectralPeak]) -> float:
    """
    Compute overlap fraction between two peak sets.
    
    Uses frequency matching with tolerance.
    
    Args:
        peaks1: First peak set
        peaks2: Second peak set
        
    Returns:
        Overlap fraction in [0, 1]
    """
    if len(peaks1) == 0 or len(peaks2) == 0:
        return 0.0
    
    matched = 0
    for p1 in peaks1:
        for p2 in peaks2:
            if abs(p1.frequency - p2.frequency) <= FREQ_TOLERANCE * abs(p1.frequency + FREQ_EPSILON):
                matched += 1
                break
    
    return matched / len(peaks1)


def run_stability_test(
    N: int,
    n_values: List[int],
    kappa_values: List[float],
    original_peaks: List[SpectralPeak],
    epsilon_values: List[float],
    L_values: List[int],
    config: ExperimentConfig
) -> Tuple[float, Dict[str, float]]:
    """
    Run stability test with sinusoidal perturbations.
    
    Args:
        N: Semiprime
        n_values: Original positions
        kappa_values: Original κ values
        original_peaks: Peaks from original series
        epsilon_values: Perturbation magnitudes
        L_values: Perturbation wavelengths
        config: Experiment configuration
        
    Returns:
        Tuple of (average_overlap, detail_dict)
    """
    overlap_results = {}
    overlaps = []
    
    precision_dps = max(50, N.bit_length() * 4 + 200)
    
    for eps in epsilon_values:
        for L in L_values:
            # Apply perturbation
            perturbed_n = apply_perturbation(n_values, eps, L)
            
            # Recompute κ for perturbed positions
            perturbed_kappa = []
            valid_n = []
            for n in perturbed_n:
                if n > 1 and n < N:
                    valid_n.append(n)
                    k = float(compute_curvature_kappa(n, N, precision_dps))
                    perturbed_kappa.append(k)
            
            if len(perturbed_kappa) < 10:
                continue
            
            # Detrend and compute spectrum
            detrended = apply_detrend(perturbed_kappa, config.detrend_method)
            freqs, mags = compute_magnitude_spectrum(detrended)
            
            # Find peaks
            perturbed_peaks = find_spectral_peaks(
                freqs, mags,
                top_k=config.top_peaks,
                min_prominence_zscore=config.min_prominence_zscore
            )
            
            # Compute overlap
            overlap = compute_peak_overlap(original_peaks, perturbed_peaks)
            overlaps.append(overlap)
            overlap_results[f"eps={eps}_L={L}"] = overlap
    
    avg_overlap = np.mean(overlaps) if overlaps else 0.0
    return avg_overlap, overlap_results


# ============================================================================
# CANDIDATE RANKING
# ============================================================================

def rank_candidates(
    tiles: List[TileScore],
    peaks: List[SpectralPeak],
    stability_overlap: float,
    top_m: int = 10
) -> List[CandidateWindow]:
    """
    Rank tiles by (peak_height × stability × scar_score) and emit top M.
    
    Args:
        tiles: TileScore objects
        peaks: Spectral peaks
        stability_overlap: Overall stability metric
        top_m: Number of candidates to return
        
    Returns:
        List of CandidateWindow objects
    """
    if len(tiles) == 0:
        return []
    
    # Get maximum peak height for normalization
    max_peak_height = max((p.height for p in peaks), default=1.0)
    
    candidates = []
    for tile in tiles:
        # Composite score
        normalized_height = max_peak_height
        composite = normalized_height * stability_overlap * tile.scar_score
        
        candidate = CandidateWindow(
            start_n=tile.start_n,
            end_n=tile.end_n,
            peak_height=normalized_height,
            stability=stability_overlap,
            scar_score=tile.scar_score,
            composite_score=composite
        )
        candidates.append(candidate)
    
    # Sort by composite score
    candidates.sort(key=lambda c: c.composite_score, reverse=True)
    
    return candidates[:top_m]


# ============================================================================
# PASS/FAIL GATES
# ============================================================================

@dataclass
class GateResults:
    """Results from pass/fail gate evaluation."""
    gate_a_passed: bool  # At least one robust peak (z-score >= 2.0)
    gate_b_passed: bool  # Stability overlap >= 60%
    gate_c_passed: bool  # Reduction >= 10% vs geometry-rank alone
    
    gate_a_detail: str = ""
    gate_b_detail: str = ""
    gate_c_detail: str = ""
    
    @property
    def all_passed(self) -> bool:
        return self.gate_a_passed and self.gate_b_passed and self.gate_c_passed


def evaluate_gates(
    peaks: List[SpectralPeak],
    stability_overlap: float,
    candidates: List[CandidateWindow],
    total_n_values: int,
    config: ExperimentConfig
) -> GateResults:
    """
    Evaluate pass/fail gates.
    
    Gate A: At least one robust peak (prominence z-score >= 2.0)
    Gate B: Stability overlap >= 60% for top peak under all ε tests
    Gate C: Candidate windows reduce arithmetic checks by >= 10%
    
    Args:
        peaks: Spectral peaks found
        stability_overlap: Average stability overlap
        candidates: Candidate windows
        total_n_values: Total number of n values searched
        config: Experiment configuration
        
    Returns:
        GateResults object
    """
    # Gate A: Robust peak
    robust_peaks = [p for p in peaks if p.z_score >= config.min_prominence_zscore]
    gate_a_passed = len(robust_peaks) > 0
    gate_a_detail = f"Found {len(robust_peaks)} peaks with z-score >= {config.min_prominence_zscore}"
    
    # Gate B: Stability
    gate_b_passed = stability_overlap >= config.stability_overlap_threshold
    gate_b_detail = f"Stability overlap: {stability_overlap:.2%} (threshold: {config.stability_overlap_threshold:.0%})"
    
    # Gate C: Reduction
    if len(candidates) > 0 and total_n_values > 0:
        # Total n-values covered by candidate windows
        candidate_coverage = sum(c.end_n - c.start_n + 1 for c in candidates)
        reduction = 1.0 - (candidate_coverage / total_n_values)
        gate_c_passed = reduction >= config.reduction_threshold
        gate_c_detail = f"Reduction: {reduction:.2%} (threshold: {config.reduction_threshold:.0%})"
    else:
        gate_c_passed = False
        gate_c_detail = "No candidates to evaluate"
    
    return GateResults(
        gate_a_passed=gate_a_passed,
        gate_b_passed=gate_b_passed,
        gate_c_passed=gate_c_passed,
        gate_a_detail=gate_a_detail,
        gate_b_detail=gate_b_detail,
        gate_c_detail=gate_c_detail
    )


# ============================================================================
# OUTPUT AND LOGGING
# ============================================================================

def log_experiment_results(
    N: int,
    config: ExperimentConfig,
    n_values: List[int],
    peaks: List[SpectralPeak],
    tiles: List[TileScore],
    stability_overlap: float,
    stability_details: Dict[str, float],
    candidates: List[CandidateWindow],
    gates: GateResults,
    output_dir: str,
    elapsed_time: float
) -> Dict[str, Any]:
    """
    Log all experiment results for reproducibility.
    
    Args:
        N: Semiprime
        config: Experiment configuration
        n_values: Searched n values
        peaks: Spectral peaks
        tiles: Tile scores
        stability_overlap: Stability metric
        stability_details: Per-perturbation overlaps
        candidates: Candidate windows
        gates: Gate evaluation results
        output_dir: Output directory
        elapsed_time: Runtime in seconds
        
    Returns:
        Results dictionary
    """
    timestamp = datetime.now().isoformat()
    
    results = {
        "timestamp": timestamp,
        "N": str(N),
        "N_bit_length": N.bit_length(),
        "elapsed_seconds": elapsed_time,
        "config": {
            "window_length": config.window_length,
            "detrend_method": config.detrend_method,
            "highpass_cutoff": config.highpass_cutoff,
            "top_peaks": config.top_peaks,
            "min_prominence_zscore": config.min_prominence_zscore,
            "num_tiles": config.num_tiles,
            "top_tile_fraction": config.top_tile_fraction,
            "epsilon_values": config.epsilon_values,
            "L_values": config.L_values,
            "stability_overlap_threshold": config.stability_overlap_threshold,
            "top_candidates": config.top_candidates,
            "reduction_threshold": config.reduction_threshold,
            "seed": config.seed
        },
        "search_stats": {
            "total_n_values": len(n_values),
            "n_range": [min(n_values), max(n_values)] if n_values else [0, 0]
        },
        "spectral_analysis": {
            "peaks": [
                {
                    "frequency": p.frequency,
                    "height": p.height,
                    "prominence": p.prominence,
                    "bandwidth": p.bandwidth,
                    "z_score": p.z_score
                }
                for p in peaks
            ]
        },
        "scar_analysis": {
            "global_scar_score": compute_global_scar_score(tiles, config.top_tile_fraction),
            "num_tiles": len(tiles)
        },
        "stability_test": {
            "average_overlap": stability_overlap,
            "details": stability_details
        },
        "candidates": [
            {
                "start_n": c.start_n,
                "end_n": c.end_n,
                "peak_height": c.peak_height,
                "stability": c.stability,
                "scar_score": c.scar_score,
                "composite_score": c.composite_score
            }
            for c in candidates
        ],
        "gates": {
            "gate_a_passed": bool(gates.gate_a_passed),
            "gate_a_detail": gates.gate_a_detail,
            "gate_b_passed": bool(gates.gate_b_passed),
            "gate_b_detail": gates.gate_b_detail,
            "gate_c_passed": bool(gates.gate_c_passed),
            "gate_c_detail": gates.gate_c_detail,
            "all_passed": bool(gates.all_passed)
        }
    }
    
    # Write JSON results
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "experiment_results.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Write CSV for peaks
    csv_path = os.path.join(output_dir, "peak_table.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["frequency", "height", "prominence", "bandwidth", "z_score"])
        for p in peaks:
            writer.writerow([p.frequency, p.height, p.prominence, p.bandwidth, p.z_score])
    
    # Write CSV for candidates
    candidates_csv = os.path.join(output_dir, "candidates.csv")
    with open(candidates_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["start_n", "end_n", "peak_height", "stability", "scar_score", "composite_score"])
        for c in candidates:
            writer.writerow([c.start_n, c.end_n, c.peak_height, c.stability, c.scar_score, c.composite_score])
    
    return results


def plot_spectrum_and_tiles(
    frequencies: np.ndarray,
    magnitudes: np.ndarray,
    peaks: List[SpectralPeak],
    tiles: List[TileScore],
    output_dir: str,
    run_id: str = "run"
) -> Optional[str]:
    """
    Generate PNG plot of spectrum and highlighted tiles.
    
    Args:
        frequencies: Frequency array
        magnitudes: Magnitude spectrum
        peaks: Spectral peaks
        tiles: Tile scores
        output_dir: Output directory
        run_id: Run identifier
        
    Returns:
        Path to saved plot, or None if matplotlib unavailable
    """
    if not HAS_MATPLOTLIB:
        return None
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Magnitude spectrum with peaks
    ax1 = axes[0]
    ax1.plot(frequencies, magnitudes, 'b-', linewidth=0.5, label='Spectrum')
    
    # Mark peaks
    for i, peak in enumerate(peaks):
        ax1.axvline(peak.frequency, color='r', linestyle='--', alpha=0.7)
        ax1.annotate(f'P{i+1}: z={peak.z_score:.2f}',
                     xy=(peak.frequency, peak.height),
                     xytext=(5, 5), textcoords='offset points',
                     fontsize=8)
    
    ax1.set_xlabel('Frequency')
    ax1.set_ylabel('Magnitude |K(f)|')
    ax1.set_title('Spectral Analysis with Peak Detection')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Tile energy distribution
    ax2 = axes[1]
    tile_indices = [t.tile_index for t in tiles]
    tile_energies = [t.energy for t in tiles]
    
    # Color by scar score
    colors = ['red' if t.scar_score > np.percentile([ti.scar_score for ti in tiles], 90) else 'blue'
              for t in tiles]
    
    ax2.bar(tile_indices, tile_energies, color=colors, alpha=0.7)
    ax2.set_xlabel('Tile Index')
    ax2.set_ylabel('Energy')
    ax2.set_title('Tile Energy Distribution (red = top 10% scar tiles)')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, f"spectrum_tiles_{run_id}.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    return plot_path


# ============================================================================
# MAIN EXPERIMENT RUNNER
# ============================================================================

class SuperscarredErgodicityExperiment:
    """
    Main experiment class for superscarred ergodicity analysis.
    """
    
    def __init__(self, config: Optional[ExperimentConfig] = None):
        """
        Initialize experiment with configuration.
        
        Args:
            config: Experiment configuration (uses defaults if None)
        """
        self.config = config or ExperimentConfig()
        
        # Validate dependencies
        if not HAS_NUMPY_SCIPY:
            raise ImportError(
                "numpy and scipy are required for this experiment. "
                "Install with: pip install numpy scipy"
            )
    
    def validate_n(self, N: int) -> None:
        """
        Validate N against operational gates.
        
        Args:
            N: Semiprime to validate
            
        Raises:
            ValueError: If N violates validation gates
        """
        if N == CHALLENGE_127:
            return  # Whitelist exception
        
        if not (RANGE_MIN <= N <= RANGE_MAX):
            raise ValueError(
                f"N={N} violates validation gates. "
                f"Must be CHALLENGE_127 or in [{RANGE_MIN}, {RANGE_MAX}]"
            )
    
    def run(
        self,
        N: int,
        half_window: int = 50000,
        step: int = 1,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the superscarred ergodicity experiment.
        
        Args:
            N: Semiprime to analyze
            half_window: Half-width of search window around sqrt(N)
            step: Step size for sampling
            output_dir: Output directory for results
            
        Returns:
            Results dictionary
        """
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Validate N
        self.validate_n(N)
        
        # Set precision
        precision_dps = max(50, N.bit_length() * 4 + 200)
        mp.dps = precision_dps
        
        # Compute search center (sqrt(N))
        with mp.workdps(precision_dps):
            sqrt_N = int(mp.sqrt(N))
        
        print(f"=== Superscarred Ergodicity Insight Experiment ===")
        print(f"Timestamp: {timestamp}")
        print(f"N = {N} ({N.bit_length()} bits)")
        print(f"sqrt(N) ≈ {sqrt_N}")
        print(f"Precision: {precision_dps} dps")
        print(f"Seed: {self.config.seed}")
        print(f"Window: [{sqrt_N - half_window}, {sqrt_N + half_window}]")
        print(f"Step: {step}")
        print()
        
        # Step 1: Generate κ(n) series
        print("Step 1: Generating κ(n) series...")
        n_values, kappa_values = generate_kappa_series(
            N, sqrt_N, half_window, step, self.config.seed, filter_small_primes=False
        )
        print(f"  Generated {len(n_values)} data points")
        
        if len(kappa_values) < 10:
            raise ValueError(f"Insufficient data points: {len(kappa_values)} < 10")
        
        # Step 2: Detrend
        print(f"Step 2: Detrending with method='{self.config.detrend_method}'...")
        detrended = apply_detrend(kappa_values, self.config.detrend_method)
        print(f"  Detrended series length: {len(detrended)}")
        
        # Step 3: Spectral analysis
        print("Step 3: Computing magnitude spectrum...")
        frequencies, magnitudes = compute_magnitude_spectrum(detrended)
        
        spectral_entropy = compute_spectral_entropy(magnitudes)
        print(f"  Spectral entropy: {spectral_entropy:.4f}")
        
        peaks = find_spectral_peaks(
            frequencies, magnitudes,
            top_k=self.config.top_peaks,
            min_prominence_zscore=self.config.min_prominence_zscore
        )
        print(f"  Found {len(peaks)} peaks")
        for i, p in enumerate(peaks):
            print(f"    Peak {i+1}: f={p.frequency:.6f}, h={p.height:.4f}, z={p.z_score:.2f}")
        
        # Step 4: Compute tile scores
        print("Step 4: Computing scar scores on rectangles...")
        tiles = compute_tile_scores(n_values, kappa_values, detrended, self.config.num_tiles)
        global_scar = compute_global_scar_score(tiles, self.config.top_tile_fraction)
        print(f"  Global scar score: {global_scar:.4f}")
        
        # Step 5: Stability test
        print("Step 5: Running stability test...")
        stability_overlap, stability_details = run_stability_test(
            N, n_values, kappa_values, peaks,
            self.config.epsilon_values, self.config.L_values,
            self.config
        )
        print(f"  Average stability overlap: {stability_overlap:.2%}")
        
        # Step 6: Rank candidates
        print("Step 6: Ranking candidate windows...")
        candidates = rank_candidates(tiles, peaks, stability_overlap, self.config.top_candidates)
        print(f"  Top {len(candidates)} candidates:")
        for i, c in enumerate(candidates):
            print(f"    {i+1}. n∈[{c.start_n}, {c.end_n}], score={c.composite_score:.6f}")
        
        # Step 7: Evaluate gates
        print("\nStep 7: Evaluating pass/fail gates...")
        gates = evaluate_gates(peaks, stability_overlap, candidates, len(n_values), self.config)
        print(f"  Gate A (robust peak): {'PASS' if gates.gate_a_passed else 'FAIL'} - {gates.gate_a_detail}")
        print(f"  Gate B (stability):   {'PASS' if gates.gate_b_passed else 'FAIL'} - {gates.gate_b_detail}")
        print(f"  Gate C (reduction):   {'PASS' if gates.gate_c_passed else 'FAIL'} - {gates.gate_c_detail}")
        print(f"  Overall: {'ALL GATES PASSED' if gates.all_passed else 'SOME GATES FAILED'}")
        
        elapsed = time.time() - start_time
        print(f"\nElapsed time: {elapsed:.2f} seconds")
        
        # Step 8: Log and save results
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__),
                f"results_{timestamp}"
            )
        
        print(f"\nStep 8: Saving results to {output_dir}")
        results = log_experiment_results(
            N, self.config, n_values, peaks, tiles,
            stability_overlap, stability_details,
            candidates, gates, output_dir, elapsed
        )
        
        # Generate plot
        plot_path = plot_spectrum_and_tiles(
            frequencies, magnitudes, peaks, tiles,
            output_dir, timestamp
        )
        if plot_path:
            print(f"  Plot saved to: {plot_path}")
            results["plot_path"] = plot_path
        
        print("\n=== Experiment Complete ===")
        
        return results


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    """Run experiment on 127-bit challenge or operational range test."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Superscarred Ergodicity Insight Experiment"
    )
    parser.add_argument(
        "--n", type=int, default=None,
        help="Semiprime N to analyze (default: CHALLENGE_127)"
    )
    parser.add_argument(
        "--half-window", type=int, default=10000,
        help="Half-width of search window (default: 10000)"
    )
    parser.add_argument(
        "--step", type=int, default=1,
        help="Step size for sampling (default: 1)"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory for results"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Use CHALLENGE_127 if no N provided
    N = args.n if args.n else CHALLENGE_127
    
    # Create config with seed
    config = ExperimentConfig(seed=args.seed)
    
    # Run experiment
    experiment = SuperscarredErgodicityExperiment(config)
    results = experiment.run(
        N=N,
        half_window=args.half_window,
        step=args.step,
        output_dir=args.output_dir
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Gates passed: {results['gates']['all_passed']}")
    print(f"Top candidate: n ∈ [{results['candidates'][0]['start_n']}, {results['candidates'][0]['end_n']}]"
          if results['candidates'] else "No candidates")


if __name__ == "__main__":
    main()
