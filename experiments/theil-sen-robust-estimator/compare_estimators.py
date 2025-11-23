#!/usr/bin/env python3
"""
Compare Theil-Sen vs OLS under various conditions.

This script demonstrates the robustness of Theil-Sen estimator compared to OLS
when outliers are present in the data.
"""

import math
import json
from pathlib import Path
from theil_sen_estimator import theil_sen, ols_regression, evaluate_fit


def generate_clean_data(n: int, true_slope: float, true_intercept: float, noise_std: float) -> tuple:
    """Generate clean synthetic data: y = mx + b + noise"""
    x = [i * 1.0 for i in range(n)]
    y = [true_slope * xi + true_intercept + noise_std * (hash(f"noise_{i}") % 1000 - 500) / 500.0 
         for i, xi in enumerate(x)]
    return x, y


def add_outliers(x: list, y: list, n_outliers: int, outlier_magnitude: float) -> tuple:
    """Add outliers to existing data"""
    x_out = x.copy()
    y_out = y.copy()
    
    # Add outliers at random positions
    for i in range(n_outliers):
        idx = (i * 7919) % len(x_out)  # Deterministic pseudo-random positions
        # Perturb y value significantly
        direction = 1 if (i % 2 == 0) else -1
        y_out[idx] = y_out[idx] + direction * outlier_magnitude
    
    return x_out, y_out


def run_comparison_experiment(scenario_name: str, x: list, y: list, true_slope: float, true_intercept: float) -> dict:
    """Run both estimators and compare results"""
    
    # Theil-Sen
    ts_slope, ts_intercept = theil_sen(x, y)
    ts_fit = evaluate_fit(x, y, ts_slope, ts_intercept)
    
    # OLS
    ols_slope, ols_intercept = ols_regression(x, y)
    ols_fit = evaluate_fit(x, y, ols_slope, ols_intercept)
    
    # Errors relative to true parameters
    ts_slope_error = abs(ts_slope - true_slope)
    ts_intercept_error = abs(ts_intercept - true_intercept)
    ols_slope_error = abs(ols_slope - true_slope)
    ols_intercept_error = abs(ols_intercept - true_intercept)
    
    return {
        'scenario': scenario_name,
        'data_points': len(x),
        'true_slope': true_slope,
        'true_intercept': true_intercept,
        'theil_sen': {
            'slope': ts_slope,
            'intercept': ts_intercept,
            'mad': ts_fit['mad'],
            'ssr': ts_fit['ssr'],
            'slope_error': ts_slope_error,
            'intercept_error': ts_intercept_error
        },
        'ols': {
            'slope': ols_slope,
            'intercept': ols_intercept,
            'mad': ols_fit['mad'],
            'ssr': ols_fit['ssr'],
            'slope_error': ols_slope_error,
            'intercept_error': ols_intercept_error
        }
    }


