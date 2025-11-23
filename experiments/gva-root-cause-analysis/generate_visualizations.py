"""
Generate Visualizations for GVA Root-Cause Analysis
====================================================

Creates plots from experimental data:
1. SNR vs bit-length decay curve (Phase 1.1)
2. Parameter sensitivity heatmap (Phase 1.2)
"""

import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict


def generate_snr_plot():
    """Generate SNR vs bit-length plot from signal decay data."""
    print("Generating SNR vs bit-length plot...")
    
    data_file = Path(__file__).parent / "signal_decay_data.json"
    
    if not data_file.exists():
        print(f"  Error: {data_file} not found. Run geodesic_signal_decay.py first.")
        return
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    results = data['results']
    
    # Group by bit length
    by_bit_length = defaultdict(list)
    for r in results:
        by_bit_length[r['bit_length']].append(r['snr'])
    
    # Calculate statistics
    bit_lengths = sorted(by_bit_length.keys())
    avg_snrs = [sum(by_bit_length[bl]) / len(by_bit_length[bl]) for bl in bit_lengths]
    min_snrs = [min(by_bit_length[bl]) for bl in bit_lengths]
    max_snrs = [max(by_bit_length[bl]) for bl in bit_lengths]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot average with error bars
    errors = [[avg - min_val for avg, min_val in zip(avg_snrs, min_snrs)],
              [max_val - avg for avg, max_val in zip(avg_snrs, max_snrs)]]
    
    ax.errorbar(bit_lengths, avg_snrs, yerr=errors, 
                fmt='o-', capsize=5, capthick=2, 
                label='Mean SNR ± range', linewidth=2, markersize=6)
    
    # Fit exponential decay (if applicable)
    if len(bit_lengths) > 5:
        try:
            # Fit: SNR = A * exp(-B * bit_length)
            log_snrs = np.log(np.maximum(avg_snrs, 1e-10))  # Avoid log(0)
            coeffs = np.polyfit(bit_lengths, log_snrs, 1)
            B = -coeffs[0]
            A = np.exp(coeffs[1])
            
            # Plot fit
            x_fit = np.linspace(min(bit_lengths), max(bit_lengths), 100)
            y_fit = A * np.exp(-B * x_fit)
            ax.plot(x_fit, y_fit, 'r--', alpha=0.7, 
                   label=f'Exponential fit: SNR = {A:.3f} × exp(-{B:.4f} × bits)')
        except Exception as e:
            print(f"  Warning: Could not fit exponential: {e}")
    
    ax.set_xlabel('Bit Length', fontsize=12)
    ax.set_ylabel('Signal-to-Noise Ratio (SNR)', fontsize=12)
    ax.set_title('Geodesic Signal Decay: SNR vs Bit Length', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.set_yscale('log')
    
    # Highlight operational range
    ax.axvspan(47, 60, alpha=0.1, color='red', 
              label='Operational range [10^14, 10^18]')
    
    output_file = Path(__file__).parent / "snr_vs_bitlength.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Plot saved to: {output_file}")


def generate_parameter_heatmap():
    """Generate parameter sensitivity heatmap."""
    print("Generating parameter sensitivity heatmap...")
    
    data_file = Path(__file__).parent / "parameter_sweep_results.json"
    
    if not data_file.exists():
        print(f"  Error: {data_file} not found. Run parameter_sensitivity_sweep.py first.")
        return
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    results = data['results']
    k_values = sorted(set(r['k'] for r in results))
    budgets = sorted(set(r['max_candidates'] for r in results))
    
    # Create success matrix
    success_matrix = np.zeros((len(budgets), len(k_values)))
    runtime_matrix = np.zeros((len(budgets), len(k_values)))
    
    for r in results:
        k_idx = k_values.index(r['k'])
        budget_idx = budgets.index(r['max_candidates'])
        success_matrix[budget_idx, k_idx] = 1 if r['success'] else 0
        runtime_matrix[budget_idx, k_idx] = r['runtime_seconds']
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Subplot 1: Success rate heatmap
    im1 = ax1.imshow(success_matrix, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
    ax1.set_xlabel('k (Geodesic Exponent)', fontsize=11)
    ax1.set_ylabel('Candidate Budget', fontsize=11)
    ax1.set_title('Success Rate (47-bit Balanced)', fontsize=12, fontweight='bold')
    ax1.set_xticks(range(len(k_values)))
    ax1.set_xticklabels([f'{k:.2f}' for k in k_values], rotation=45)
    ax1.set_yticks(range(len(budgets)))
    ax1.set_yticklabels([f'{b:,}' for b in budgets])
    
    # Add colorbar
    cbar1 = plt.colorbar(im1, ax=ax1)
    cbar1.set_label('Success (1=✅, 0=❌)', fontsize=10)
    
    # Add text annotations
    for i in range(len(budgets)):
        for j in range(len(k_values)):
            text = '✅' if success_matrix[i, j] == 1 else '❌'
            ax1.text(j, i, text, ha='center', va='center', fontsize=10)
    
    # Subplot 2: Runtime heatmap
    im2 = ax2.imshow(runtime_matrix, aspect='auto', cmap='viridis', norm=matplotlib.colors.LogNorm())
    ax2.set_xlabel('k (Geodesic Exponent)', fontsize=11)
    ax2.set_ylabel('Candidate Budget', fontsize=11)
    ax2.set_title('Runtime (seconds, log scale)', fontsize=12, fontweight='bold')
    ax2.set_xticks(range(len(k_values)))
    ax2.set_xticklabels([f'{k:.2f}' for k in k_values], rotation=45)
    ax2.set_yticks(range(len(budgets)))
    ax2.set_yticklabels([f'{b:,}' for b in budgets])
    
    # Add colorbar
    cbar2 = plt.colorbar(im2, ax=ax2)
    cbar2.set_label('Runtime (s)', fontsize=10)
    
    output_file = Path(__file__).parent / "parameter_sensitivity_heatmap.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Plot saved to: {output_file}")


if __name__ == '__main__':
    print("=" * 80)
    print("Generating Visualizations")
    print("=" * 80)
    print()
    
    generate_snr_plot()
    generate_parameter_heatmap()
    
    print()
    print("Visualization generation complete.")
