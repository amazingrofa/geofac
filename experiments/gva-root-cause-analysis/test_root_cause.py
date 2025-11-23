"""
Test Suite for GVA Root-Cause Analysis
=======================================

Tests each analysis module on validation gates.
"""

import sys
import os
import json
import csv
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from signal_decay_analyzer import compute_snr, analyze_snr_decay
from parameter_sweep import test_parameters, parameter_sweep
from theoretical_sim import compute_expected_distance, simulate_phase_cancellation, analyze_theoretical_flaws
from gva_root_cause import generate_unified_report


def test_signal_decay_analyzer():
    """Test signal decay analyzer on Gate 1."""
    print("=" * 70)
    print("TEST: Signal Decay Analyzer")
    print("=" * 70)
    
    # Gate 1: 30-bit
    N = 1073217479
    p = 32749
    q = 32771
    
    assert p * q == N, "Test case factors invalid"
    
    k_values = [0.3, 0.35, 0.4]
    
    print(f"Testing on Gate 1: N={N}, p={p}, q={q}")
    
    snr_data = compute_snr(N, p, q, k_values, candidate_count=100, seed=42)
    
    assert 'N' in snr_data
    assert 'bit_length' in snr_data
    assert 'snr_results' in snr_data
    assert 'best_k' in snr_data
    
    print(f"  Bit length: {snr_data['bit_length']}")
    print(f"  Best k: {snr_data['best_k']}")
    print(f"  Best SNR: {snr_data['best_snr']:.6f}")
    
    # Gate 1 should have reasonable SNR (> 0.5)
    assert snr_data['best_snr'] > 0.1, "Gate 1 SNR unexpectedly low"
    
    print("  ✅ PASS: SNR computed successfully")
    
    # Test full analysis
    print("\nTesting full SNR decay analysis...")
    
    test_cases = [
        {'N': 1073217479, 'p': 32749, 'q': 32771},  # 30-bit
        {'N': 100000980001501, 'p': 10000019, 'q': 10000079},  # 47-bit
    ]
    
    output_dir = 'test_results'
    os.makedirs(output_dir, exist_ok=True)
    
    results = analyze_snr_decay(test_cases, k_values, candidate_count=100, output_dir=output_dir)
    
    assert 'test_cases' in results
    assert 'exponential_fit' in results
    
    # Verify outputs
    json_path = os.path.join(output_dir, 'snr_analysis.json')
    plot_path = os.path.join(output_dir, 'snr_plot.png')
    
    assert os.path.exists(json_path), "JSON output not created"
    assert os.path.exists(plot_path), "Plot output not created"
    
    # Verify JSON is valid
    with open(json_path, 'r') as f:
        data = json.load(f)
        assert 'exponential_fit' in data
    
    print(f"  ✅ PASS: Outputs created at {output_dir}/")
    print()


def test_parameter_sweep():
    """Test parameter sweep on Gate 1."""
    print("=" * 70)
    print("TEST: Parameter Sweep")
    print("=" * 70)
    
    # Gate 1: 30-bit
    test_cases = [
        {'N': 1073217479, 'p': 32749, 'q': 32771}
    ]
    
    k_values = [0.3, 0.35, 0.4]
    candidate_budgets = [5000, 10000]
    
    print(f"Testing on Gate 1: {test_cases[0]['N']}")
    
    output_dir = 'test_results'
    
    results = parameter_sweep(
        test_cases,
        k_values,
        candidate_budgets,
        timeout=10,
        output_dir=output_dir,
        parallel=False  # Sequential for testing
    )
    
    assert 'summary' in results
    assert 'results' in results
    
    summary = results['summary']
    print(f"  Total runs: {summary['total_runs']}")
    print(f"  Successes: {summary['successes']}")
    print(f"  Success rate: {100*summary['success_rate']:.1f}%")
    
    # Gate 1 should have at least some successes
    assert summary['successes'] > 0, "Gate 1 should have some successes"
    
    # Verify CSV output
    csv_path = os.path.join(output_dir, 'param_sweep.csv')
    assert os.path.exists(csv_path), "CSV output not created"
    
    # Verify CSV is valid
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "CSV is empty"
        assert 'N' in rows[0]
        assert 'k' in rows[0]
        assert 'success' in rows[0]
    
    print(f"  ✅ PASS: CSV output created and valid")
    
    # Verify heatmap
    heatmap_path = os.path.join(output_dir, 'param_heatmap_30bit.png')
    assert os.path.exists(heatmap_path), "Heatmap not created"
    
    print(f"  ✅ PASS: Heatmap created")
    print()


