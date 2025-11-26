"""
Band-First Router + Early-Exit Guard Falsification Experiment
==============================================================

Implements and tests the hypothesis that:
1. Band-first router: Dividing the search space into bands based on expected
   factor gap Δ ≈ ln(√N) with wheel mask (mod-210) prefiltering reduces
   candidate count while maintaining coverage.
2. Early-exit guard: Aborting bands with flat amplitude/curvature surfaces
   (|∂A|<τ₁ && |∂²A|<τ₂ over L steps) improves efficiency without significant
   recall loss.

Key functions:
- plan_bands(N, C, alpha, wheel) -> [Band] - Plan bands based on expected gap
- apply_wheel(candidates, wheel) -> candidates' - Wheel mask filter
- scan_band_Z5D(band, params) -> Peaks - Z5D intra-band scanning
- is_flat(window, tau, L) -> bool - Flat-surface detector
- run_scan(N, params, guards) -> Report - Full scan with optional early-exit

Constants:
- CHALLENGE_127 = 137524771864208156028430259349934309717
- RANGE_MIN = 10**14
- RANGE_MAX = 10**18
"""

import sys
import os
import json
import time
import subprocess
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Iterator, Dict, Any
from math import log, isqrt
from datetime import datetime, timezone

import mpmath as mp

# Add path to z5d-informed-gva for wheel_residues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'z5d-informed-gva'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'z5d-comprehensive-challenge'))

from wheel_residues import (
    is_admissible, next_admissible, prev_admissible,
    admissible_in_range, count_admissible_in_range,
    WHEEL_MODULUS, WHEEL_SIZE, WHEEL_210_RESIDUES
)
from z5d_api import local_prime_density, expected_gap

# Precompute residue-to-index mapping for O(1) lookup
WHEEL_RESIDUE_INDEX = {r: i for i, r in enumerate(WHEEL_210_RESIDUES)}


# ============================================================================
# Constants
# ============================================================================

CHALLENGE_127 = 137524771864208156028430259349934309717
RANGE_MIN = 10**14
RANGE_MAX = 10**18

# Default parameters
DEFAULT_C = 0.9         # Coverage target
DEFAULT_ALPHA = 1.0     # Inner-band scale factor
DEFAULT_WHEEL = 210     # Wheel modulus
DEFAULT_TAU_GRAD = 1e-6 # Gradient threshold for flat detection
DEFAULT_TAU_CURV = 1e-8 # Curvature threshold for flat detection
DEFAULT_L = 8           # Window size for flat detection


# ============================================================================
# Utility Functions
# ============================================================================

def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bitLength() × 4 + 200)
    """
    return max(50, N.bit_length() * 4 + 200)


def get_git_head() -> str:
    """Get current git HEAD commit hash."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def timestamp_utc() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class Band:
    """Represents a search band around √N."""
    id: int
    center: int           # Center of band (√N + offset)
    delta_start: int      # Start offset from √N
    delta_end: int        # End offset from √N
    width: int            # Band width (computed from delta_end - delta_start)
    expected_density: float
    priority: int         # Lower is higher priority


@dataclass
class Peak:
    """Represents a resonance peak found during scanning."""
    candidate: int
    delta: int            # Offset from √N
    amplitude: float      # Geodesic amplitude (lower = better)
    band_id: int
    step_index: int


@dataclass
class ScanReport:
    """Report from a scan operation."""
    N: int
    sqrt_N: int
    seed: int
    C: float
    alpha: float
    wheel: int
    tau_grad: float
    tau_curv: float
    L: int
    dps: int
    git_head: str
    timestamp_utc: str
    
    # Results
    bands_planned: int = 0
    candidates_total: int = 0
    candidates_masked: int = 0
    candidates_scanned: int = 0
    z5d_steps: int = 0
    early_exits: int = 0
    peaks_found: int = 0
    factors_found: Optional[Tuple[int, int]] = None
    wall_time_sec: float = 0.0
    
    # Artifacts
    bands: List[Dict] = field(default_factory=list)
    peaks: List[Dict] = field(default_factory=list)


# ============================================================================
# JSONL Logger
# ============================================================================

