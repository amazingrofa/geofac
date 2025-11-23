"""
Signal Decay Analyzer
======================

Quantify geodesic signal decay in GVA factorization by computing
Signal-to-Noise Ratio (SNR) across different bit lengths.

SNR measures how well geodesic distance discriminates true factors
from random candidates.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import mpmath as mp
import numpy as np
import json
from typing import List, Dict
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from gva_factorization import embed_torus_geodesic, riemannian_distance, adaptive_precision


def compute_snr(N: int, p: int, q: int, k_values: List[float], 
                candidate_count: int = 1000, seed: int = 42) -> Dict:
    """
    Compute Signal-to-Noise Ratio for geodesic distance at true factors.
    
    SNR = min_distance_at_factors / avg_distance_over_candidates
    
    Higher SNR indicates better signal discrimination.
    
    Args:
        N: Semiprime to analyze
        p, q: True factors
        k_values: List of geodesic exponents to test
        candidate_count: Number of random candidates to sample
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with SNR analysis results
    """
    np.random.seed(seed)
    
    bit_length = N.bit_length()
    required_dps = adaptive_precision(N)
    
    with mp.workdps(required_dps):
        sqrt_N = int(mp.sqrt(N))
        
        # Compute distances at true factors
        factor_distances = {}
        for k in k_values:
            N_coords = embed_torus_geodesic(N, k)
            p_coords = embed_torus_geodesic(p, k)
            q_coords = embed_torus_geodesic(q, k)
            
            dist_p = float(riemannian_distance(N_coords, p_coords))
            dist_q = float(riemannian_distance(N_coords, q_coords))
            
            factor_distances[k] = {
                'dist_p': dist_p,
                'dist_q': dist_q,
                'min_dist': min(dist_p, dist_q)
            }
        
        # Sample random candidates around sqrt(N)
        window = max(10000, sqrt_N // 100)
        candidate_distances = {k: [] for k in k_values}
        
        candidates_sampled = 0
        while candidates_sampled < candidate_count:
            offset = np.random.randint(-window, window + 1)
            candidate = sqrt_N + offset
            
            # Skip invalid candidates
            if candidate <= 1 or candidate >= N:
                continue
            if candidate == p or candidate == q:
                continue
            if candidate % 2 == 0 or candidate % 3 == 0 or candidate % 5 == 0:
                continue
            
            for k in k_values:
                N_coords = embed_torus_geodesic(N, k)
                cand_coords = embed_torus_geodesic(candidate, k)
                dist = float(riemannian_distance(N_coords, cand_coords))
                candidate_distances[k].append(dist)
            
            candidates_sampled += 1
        
        # Compute SNR for each k
        snr_results = {}
        for k in k_values:
            min_factor_dist = factor_distances[k]['min_dist']
            avg_candidate_dist = np.mean(candidate_distances[k])
            std_candidate_dist = np.std(candidate_distances[k])
            
            snr = min_factor_dist / avg_candidate_dist if avg_candidate_dist > 0 else 0
            
            snr_results[k] = {
                'min_factor_distance': min_factor_dist,
                'avg_candidate_distance': avg_candidate_dist,
                'std_candidate_distance': std_candidate_dist,
                'snr': snr
            }
        
        # Find best k
        best_k = max(k_values, key=lambda k: snr_results[k]['snr'])
        
        return {
            'N': str(N),
            'p': str(p),
            'q': str(q),
            'bit_length': bit_length,
            'precision_dps': required_dps,
            'k_values': k_values,
            'candidate_count': candidates_sampled,
            'seed': seed,
            'factor_distances': {str(k): v for k, v in factor_distances.items()},
            'snr_results': {str(k): v for k, v in snr_results.items()},
            'best_k': best_k,
            'best_snr': snr_results[best_k]['snr']
        }


def analyze_snr_decay(test_cases: List[Dict], k_values: List[float],
                     candidate_count: int = 1000, output_dir: str = 'results') -> Dict:
    """
    Analyze SNR decay across multiple bit lengths and fit exponential decay.
    
    Args:
        test_cases: List of dicts with 'N', 'p', 'q' keys
        k_values: Geodesic exponents to test
        candidate_count: Candidates per test case
        output_dir: Output directory for results
        
    Returns:
        Analysis results with exponential fit
    """
    results = []
    
    print("=" * 70)
    print("SNR Decay Analysis")
    print("=" * 70)
    print(f"Test cases: {len(test_cases)}")
    print(f"k values: {k_values}")
    print(f"Candidates per case: {candidate_count}")
    print(f"Output directory: {output_dir}")
    print()
    
    for i, case in enumerate(test_cases):
        N, p, q = case['N'], case['p'], case['q']
        print(f"[{i+1}/{len(test_cases)}] Analyzing N={N} ({N.bit_length()} bits)")
        
        snr_data = compute_snr(N, p, q, k_values, candidate_count)
        results.append(snr_data)
        
        print(f"  Best k={snr_data['best_k']}, SNR={snr_data['best_snr']:.6f}")
        print()
    
    # Extract data for fitting
    bit_lengths = [r['bit_length'] for r in results]
    best_snrs = [r['best_snr'] for r in results]
    
    # Fit exponential decay: SNR = a * exp(-b * bit_length)
    log_snrs = np.log(np.maximum(best_snrs, 1e-10))  # Avoid log(0)
    coeffs = np.polyfit(bit_lengths, log_snrs, 1)
    a_fit = np.exp(coeffs[1])
    b_fit = -coeffs[0]
    
    # Generate plot
    os.makedirs(output_dir, exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    plt.scatter(bit_lengths, best_snrs, s=100, alpha=0.7, label='Measured SNR')
    
    # Plot fitted curve
    bit_range = np.linspace(min(bit_lengths), max(bit_lengths), 100)
    snr_fit = a_fit * np.exp(-b_fit * bit_range)
    plt.plot(bit_range, snr_fit, 'r--', linewidth=2, 
             label=f'Fit: SNR = {a_fit:.3f} × exp(-{b_fit:.4f} × bits)')
    
    plt.xlabel('Bit Length', fontsize=12)
    plt.ylabel('Signal-to-Noise Ratio (SNR)', fontsize=12)
    plt.title('GVA Geodesic Signal Decay Analysis', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, 'snr_plot.png')
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    print(f"Plot saved: {plot_path}")
    
    # Save JSON report
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_cases': results,
        'exponential_fit': {
            'formula': 'SNR = a * exp(-b * bit_length)',
            'a': float(a_fit),
            'b': float(b_fit),
            'interpretation': f'SNR decays by factor of {np.exp(b_fit):.3f} per bit'
        },
        'summary': {
            'bit_lengths': bit_lengths,
            'best_snrs': best_snrs,
            'min_snr': float(min(best_snrs)),
            'max_snr': float(max(best_snrs))
        }
    }
    
    json_path = os.path.join(output_dir, 'snr_analysis.json')
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"JSON report saved: {json_path}")
    print()
    print("=" * 70)
    print("Exponential Fit Results")
    print("=" * 70)
    print(f"SNR = {a_fit:.6f} × exp(-{b_fit:.6f} × bit_length)")
    print(f"Decay factor per bit: {np.exp(b_fit):.6f}")
    print(f"SNR at 30 bits: {a_fit * np.exp(-b_fit * 30):.6f}")
    print(f"SNR at 50 bits: {a_fit * np.exp(-b_fit * 50):.6f}")
    print()
    
    return report


if __name__ == '__main__':
    # Test cases at different bit lengths
    test_cases = [
        # Gate 1: 30-bit balanced
        {'N': 1073217479, 'p': 32749, 'q': 32771},
        
        # 40-bit balanced (synthetic for scale testing, using RSA-style construction)
        # Note: This is allowed for diagnostic analysis only
        {'N': 1099493294233, 'p': 1048571, 'q': 1048583},
        
        # 47-bit balanced (from 8d experiment)
        {'N': 100000980001501, 'p': 10000019, 'q': 10000079},
        
        # 50-bit balanced
        {'N': 1125899839733759, 'p': 33554393, 'q': 33554467},
    ]
    
    k_values = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    
    analyze_snr_decay(test_cases, k_values, candidate_count=1000, 
                     output_dir='results')
