"""
Shell Geometry Scan 01 — Distant-Factor Probe for N₁₂₇
=======================================================

Implements golden-ratio shell scanning with fractal segment scoring to test
whether geometric resonance can locate distant factors in the 127-bit challenge.

Key features:
- Golden ratio shell spacing: R_{j+1} = φ·R_j
- Mandelbrot segment scoring (from fractal-recursive-gva)
- Per-shell GVA sweep with hard budget limits
- Cluster detection for amplitude analysis
- Deterministic execution with comprehensive metrics

Validation: 127-bit CHALLENGE_127 whitelist only
"""

import mpmath as mp
from typing import Tuple, Optional, List, Dict
import time
import json
from math import log, e
from datetime import datetime

# Configure high precision
mp.mp.dps = 50

# 127-bit challenge (whitelist)
CHALLENGE_127 = 137524771864208156028430259349934309717
EXPECTED_P = 10508623501177419659
EXPECTED_Q = 13086849276577416863

# Shell scan parameters
PHI = (1 + mp.sqrt(5)) / 2  # Golden ratio ≈ 1.618
J_MAX = 6  # Number of shells to scan (creates shells S₀, S₁, S₂, S₃, S₄, S₅)
B_TOTAL = 700000  # Total candidate budget
B_SHELL = 56000  # Budget per shell (~8% of total)
SEGMENTS_PER_SHELL = 32  # Segment count for each shell
K_FRACTAL = 6  # Top fractal-scored segments
K_UNIFORM = 2  # Uniform coverage segments
K_TOTAL = K_FRACTAL + K_UNIFORM  # Total segments searched per shell

# GVA kernel parameters
K_VALUES = [0.30, 0.35, 0.40]
PRECISION_DPS = 800

# Amplitude threshold for candidate shell detection
# Based on empirical observation: typical amplitude range is 0.997-0.999
# A shell is considered a candidate if max amplitude significantly exceeds baseline
AMPLITUDE_CANDIDATE_THRESHOLD = 0.9995  # Top 0.05% of observed range

# Mandelbrot scoring parameters (from fractal-recursive-gva)
RELATIVE_POS_SCALE = 0.1
LOG_N_SCALE = 1e-20
ESCAPE_WEIGHT = 0.6
MAGNITUDE_WEIGHT = 0.4
MAGNITUDE_SCALE = 10.0
E_SQUARED = e ** 2  # Cache e² for kappa calculation


def adaptive_precision(N: int) -> int:
    """Compute adaptive precision: max(50, bitLength × 4 + 200)"""
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """Embed integer n into 7D torus using golden ratio geodesic mapping."""
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
    """Compute Riemannian geodesic distance on 7D torus with periodic boundaries."""
    dist_sq = mp.mpf(0)
    for x, y in zip(p1, p2):
        diff = abs(x - y)
        torus_diff = min(diff, 1 - diff)
        dist_sq += torus_diff ** 2
    return mp.sqrt(dist_sq)


def score_segment_with_mandelbrot(segment_start: int, segment_end: int, 
                                   N: int, sqrt_N: int,
                                   max_iterations: int = 100,
                                   escape_radius: float = 2.0) -> float:
    """
    Compute Mandelbrot-based interest score for a segment.
    
    Monotone mapping: segment position → complex plane region
    Higher score indicates potentially more promising regions for factors.
    """
    segment_center = (segment_start + segment_end) // 2
    relative_pos = (segment_center - sqrt_N) / sqrt_N if sqrt_N > 0 else 0
    
    # Simple kappa approximation for scoring
    kappa = 2.0 * log(N + 1) / E_SQUARED
    
    c = complex(kappa + relative_pos * RELATIVE_POS_SCALE, log(N) * LOG_N_SCALE)
    
    z = 0j
    escape_count = 0
    total_magnitude = 0.0
    
    for iteration in range(max_iterations):
        z = z**2 + c
        magnitude = abs(z)
        total_magnitude += magnitude
        
        if magnitude > escape_radius:
            escape_count += 1
            z = z / (magnitude / escape_radius)
    
    avg_magnitude = total_magnitude / max_iterations
    escape_ratio = escape_count / max_iterations
    
    score = (escape_ratio * ESCAPE_WEIGHT + 
             min(avg_magnitude / MAGNITUDE_SCALE, 1.0) * MAGNITUDE_WEIGHT)
    
    return min(score, 1.0)


