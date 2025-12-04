#!/usr/bin/env python3
"""
GEOFAC Scaling Analysis
=======================

Reveals GEOFAC's scaling behavior through diagnostic visualizations:
1. Log-log plot: trials vs √N with regression and 95% CI
2. Survival curve: rank of true factor with bootstrap CI

Validation: Only works in operational range [10^14, 10^18] or 127-bit challenge.

Usage:
    python3 scripts/scaling_analysis.py --output-dir results/scaling --num-samples 10
    python3 scripts/scaling_analysis.py --output-dir results/scaling --num-samples 20 --verbose
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Add repo root for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import mpmath as mp
from gva_factorization import (
    CHALLENGE_127,
    RANGE_MIN,
    RANGE_MAX,
    adaptive_precision,
    embed_torus_geodesic,
    riemannian_distance,
)

# Constants
SEED = 20241204  # Pinned seed for reproducibility
RNG = np.random.default_rng(SEED)

# Pre-registered thresholds (success criteria)
THRESHOLD_MEDIAN_RANK = 100
THRESHOLD_S100 = 0.2  # P(rank > 100) should be ≤ 0.2


def validate_n(n: int) -> bool:
    """Validate N is in operational range or whitelisted 127-bit challenge."""
    if n == CHALLENGE_127:
        return True
    return RANGE_MIN <= n <= RANGE_MAX


def is_prime(n: int) -> bool:
    """Miller-Rabin primality test."""
    n = int(n)  # Ensure Python int
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
    
    # Witnesses for deterministic test up to 3,317,044,064,679,887,385,961,981
    witnesses = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    
    for a in witnesses:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def next_prime(n: int) -> int:
    """Find next prime >= n."""
    n = int(n)  # Ensure Python int
    if n <= 2:
        return 2
    if n % 2 == 0:
        n += 1
    while not is_prime(n):
        n += 2
    return n


def generate_balanced_semiprime(target_bits: int, rng: np.random.Generator) -> Tuple[int, int, int]:
    """
    Generate a balanced semiprime N = p * q where p ≈ q.
    
    Ensures N is within operational range [RANGE_MIN, RANGE_MAX].
    
    Args:
        target_bits: Target bit length for N
        rng: Random number generator
        
    Returns:
        Tuple (N, p, q)
    """
    max_attempts = 10
    
    for _ in range(max_attempts):
        half_bits = target_bits // 2
        
        # Generate p near 2^(half_bits) with controlled offset
        base = 1 << half_bits
        max_offset = max(1, base // 20)  # Smaller offset for tighter control
        offset = rng.integers(0, max_offset)
        p = next_prime(base + offset)
        
        # Generate q near p (balanced semiprime)
        q_offset = rng.integers(1, 500)
        q = next_prime(p + q_offset * 2)
        
        N = p * q
        
        # Check if in range
        if RANGE_MIN <= N <= RANGE_MAX:
            return N, min(p, q), max(p, q)
        
        # If too large, try smaller factors
        if N > RANGE_MAX:
            target_bits -= 1
            continue
        
        # If too small, try larger factors
        if N < RANGE_MIN:
            target_bits += 1
            continue
    
    # Fallback: generate something in middle of range
    # (RANGE_MIN * RANGE_MAX)^0.25 = (geometric_mean)^0.5 ≈ target p,q
    target_sqrt = int((RANGE_MIN * RANGE_MAX) ** 0.25)
    p = next_prime(target_sqrt)
    q = next_prime(p + rng.integers(100, 1000))
    N = p * q
    return N, min(p, q), max(p, q)


def factor_with_tracking(
    N: int,
    p_true: int,
    q_true: int,
    k_values: Optional[List[float]] = None,
    max_candidates: int = 10000,
    verbose: bool = False
) -> Tuple[int, int]:
    """
    Factor N while tracking trials and rank.
    
    Returns:
        (trials_to_hit, rank_of_hit)
        - trials_to_hit: Number of candidates tested until factor found
        - rank_of_hit: Position in ranked candidate list where true factor appears
    """
    if k_values is None:
        k_values = [0.30, 0.35, 0.40]
    
    required_dps = adaptive_precision(N)
    
    with mp.workdps(required_dps):
        sqrt_N = int(mp.sqrt(N))
        bit_length = N.bit_length()
        
        # Use fixed window for faster analysis (goal: measure ranking quality)
        # Window is capped to keep runtime reasonable for large N
        base_window = 10000  # Fixed window for consistent analysis
        
        if verbose:
            print(f"  N = {N}, bits = {bit_length}, sqrt(N) ≈ {sqrt_N}")
            print(f"  Window = ±{base_window}, precision = {required_dps} dps")
        
        # Generate candidates with distances (for ranking)
        best_k = k_values[0]
        N_coords = embed_torus_geodesic(N, best_k)
        
        # Sample offsets - limit to reasonable number for analysis
        num_samples = min(2000, 2 * base_window)
        sample_step = max(1, (2 * base_window) // num_samples)
        offsets = list(range(-base_window, base_window + 1, sample_step))
        
        # Also ensure true factor offset is in sample if within window
        true_factor = min(p_true, q_true)  # Smaller factor is closer to sqrt(N)
        true_offset = true_factor - sqrt_N
        if abs(true_offset) <= base_window:
            offsets.append(true_offset)
            offsets = list(set(offsets))  # Remove duplicates
        
        candidates_with_dist = []
        for offset in offsets:
            candidate = sqrt_N + offset
            if candidate <= 1 or candidate >= N:
                continue
            if candidate % 2 == 0:
                continue
            
            cand_coords = embed_torus_geodesic(candidate, best_k)
            dist = float(riemannian_distance(N_coords, cand_coords))
            candidates_with_dist.append((dist, candidate))
        
        # Sort by distance (ascending)
        candidates_with_dist.sort()
        
        # Find rank of true factor in sorted list
        rank_of_hit = -1
        for i, (_, cand) in enumerate(candidates_with_dist):
            if cand == p_true or cand == q_true:
                rank_of_hit = i + 1  # 1-indexed
                break
        
        # Count trials to hit using ranked search
        trials_to_hit = 0
        found = False
        
        for dist, cand in candidates_with_dist:
            trials_to_hit += 1
            if N % cand == 0:
                found = True
                break
            if trials_to_hit >= max_candidates:
                break
        
        # If rank not found in sample, use trials as estimate
        if rank_of_hit == -1:
            rank_of_hit = trials_to_hit if found else len(candidates_with_dist) + 1
        
        if verbose:
            print(f"  Found: {found}, trials = {trials_to_hit}, rank = {rank_of_hit}")
        
        return trials_to_hit, rank_of_hit


def collect_data(
    num_samples: int,
    bit_range: Tuple[int, int],
    output_dir: Path,
    verbose: bool = False
) -> List[dict]:
    """
    Collect scaling data for analysis.
    
    Args:
        num_samples: Number of semiprimes to test
        bit_range: (min_bits, max_bits) for N
        output_dir: Directory to save data
        verbose: Enable detailed logging
        
    Returns:
        List of data records
    """
    min_bits, max_bits = bit_range
    data = []
    
    # Distribute samples across bit range
    if num_samples == 1:
        bit_sizes = [(min_bits + max_bits) // 2]
    else:
        bit_sizes = np.linspace(min_bits, max_bits, num_samples, dtype=int)
    
    print(f"\nCollecting data for {num_samples} semiprimes ({min_bits}-{max_bits} bits)")
    print(f"Seed: {SEED}")
    print("-" * 60)
    
    for i, target_bits in enumerate(bit_sizes):
        print(f"\n[{i+1}/{num_samples}] Generating {target_bits}-bit semiprime...")
        
        # Generate semiprime
        N, p, q = generate_balanced_semiprime(int(target_bits), RNG)
        
        # Validate it's in operational range
        if not validate_n(N):
            print(f"  SKIP: N={N} outside operational range")
            continue
        
        sqrt_N = int(mp.sqrt(N))
        
        # Run factorization with tracking
        start_time = time.time()
        trials, rank = factor_with_tracking(N, p, q, verbose=verbose)
        elapsed = time.time() - start_time
        
        record = {
            'N': N,
            'bit_length': N.bit_length(),
            'sqrt_N': sqrt_N,
            'trials_to_hit': trials,
            'rank_of_hit': rank,
            'p': p,
            'q': q,
            'time_s': elapsed
        }
        data.append(record)
        
        print(f"  N = {N}")
        print(f"  bits = {record['bit_length']}, trials = {trials}, rank = {rank}, time = {elapsed:.2f}s")
    
    return data


def save_csv(data: List[dict], output_path: Path) -> None:
    """Save data to CSV file."""
    if not data:
        return
    
    fieldnames = ['N', 'bit_length', 'sqrt_N', 'trials_to_hit', 'rank_of_hit', 'p', 'q', 'time_s']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def compute_regression(x: np.ndarray, y: np.ndarray) -> dict:
    """
    Compute log-log regression with 95% CI.
    
    Requires at least 3 data points for valid degrees of freedom.
    
    Returns:
        Dict with slope, intercept, r_squared, slope_ci, p_value_slope_1
    """
    n = len(x)
    if n < 3:
        # Not enough data for valid regression CI
        return {
            'slope': np.nan,
            'intercept': np.nan,
            'r_squared': np.nan,
            'slope_ci': (np.nan, np.nan),
            'std_err': np.nan,
            'p_value_slope_1': np.nan
        }
    
    log_x = np.log(x)
    log_y = np.log(y)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
    
    dof = n - 2  # Degrees of freedom, guaranteed >= 1 since n >= 3
    t_crit = stats.t.ppf(0.975, dof)
    slope_ci = (slope - t_crit * std_err, slope + t_crit * std_err)
    
    # Hypothesis test: slope = 1.0
    if std_err > 0:
        t_stat = (slope - 1.0) / std_err
        p_value_slope_1 = 2 * (1 - stats.t.cdf(abs(t_stat), dof))
    else:
        p_value_slope_1 = 1.0  # No variance, can't test
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value ** 2,
        'slope_ci': slope_ci,
        'std_err': std_err,
        'p_value_slope_1': p_value_slope_1
    }


def plot_loglog(data: List[dict], output_path: Path) -> dict:
    """
    Create log-log plot of trials vs √N.
    
    Returns:
        Regression statistics
    """
    if len(data) < 3:
        print("Not enough data for log-log plot (need at least 3 points)")
        return {}
    
    sqrt_N = np.array([d['sqrt_N'] for d in data], dtype=float)
    trials = np.array([d['trials_to_hit'] for d in data], dtype=float)
    
    # Filter out zeros
    mask = (sqrt_N > 0) & (trials > 0)
    sqrt_N = sqrt_N[mask]
    trials = trials[mask]
    
    if len(sqrt_N) < 3:
        print("Not enough valid data points for regression (need at least 3)")
        return {}
    
    # Compute regression
    reg = compute_regression(sqrt_N, trials)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Data points with jitter and transparency
    jitter = np.exp(RNG.normal(0, 0.02, len(sqrt_N)))
    ax.scatter(sqrt_N * jitter, trials, alpha=0.6, s=50, c='steelblue', 
               edgecolors='white', linewidth=0.5, label='Observed')
    
    # Regression line
    x_line = np.logspace(np.log10(sqrt_N.min()), np.log10(sqrt_N.max()), 100)
    y_line = np.exp(reg['intercept']) * (x_line ** reg['slope'])
    ax.plot(x_line, y_line, 'r-', linewidth=2, 
            label=f'Fit: slope={reg["slope"]:.3f} (R²={reg["r_squared"]:.3f})')
    
    # 95% CI band (n >= 3 guaranteed by earlier check)
    n = len(sqrt_N)
    dof = n - 2
    log_x = np.log(sqrt_N)
    log_x_line = np.log(x_line)
    x_mean = np.mean(log_x)
    ss_x = np.sum((log_x - x_mean) ** 2)
    
    se_fit = reg['std_err'] * np.sqrt(1/n + (log_x_line - x_mean)**2 / ss_x)
    t_crit = stats.t.ppf(0.975, dof)
    
    y_upper = np.exp(reg['intercept'] + reg['slope'] * log_x_line + t_crit * se_fit)
    y_lower = np.exp(reg['intercept'] + reg['slope'] * log_x_line - t_crit * se_fit)
    
    ax.fill_between(x_line, y_lower, y_upper, alpha=0.2, color='red', label='95% CI')
    
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('√N', fontsize=12)
    ax.set_ylabel('Trials to Hit', fontsize=12)
    ax.set_title('GEOFAC Scaling: Trials vs √N (Log-Log)', fontsize=14)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3, which='both')
    
    # Add stats text box
    stats_text = (
        f"Slope: {reg['slope']:.3f} ± {t_crit * reg['std_err']:.3f}\n"
        f"R²: {reg['r_squared']:.4f}\n"
        f"p-value (H₀: slope=1): {reg['p_value_slope_1']:.4f}"
    )
    ax.text(0.97, 0.03, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    print(f"Saved log-log plot: {output_path}")
    return reg


def bootstrap_survival(ranks: np.ndarray, n_bootstrap: int = 10000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute survival curve S(k) = P(rank > k) with bootstrap CI.
    
    Returns:
        (k_values, survival_mean, survival_ci)
    """
    max_rank = int(np.max(ranks)) + 100
    k_values = np.arange(1, max_rank + 1)
    
    # Bootstrap resampling
    survival_samples = np.zeros((n_bootstrap, len(k_values)))
    
    for b in range(n_bootstrap):
        sample = RNG.choice(ranks, size=len(ranks), replace=True)
        for i, k in enumerate(k_values):
            survival_samples[b, i] = np.mean(sample > k)
    
    survival_mean = np.mean(survival_samples, axis=0)
    survival_lower = np.percentile(survival_samples, 2.5, axis=0)
    survival_upper = np.percentile(survival_samples, 97.5, axis=0)
    
    return k_values, survival_mean, (survival_lower, survival_upper)


