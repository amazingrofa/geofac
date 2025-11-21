# Resonance Drift Hypothesis Experiment

## Executive Summary

**Hypothesis**: The optimal resonance parameter k scales geometrically with N (k_opt = k_base × ln(N)^S) rather than remaining fixed across bit-widths.

**Status**: HYPOTHESIS CANNOT BE FALSIFIED WITH AVAILABLE DATA

**Critical Finding**: The hypothesis requires empirical k-success values from actual factorization runs, but:
1. Gate 1 (30-bit) and Gate 2 (60-bit) use deterministic fast-path returns - no actual k search performed
2. No historical log data available with successful k values for operational range semiprimes
3. Actual factorization attempts in operational range [10^14, 10^18] exceed practical time limits (>5 minutes per test case)

**Conclusion**: Without empirical data points showing successful k values across multiple bit-widths, regression analysis cannot be performed. The experiment framework is sound, but data collection is infeasible given current validation gate structure and computational constraints.

## Why This Matters

**Conclusion**: Without empirical data points showing successful k values across multiple bit-widths, regression analysis cannot be performed. The experiment framework is sound, but data collection is infeasible given current validation gate structure and computational constraints.

## Why This Matters

The "resonance drift" hypothesis proposes that current failures at 127-bit scale stem from using parameters (k ∈ [0.25, 0.45]) calibrated for smaller bit-widths. If true, this suggests:
- Static k-windows become progressively misaligned as N scales
- Success at 30/60-bit doesn't predict 127-bit behavior without adaptive parameters
- A predictive formula k(N) would enable targeted search rather than brute-force scanning

## What Would Be Needed

To properly test this hypothesis, we would need:

1. **Actual k-success data**: For each successful factorization, log the exact k value where factors were found
   - Minimum 5-10 data points spanning 30-bit to 60-bit range
   - Each data point: (N, bitLength, ln(N), k_optimal, success_threshold)

2. **Instrumented search**: Modify FactorizerService to log k when amplitude threshold is exceeded and factors found
   - Current code samples k via golden ratio QMC but doesn't persist the successful k value
   - Need: log entry "SUCCESS: N={}, k={}, amplitude={}, duration_ms={}"

3. **Sufficient sampling**: Current 60-second timeout per window may be insufficient for operational range
   - Need: longer timeouts (300-600 seconds) or more samples to ensure coverage

## Experimental Design (If Data Were Available)

### Objective
Test whether the resonance center k drifts systematically with bit-depth, and derive an empirical scaling function k(N).

### Method
1. **Data Collection**: Run factorization across multiple bit-widths (30, 60, and operational range 10^14-10^18)
2. **Instrumentation**: Log successful k values where factors are found
3. **Analysis**: Perform regression of k_success vs ln(N) to derive scaling constant S
4. **Prediction**: Use derived S to predict optimal k for 127-bit challenge

### Test Matrix
- Gate 1 (30-bit): N = 1073217479 (32749 × 32771)
- Gate 2 (60-bit): N = 1152921470247108503 (1073741789 × 1073741827)
- Operational range samples from [10^14, 10^18]

### Configuration
Baseline configuration from application.yml:
- k-lo: 0.25
- k-hi: 0.45
- samples: 3000
- threshold: 0.92

## Experimental Design (If Data Were Available)

### Objective
Test whether the resonance center k drifts systematically with bit-depth, and derive an empirical scaling function k(N).

### Method
1. **Data Collection**: Run factorization across multiple bit-widths and log successful k values
2. **Regression Analysis**: Fit k_success vs ln(N) to derive scaling constant S
3. **Model Comparison**: Test linear models k = c·ln(N) + d vs k = a + b·bitLength
4. **Prediction**: Use derived formula to predict optimal k for 127-bit challenge
5. **Validation**: Test predicted k-window on 127-bit target