class JSONLLogger:
    """Logs events to JSONL file."""
    
    def __init__(self, filepath: str, base_params: Dict[str, Any]):
        self.filepath = filepath
        self.base_params = base_params
        self.file = open(filepath, 'w')
    
    def log(self, event: str, **kwargs):
        """Log an event with base params + kwargs."""
        record = {
            'event': event,
            **self.base_params,
            **kwargs,
            'timestamp_utc': timestamp_utc()
        }
        self.file.write(json.dumps(record) + '\n')
        self.file.flush()
    
    def close(self):
        self.file.close()


# ============================================================================
# Core Implementation
# ============================================================================

def plan_bands(N: int, C: float = DEFAULT_C, alpha: float = DEFAULT_ALPHA,
               wheel: int = DEFAULT_WHEEL, num_bands: int = 20) -> List[Band]:
    """
    Plan search bands based on expected factor gap and coverage target.
    
    Band width w = α × Δ where Δ ≈ ln(√N) is the expected gap.
    Total coverage = C × (expected factor range).
    
    Args:
        N: Semiprime to factor
        C: Coverage target (0.8 to 0.98)
        alpha: Inner-band scale factor (0.6 to 1.6)
        wheel: Wheel modulus (default 210)
        num_bands: Number of bands to create
        
    Returns:
        List of Band objects sorted by priority (density-based)
    """
    sqrt_N = isqrt(N)
    
    # Expected prime gap near √N
    delta_expected = expected_gap(float(sqrt_N))
    
    # Band width based on alpha scaling
    band_width = max(1, int(alpha * delta_expected))
    
    # Total search radius based on coverage C
    # For balanced semiprimes, factors are typically within a few multiples of gap
    # Use coverage to determine how far to search
    search_radius = int(C * num_bands * band_width)
    
    bands = []
    
    # Create bands centered around √N, expanding outward
    for i in range(num_bands):
        # Alternate between positive and negative offsets
        sign = 1 if i % 2 == 0 else -1
        band_index = (i + 1) // 2
        
        if sign > 0:
            delta_start = band_index * band_width
            delta_end = (band_index + 1) * band_width
        else:
            delta_start = -(band_index + 1) * band_width
            delta_end = -band_index * band_width
        
        center = sqrt_N + (delta_start + delta_end) // 2
        
        # Estimate density in this band
        density = local_prime_density(float(center))
        
        band = Band(
            id=i,
            center=center,
            delta_start=delta_start,
            delta_end=delta_end,
            width=band_width,
            expected_density=density,
            priority=i  # Will be re-sorted
        )
        bands.append(band)
    
    # Sort by density (descending) - search denser regions first
    bands.sort(key=lambda b: b.expected_density, reverse=True)
    
    # Update priorities after sorting
    for i, band in enumerate(bands):
        band.priority = i
    
    return bands


def apply_wheel(candidates: List[int], wheel: int = DEFAULT_WHEEL) -> List[int]:
    """
    Apply wheel mask filter to candidates.
    
    Only candidates coprime to the wheel modulus pass through.
    For wheel=210, this prunes ~77% of candidates.
    
    Args:
        candidates: List of candidate integers
        wheel: Wheel modulus (default 210)
        
    Returns:
        Filtered list of admissible candidates
    """
    if wheel != 210:
        raise ValueError("Only wheel=210 is currently supported")
    
    return [c for c in candidates if is_admissible(c)]


def generate_band_candidates(band: Band, sqrt_N: int, wheel: int = DEFAULT_WHEEL) -> Iterator[int]:
    """
    Generate wheel-filtered candidates within a band.
    
    Args:
        band: Band to scan
        sqrt_N: Square root of N
        wheel: Wheel modulus
        
    Yields:
        Admissible candidates in the band
    """
    start = sqrt_N + band.delta_start
    end = sqrt_N + band.delta_end
    
    if start > end:
        start, end = end, start
    
    # Start from first admissible in range
    current = next_admissible(start)
    
    while current <= end:
        yield current
        
        # Jump to next admissible using wheel structure (O(1) lookup)
        residue = current % WHEEL_MODULUS
        residue_idx = WHEEL_RESIDUE_INDEX[residue]
        
        if residue_idx < WHEEL_SIZE - 1:
            next_residue = WHEEL_210_RESIDUES[residue_idx + 1]
            current += (next_residue - residue)
        else:
            current += (WHEEL_MODULUS - residue) + WHEEL_210_RESIDUES[0]


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """Embed integer n into 7D torus using geodesic mapping."""
    phi = mp.mpf(1 + mp.sqrt(5)) / 2
    coords = []
    for d in range(dimensions):
        phi_power = phi ** (d + 1)
        coord = mp.fmod(n * phi_power, 1)
        if k != 1.0:
            coord = mp.power(coord, k)
            coord = mp.fmod(coord, 1)
        coords.append(coord)
    return coords


