#!/usr/bin/env python3
"""
Apply Theil-Sen estimator to resonance parameter estimation.

Tests the hypothesis that Theil-Sen provides more robust k_opt(ln N) predictions
than OLS when working with noisy or incomplete empirical data.
"""

import math
import json
from pathlib import Path
from theil_sen_estimator import theil_sen, ols_regression, evaluate_fit


def generate_synthetic_k_data():
    """
    Generate synthetic k-success data mimicking potential real observations.
    
    Assumption: k_opt scales weakly with ln(N) but with measurement noise and outliers
    from failed search runs or parameter mistuning.
    """
    # Hypothetical true relationship: k_opt ≈ 0.30 + 0.005 * ln(N)
    # This is purely synthetic - real data doesn't exist per resonance-drift-hypothesis
    
    data_points = [
        # (bit_length, N_str, true_k, measured_k)
        # Format: Small variations around true k, with occasional outliers
        (30, "1073217479", 0.334, 0.340),  # Gate 1 (if data existed)
        (40, "1099511627791", 0.345, 0.343),  # Synthetic 40-bit
        (45, "35184372088831", 0.355, 0.358),  # Synthetic 45-bit
        (50, "1125899906842597", 0.362, 0.368),  # Synthetic 50-bit
        (55, "36028797018963913", 0.370, 0.375),  # Synthetic 55-bit
        (60, "1152921470247108503", 0.378, 0.950),  # Outlier! (Search failure artifact)
        (65, "36893488147419103181", 0.385, 0.382),  # Synthetic 65-bit
        (70, "1180591620717411303397", 0.392, 0.388),  # Synthetic 70-bit
        (75, "37778931862957161709543", 0.398, 0.150),  # Outlier! (Spurious correlation)
        (80, "1208925819614629174706143", 0.404, 0.407),  # Synthetic 80-bit
    ]
    
    # Extract ln(N) and measured k values
    ln_N_values = []
    k_values = []
    
    for bit_length, N_str, true_k, measured_k in data_points:
        N = int(N_str)
        ln_N = math.log(N)
        ln_N_values.append(ln_N)
        k_values.append(measured_k)
    
    return ln_N_values, k_values, data_points


def predict_127bit_k(slope: float, intercept: float) -> dict:
    """Predict k for 127-bit challenge using fitted model"""
    # 127-bit challenge number
    N_127 = int("137524771864208156028430259349934309717")
    ln_N_127 = math.log(N_127)
    k_pred = slope * ln_N_127 + intercept
    
    return {
        'N': str(N_127),
        'ln_N': ln_N_127,
        'k_predicted': k_pred,
        'suggested_window_lo': max(0.0, k_pred - 0.05),
        'suggested_window_hi': min(1.0, k_pred + 0.05)
    }


