#!/usr/bin/env python3
"""
Regression Analysis for Resonance Drift Hypothesis

Analyzes k-success data across bit-widths to derive scaling constant S.
Tests hypothesis: k_opt = k_base * ln(N)^S
"""

import sys
import math
import json
from pathlib import Path

def parse_data_file(filepath):
    """Parse data_collection.log and extract successful k values."""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 9:
                continue
            
            name = parts[0]
            bit_length = int(parts[1])
            N_str = parts[2]
            ln_N = float(parts[3])
            k_lo = float(parts[4])
            k_hi = float(parts[5])
            success = parts[6].lower() == 'true'
            k_optimal = float(parts[7])
            duration_ms = int(parts[8])
            
            if success:
                data.append({
                    'name': name,
                    'bit_length': bit_length,
                    'N': N_str,
                    'ln_N': ln_N,
                    'k_optimal': k_optimal,
                    'k_lo': k_lo,
                    'k_hi': k_hi,
                    'duration_ms': duration_ms
                })
    
    return data

def linear_regression(x_vals, y_vals):
    """Perform simple linear regression: y = mx + b"""
    n = len(x_vals)
    if n < 2:
        return None, None, None
    
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xx = sum(x*x for x in x_vals)
    sum_xy = sum(x*y for x, y in zip(x_vals, y_vals))
    
    # Calculate slope (m) and intercept (b)
    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-10:
        return None, None, None
    
    m = (n * sum_xy - sum_x * sum_y) / denom
    b = (sum_y - m * sum_x) / n
    
    # Calculate R²
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean)**2 for y in y_vals)
    ss_res = sum((y - (m*x + b))**2 for x, y in zip(x_vals, y_vals))
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return m, b, r_squared

def analyze_resonance_drift(data):
    """
    Analyze k vs ln(N) relationship.
    
    Test models:
    1. k = c * ln(N) + d  (linear in ln(N))
    2. k = a + b * bit_length (linear in bits)
    """
    
    print("=== Resonance Drift Analysis ===\n")
    print(f"Data points collected: {len(data)}\n")
    
    if len(data) < 2:
        print("ERROR: Insufficient data for regression (need at least 2 successful points)")
        return None
    
    # Model 1: k vs ln(N)
    ln_N_vals = [d['ln_N'] for d in data]
    k_vals = [d['k_optimal'] for d in data]
    
    m1, b1, r2_1 = linear_regression(ln_N_vals, k_vals)
    
    print("Model 1: k = c * ln(N) + d")
    if m1 is not None:
        print(f"  c = {m1:.10f}")
        print(f"  d = {b1:.10f}")
        print(f"  R² = {r2_1:.6f}")
    else:
        print("  Could not fit model")
    print()
    
    # Model 2: k vs bit_length
    bit_vals = [d['bit_length'] for d in data]
    
    m2, b2, r2_2 = linear_regression(bit_vals, k_vals)
    
    print("Model 2: k = a + b * bit_length")
    if m2 is not None:
        print(f"  a = {b2:.10f}")
        print(f"  b = {m2:.10f}")
        print(f"  R² = {r2_2:.6f}")
    else:
        print("  Could not fit model")
    print()
    
    # Determine best model
    best_model = None
    if r2_1 is not None and r2_2 is not None:
        if r2_1 > r2_2:
            best_model = "ln(N)"
            print(f"Best fit: Model 1 (k vs ln(N)) with R² = {r2_1:.6f}")
        else:
            best_model = "bit_length"
            print(f"Best fit: Model 2 (k vs bit_length) with R² = {r2_2:.6f}")
    elif r2_1 is not None:
        best_model = "ln(N)"
        print(f"Best fit: Model 1 (k vs ln(N)) with R² = {r2_1:.6f}")
    elif r2_2 is not None:
        best_model = "bit_length"
        print(f"Best fit: Model 2 (k vs bit_length) with R² = {r2_2:.6f}")
    
    print()
    
    # Predict for 127-bit challenge
    N_127 = "137524771864208156028430259349934309717"
    ln_N_127 = math.log(float(N_127))
    bit_127 = 127
    
    print("=== Prediction for 127-bit Challenge ===")
    print(f"N = {N_127}")
    print(f"ln(N) = {ln_N_127:.6f}")
    print(f"bit_length = {bit_127}")
    print()
    
    k_pred_1 = None
    k_pred_2 = None
    
    if m1 is not None:
        k_pred_1 = m1 * ln_N_127 + b1
        print(f"Model 1 prediction: k_opt ≈ {k_pred_1:.6f}")
        print(f"  Suggested window: [{k_pred_1 - 0.05:.6f}, {k_pred_1 + 0.05:.6f}]")
    
    if m2 is not None:
        k_pred_2 = m2 * bit_127 + b2
        print(f"Model 2 prediction: k_opt ≈ {k_pred_2:.6f}")
        print(f"  Suggested window: [{k_pred_2 - 0.05:.6f}, {k_pred_2 + 0.05:.6f}]")
    
    print()
    
    # Return results
    results = {
        'data_points': len(data),
        'model_1': {
            'type': 'k = c * ln(N) + d',
            'c': m1,
            'd': b1,
            'r_squared': r2_1
        },
        'model_2': {
            'type': 'k = a + b * bit_length',
            'a': b2,
            'b': m2,
            'r_squared': r2_2
        },
        'best_model': best_model,
        'prediction_127bit': {
            'N': N_127,
            'ln_N': ln_N_127,
            'bit_length': bit_127,
            'k_pred_model1': k_pred_1,
            'k_pred_model2': k_pred_2,
            'suggested_window': [k_pred_1 - 0.05, k_pred_1 + 0.05] if k_pred_1 else None
        },
        'empirical_data': data
    }
    
    return results

def main():
    experiment_dir = Path('experiments/resonance-drift-hypothesis')
    data_file = experiment_dir / 'data_collection.log'
    results_file = experiment_dir / 'results.json'
    
    if not data_file.exists():
        print(f"ERROR: Data file not found: {data_file}")
        print("Run the experiment first: ./gradlew test --tests '*ResonanceDriftExperiment*'")
        sys.exit(1)
    
    print(f"Loading data from {data_file}...\n")
    data = parse_data_file(data_file)
    
    if not data:
        print("ERROR: No successful data points found in log file")
        sys.exit(1)
    
    results = analyze_resonance_drift(data)
    
    if results:
        # Save results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {results_file}")
    else:
        print("\nAnalysis failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