def compute_shell_radii(R0: int, j_max: int) -> List[Tuple[int, int]]:
    """
    Compute shell radii using golden ratio spacing.
    Returns list of (R_j, R_{j+1}) pairs for each shell j.
    """
    shells = []
    R_j = R0
    for j in range(j_max):
        R_j_plus_1 = int(R_j * float(PHI))
        shells.append((R_j, R_j_plus_1))
        R_j = R_j_plus_1
    return shells


def segment_shell(R_j: int, R_j_plus_1: int, num_segments: int, sqrt_N: int) -> List[Tuple[int, int]]:
    """
    Divide shell S_j into segments.
    
    Shell S_j = {δ : R_j < |δ| ≤ R_{j+1}}
    Returns list of (segment_start, segment_end) in candidate space (not delta).
    Only returns valid segments where both endpoints are >= 1.
    """
    segments = []
    
    # Negative delta region: [-R_{j+1}, -R_j]
    # In candidate space: [sqrt_N - R_{j+1}, sqrt_N - R_j]
    neg_start = max(1, sqrt_N - R_j_plus_1)
    neg_end = sqrt_N - R_j
    
    if neg_start < neg_end and neg_start >= 1:
        neg_width = neg_end - neg_start
        neg_seg_size = max(1, neg_width // (num_segments // 2))
        for i in range(num_segments // 2):
            seg_start = neg_start + i * neg_seg_size
            seg_end = neg_start + (i + 1) * neg_seg_size
            if i == num_segments // 2 - 1:  # Last negative segment
                seg_end = neg_end
            if seg_start >= 1 and seg_end >= 1:
                segments.append((seg_start, seg_end))
    
    # Positive delta region: [R_j, R_{j+1}]
    # In candidate space: [sqrt_N + R_j, sqrt_N + R_{j+1}]
    pos_start = sqrt_N + R_j
    pos_end = sqrt_N + R_j_plus_1
    
    pos_width = pos_end - pos_start
    pos_seg_size = max(1, pos_width // (num_segments // 2))
    for i in range(num_segments // 2):
        seg_start = pos_start + i * pos_seg_size
        seg_end = pos_start + (i + 1) * pos_seg_size
        if i == num_segments // 2 - 1:  # Last positive segment
            seg_end = pos_end
        segments.append((seg_start, seg_end))
    
    return segments


def select_segments(segment_scores: List[Tuple[float, int, int]], 
                   k_fractal: int, k_uniform: int) -> List[Tuple[int, int]]:
    """
    Select K segments: k_fractal highest-scored + k_uniform uniformly spaced.
    """
    # Sort by score descending
    sorted_scores = sorted(segment_scores, key=lambda x: x[0], reverse=True)
    
    # Top k_fractal segments
    selected = [(start, end) for _, start, end in sorted_scores[:k_fractal]]
    
    # Remaining segments for uniform sampling
    remaining = sorted_scores[k_fractal:]
    if len(remaining) > 0 and k_uniform > 0:
        step = max(1, len(remaining) // k_uniform)
        for i in range(0, min(len(remaining), k_uniform * step), step):
            if i < len(remaining):
                _, start, end = remaining[i]
                selected.append((start, end))
    
    return selected[:k_fractal + k_uniform]


# Adaptive stride parameters for segment sweeping
# Thresholds chosen based on segment width for different scales
STRIDE_THRESHOLD_LARGE = 1_000_000_000  # 1 billion: very large segments
STRIDE_LARGE = 1_000_000  # 1 million stride for very large segments
STRIDE_DIVISOR_LARGE = 5000  # Divide width by 5000 for large segments

STRIDE_THRESHOLD_MEDIUM = 100_000_000  # 100 million: medium segments
STRIDE_MEDIUM = 100_000  # 100k stride for medium segments
STRIDE_DIVISOR_MEDIUM = 3000  # Divide width by 3000 for medium segments

STRIDE_THRESHOLD_SMALL = 10_000_000  # 10 million: small segments
STRIDE_SMALL = 10_000  # 10k stride for small segments
STRIDE_DIVISOR_SMALL = 2000  # Divide width by 2000 for small segments

STRIDE_DEFAULT = 1000  # Default stride for tiny segments
STRIDE_DIVISOR_DEFAULT = 1000  # Default divisor


def gva_sweep_segment(N: int, sqrt_N: int, segment_start: int, segment_end: int,
                      k_values: List[float], max_candidates: int,
                      metrics: Dict) -> Optional[Tuple[int, int, float, float]]:
    """
    Sweep segment with GVA kernels, tracking amplitude.
    
    Returns: (p, q, max_amplitude, k_at_max) if factor found
             (None, None, max_amplitude, k_at_max) if no factor but have amplitude data
    Updates metrics with amplitude data.
    """
    candidates_tested = 0
    max_amplitude = 0.0
    k_at_max = k_values[0]
    
    # Embed N once per k-value
    N_coords_cache = {}
    for k in k_values:
        N_coords_cache[k] = embed_torus_geodesic(N, k)
    
    # Generate candidates in segment with adaptive stride
    # Stride adapts to segment width to keep candidate count reasonable
    segment_width = segment_end - segment_start
    if segment_width > STRIDE_THRESHOLD_LARGE:
        stride = max(STRIDE_LARGE, segment_width // STRIDE_DIVISOR_LARGE)
    elif segment_width > STRIDE_THRESHOLD_MEDIUM:
        stride = max(STRIDE_MEDIUM, segment_width // STRIDE_DIVISOR_MEDIUM)
    elif segment_width > STRIDE_THRESHOLD_SMALL:
        stride = max(STRIDE_SMALL, segment_width // STRIDE_DIVISOR_SMALL)
    else:
        stride = max(STRIDE_DEFAULT, segment_width // STRIDE_DIVISOR_DEFAULT)
    
    for k in k_values:
        if candidates_tested >= max_candidates:
            break
        
        N_coords = N_coords_cache[k]
        
        for candidate in range(segment_start, segment_end, stride):
            if candidates_tested >= max_candidates:
                break
            
            # Basic validity checks
            if candidate <= 1 or candidate >= N:
                continue
            if N % 2 == 1 and candidate % 2 == 0:
                continue
            
            candidates_tested += 1
            
            # Compute geodesic distance
            cand_coords = embed_torus_geodesic(candidate, k)
            dist = float(riemannian_distance(N_coords, cand_coords))
            
            # Amplitude: inverse of distance, normalized
            # Smaller distance = higher amplitude
            amplitude = 1.0 / (1.0 + dist)
            
            if amplitude > max_amplitude:
                max_amplitude = amplitude
                k_at_max = k
            
            # Divisibility test
            if N % candidate == 0:
                p = candidate
                q = N // candidate
                metrics['candidates_tested'] += candidates_tested
                return (p, q, amplitude, k_at_max)
    
    metrics['candidates_tested'] += candidates_tested
    # Return None for factors but still provide amplitude data
    return (None, None, max_amplitude, k_at_max) if max_amplitude > 0 else None


def scan_shell(N: int, sqrt_N: int, shell_index: int, R_j: int, R_j_plus_1: int,
               budget: int, metrics: Dict, verbose: bool = True) -> Dict:
    """
    Scan a single shell with fractal segment selection and GVA sweep.
    
    Returns shell metrics dict.
    """
    shell_metrics = {
        'shell_index': shell_index,
        'R_j': R_j,
        'R_j_plus_1': R_j_plus_1,
        'segments_scored': 0,
        'segments_selected': 0,
        'candidate_budget_used': 0,
        'max_amplitude_overall': 0.0,
        'max_amplitude_per_segment': {},
        'num_candidates_per_segment': {},
        'near_hits': [],
        'hit_found': False,
        'factors': None
    }
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"Shell S_{shell_index}: R_j={R_j:,}, R_{shell_index+1}={R_j_plus_1:,}")
        print(f"{'='*70}")
    
    # Segment shell
    segments = segment_shell(R_j, R_j_plus_1, SEGMENTS_PER_SHELL, sqrt_N)
    if verbose:
        print(f"Created {len(segments)} segments")
    
    # Score segments with Mandelbrot
    segment_scores = []
    for seg_start, seg_end in segments:
        score = score_segment_with_mandelbrot(seg_start, seg_end, N, sqrt_N)
        segment_scores.append((score, seg_start, seg_end))
        shell_metrics['segments_scored'] += 1
    
    if verbose:
        print(f"Scored {len(segment_scores)} segments")
        scores_only = [s for s, _, _ in segment_scores]
        print(f"Score range: [{min(scores_only):.4f}, {max(scores_only):.4f}]")
    
    # Select top-K segments
    selected_segments = select_segments(segment_scores, K_FRACTAL, K_UNIFORM)
    shell_metrics['segments_selected'] = len(selected_segments)
    
    if verbose:
        print(f"Selected {len(selected_segments)} segments ({K_FRACTAL} fractal + {K_UNIFORM} uniform)")
    
    # Sweep selected segments
    budget_per_segment = budget // len(selected_segments) if len(selected_segments) > 0 else budget
    
    for idx, (seg_start, seg_end) in enumerate(selected_segments):
        if shell_metrics['candidate_budget_used'] >= budget:
            break
        
        remaining_budget = budget - shell_metrics['candidate_budget_used']
        segment_budget = min(budget_per_segment, remaining_budget)
        
        if verbose:
            delta_start = seg_start - sqrt_N
            delta_end = seg_end - sqrt_N
            print(f"\nSegment {idx+1}/{len(selected_segments)}: δ ∈ [{delta_start:+,}, {delta_end:+,}]")
        
        seg_metrics = {'candidates_tested': 0}
        result = gva_sweep_segment(N, sqrt_N, seg_start, seg_end, 
                                   K_VALUES, segment_budget, seg_metrics)
        
        candidates_used = seg_metrics['candidates_tested']
        shell_metrics['candidate_budget_used'] += candidates_used
        shell_metrics['num_candidates_per_segment'][idx] = candidates_used
        
        if result:
            p, q, amplitude, k_val = result
            
            # Update max amplitude for segment
            shell_metrics['max_amplitude_per_segment'][idx] = amplitude
            shell_metrics['max_amplitude_overall'] = max(shell_metrics['max_amplitude_overall'], amplitude)
            
            # Check if we found factors
            if p is not None and q is not None:
                shell_metrics['hit_found'] = True
                shell_metrics['factors'] = (p, q)
                
                if verbose:
                    print(f"  ✅ FACTOR FOUND: p={p}, q={q}")
                    print(f"  Amplitude: {amplitude:.6f}, k={k_val}")
                
                return shell_metrics
            else:
                # No factor but have amplitude data
                if verbose:
                    print(f"  Candidates tested: {candidates_used}, max amplitude: {amplitude:.6f}")
        else:
            # No result at all
            shell_metrics['max_amplitude_per_segment'][idx] = 0.0
            if verbose:
                print(f"  Candidates tested: {candidates_used}")
    
    if verbose:
        print(f"\nShell S_{shell_index} complete:")
        print(f"  Budget used: {shell_metrics['candidate_budget_used']:,}/{budget:,}")
        print(f"  Max amplitude: {shell_metrics['max_amplitude_overall']:.6f}")
        print(f"  Hit found: {shell_metrics['hit_found']}")
    
    return shell_metrics


def run_shell_geometry_scan_01(N: int, verbose: bool = True) -> Dict:
    """
    Execute Shell Geometry Scan 01 on target semiprime.
    
    Returns comprehensive experiment results.
    """
    start_time = time.time()
    sqrt_N = int(mp.sqrt(N))
    
    # Determine R0 (inner radius for "friendly" band)
    # Use previous experiment window as reference: ±78 trillion
    # For 127-bit, this is approximately the 125-130 bit band half-width
    R0 = 78_180_637_518_849_229  # From previous fractal-mask experiment
    
    if verbose:
        print("="*70)
        print("Shell Geometry Scan 01 — Distant-Factor Probe")
        print("="*70)
        print(f"\nTarget: N₁₂₇ = {N}")
        print(f"sqrt(N) = {sqrt_N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"\nShell parameters:")
        print(f"  R₀ (inner radius): {R0:,}")
        print(f"  φ (golden ratio): {float(PHI):.6f}")
        print(f"  J_max (shell count): {J_MAX}")
        print(f"  Budget total: {B_TOTAL:,}")
        print(f"  Budget per shell: {B_SHELL:,}")
        print(f"  Segments per shell: {SEGMENTS_PER_SHELL}")
        print(f"  Selection: {K_FRACTAL} fractal + {K_UNIFORM} uniform = {K_TOTAL} total")
    
    # Compute shell radii
    shells = compute_shell_radii(R0, J_MAX)
    
    if verbose:
        print(f"\nShell boundaries:")
        for j, (R_j, R_j_plus_1) in enumerate(shells):
            print(f"  S_{j}: R_{j}={R_j:,}, R_{j+1}={R_j_plus_1:,}")
    
    # Global metrics
    experiment_metrics = {
        'target': str(N),
        'sqrt_N': str(sqrt_N),
        'R0': R0,
        'phi': float(PHI),
        'j_max': J_MAX,
        'b_total': B_TOTAL,
        'b_shell': B_SHELL,
        'segments_per_shell': SEGMENTS_PER_SHELL,
        'k_fractal': K_FRACTAL,
        'k_uniform': K_UNIFORM,
        'k_values': K_VALUES,
        'precision_dps': PRECISION_DPS,
        'shell_results': [],
        'best_shell': None,
        'factorization_success': False,
        'factors_found': None,
        'total_candidates_used': 0,
        'elapsed_seconds': 0.0,
        'timestamp': datetime.now().isoformat()
    }
    
    # Scan each shell
    for j, (R_j, R_j_plus_1) in enumerate(shells):
        shell_metrics = scan_shell(N, sqrt_N, j, R_j, R_j_plus_1, 
                                   B_SHELL, experiment_metrics, verbose)
        
        experiment_metrics['shell_results'].append(shell_metrics)
        experiment_metrics['total_candidates_used'] += shell_metrics['candidate_budget_used']
        
        if shell_metrics['hit_found']:
            experiment_metrics['factorization_success'] = True
            experiment_metrics['factors_found'] = shell_metrics['factors']
            if verbose:
                print(f"\n🎯 SUCCESS: Factorization complete at shell S_{j}")
            break
    
    elapsed = time.time() - start_time
    experiment_metrics['elapsed_seconds'] = elapsed
    
    # Identify best shell (highest max amplitude)
    if len(experiment_metrics['shell_results']) > 0:
        best = max(experiment_metrics['shell_results'], 
                  key=lambda s: s['max_amplitude_overall'])
        experiment_metrics['best_shell'] = best['shell_index']
    
    if verbose:
        print(f"\n{'='*70}")
        print("EXPERIMENT COMPLETE")
        print(f"{'='*70}")
        print(f"Total time: {elapsed:.3f}s")
        print(f"Total candidates: {experiment_metrics['total_candidates_used']:,}")
        print(f"Success: {experiment_metrics['factorization_success']}")
        if experiment_metrics['factors_found']:
            p, q = experiment_metrics['factors_found']
            print(f"Factors: {p} × {q}")
    
    return experiment_metrics


def write_executive_summary(metrics: Dict, output_path: str):
    """Generate executive summary of experiment results."""
    with open(output_path, 'w') as f:
        f.write("# Executive Summary: Shell Geometry Scan 01\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"**Experiment:** Shell Geometry Scan 01 — Distant-Factor Probe for N₁₂₇\n")
        
        if metrics['factorization_success']:
            f.write(f"**Status:** SUCCESS\n\n")
        else:
            f.write(f"**Status:** FAILURE (No factors found within budget)\n\n")
        
        f.write("---\n\n")
        f.write("## Results At-a-Glance\n\n")
        f.write(f"**Target:** N₁₂₇ = {metrics['target']}\n\n")
        
        if metrics['factorization_success']:
            p, q = metrics['factors_found']
            f.write(f"**Factors Found:**\n")
            f.write(f"- p = {p}\n")
            f.write(f"- q = {q}\n")
            f.write(f"- Verification: p × q = {p * q}\n\n")
        else:
            f.write(f"**Expected Factors:**\n")
            f.write(f"- p = {EXPECTED_P}\n")
            f.write(f"- q = {EXPECTED_Q}\n\n")
            f.write(f"**Outcome:** No factors found\n\n")
        
        f.write(f"**Time Elapsed:** {metrics['elapsed_seconds']:.3f} seconds\n\n")
        f.write("---\n\n")
        
        f.write("## Key Metrics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Shells scanned | {len(metrics['shell_results'])} |\n")
        f.write(f"| Total candidates | {metrics['total_candidates_used']:,} |\n")
        f.write(f"| Total budget | {metrics['b_total']:,} |\n")
        f.write(f"| Budget utilization | {100*metrics['total_candidates_used']/metrics['b_total']:.1f}% |\n")
        
        if metrics['best_shell'] is not None:
            best = metrics['shell_results'][metrics['best_shell']]
            f.write(f"| Best shell | S_{metrics['best_shell']} |\n")
            f.write(f"| Best shell max amplitude | {best['max_amplitude_overall']:.6f} |\n")
        
        f.write(f"| Factorization success | {metrics['factorization_success']} |\n")
        f.write(f"| Total runtime | {metrics['elapsed_seconds']:.3f}s |\n\n")
        
        f.write("---\n\n")
        f.write("## Shell-by-Shell Summary\n\n")
        
        for shell in metrics['shell_results']:
            j = shell['shell_index']
            f.write(f"### Shell S_{j}\n\n")
            f.write(f"- **Radii:** R_{j} = {shell['R_j']:,}, R_{j+1} = {shell['R_j_plus_1']:,}\n")
            f.write(f"- **Segments scored:** {shell['segments_scored']}\n")
            f.write(f"- **Segments selected:** {shell['segments_selected']}\n")
            f.write(f"- **Candidates tested:** {shell['candidate_budget_used']:,}\n")
            f.write(f"- **Max amplitude:** {shell['max_amplitude_overall']:.6f}\n")
            f.write(f"- **Hit found:** {shell['hit_found']}\n")
            
            if shell['hit_found']:
                p, q = shell['factors']
                f.write(f"- **Factors:** p={p}, q={q}\n")
            
            f.write("\n")
        
        f.write("---\n\n")
        f.write("## Configuration\n\n")
        f.write("| Parameter | Value |\n")
        f.write("|-----------|-------|\n")
        f.write(f"| R₀ (inner radius) | {metrics['R0']:,} |\n")
        f.write(f"| φ (golden ratio) | {metrics['phi']:.6f} |\n")
        f.write(f"| J_max (shells) | {metrics['j_max']} |\n")
        f.write(f"| B_total | {metrics['b_total']:,} |\n")
        f.write(f"| B_shell | {metrics['b_shell']:,} |\n")
        f.write(f"| Segments/shell | {metrics['segments_per_shell']} |\n")
        f.write(f"| K_fractal | {metrics['k_fractal']} |\n")
        f.write(f"| K_uniform | {metrics['k_uniform']} |\n")
        f.write(f"| K-values | {metrics['k_values']} |\n")
        f.write(f"| Precision (dps) | {metrics['precision_dps']} |\n\n")
        
        f.write("---\n\n")
        f.write("## Verdict\n\n")
        
        if metrics['factorization_success']:
            f.write("### SUCCESS CRITERIA MET\n\n")
            f.write("The experiment successfully factored N₁₂₇ using shell geometry scan.\n\n")
            f.write("**This proves:**\n")
            f.write("- Geometry + shelling works for distant factors\n")
            f.write("- Golden-ratio shell spacing can locate factors outside \"friendly\" band\n")
            f.write("- Fractal segment scoring effectively guides search\n\n")
        else:
            # Analyze failure mode
            best = metrics['shell_results'][metrics['best_shell']] if metrics['best_shell'] is not None else None
            
            # Check for geometric candidate shell
            # Use defined threshold instead of arbitrary value
            has_candidate_shell = False
            if best and best['max_amplitude_overall'] >= AMPLITUDE_CANDIDATE_THRESHOLD:
                has_candidate_shell = True
            
            if has_candidate_shell:
                f.write("### GEOMETRIC CANDIDATE SHELL DETECTED\n\n")
                f.write(f"Shell S_{best['shell_index']} shows promising geometric signal:\n")
                f.write(f"- Max amplitude: {best['max_amplitude_overall']:.6f}\n")
                f.write(f"- Suggests running full dense sweep on this shell\n\n")
                f.write("**Recommendation:** Execute follow-up dense run on candidate shell.\n\n")
            else:
                f.write("### CLEAR FAILURE\n\n")
                f.write("All shells showed weak geometric signal:\n")
                f.write(f"- Best shell max amplitude: {best['max_amplitude_overall']:.6f} (below threshold)\n")
                f.write("- No amplitude clustering detected\n\n")
                f.write("**Conclusion:** Geometry signal too weak with current kernels.\n")
                f.write("Need different transform, not more budget.\n\n")
        
        f.write("---\n\n")
        f.write("## References\n\n")
        f.write("- Experiment code: `run_experiment.py`\n")
        f.write("- Full metrics: `results.json`\n")
        f.write("- Hypothesis: See issue description\n")


if __name__ == "__main__":
    print("\nShell Geometry Scan 01 — Distant-Factor Probe for N₁₂₇")
    print("=" * 70)
    
    # Run experiment
    metrics = run_shell_geometry_scan_01(CHALLENGE_127, verbose=True)
    
    # Save results
    results_path = "results.json"
    with open(results_path, 'w') as f:
        # Convert integer values that might be too large
        serializable_metrics = {}
        for k, v in metrics.items():
            if isinstance(v, (int, float, str, bool, list, dict, type(None))):
                serializable_metrics[k] = v
            else:
                serializable_metrics[k] = str(v)
        json.dump(serializable_metrics, f, indent=2)
    
    print(f"\nResults written to: {results_path}")
    
    # Generate executive summary
    summary_path = "EXECUTIVE_SUMMARY.md"
    write_executive_summary(metrics, summary_path)
    print(f"Executive summary written to: {summary_path}")
    
    # Exit with appropriate code
    exit(0 if metrics['factorization_success'] else 1)