def riemannian_distance(p1: List[mp.mpf], p2: List[mp.mpf]) -> mp.mpf:
    """Compute Riemannian geodesic distance on 7D torus."""
    dist_sq = mp.mpf(0)
    for c1, c2 in zip(p1, p2):
        diff = abs(c1 - c2)
        wrap_diff = mp.mpf(1) - diff
        min_diff = min(diff, wrap_diff)
        dist_sq += min_diff * min_diff
    return mp.sqrt(dist_sq)


def compute_amplitude(candidate: int, N_embedding: List[mp.mpf], k: float = 0.35) -> float:
    """
    Compute geodesic amplitude for a candidate.
    
    Args:
        candidate: Candidate value
        N_embedding: Pre-computed embedding of N
        k: Geodesic exponent
        
    Returns:
        Amplitude (smaller = better resonance)
    """
    cand_embedding = embed_torus_geodesic(candidate, k)
    distance = riemannian_distance(N_embedding, cand_embedding)
    return float(distance)


def is_flat(amplitudes: List[float], tau_grad: float = DEFAULT_TAU_GRAD,
            tau_curv: float = DEFAULT_TAU_CURV, L: int = DEFAULT_L) -> bool:
    """
    Detect if amplitude surface is flat (no resonance signal).
    
    A flat surface indicates no factors are nearby - abort band early.
    
    Criteria:
    - |∂A| < tau_grad: normalized gradient is small
    - |∂²A| < tau_curv: curvature is small
    - Both must hold over L consecutive steps
    
    Args:
        amplitudes: Recent amplitude values
        tau_grad: Gradient threshold
        tau_curv: Curvature threshold
        L: Window size
        
    Returns:
        True if surface is flat (should abort)
    """
    if len(amplitudes) < L:
        return False
    
    window = amplitudes[-L:]
    
    # Compute gradients (first differences)
    gradients = [window[i+1] - window[i] for i in range(len(window) - 1)]
    
    # Compute curvatures (second differences)
    curvatures = [gradients[i+1] - gradients[i] for i in range(len(gradients) - 1)]
    
    if not gradients or not curvatures:
        return False
    
    # Check if all gradients and curvatures are below thresholds
    max_grad = max(abs(g) for g in gradients)
    max_curv = max(abs(c) for c in curvatures)
    
    return max_grad < tau_grad and max_curv < tau_curv


def scan_band_Z5D(band: Band, N: int, sqrt_N: int, N_embedding: List[mp.mpf],
                  k: float = 0.35, max_steps: int = 10000,
                  early_exit: bool = False,
                  tau_grad: float = DEFAULT_TAU_GRAD,
                  tau_curv: float = DEFAULT_TAU_CURV,
                  L: int = DEFAULT_L,
                  logger: Optional[JSONLLogger] = None) -> Tuple[List[Peak], int, bool]:
    """
    Scan a band using Z5D-guided stepping with optional early exit.
    
    Args:
        band: Band to scan
        N: Semiprime
        sqrt_N: Square root of N
        N_embedding: Pre-computed N embedding
        k: Geodesic exponent
        max_steps: Maximum steps per band
        early_exit: Enable early-exit guard
        tau_grad: Gradient threshold for flat detection
        tau_curv: Curvature threshold for flat detection
        L: Window size for flat detection
        logger: Optional JSONL logger
        
    Returns:
        Tuple of (peaks found, steps taken, early_exited)
    """
    peaks = []
    amplitudes = []
    steps = 0
    early_exited = False
    
    for candidate in generate_band_candidates(band, sqrt_N):
        if steps >= max_steps:
            break
        
        steps += 1
        
        # Compute amplitude
        amplitude = compute_amplitude(candidate, N_embedding, k)
        amplitudes.append(amplitude)
        
        # Check for factor
        if N % candidate == 0:
            peak = Peak(
                candidate=candidate,
                delta=candidate - sqrt_N,
                amplitude=amplitude,
                band_id=band.id,
                step_index=steps
            )
            peaks.append(peak)
            
            if logger:
                logger.log('peak', candidate=candidate, delta=peak.delta,
                          amplitude=amplitude, band_id=band.id, step=steps)
        
        # Log step periodically
        if logger and steps % 100 == 0:
            logger.log('step', band_id=band.id, step=steps,
                      candidate=candidate, amplitude=amplitude)
        
        # Check early exit condition
        if early_exit and is_flat(amplitudes, tau_grad, tau_curv, L):
            early_exited = True
            if logger:
                logger.log('early_exit', band_id=band.id, step=steps,
                          reason='flat_surface')
            break
    
    return peaks, steps, early_exited