def main():
    """Run Theil-Sen vs OLS on resonance parameter data"""
    
    print("=== Theil-Sen Application to Resonance Parameter Estimation ===\n")
    
    # Generate synthetic data (real data doesn't exist - see resonance-drift-hypothesis)
    ln_N_values, k_values, data_points = generate_synthetic_k_data()
    
    print(f"Data points: {len(data_points)}")
    print("Note: This is synthetic data. Real k-success values are not available.")
    print("See experiments/resonance-drift-hypothesis for data collection barriers.\n")
    
    # Print data
    print("Synthetic k observations:")
    for i, (bit_len, N_str, true_k, measured_k) in enumerate(data_points):
        marker = " ⚠ OUTLIER" if abs(measured_k - true_k) > 0.1 else ""
        print(f"  {bit_len:3d}-bit: ln(N)={ln_N_values[i]:6.2f}, k_measured={measured_k:.3f}{marker}")
    print()
    
    # Fit with OLS
    print("OLS Regression: k = m * ln(N) + b")
    ols_slope, ols_intercept = ols_regression(ln_N_values, k_values)
    ols_fit = evaluate_fit(ln_N_values, k_values, ols_slope, ols_intercept)
    print(f"  Slope:     {ols_slope:.10f}")
    print(f"  Intercept: {ols_intercept:.10f}")
    print(f"  MAD:       {ols_fit['mad']:.6f}")
    print(f"  SSR:       {ols_fit['ssr']:.6f}")
    print()
    
    # Fit with Theil-Sen
    print("Theil-Sen Robust Regression: k = m * ln(N) + b")
    ts_slope, ts_intercept = theil_sen(ln_N_values, k_values)
    ts_fit = evaluate_fit(ln_N_values, k_values, ts_slope, ts_intercept)
    print(f"  Slope:     {ts_slope:.10f}")
    print(f"  Intercept: {ts_intercept:.10f}")
    print(f"  MAD:       {ts_fit['mad']:.6f}")
    print(f"  SSR:       {ts_fit['ssr']:.6f}")
    print()
    
    # Compare parameter estimates
    print("Parameter Comparison:")
    slope_diff = abs(ols_slope - ts_slope)
    intercept_diff = abs(ols_intercept - ts_intercept)
    print(f"  Slope difference:     {slope_diff:.10f} ({slope_diff / abs(ts_slope) * 100:.1f}%)")
    print(f"  Intercept difference: {intercept_diff:.10f} ({intercept_diff / abs(ts_intercept) * 100:.1f}%)")
    print()
    
    # Predict for 127-bit
    print("=== Prediction for 127-bit Challenge ===")
    ols_pred = predict_127bit_k(ols_slope, ols_intercept)
    ts_pred = predict_127bit_k(ts_slope, ts_intercept)
    
    print(f"N = {ols_pred['N']}")
    print(f"ln(N) = {ols_pred['ln_N']:.6f}")
    print()
    print(f"OLS prediction:")
    print(f"  k_opt ≈ {ols_pred['k_predicted']:.6f}")
    print(f"  Suggested window: [{ols_pred['suggested_window_lo']:.6f}, {ols_pred['suggested_window_hi']:.6f}]")
    print()
    print(f"Theil-Sen prediction:")
    print(f"  k_opt ≈ {ts_pred['k_predicted']:.6f}")
    print(f"  Suggested window: [{ts_pred['suggested_window_lo']:.6f}, {ts_pred['suggested_window_hi']:.6f}]")
    print()
    
    k_pred_diff = abs(ols_pred['k_predicted'] - ts_pred['k_predicted'])
    print(f"Prediction difference: {k_pred_diff:.6f}")
    print()
    
    # Interpret results
    print("=== Interpretation ===")
    if ols_fit['mad'] > ts_fit['mad'] * 1.2:
        print("✓ Theil-Sen shows substantially better robustness (lower MAD)")
    elif ts_fit['mad'] > ols_fit['mad'] * 1.2:
        print("✗ OLS outperforms Theil-Sen (lower MAD) - data may be outlier-free")
    else:
        print("≈ Both estimators show similar robustness")
    print()
    
    if k_pred_diff > 0.05:
        print(f"⚠ Large prediction divergence ({k_pred_diff:.3f}) suggests outlier influence on OLS")
        print("  Recommendation: Use Theil-Sen prediction for robust parameter search")
    else:
        print(f"✓ Predictions agree within {k_pred_diff:.3f} - both methods stable")
    print()
    
    # Save results
    output_dir = Path('experiments/theil-sen-robust-estimator')
    output_file = output_dir / 'resonance_application_results.json'
    
    results = {
        'experiment': 'Theil-Sen Application to Resonance Parameters',
        'note': 'Synthetic data - real k-success values not available',
        'data_points': len(data_points),
        'ols': {
            'slope': ols_slope,
            'intercept': ols_intercept,
            'mad': ols_fit['mad'],
            'ssr': ols_fit['ssr'],
            'prediction_127bit': ols_pred
        },
        'theil_sen': {
            'slope': ts_slope,
            'intercept': ts_intercept,
            'mad': ts_fit['mad'],
            'ssr': ts_fit['ssr'],
            'prediction_127bit': ts_pred
        },
        'comparison': {
            'slope_difference': slope_diff,
            'intercept_difference': intercept_diff,
            'prediction_difference': k_pred_diff,
            'mad_ratio_ols_to_ts': ols_fit['mad'] / ts_fit['mad'] if ts_fit['mad'] > 0 else float('inf')
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == '__main__':
    main()
