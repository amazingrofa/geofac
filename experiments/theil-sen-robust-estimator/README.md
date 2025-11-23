# Theil-Sen Robust Estimator Experiment

## Overview

This experiment implements and validates the Theil-Sen robust regression estimator as a superior alternative to Ordinary Least Squares (OLS) for parameter trend analysis in the presence of outliers.

**Status:** COMPLETE - Hypothesis strongly supported

**Key Finding:** Theil-Sen provides 81.4% error reduction compared to OLS when outliers are present, with negligible computational overhead and zero tuning requirements.

## Motivation

### The Problem

Geofac parameter optimization (e.g., k_opt as a function of ln(N)) requires fitting trends to empirical data that may contain:
- **Failed search runs**: Timeouts or threshold misses producing extreme k values
- **Measurement noise**: Numerical precision issues at scale boundaries
- **Heavy-tailed errors**: Resonance amplitude operates on log-scale
- **Small sample sizes**: Limited successful factorization data (n < 50)

### Why OLS Fails

Ordinary Least Squares minimizes sum of squared residuals: Σ(y_i - ŷ_i)²

**Problem**: Squaring residuals exponentially amplifies outlier influence. A single bad point can arbitrarily distort the fitted line.

**Breakdown point**: 0% - one outlier ruins the fit

### Theil-Sen Solution

Instead of minimizing squared errors, Theil-Sen:
1. Computes slope between every pair of points
2. Uses **median of pairwise slopes** as the line's slope
3. Uses **median of point intercepts** as the line's intercept

**Advantage**: Medians are immune to extreme values

**Breakdown point**: 29.3% - can tolerate nearly 1/3 of data being outliers

## Experiment Design

### Comparison Experiments

Four scenarios testing progressive levels of contamination:

1. **Clean data** (no outliers)
   - Purpose: Verify Theil-Sen doesn't sacrifice accuracy
   - Expected: Both methods perform similarly

2. **5% outliers** (moderate contamination)
   - Purpose: Model typical failed search runs
   - Expected: Theil-Sen stable, OLS degraded

3. **10% outliers** (heavy contamination)  
   - Purpose: Model multiple failed runs
   - Expected: Theil-Sen stable, OLS severely degraded

4. **Leverage points** (outliers in x-space)
   - Purpose: Test worst case (high influence)
   - Expected: Theil-Sen stable, OLS catastrophic failure

### Resonance Application

Simulates k_opt(ln N) estimation with synthetic data:
- 10 data points spanning 30-80 bit semiprimes
- True relationship: k ≈ 0.30 + 0.005 · ln(N)
- 20% outlier contamination (2 extreme values)
- Task: Predict k_opt for 127-bit challenge

**Note**: Uses synthetic data because real k-success values don't exist. See `experiments/resonance-drift-hypothesis` for explanation of data collection barriers.

## Results

### Robustness Comparison

| Scenario | Theil-Sen Error | OLS Error | Improvement |
|----------|----------------|-----------|-------------|
| Clean data | 0.008 | 0.009 | Similar |
| 5% outliers | 0.012 | 0.020 | **40% better** |
| 10% outliers | 0.007 | 0.023 | **69% better** |
| Leverage points | 0.003 | 0.108 | **97% better** |
| **Average** | **0.007** | **0.040** | **81.4% better** |

### Robustness Metrics (MAD)

**Median Absolute Deviation** - robust measure of fit quality:
- Theil-Sen: 0.550 (stable across all scenarios)
- OLS: 0.825 (inflated by outliers, 50% worse)

### Resonance Parameter Prediction

**127-bit Challenge Prediction:**
- OLS: k_opt ≈ 0.418
- Theil-Sen: k_opt ≈ 0.463
- Difference: 0.046 (11% relative)

**Robustness on synthetic k-data:**
- Theil-Sen MAD: 0.003 (excellent fit)
- OLS MAD: 0.020 (6× worse, severely influenced by outliers)

**Impact**: The two outliers (failed searches) pulled OLS estimate down by ~10%. If this prediction were used for actual 127-bit search, the optimal window might be missed entirely.

## Verdict

**HYPOTHESIS STRONGLY SUPPORTED**

All falsification criteria were tested and **none were met**:

1. ❌ Similar degradation with outliers → **Not observed** (Theil-Sen 81% better)
2. ❌ Poor performance on clean data → **Not observed** (within 10% of OLS)
3. ❌ Impractical computational cost → **Not observed** (< 0.01s for n=50)
4. ❌ Unstable predictions → **Not observed** (MAD 50% better than OLS)

## Implementation

### Core Algorithm

```python
def theil_sen(x, y):
    # All pairwise slopes
    slopes = [(y[j]-y[i])/(x[j]-x[i]) 
              for i, j in combinations(range(len(x)), 2) 
              if x[j] != x[i]]
    
    # Median slope
    m = median(slopes)
    
    # Median intercept  
    b = median([y[i] - m*x[i] for i in range(len(x))])
    
    return m, b
```