def plot_survival(data: List[dict], output_path: Path) -> dict:
    """
    Create survival curve plot for rank of true factor.
    
    Returns:
        Survival statistics
    """
    if len(data) < 2:
        print("Not enough data for survival curve (need at least 2 points)")
        return {}
    
    ranks = np.array([d['rank_of_hit'] for d in data], dtype=float)
    ranks = ranks[ranks > 0]  # Filter invalid ranks
    
    if len(ranks) < 2:
        print("Not enough valid ranks for survival analysis")
        return {}
    
    # Compute bootstrap survival
    k_values, survival_mean, (survival_lower, survival_upper) = bootstrap_survival(ranks)
    
    # Compute statistics
    median_rank = np.median(ranks)
    auc = np.trapezoid(survival_mean, k_values)  # Area under curve (lower is better)
    
    # S(k) values: P(rank > k)
    s10 = np.mean(ranks > 10)
    s100 = np.mean(ranks > 100)
    s1000 = np.mean(ranks > 1000)
    
    # P(rank ≤ k) = 1 - S(k)
    p10 = 1 - s10
    p100 = 1 - s100
    p1000 = 1 - s1000
    
    stats_dict = {
        'median_rank': median_rank,
        'auc': auc,
        's10': s10,
        's100': s100,
        's1000': s1000,
        'p10': p10,
        'p100': p100,
        'p1000': p1000
    }
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 7))
    
    ax.plot(k_values, survival_mean, 'b-', linewidth=2, label='S(k) = P(rank > k)')
    ax.fill_between(k_values, survival_lower, survival_upper, alpha=0.3, color='blue',
                    label='95% CI (10k bootstrap)')
    
    # Mark key thresholds
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=median_rank, color='green', linestyle='--', alpha=0.7, 
               label=f'Median rank = {median_rank:.0f}')
    ax.axvline(x=100, color='orange', linestyle=':', alpha=0.7,
               label=f'k=100, S(100)={s100:.3f}')
    
    ax.set_xlabel('Rank k', fontsize=12)
    ax.set_ylabel('S(k) = P(rank > k)', fontsize=12)
    ax.set_title('GEOFAC Survival Curve: Rank of True Factor', fontsize=14)
    ax.set_xlim(0, min(max(k_values), 2000))
    ax.set_ylim(0, 1.05)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Add stats text box
    stats_text = (
        f"Median rank: {median_rank:.0f}\n"
        f"AUC: {auc:.1f}\n"
        f"P(r≤10): {p10:.3f}\n"
        f"P(r≤100): {p100:.3f}\n"
        f"P(r≤1000): {p1000:.3f}"
    )
    ax.text(0.97, 0.97, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    print(f"Saved survival curve: {output_path}")
    return stats_dict


def compute_binned_stats(data: List[dict]) -> List[dict]:
    """Compute statistics per bit-range bin."""
    if not data:
        return []
    
    # Group by 10-bit bins
    bins = {}
    for d in data:
        bin_start = (d['bit_length'] // 10) * 10
        bin_label = f"{bin_start}-{bin_start+9}"
        if bin_label not in bins:
            bins[bin_label] = []
        bins[bin_label].append(d)
    
    results = []
    for bin_label in sorted(bins.keys()):
        records = bins[bin_label]
        trials = np.array([r['trials_to_hit'] for r in records])
        ranks = np.array([r['rank_of_hit'] for r in records])
        sqrt_Ns = np.array([r['sqrt_N'] for r in records], dtype=float)
        
        result = {
            'bin': bin_label,
            'n_samples': len(records),
            'median_trials': np.median(trials),
            'p90_trials': np.percentile(trials, 90) if len(trials) > 0 else 0,
            'median_rank': np.median(ranks),
        }
        
        # Compute slope for bin if enough data (need >=3 for positive dof)
        if len(records) >= 3:
            mask = (sqrt_Ns > 0) & (trials > 0)
            if np.sum(mask) >= 3:
                reg = compute_regression(sqrt_Ns[mask], trials[mask])
                if not np.isnan(reg['slope']):
                    dof = np.sum(mask) - 2
                    t_crit = stats.t.ppf(0.975, dof)
                    result['slope'] = reg['slope']
                    result['slope_ci'] = f"±{t_crit * reg['std_err']:.3f}"
                else:
                    result['slope'] = None
                    result['slope_ci'] = "N/A"
            else:
                result['slope'] = None
                result['slope_ci'] = "N/A"
        else:
            result['slope'] = None
            result['slope_ci'] = "N/A"
        
        results.append(result)
    
    return results


def print_tables(data: List[dict], reg_stats: dict, survival_stats: dict) -> str:
    """Print and return formatted statistics tables."""
    lines = []
    
    lines.append("\n" + "=" * 70)
    lines.append("SCALING TABLE (per bit-range bin)")
    lines.append("=" * 70)
    
    binned = compute_binned_stats(data)
    lines.append(f"{'Bit Range':<12} {'N':<5} {'Slope':<12} {'Median Trials':<15} {'P90 Trials':<12}")
    lines.append("-" * 60)
    for b in binned:
        slope_str = f"{b['slope']:.3f} {b['slope_ci']}" if b['slope'] is not None else "N/A"
        lines.append(f"{b['bin']:<12} {b['n_samples']:<5} {slope_str:<12} {b['median_trials']:<15.0f} {b['p90_trials']:<12.0f}")
    
    lines.append("\n" + "=" * 70)
    lines.append("OVERALL REGRESSION STATISTICS")
    lines.append("=" * 70)
    
    if reg_stats:
        ci_low, ci_high = reg_stats.get('slope_ci', (0, 0))
        lines.append(f"Slope: {reg_stats['slope']:.4f} [{ci_low:.4f}, {ci_high:.4f}]")
        lines.append(f"R²: {reg_stats['r_squared']:.4f}")
        lines.append(f"p-value (H₀: slope=1): {reg_stats['p_value_slope_1']:.4f}")
    else:
        lines.append("Insufficient data for regression")
    
    lines.append("\n" + "=" * 70)
    lines.append("CONSISTENCY TABLE (rank statistics)")
    lines.append("=" * 70)
    
    if survival_stats:
        lines.append(f"Median rank: {survival_stats['median_rank']:.0f}")
        lines.append(f"AUC: {survival_stats['auc']:.1f} (lower is better)")
        lines.append(f"P(r ≤ 10): {survival_stats['p10']:.3f}")
        lines.append(f"P(r ≤ 100): {survival_stats['p100']:.3f}")
        lines.append(f"P(r ≤ 1000): {survival_stats['p1000']:.3f}")
        lines.append(f"S(10): {survival_stats['s10']:.3f}")
        lines.append(f"S(100): {survival_stats['s100']:.3f}")
        lines.append(f"S(1000): {survival_stats['s1000']:.3f}")
    else:
        lines.append("Insufficient data for survival analysis")
    
    lines.append("\n" + "=" * 70)
    lines.append("PRE-REGISTERED SUCCESS CRITERIA")
    lines.append("=" * 70)
    
    if survival_stats:
        median_ok = survival_stats['median_rank'] <= THRESHOLD_MEDIAN_RANK
        s100_ok = survival_stats['s100'] <= THRESHOLD_S100
        
        lines.append(f"Median rank ≤ {THRESHOLD_MEDIAN_RANK}: {'✓ PASS' if median_ok else '✗ FAIL'} ({survival_stats['median_rank']:.0f})")
        lines.append(f"S(100) ≤ {THRESHOLD_S100}: {'✓ PASS' if s100_ok else '✗ FAIL'} ({survival_stats['s100']:.3f})")
        lines.append(f"Overall: {'✓ SUCCESS' if median_ok and s100_ok else '✗ FAILURE'}")
    else:
        lines.append("Insufficient data to evaluate criteria")
    
    output = "\n".join(lines)
    print(output)
    return output


def main():
    parser = argparse.ArgumentParser(
        description='GEOFAC Scaling Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--output-dir', type=str, default='results/scaling',
                        help='Output directory for results (default: results/scaling)')
    parser.add_argument('--num-samples', type=int, default=10,
                        help='Number of test semiprimes (default: 10)')
    parser.add_argument('--min-bits', type=int, default=48,
                        help='Minimum bit length for N (default: 48, gives N ≥ 10^14)')
    parser.add_argument('--max-bits', type=int, default=60,
                        help='Maximum bit length for N (default: 60, gives N ≤ 10^18)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--seed', type=int, default=SEED,
                        help=f'Random seed (default: {SEED})')
    
    args = parser.parse_args()
    
    # Update global RNG with provided seed
    global RNG
    RNG = np.random.default_rng(args.seed)
    
    # Validate bit range produces valid N
    min_N = 1 << args.min_bits
    max_N = 1 << args.max_bits
    
    if min_N < RANGE_MIN:
        print(f"WARNING: min-bits {args.min_bits} produces N < {RANGE_MIN}")
        print(f"Adjusting to ensure N ≥ {RANGE_MIN}")
        args.min_bits = max(args.min_bits, 47)  # 2^47 ≈ 1.4×10^14
    
    if max_N > RANGE_MAX:
        print(f"WARNING: max-bits {args.max_bits} produces N > {RANGE_MAX}")
        print(f"Adjusting to ensure N ≤ {RANGE_MAX}")
        args.max_bits = min(args.max_bits, 60)  # 2^60 ≈ 1.15×10^18
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Log parameters
    timestamp = datetime.now().isoformat()
    print("=" * 70)
    print("GEOFAC SCALING ANALYSIS")
    print("=" * 70)
    print(f"Timestamp: {timestamp}")
    print(f"Seed: {args.seed}")
    print(f"Samples: {args.num_samples}")
    print(f"Bit range: {args.min_bits}-{args.max_bits}")
    print(f"Operational range: [{RANGE_MIN}, {RANGE_MAX}]")
    print(f"Output directory: {output_dir}")
    print("=" * 70)
    
    # Collect data
    data = collect_data(
        num_samples=args.num_samples,
        bit_range=(args.min_bits, args.max_bits),
        output_dir=output_dir,
        verbose=args.verbose
    )
    
    if not data:
        print("\nNo data collected. Exiting.")
        return 1
    
    # Save CSV
    csv_path = output_dir / 'scaling_data.csv'
    save_csv(data, csv_path)
    print(f"\nSaved CSV: {csv_path}")
    
    # Generate plots
    loglog_path = output_dir / 'loglog_trials_vs_sqrt_n.png'
    reg_stats = plot_loglog(data, loglog_path)
    
    survival_path = output_dir / 'survival_curve.png'
    survival_stats = plot_survival(data, survival_path)
    
    # Print tables
    tables_output = print_tables(data, reg_stats, survival_stats)
    
    # Save tables to file
    tables_path = output_dir / 'analysis_summary.txt'
    with open(tables_path, 'w') as f:
        f.write(f"GEOFAC Scaling Analysis Summary\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Seed: {args.seed}\n")
        f.write(f"Samples: {args.num_samples}\n")
        f.write(tables_output)
    
    print(f"\nSaved summary: {tables_path}")
    print("\nDone.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
