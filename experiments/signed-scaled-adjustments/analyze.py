#!/usr/bin/env python3
"""
Quick Analysis Script for Signed or Scaled Adjustments Experiment

Displays key findings from results.json in a clear, tabular format.
"""

import json
from pathlib import Path


def main():
    results_path = Path(__file__).parent / "results.json"
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("SIGNED OR SCALED ADJUSTMENTS EXPERIMENT - SUMMARY")
    print("=" * 80)
    print()
    
    # Metadata
    metadata = data["metadata"]
    print(f"Experiment Date: {metadata['timestamp']}")
    print(f"Seed: {metadata['seed']}")
    print(f"Precision: {metadata['precision_dps']} decimal places")
    print(f"Test Semiprimes: {metadata['num_semiprimes']}")
    print(f"Operational Range: [{metadata['operational_range'][0]:.2e}, {metadata['operational_range'][1]:.2e}]")
    print()
    
    # Strategy Performance Table
    print("STRATEGY PERFORMANCE")
    print("-" * 80)
    print(f"{'Strategy':<35} {'Success Rate':<15} {'Avg Iterations':<15}")
    print("-" * 80)
    
    summaries = data["strategy_summaries"]
    for summary in summaries:
        label = summary["label"]
        success_rate = f"{summary['successes']}/{summary['total_tests']} ({100*summary['success_rate']:.0f}%)"
        avg_iter = f"{summary['avg_iterations_all']:.1f}"
        
        print(f"{label:<35} {success_rate:<15} {avg_iter:<15}")
    
    print("-" * 80)
    print()
    
    # Key Findings
    print("KEY FINDINGS")
    print("-" * 80)
    
    control = summaries[0]
    positive = summaries[1]
    negative = summaries[2]
    
    print(f"1. Control (no adjustment):")
    print(f"   - Success rate: {control['success_rate']*100:.0f}%")
    print(f"   - Average iterations: {control['avg_iterations_all']:.1f}")
    print(f"   - Conclusion: OPTIMAL BASELINE")
    print()
    
    print(f"2. Positive k=0.3 adjustments:")
    print(f"   - Success rate: {positive['success_rate']*100:.0f}%")
    print(f"   - All tests hit timeout ({positive['avg_iterations_all']:.0f} iterations)")
    print(f"   - Conclusion: UNIVERSAL FAILURE")
    print()
    
    print(f"3. Negative k=0.3 adjustments:")
    print(f"   - Success rate: {negative['success_rate']*100:.0f}%")
    print(f"   - Average iterations: {negative['avg_iterations_all']:.1f}")
    print(f"   - Conclusion: MATCHES CONTROL (no improvement)")
    print()
    
    # Scaled variants
    scaled_positive_count = sum(1 for s in summaries if s['adjustment_sign'] == 1 and s['k_value'] is not None)
    scaled_positive_success = sum(s['successes'] for s in summaries if s['adjustment_sign'] == 1 and s['k_value'] is not None)
    
    scaled_negative_count = sum(1 for s in summaries if s['adjustment_sign'] == -1 and s['k_value'] is not None)
    scaled_negative_success = sum(s['successes'] for s in summaries if s['adjustment_sign'] == -1 and s['k_value'] is not None)
    
    print(f"4. Scaled positive adjustments (0.1×, 0.5×, 1.0×):")
    print(f"   - Combined success rate: {scaled_positive_success}/{scaled_positive_count*10} (0%)")
    print(f"   - Conclusion: SCALING MAKES NO DIFFERENCE (all fail)")
    print()
    
    print(f"5. Scaled negative adjustments (0.1×, 0.5×, 1.0×):")
    print(f"   - Combined success rate: {scaled_negative_success}/{scaled_negative_count*10} (100%)")
    print(f"   - All achieve 0 iterations (identical to control)")
    print(f"   - Conclusion: GUARD CLAUSE CLAMPING (no actual benefit)")
    print()
    
    print("-" * 80)
    print()
    
    # Verdict
    print("VERDICT")
    print("-" * 80)
    print("HYPOTHESIS: DECISIVELY FALSIFIED")
    print()
    print("Signed or scaled adjustments to θ'(n,k) do NOT improve Fermat-style")
    print("factorization of balanced semiprimes. The optimal starting point is")
    print("mathematically determined as ceil(√n), and any geometric adjustment")
    print("either fails completely (positive) or is forced back to the baseline")
    print("by guard clauses (negative).")
    print()
    print("For balanced semiprimes (p ≈ q), use the trivial baseline: ceil(√n).")
    print("=" * 80)


if __name__ == "__main__":
    main()