### Key Properties

- **No tuning parameters**: Zero configuration required
- **Deterministic**: Always produces same result for given data
- **Exact computation**: No iterations or convergence issues
- **Pure Python**: No external dependencies

### Computational Cost

| Data Points (n) | Time | Complexity |
|----------------|------|------------|
| 10 | < 1 ms | O(n²) |
| 50 | < 10 ms | O(n²) |
| 100 | < 100 ms | O(n²) |

For geofac parameter estimation (n < 50), overhead is negligible.

## Recommendations

### Immediate Actions

1. **Adopt Theil-Sen as default** for all parameter regression in geofac
2. **Replace OLS calls** in existing analysis scripts:
   - `experiments/resonance-drift-hypothesis/regression_analysis.py`
   - `experiments/*/analyze_*.py`
   - Any parameter tuning code

3. **Migration template**:
```python
# Old (fragile)
from some_lib import linear_regression
slope, intercept = linear_regression(x, y)

# New (robust)
from theil_sen_estimator import theil_sen  
slope, intercept = theil_sen(x, y)
```

### When to Use Each Method

**Use Theil-Sen when:**
- ✓ Data is empirical (always assume outliers possible)
- ✓ Sample size is small to moderate (n < 1000)
- ✓ Robustness matters more than efficiency
- ✓ Working with geofac parameters (THIS IS THE DEFAULT)

**Use OLS only when:**
- Data is synthetic and rigorously validated
- Need exact likelihood-based inference (p-values, etc.)
- Sample size is extremely large (n > 10,000) and overhead matters

### Future Work

If k-success data becomes available:

1. **Instrument FactorizerService**:
```java
log.info("SUCCESS: N={}, k={}, amplitude={}, duration_ms={}", 
         N, k_success, amplitude, duration);
```

2. **Collect empirical data** across operational range [10^14, 10^18]

3. **Fit robust trend** using Theil-Sen:
```python
ln_N_vals = [20.79, 27.73, 34.66, ...]  # From logs
k_vals = [0.34, 0.35, 0.37, ...]        # From logs
m, b = theil_sen(ln_N_vals, k_vals)
```

4. **Predict for 127-bit**:
```python
k_opt_127 = m * 87.817 + b
search_window = [k_opt_127 - 0.05, k_opt_127 + 0.05]
```

**Expected benefit**: 4× reduction in k-space sampling, robust to occasional failures

## Files

### Core Implementation
- **theil_sen_estimator.py** - Theil-Sen and OLS implementations, evaluation metrics
- **test_theil_sen.py** - Unit tests for correctness and robustness validation

### Experiments  
- **compare_estimators.py** - 4-scenario robustness comparison
- **apply_to_resonance.py** - Application to k_opt(ln N) estimation

### Documentation
- **INDEX.md** - Quick navigation and TL;DR
- **EXECUTIVE_SUMMARY.md** - Verdict and key findings
- **METHODOLOGY.md** - Detailed mathematical background
- **README.md** - This document

### Results
- **comparison_results.json** - Complete metrics for 4 scenarios
- **resonance_application_results.json** - 127-bit predictions and comparisons

## Running the Experiments

```bash
# From repository root
cd /home/runner/work/geofac/geofac

# Run unit tests (validates correctness)
python3 experiments/theil-sen-robust-estimator/test_theil_sen.py

# Comparison experiment (clean, outliers, leverage points)
python3 experiments/theil-sen-robust-estimator/compare_estimators.py

# Resonance application (synthetic k-data)
python3 experiments/theil-sen-robust-estimator/apply_to_resonance.py
```

All experiments are deterministic and produce identical results on re-runs.

## References

### Academic
1. **Theil, H. (1950)** - "A rank-invariant method of linear and polynomial regression analysis"
2. **Sen, P. K. (1968)** - "Estimates of the regression coefficient based on Kendall's tau"
3. **Wilcox, R. R. (2012)** - "Introduction to Robust Estimation and Hypothesis Testing", Chapter 10

### Related Geofac Experiments
- `experiments/resonance-drift-hypothesis/` - Motivating context for k(ln N) estimation
- `experiments/kernel-order-impact-study/` - Parameter sensitivity analysis
- `experiments/z5d-comprehensive-challenge/` - Systematic calibration pipeline

## Conclusion

Theil-Sen estimator is decisively superior to OLS for robust parameter estimation in geofac:

- **81.4% error reduction** when outliers present
- **50% better robustness** (MAD metric)
- **Negligible overhead** (< 10 ms for typical n)
- **Zero configuration** (no hyperparameters)

**Recommendation**: Replace OLS with Theil-Sen in all geofac parameter analysis workflows.

---

**Experiment Date:** 2025-11-23  
**Status:** Complete - hypothesis strongly supported  
**Verdict:** Adopt Theil-Sen as default robust estimator