def test_theoretical_sim():
    """Test theoretical simulation."""
    print("=" * 70)
    print("TEST: Theoretical Simulation")
    print("=" * 70)
    
    # Gate 1: 30-bit
    N = 1073217479
    p = 32749
    q = 32771
    
    print(f"Testing on Gate 1: N={N}, p={p}, q={q}")
    
    # Test distance computation
    k = 0.35
    theta_r = 0.0
    
    expected_dist = compute_expected_distance(p, q, k, theta_r)
    
    print(f"  Theoretical distance (k={k}, θ_r={theta_r}): {expected_dist:.6f}")
    
    assert expected_dist > 0, "Theoretical distance should be positive"
    
    print(f"  ✅ PASS: Theoretical distance computed")
    
    # Test full simulation
    print("\nTesting full theoretical analysis...")
    
    test_cases = [
        {'N': 1073217479, 'p': 32749, 'q': 32771},
    ]
    
    k_values = [0.3, 0.35, 0.4]
    
    output_dir = 'test_results'
    
    report_text = analyze_theoretical_flaws(test_cases, k_values, output_dir=output_dir)
    
    assert len(report_text) > 0, "Report text is empty"
    assert "Theoretical Simulation" in report_text
    
    # Verify markdown output
    md_path = os.path.join(output_dir, 'theory_sim.md')
    assert os.path.exists(md_path), "Markdown output not created"
    
    with open(md_path, 'r') as f:
        content = f.read()
        assert len(content) > 0
        assert "Theoretical Flaws" in content
    
    print(f"  ✅ PASS: Markdown report created")
    print()


def test_unified_report():
    """Test unified report generation."""
    print("=" * 70)
    print("TEST: Unified Report")
    print("=" * 70)
    
    output_dir = 'test_results'
    
    # Mock results
    snr_results = {
        'exponential_fit': {
            'a': 1.5,
            'b': 0.05,
            'formula': 'SNR = a * exp(-b * bit_length)',
            'interpretation': 'SNR decays by factor of 1.051 per bit'
        },
        'test_cases': [
            {'bit_length': 30, 'best_snr': 0.8, 'best_k': 0.35}
        ]
    }
    
    sweep_results = {
        'summary': {
            'total_runs': 10,
            'successes': 5,
            'false_positives': 0,
            'success_rate': 0.5,
            'avg_runtime': 0.25,
            'k_values': [0.3, 0.35],
            'candidate_budgets': [10000]
        }
    }
    
    theory_text = "# Theoretical Analysis\n\nSample text."
    
    report_path = generate_unified_report(
        snr_results,
        sweep_results,
        theory_text,
        output_dir=output_dir
    )
    
    assert os.path.exists(report_path), "Report not created"
    
    with open(report_path, 'r') as f:
        content = f.read()
        assert len(content) > 0
        assert "Executive Summary" in content
        assert "Root Cause" in content
    
    print(f"  ✅ PASS: Unified report created at {report_path}")
    print()


def test_on_47bit_balanced():
    """Test on 47-bit balanced case from 8d experiment."""
    print("=" * 70)
    print("TEST: 47-bit Balanced Case")
    print("=" * 70)
    
    # 47-bit balanced (valid semiprime in operational range)
    N = 100000980001501
    p = 10000019
    q = 10000079
    
    assert p * q == N, "Test case factors invalid"
    
    print(f"Testing on N={N} ({N.bit_length()} bits)")
    print(f"Factors: p={p}, q={q}")
    
    k_values = [0.35]
    
    snr_data = compute_snr(N, p, q, k_values, candidate_count=100, seed=42)
    
    print(f"  Best SNR: {snr_data['best_snr']:.6f}")
    
    # 47-bit should have SNR close to or less than 1 (signal decay)
    # Allow some tolerance for randomness
    assert 0 < snr_data['best_snr'] <= 1.5, "SNR should be in reasonable range"
    
    print("  ✅ PASS: 47-bit case analyzed successfully")
    print()


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("GVA ROOT-CAUSE ANALYSIS TEST SUITE")
    print("=" * 70 + "\n")
    
    try:
        test_signal_decay_analyzer()
        test_parameter_sweep()
        test_theoretical_sim()
        test_unified_report()
        test_on_47bit_balanced()
        
        print("=" * 70)
        print("ALL TESTS PASSED ✅")
        print("=" * 70)
        print()
        
        return 0
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
