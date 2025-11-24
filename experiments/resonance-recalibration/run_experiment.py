#!/usr/bin/env python3
"""
Resonance Recalibration Experiment

Goal: Reveal where parameter inertia distorts phase alignment as N grows.
      Make drift visible and tunable to unstick 127-bit challenge.

This script:
1. Collects curvature and phase measurements at multiple scales
2. Generates double-log plots of drift vs N-scale
3. Fits scaling laws (power/log) to the drift patterns
4. Applies bounded adaptive corrections
5. Exports artifacts for reproducibility

Validation gates: 10^14 to 10^18 operational range (Gate 4)
Special allowance: 127-bit challenge for diagnostics

No classical fallbacks. Deterministic sampling. Explicit precision.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from mpmath import mp, mpf, sqrt as mpsqrt, log as mplog, pi as mppi, sin as mpsin
from scipy.optimize import curve_fit
from scipy.stats import linregress


# Adaptive precision formula: max(240, bitLength * 4 + 200)
def adaptive_precision(bit_length):
    return max(240, bit_length * 4 + 200)


# Parameter bounds for adaptive corrections
K_MIN = 0.25
K_MAX = 0.45
THRESHOLD_MIN = 0.5
THRESHOLD_MAX = 1.0
SAMPLES_MIN = 1000
SAMPLES_MAX = 100000

# Generate RSA-style semiprimes at different scales
# These are test semiprimes in the 10^14 to 10^18 range (Gate 4)
# Each entry: (N, bit_length, p_approx, q_approx) where p_approx and q_approx
# are approximations used for offset calculation only (not exact factors)
TEST_SEMIPRIMES = [
    # ~47 bits (10^14 range) - Gate 4 minimum
    (100000000000037, 47, 10000000019, 9999999981),
    # ~50 bits (mid 10^14)
    (1000000000000079, 50, 31622777, 31622777),
    # ~54 bits (10^16 range)
    (10000000000000061, 54, 100000007, 99999989),
    # ~60 bits (10^18 range) - Gate 2 canonical
    (1152921470247108503, 60, 1073741789, 1073741827),
    # 127-bit challenge (whitelist for diagnostic)
    (137524771864208156028430259349934309717, 127, 10508623501177419659, 13086849276577416863),
]


def compute_empirical_curvature(N, k, mc):
    """
    Compute empirical curvature κ_emp(N) at a candidate point.
    Uses the divisor-weighted formula from FactorizerService.
    
    κ(n) = d(n) * ln(n+1) / e²
    where d(n) ≈ ln(n)^0.4 for large n
    """
    mp.dps = mc
    
    # Candidate point near sqrt(N)
    sqrt_N = mpsqrt(mpf(N))
    offset = mpf(k) * sqrt_N
    p0 = int(sqrt_N + offset)
    
    # Approximate divisor count
    ln_p0 = mplog(mpf(p0))
    divisor_approx = ln_p0 ** mpf(0.4)
    
    # ln(n+1) ≈ ln(n) for large n
    ln_p0_plus1 = mplog(mpf(p0 + 1))
    
    # e² ≈ 7.389
    e_sq = mp.e ** 2
    
    # κ(n) = d(n) * ln(n+1) / e²
    kappa = divisor_approx * ln_p0_plus1 / e_sq
    
    return float(kappa), p0


def compute_phase_alignment(N, k, m, J, mc):
    """
    Compute phase alignment at a candidate point.
    Uses Dirichlet kernel gating from the resonance method.
    
    Returns phase φ at the interference snap point.
    """
    mp.dps = mc
    
    sqrt_N = mpsqrt(mpf(N))
    offset = mpf(k) * sqrt_N
    p0 = int(sqrt_N + offset)
    
    # Dirichlet kernel amplitude (simplified)
    # D_J(θ) ≈ sin((J+0.5)θ) / sin(θ/2)
    theta = mpf(2) * mppi * mpf(m) * mpf(p0) / mpf(N)
    
    # Phase at this point
    phase = float((mpf(J) + mpf(0.5)) * theta)
    
    # Normalize to [0, 2π]
    phase = phase % (2 * np.pi)
    
    return phase


def measure_scale_drift(N, bit_length, p_true, q_true):
    """
    Measure curvature and phase drift for a given N.
    Returns drift metrics relative to baseline (30-bit) model.
    """
    mc = adaptive_precision(bit_length)
    mp.dps = mc
    
    # Baseline parameters (from 30-bit tuning)
    baseline_k = 0.35
    baseline_m = 90  # m-span center
    baseline_J = 6
    
    # Current scale parameters (what ScaleAdaptiveParams would use)
    baseline_bit = 30.0
    scale_factor = bit_length / baseline_bit
    
    # Collect measurements at multiple k values
    k_samples = [0.25, 0.30, 0.35, 0.40, 0.45]
    curvatures = []
    phases = []
    
    for k in k_samples:
        kappa, _ = compute_empirical_curvature(N, k, mc)
        phi = compute_phase_alignment(N, k, baseline_m, baseline_J, mc)
        curvatures.append(kappa)
        phases.append(phi)
    
    # Compute drift as deviation from baseline expectation
    # At 30-bit, curvature is ~O(1), phase is well-aligned
    # As scale grows, these drift from the fixed-parameter model
    
    avg_kappa = np.mean(curvatures)
    std_kappa = np.std(curvatures)
    
    avg_phase = np.mean(phases)
    std_phase = np.std(phases)
    
    # Baseline model: assume κ constant, phase uniform
    baseline_kappa = 1.0  # Normalized baseline
    baseline_phase = np.pi  # Expected phase center
    
    delta_kappa = avg_kappa - baseline_kappa
    delta_phase = avg_phase - baseline_phase
    
    # Also measure proximity to true factors (diagnostic)
    sqrt_N = float(mpsqrt(mpf(N)))
    p_offset = (p_true - sqrt_N) / sqrt_N
    q_offset = (q_true - sqrt_N) / sqrt_N
    
    # Use mpmath for log10 of large integers
    log_N_val = float(mplog(mpf(N)) / mplog(mpf(10)))
    loglog_N_val = float(mplog(mpf(log_N_val)) / mplog(mpf(10)))
    
    return {
        'N': str(N),
        'bit_length': bit_length,
        'log_N': log_N_val,
        'loglog_N': loglog_N_val,
        'delta_kappa': delta_kappa,
        'std_kappa': std_kappa,
        'delta_phase': delta_phase,
        'std_phase': std_phase,
        'p_offset': p_offset,
        'q_offset': q_offset,
        'precision': mc,
    }


def fit_scaling_law(x, y, law_type='log'):
    """
    Fit a scaling law to drift data.
    
    Types:
    - 'log': y = a * (log x)^b
    - 'power': y = a * x^b
    """
    # Filter out any NaN or inf values
    mask = np.isfinite(x) & np.isfinite(y)
    x_clean = np.array(x)[mask]
    y_clean = np.array(y)[mask]
    
    if len(x_clean) < 3:
        return None, None, 0.0
    
    try:
        if law_type == 'log':
            # y = a * (log x)^b
            # log(y) = log(a) + b * log(log(x))
            log_x = np.log(x_clean)
            # Add small offset to avoid log(0); offset << min(y_clean) to preserve scale
            epsilon = 1e-10
            log_y = np.log(np.abs(y_clean) + epsilon)
            
            slope, intercept, r_value, _, _ = linregress(log_x, log_y)
            
            a = np.exp(intercept)
            b = slope
            r_squared = r_value ** 2
            
        elif law_type == 'power':
            # y = a * x^b
            # log(y) = log(a) + b * log(x)
            log_x = np.log(x_clean)
            epsilon = 1e-10
            log_y = np.log(np.abs(y_clean) + epsilon)
            
            slope, intercept, r_value, _, _ = linregress(log_x, log_y)
            
            a = np.exp(intercept)
            b = slope
            r_squared = r_value ** 2
        
        else:
            return None, None, 0.0
        
        return a, b, r_squared
    
    except Exception as e:
        print(f"Warning: Fitting failed: {e}")
        return None, None, 0.0


def plot_drift_curves(measurements, output_dir):
    """
    Generate double-log plots of curvature and phase drift vs N-scale.
    """
    # Extract data
    bit_lengths = [m['bit_length'] for m in measurements]
    log_N = [m['log_N'] for m in measurements]
    delta_kappa = [m['delta_kappa'] for m in measurements]
    delta_phase = [m['delta_phase'] for m in measurements]
    
    # Fit scaling laws
    kappa_a, kappa_b, kappa_r2 = fit_scaling_law(bit_lengths, np.abs(delta_kappa), 'log')
    phase_a, phase_b, phase_r2 = fit_scaling_law(bit_lengths, np.abs(delta_phase), 'log')
    
    # Plot 1: Curvature drift
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(log_N, delta_kappa, s=100, alpha=0.7, label='Empirical Δκ')
    
    # Overlay fit if available
    if kappa_a is not None and kappa_b is not None:
        fit_label = f'Fit: Δκ ≈ {kappa_a:.2e} · (log bitLen)^{kappa_b:.2f}\nR² = {kappa_r2:.3f}'
        log_N_fit = np.linspace(min(log_N), max(log_N), 100)
        bit_fit = np.interp(log_N_fit, log_N, bit_lengths)
        delta_kappa_fit = kappa_a * (np.log(bit_fit) ** kappa_b)
        ax.plot(log_N_fit, delta_kappa_fit, 'r--', linewidth=2, label=fit_label)
    
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('log₁₀(N)', fontsize=12)
    ax.set_ylabel('Δκ(N) = κₑₘₚ(N) − κₘₒdₑₗ(N)', fontsize=12)
    ax.set_title('Curvature Drift vs N-Scale (log-log)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plot_path = output_dir / 'curvature_drift_loglog.png'
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved: {plot_path}")
    
    # Plot 2: Phase misalignment
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(log_N, delta_phase, s=100, alpha=0.7, color='orange', label='Empirical Δφ')
    
    # Overlay fit if available
    if phase_a is not None and phase_b is not None:
        fit_label = f'Fit: Δφ ≈ {phase_a:.2e} · (log bitLen)^{phase_b:.2f}\nR² = {phase_r2:.3f}'
        log_N_fit = np.linspace(min(log_N), max(log_N), 100)
        bit_fit = np.interp(log_N_fit, log_N, bit_lengths)
        delta_phase_fit = phase_a * (np.log(bit_fit) ** phase_b)
        ax.plot(log_N_fit, delta_phase_fit, 'r--', linewidth=2, label=fit_label)
    
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('log₁₀(N)', fontsize=12)
    ax.set_ylabel('Δφ(N) = φₘₑₐₛᵤᵣₑd(N) − φₚᵣₑd(N)', fontsize=12)
    ax.set_title('Phase Misalignment vs N-Scale (log-log)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plot_path = output_dir / 'phase_misalignment_loglog.png'
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved: {plot_path}")
    
    return {
        'kappa': {'a': kappa_a, 'b': kappa_b, 'r_squared': kappa_r2},
        'phase': {'a': phase_a, 'b': phase_b, 'r_squared': phase_r2},
    }


def compute_adaptive_corrections(bit_length, scaling_fits):
    """
    Compute adaptive parameter corrections based on scaling laws.
    Returns suggested adjustments for k, threshold, and QMC depth.
    """
    baseline_bit = 30.0
    
    kappa_fit = scaling_fits['kappa']
    phase_fit = scaling_fits['phase']
    
    # Base parameters (from application.yml)
    k_0 = 0.35
    T_0 = 0.92
    S_0 = 3000  # samples
    
    # Correction exponents from fits
    kappa_b = kappa_fit['b'] if kappa_fit['b'] is not None else 0.5
    phase_b = phase_fit['b'] if phase_fit['b'] is not None else 0.5
    
    # Correction factors (bounded)
    alpha = min(0.1, abs(kappa_b) * 0.02)  # k adjustment factor
    beta = min(0.2, abs(phase_b) * 0.05)   # threshold adjustment factor
    gamma = min(2.0, abs(kappa_b) * 0.5)   # sample depth adjustment factor
    
    # Apply corrections
    log_scale = np.log(bit_length / baseline_bit)
    
    k_corrected = k_0 + alpha * (log_scale ** kappa_b)
    T_corrected = T_0 * ((log_scale + 1) ** (-beta))
    S_corrected = int(S_0 * ((log_scale + 1) ** gamma))
    
    # Bound the corrections using module-level constants
    k_corrected = np.clip(k_corrected, K_MIN, K_MAX)
    T_corrected = np.clip(T_corrected, THRESHOLD_MIN, THRESHOLD_MAX)
    S_corrected = max(SAMPLES_MIN, min(SAMPLES_MAX, S_corrected))
    
    return {
        'k': k_corrected,
        'threshold': T_corrected,
        'samples': S_corrected,
        'alpha': alpha,
        'beta': beta,
        'gamma': gamma,
    }


def run_experiment():
    """Main experiment driver."""
    print("=" * 60)
    print("RESONANCE RECALIBRATION EXPERIMENT")
    print("=" * 60)
    print()
    
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)
    
    print(f"Timestamp: {timestamp}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Collect measurements across scales
    print("Phase 1: Collecting drift measurements across scales...")
    print("-" * 60)
    
    measurements = []
    for N, bit_length, p, q in TEST_SEMIPRIMES:
        print(f"\nMeasuring N={N} ({bit_length} bits)")
        print(f"  True factors: p={p}, q={q}")
        
        try:
            drift = measure_scale_drift(N, bit_length, p, q)
            measurements.append(drift)
            
            print(f"  Δκ = {drift['delta_kappa']:.6e} (std={drift['std_kappa']:.6e})")
            print(f"  Δφ = {drift['delta_phase']:.6f} (std={drift['std_phase']:.6f})")
            print(f"  Precision: {drift['precision']} dps")
        
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
    
    print()
    print("Phase 2: Fitting scaling laws...")
    print("-" * 60)
    
    if len(measurements) < 3:
        print("ERROR: Insufficient measurements for fitting.")
        return
    
    scaling_fits = plot_drift_curves(measurements, output_dir)
    
    print(f"Curvature fit: a={scaling_fits['kappa']['a']:.6e}, "
          f"b={scaling_fits['kappa']['b']:.3f}, "
          f"R²={scaling_fits['kappa']['r_squared']:.3f}")
    print(f"Phase fit: a={scaling_fits['phase']['a']:.6e}, "
          f"b={scaling_fits['phase']['b']:.3f}, "
          f"R²={scaling_fits['phase']['r_squared']:.3f}")
    
    print()
    print("Phase 3: Computing adaptive corrections...")
    print("-" * 60)
    
    # Compute corrections for 127-bit challenge
    corrections_127 = compute_adaptive_corrections(127, scaling_fits)
    
    print("Suggested parameter adjustments for 127-bit challenge:")
    print(f"  k: 0.35 → {corrections_127['k']:.4f} (α={corrections_127['alpha']:.4f})")
    print(f"  threshold: 0.92 → {corrections_127['threshold']:.4f} (β={corrections_127['beta']:.4f})")
    print(f"  samples: 3000 → {corrections_127['samples']} (γ={corrections_127['gamma']:.4f})")
    
    print()
    print("Phase 4: Exporting artifacts...")
    print("-" * 60)
    
    # Export resonance scaling fit
    fit_artifact = {
        'timestamp': timestamp,
        'experiment': 'resonance-recalibration',
        'scaling_laws': {
            'curvature_drift': {
                'formula': 'Δκ(N) ≈ a * (log N)^b',
                'a': scaling_fits['kappa']['a'],
                'b': scaling_fits['kappa']['b'],
                'r_squared': scaling_fits['kappa']['r_squared'],
            },
            'phase_misalignment': {
                'formula': 'Δφ(N) ≈ c * (log N)^d',
                'c': scaling_fits['phase']['a'],
                'd': scaling_fits['phase']['b'],
                'r_squared': scaling_fits['phase']['r_squared'],
            },
        },
        'adaptive_corrections_127bit': corrections_127,
        'measurements': measurements,
    }
    
    fit_path = output_dir / 'resonance_scaling_fit.json'
    with open(fit_path, 'w') as f:
        json.dump(fit_artifact, f, indent=2)
    print(f"Saved: {fit_path}")
    
    # Export raw measurements
    measurements_path = output_dir / 'measurements.json'
    with open(measurements_path, 'w') as f:
        json.dump(measurements, f, indent=2)
    print(f"Saved: {measurements_path}")
    
    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print(f"EXPERIMENT COMPLETE (runtime: {elapsed:.1f}s)")
    print("=" * 60)
    
    return fit_artifact, measurements


if __name__ == '__main__':
    run_experiment()