def main():
    """Run comparison experiments and save results"""
    
    # True parameters
    TRUE_SLOPE = 2.5
    TRUE_INTERCEPT = 10.0
    NOISE_STD = 1.0
    
    results = []
    
    # Scenario 1: Clean data (no outliers)
    print("Scenario 1: Clean data (no outliers)")
    x1, y1 = generate_clean_data(n=50, true_slope=TRUE_SLOPE, true_intercept=TRUE_INTERCEPT, noise_std=NOISE_STD)
    result1 = run_comparison_experiment("clean_data", x1, y1, TRUE_SLOPE, TRUE_INTERCEPT)
    results.append(result1)
    print(f"  Theil-Sen: slope={result1['theil_sen']['slope']:.6f}, intercept={result1['theil_sen']['intercept']:.6f}")
    print(f"  OLS:       slope={result1['ols']['slope']:.6f}, intercept={result1['ols']['intercept']:.6f}")
    print(f"  Theil-Sen MAD: {result1['theil_sen']['mad']:.6f}, OLS MAD: {result1['ols']['mad']:.6f}")
    print()
    
    # Scenario 2: Data with 5% outliers
    print("Scenario 2: 5% outliers (moderate contamination)")
    x2, y2 = generate_clean_data(n=50, true_slope=TRUE_SLOPE, true_intercept=TRUE_INTERCEPT, noise_std=NOISE_STD)
    x2, y2 = add_outliers(x2, y2, n_outliers=3, outlier_magnitude=20.0)
    result2 = run_comparison_experiment("5pct_outliers", x2, y2, TRUE_SLOPE, TRUE_INTERCEPT)
    results.append(result2)
    print(f"  Theil-Sen: slope={result2['theil_sen']['slope']:.6f}, intercept={result2['theil_sen']['intercept']:.6f}")
    print(f"  OLS:       slope={result2['ols']['slope']:.6f}, intercept={result2['ols']['intercept']:.6f}")
    print(f"  Theil-Sen slope error: {result2['theil_sen']['slope_error']:.6f}")
    print(f"  OLS slope error:       {result2['ols']['slope_error']:.6f}")
    print()
    
    # Scenario 3: Data with 10% outliers
    print("Scenario 3: 10% outliers (heavy contamination)")
    x3, y3 = generate_clean_data(n=50, true_slope=TRUE_SLOPE, true_intercept=TRUE_INTERCEPT, noise_std=NOISE_STD)
    x3, y3 = add_outliers(x3, y3, n_outliers=5, outlier_magnitude=25.0)
    result3 = run_comparison_experiment("10pct_outliers", x3, y3, TRUE_SLOPE, TRUE_INTERCEPT)
    results.append(result3)
    print(f"  Theil-Sen: slope={result3['theil_sen']['slope']:.6f}, intercept={result3['theil_sen']['intercept']:.6f}")
    print(f"  OLS:       slope={result3['ols']['slope']:.6f}, intercept={result3['ols']['intercept']:.6f}")
    print(f"  Theil-Sen slope error: {result3['theil_sen']['slope_error']:.6f}")
    print(f"  OLS slope error:       {result3['ols']['slope_error']:.6f}")
    print()
    
    # Scenario 4: Data with leverage points (outliers in x)
    print("Scenario 4: Leverage points (outliers in x-space)")
    x4, y4 = generate_clean_data(n=50, true_slope=TRUE_SLOPE, true_intercept=TRUE_INTERCEPT, noise_std=NOISE_STD)
    # Add points with extreme x values and moderate y deviation
    x4.extend([100.0, 105.0])
    y4.extend([TRUE_SLOPE * 100.0 + TRUE_INTERCEPT + 15.0, 
               TRUE_SLOPE * 105.0 + TRUE_INTERCEPT + 18.0])
    result4 = run_comparison_experiment("leverage_points", x4, y4, TRUE_SLOPE, TRUE_INTERCEPT)
    results.append(result4)
    print(f"  Theil-Sen: slope={result4['theil_sen']['slope']:.6f}, intercept={result4['theil_sen']['intercept']:.6f}")
    print(f"  OLS:       slope={result4['ols']['slope']:.6f}, intercept={result4['ols']['intercept']:.6f}")
    print(f"  Theil-Sen slope error: {result4['theil_sen']['slope_error']:.6f}")
    print(f"  OLS slope error:       {result4['ols']['slope_error']:.6f}")
    print()
    
    # Save results
    output_dir = Path('experiments/theil-sen-robust-estimator')
    output_file = output_dir / 'comparison_results.json'
    
    with open(output_file, 'w') as f:
        json.dump({
            'experiment': 'Theil-Sen vs OLS Comparison',
            'true_parameters': {
                'slope': TRUE_SLOPE,
                'intercept': TRUE_INTERCEPT,
                'noise_std': NOISE_STD
            },
            'scenarios': results
        }, f, indent=2)
    
    print(f"Results saved to {output_file}")
    
    # Summary statistics
    print("\n=== SUMMARY ===")
    print("Average slope errors:")
    ts_avg_error = sum(r['theil_sen']['slope_error'] for r in results) / len(results)
    ols_avg_error = sum(r['ols']['slope_error'] for r in results) / len(results)
    print(f"  Theil-Sen: {ts_avg_error:.6f}")
    print(f"  OLS:       {ols_avg_error:.6f}")
    print(f"  Improvement: {(1 - ts_avg_error / ols_avg_error) * 100:.1f}% lower error with Theil-Sen")
    print()
    print("Median Absolute Deviations (average across scenarios):")
    ts_avg_mad = sum(r['theil_sen']['mad'] for r in results) / len(results)
    ols_avg_mad = sum(r['ols']['mad'] for r in results) / len(results)
    print(f"  Theil-Sen: {ts_avg_mad:.6f}")
    print(f"  OLS:       {ols_avg_mad:.6f}")


if __name__ == '__main__':
    main()