def run_scan(N: int, seed: int, C: float = DEFAULT_C, alpha: float = DEFAULT_ALPHA,
             wheel: int = DEFAULT_WHEEL, num_bands: int = 20,
             max_steps_per_band: int = 10000, k: float = 0.35,
             early_exit: bool = False,
             tau_grad: float = DEFAULT_TAU_GRAD,
             tau_curv: float = DEFAULT_TAU_CURV,
             L: int = DEFAULT_L,
             log_file: Optional[str] = None,
             verbose: bool = False) -> ScanReport:
    """
    Run full band-router scan with optional early-exit guard.
    
    Args:
        N: Semiprime to factor
        seed: Random seed for reproducibility
        C: Coverage target
        alpha: Inner-band scale factor
        wheel: Wheel modulus
        num_bands: Number of bands to create
        max_steps_per_band: Maximum steps per band
        k: Geodesic exponent
        early_exit: Enable early-exit guard
        tau_grad: Gradient threshold
        tau_curv: Curvature threshold
        L: Window size
        log_file: Path for JSONL log
        verbose: Enable verbose output
        
    Returns:
        ScanReport with full results
    """
    start_time = time.time()
    sqrt_N = isqrt(N)
    dps = adaptive_precision(N)
    git_head = get_git_head()
    ts = timestamp_utc()
    
    # Initialize report
    report = ScanReport(
        N=N,
        sqrt_N=sqrt_N,
        seed=seed,
        C=C,
        alpha=alpha,
        wheel=wheel,
        tau_grad=tau_grad,
        tau_curv=tau_curv,
        L=L,
        dps=dps,
        git_head=git_head,
        timestamp_utc=ts
    )
    
    # Setup logger
    logger = None
    if log_file:
        base_params = {
            'seed': seed,
            'C': C,
            'alpha': alpha,
            'wheel': wheel,
            'tau': tau_grad,
            'L': L,
            'dps': dps,
            'git_head': git_head
        }
        logger = JSONLLogger(log_file, base_params)
    
    with mp.workdps(dps):
        if verbose:
            print(f"Scanning N = {N}")
            print(f"√N = {sqrt_N}")
            print(f"Precision: {dps} dps")
            print(f"Early-exit: {early_exit}")
        
        # Plan bands
        bands = plan_bands(N, C, alpha, wheel, num_bands)
        report.bands_planned = len(bands)
        report.bands = [asdict(b) for b in bands]
        
        if logger:
            logger.log('plan', num_bands=len(bands),
                      total_width=sum(b.width for b in bands))
        
        if verbose:
            print(f"Planned {len(bands)} bands")
        
        # Count total candidates (unbanded)
        delta_max = max(abs(b.delta_end) for b in bands)
        total_range = 2 * delta_max
        report.candidates_total = total_range
        
        # Count wheel-filtered candidates
        start_range = sqrt_N - delta_max
        end_range = sqrt_N + delta_max
        report.candidates_masked = count_admissible_in_range(start_range, end_range)
        
        if logger:
            logger.log('mask', candidates_total=report.candidates_total,
                      candidates_masked=report.candidates_masked,
                      reduction_pct=100*(1 - report.candidates_masked/report.candidates_total))
        
        # Pre-compute N embedding
        N_embedding = embed_torus_geodesic(N, k)
        
        # Scan each band
        all_peaks = []
        total_steps = 0
        early_exits = 0
        
        for band in bands:
            if verbose:
                print(f"  Scanning band {band.id}: δ=[{band.delta_start}, {band.delta_end}]")
            
            peaks, steps, exited = scan_band_Z5D(
                band, N, sqrt_N, N_embedding, k,
                max_steps=max_steps_per_band,
                early_exit=early_exit,
                tau_grad=tau_grad,
                tau_curv=tau_curv,
                L=L,
                logger=logger
            )
            
            all_peaks.extend(peaks)
            total_steps += steps
            if exited:
                early_exits += 1
        
        report.candidates_scanned = total_steps
        report.z5d_steps = total_steps
        report.early_exits = early_exits
        report.peaks_found = len(all_peaks)
        report.peaks = [asdict(p) for p in all_peaks]
        
        # Check if we found factors
        for peak in all_peaks:
            p = peak.candidate
            if N % p == 0:
                q = N // p
                report.factors_found = (p, q)
                break
    
    report.wall_time_sec = time.time() - start_time
    
    if logger:
        logger.log('complete', peaks_found=report.peaks_found,
                  z5d_steps=report.z5d_steps, early_exits=report.early_exits,
                  wall_time_sec=report.wall_time_sec,
                  factors_found=report.factors_found is not None)
        logger.close()
    
    if verbose:
        print(f"\nScan complete:")
        print(f"  Bands: {report.bands_planned}")
        print(f"  Steps: {report.z5d_steps}")
        print(f"  Early exits: {report.early_exits}")
        print(f"  Peaks: {report.peaks_found}")
        print(f"  Time: {report.wall_time_sec:.2f}s")
        if report.factors_found:
            print(f"  Factors: {report.factors_found}")
    
    return report