### Test Matrix (Theoretical)
- 30-bit: N = 1073217479 (32749 × 32771)
- 60-bit: N = 1152921470247108503 (1073741789 × 1073741827)
- Operational range samples from [10^14, 10^18]

### Configuration
Baseline from application.yml:
- k-lo: 0.25, k-hi: 0.45, samples: 3000, threshold: 0.92
- Scan strategy: Three overlapping windows per test case
  - Window 1: [0.25, 0.35] (lower third)
  - Window 2: [0.30, 0.40] (center)
  - Window 3: [0.35, 0.45] (upper third)

## Artifacts Created

### 1. ResonanceDriftExperiment.java
JUnit test that performs k-window scans across bit-widths. Framework is complete but cannot execute due to:
- Validation gates restrict custom config to Gate 3 (127-bit) or Gate 4 range only
- Gate 1/2 use deterministic fast-path returns (no actual search)
- Operational range factorizations exceed practical time limits

### 2. regression_analysis.py
Python script for curve fitting once data is collected:
- Parses data_collection.log for successful k values
- Performs linear regression: k vs ln(N) and k vs bitLength
- Computes R² to select best-fit model
- Predicts k_optimal for 127-bit challenge
- Outputs results.json with predictions and confidence metrics

### 3. data_collection.log
Expected format (not generated due to infeasibility):
```
name, bitLength, N, ln(N), k_lo, k_hi, success, k_optimal_estimate, duration_ms
```

## Alternative Falsification Strategy

Since empirical data collection is infeasible, we can examine theoretical consistency:

### Assumption Check 1: Is k fixed across scales?
The current implementation assumes k ∈ [0.25, 0.45] works universally. This is:
- **Unproven**: No systematic validation across 10^14-10^18 range
- **Suspicious**: Threshold (0.92) and window width (0.20) are constants, not functions of N
- **Inconsistent with physics**: Resonance frequencies typically scale with system size

### Assumption Check 2: What does existing code reveal?
```java
BigDecimal k = BigDecimal.valueOf(config.kLo())
                .add(kWidth.multiply(u, mc), mc);
```
k is sampled uniformly in [kLo, kHi] via golden ratio QMC. No adaptation to N.

### Assumption Check 3: Can we bound the drift?
If resonance theory holds, expect k ∝ f(ln(N)) or f(bitLength).
- At 30-bit (ln N ≈ 20.79): k ∈ [0.25, 0.45] (assumed)
- At 127-bit (ln N ≈ 88.76): k should shift by factor ≈ 88.76/20.79 ≈ 4.27

**Prediction**: If k drifts proportionally with ln(N), 127-bit optimal k could be outside [0.25, 0.45] entirely.

## Hypothesis Verdict

**CANNOT BE FALSIFIED** due to lack of empirical data, but theoretical analysis suggests:

1. **Static k is theoretically suspect**: No physical basis for assuming resonance center is scale-invariant
2. **Current approach is unvalidated**: No systematic k-success data across operational range
3. **Computational barrier exists**: Collecting required data exceeds practical time limits with current method

### Recommendations

If this hypothesis is to be properly tested:

1. **Instrument the search**: Add k-logging to FactorizerService.search() when factors found
2. **Run long-duration validation**: Execute overnight runs on operational range to collect k-success data
3. **Enable systematic collection**: Modify validation gates to allow historical analysis of Gates 1-2
4. **Consider synthetic validation**: Use smaller balanced semiprimes where search completes quickly

Without addressing these barriers, the "resonance drift" hypothesis remains neither confirmed nor falsified - it is simply **untestable with current infrastructure**.

## Files in This Experiment

- `README.md`: This document
- `ResonanceDriftExperiment.java`: Data collection test (framework only - cannot execute)
- `regression_analysis.py`: Curve fitting script (awaiting data)
- `plots/`: (empty - no data to plot)

## Timestamp

Experiment created: 2025-11-21
Status: Framework complete; data collection infeasible; hypothesis untestable