def compute_band_coverage(bands: List[Band], sqrt_N: int) -> float:
    """
    Compute coverage as fraction of expected gap mass covered.
    
    Args:
        bands: List of bands
        sqrt_N: Square root of N
        
    Returns:
        Coverage fraction [0, 1]
    """
    expected = expected_gap(float(sqrt_N))
    total_width = sum(b.width for b in bands)
    
    # Coverage = total band width / (expected gap × reasonable multiple)
    # A multiple of ~20 bands should give ~0.9 coverage
    return min(1.0, total_width / (20 * expected))


def compute_reduction_ratio(masked: int, unbanded: int) -> float:
    """
    Compute candidate reduction ratio.
    
    Args:
        masked: Number of candidates after wheel mask
        unbanded: Number of candidates without banding (raw range)
        
    Returns:
        Reduction ratio (1 - masked/unbanded)
    """
    if unbanded <= 0:
        return 0.0
    return 1.0 - (masked / unbanded)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Band-First Router + Early-Exit Guard Experiment")
    print("=" * 70)
    print()
    
    # Quick test on CHALLENGE_127
    N = CHALLENGE_127
    sqrt_N = isqrt(N)
    
    print(f"N = {N}")
    print(f"√N = {sqrt_N}")
    print(f"Bit-length: {N.bit_length()}")
    print(f"Expected gap: {expected_gap(float(sqrt_N)):.2f}")
    print()
    
    # Test band planning
    print("Testing band planning...")
    bands = plan_bands(N, C=0.9, alpha=1.0, num_bands=10)
    print(f"Planned {len(bands)} bands:")
    for i, band in enumerate(bands[:5]):
        print(f"  {i+1}. δ=[{band.delta_start}, {band.delta_end}], "
              f"density={band.expected_density:.6e}, priority={band.priority}")
    print()
    
    # Test wheel filtering
    print("Testing wheel filtering...")
    test_candidates = list(range(sqrt_N, sqrt_N + 1000))
    filtered = apply_wheel(test_candidates)
    reduction = compute_reduction_ratio(len(filtered), len(test_candidates))
    print(f"  Original: {len(test_candidates)} candidates")
    print(f"  Filtered: {len(filtered)} candidates")
    print(f"  Reduction: {reduction:.1%}")
    print()
    
    # Test flat detection
    print("Testing flat surface detection...")
    flat_amps = [0.5 + 1e-7 * i for i in range(10)]  # Nearly flat
    varied_amps = [0.5 + 0.1 * (i % 2) for i in range(10)]  # Varying
    print(f"  Flat amplitudes: is_flat={is_flat(flat_amps)}")
    print(f"  Varied amplitudes: is_flat={is_flat(varied_amps)}")
    print()
    
    print("Quick test complete. Run test_band_router.py for full experiments.")
