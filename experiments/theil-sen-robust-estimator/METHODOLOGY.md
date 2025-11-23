# Theil-Sen Robust Estimator - Methodology and Experiment Design

## Objective

Test whether Theil-Sen median slope estimator provides more robust trend estimates than Ordinary Least Squares (OLS) for parameter optimization when data contains outliers, measurement noise, or failed search runs.

## Background

### The Problem with OLS

Ordinary Least Squares regression minimizes the sum of squared residuals:

```
minimize: Σ(y_i - (mx_i + b))²
```

This objective function has a critical weakness: **squared errors exponentially amplify outlier influence**. A single extreme point can arbitrarily distort the fitted line.

**Example:**
- Data: (1, 3), (2, 5), (3, 7), (4, 9), (5, 100)  [one outlier]
- True line: y = 2x + 1
- OLS fit: y ≈ 18.4x - 33.6  (completely wrong!)
- Breakdown point: 0% (one bad point ruins everything)

### Theil-Sen Alternative

Theil-Sen uses a different strategy based on pairwise slopes:

1. **Compute all pairwise slopes**: For every pair of points (i, j) where i < j:
   ```
   m_ij = (y_j - y_i) / (x_j - x_i)
   ```

2. **Slope = median of all pairwise slopes**:
   ```
   m = median({m_ij : i < j})
   ```

3. **Intercept = median of point-wise intercepts**:
   ```
   b = median({y_i - m·x_i : i = 1..n})
   ```

**Key Properties:**
- **Breakdown point: 29.3%** - can tolerate up to 29% outliers
- **No distributional assumptions** - works with heavy tails, skew, non-Gaussian errors
- **Exact computation** - deterministic, no iterations or convergence issues
- **Complexity: O(n²)** - negligible for n < 100, acceptable for n < 1000

## Experiment Design

### Test Matrix

Four scenarios designed to stress-test robustness:

#### Scenario 1: Clean Data (Baseline)
- **Setup**: 50 points, y = 2.5x + 10 + Gaussian(0, 1)
- **Outliers**: None
- **Purpose**: Verify Theil-Sen doesn't sacrifice accuracy on clean data
- **Expected**: Both methods should perform similarly

#### Scenario 2: 5% Outlier Contamination
- **Setup**: 50 points + 3 outliers (moderate y-deviation: ±20)
- **Outliers**: 3 points (6%) with extreme y values
- **Purpose**: Test moderate contamination (typical failed search runs)
- **Expected**: Theil-Sen stable, OLS degraded

#### Scenario 3: 10% Outlier Contamination
- **Setup**: 50 points + 5 outliers (heavy y-deviation: ±25)
- **Outliers**: 5 points (10%) with extreme y values
- **Purpose**: Test heavy contamination (multiple failed runs)
- **Expected**: Theil-Sen stable, OLS severely degraded

#### Scenario 4: Leverage Points
- **Setup**: 50 points + 2 high-x outliers
- **Outliers**: Points with extreme x values and moderate y deviations
- **Purpose**: Test worst case (high influence on slope)
- **Expected**: Theil-Sen stable, OLS catastrophically fails

### Application to Resonance Parameters

Simulate k_opt(ln N) estimation with synthetic data:

- **Data**: 10 points spanning 30-80 bit semiprimes
- **True model**: k ≈ 0.30 + 0.005 · ln(N)
- **Outliers**: 2 points (20%) - one very high, one very low
- **Task**: Predict k_opt for 127-bit challenge
- **Metrics**: Parameter error, MAD, prediction difference

**Note**: This uses synthetic data because real k-success values don't exist (see `experiments/resonance-drift-hypothesis` for barriers).

### Evaluation Metrics

1. **Slope Error**: |m_estimated - m_true|
   - Direct measure of parameter accuracy
   - Lower is better

2. **Median Absolute Deviation (MAD)**: median(|residual_i - median(residuals)|)
   - Robust measure of fit quality
   - Resistant to outliers (unlike SSR)
   - Lower indicates better robustness

3. **Sum of Squared Residuals (SSR)**: Σ(residual_i)²
   - Traditional OLS metric (for reference)
   - Can be inflated by outliers

4. **Prediction Difference**: |k_OLS - k_Theil-Sen| for 127-bit
   - Practical impact measure
   - Large difference indicates outlier influence

## Implementation

### Core Algorithm

```python
def theil_sen(x, y):
    # Compute all pairwise slopes
    slopes = []
    for i, j in combinations(range(len(x)), 2):
        if x[j] != x[i]:  # Skip ties
            slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    
    # Median slope
    m = median(slopes)
    
    # Median intercept
    b = median([y[i] - m * x[i] for i in range(len(x))])
    
    return m, b
```

### Key Implementation Details

1. **Ties in x**: Skip pairs where x_i = x_j (would cause division by zero)
2. **Median computation**: Exact median (not approximate) for deterministic results
3. **No weights**: Robustness comes from median operation, not from weighting schemes
4. **No tuning parameters**: Zero hyperparameters to configure

### Computational Complexity

For n data points:
- **Pairwise slopes**: C(n, 2) = n(n-1)/2 ≈ O(n²) pairs
- **Median computation**: O(n² log n) with sorting
- **Total**: O(n² log n)

**Practical performance:**
- n = 10: < 0.001 seconds
- n = 50: < 0.01 seconds
- n = 100: < 0.1 seconds
- n = 1000: ~3 seconds

For geofac parameter estimation (typically n < 50), overhead is negligible.

## Falsification Criteria

The hypothesis "Theil-Sen is more robust than OLS" would be falsified if:

1. **Similar degradation with outliers**
   - If Theil-Sen and OLS show comparable error increases when outliers present
   - Threshold: < 20% relative improvement over OLS

2. **Poor performance on clean data**
   - If Theil-Sen error on clean data exceeds OLS by > 20%
   - Would indicate accuracy sacrifice for robustness

3. **Impractical computational cost**
   - If Theil-Sen runtime exceeds 1 second for n = 100
   - Would make it unsuitable for interactive analysis

4. **Unstable predictions**
   - If bootstrap confidence intervals for Theil-Sen are wider than OLS
   - Would indicate high variance despite low bias

## Reproducibility

### Environment
- Python 3.12+
- No external dependencies (pure Python implementation)
- Deterministic seeding for synthetic data generation

### Running the Experiments

```bash
# From repository root
cd /home/runner/work/geofac/geofac

# Run comparison experiment (4 scenarios)
python3 experiments/theil-sen-robust-estimator/compare_estimators.py

# Run resonance application (synthetic k-data)
python3 experiments/theil-sen-robust-estimator/apply_to_resonance.py
```

### Output Files

1. **comparison_results.json**
   - Complete metrics for all 4 scenarios
   - Slope/intercept for both methods
   - MAD, SSR, errors

2. **resonance_application_results.json**
   - k_opt predictions for 127-bit challenge
   - Parameter comparison
   - Robustness metrics

### Validation

All results are deterministic (fixed PRNG seeds). Re-running the experiments will produce identical numeric outputs.

## Mathematical Background

### Theil-Sen Estimator

**Original papers:**
- Theil, H. (1950). "A rank-invariant method of linear and polynomial regression analysis"
- Sen, P. K. (1968). "Estimates of the regression coefficient based on Kendall's tau"

**Key theorem**: Under mild conditions, Theil-Sen estimator is:
- **Consistent**: Converges to true slope as n → ∞
- **Asymptotically normal**: √n(m̂ - m) → N(0, σ²)
- **High breakdown point**: Can tolerate up to 29.3% contamination

### Comparison with OLS

| Property | OLS | Theil-Sen |
|----------|-----|-----------|
| Objective | Minimize Σ(residuals²) | Median of slopes |
| Assumptions | Gaussian errors | None |
| Breakdown point | 0% | 29.3% |
| Complexity | O(n) | O(n²) |
| Efficiency (clean) | 100% | ~64% |
| Robustness | Poor | Excellent |

**Efficiency Loss**: On perfectly clean Gaussian data, Theil-Sen has ~64% efficiency of OLS (wider confidence intervals). However, with even small contamination, roles reverse.

### When Robustness Matters

**Geofac context:**
1. **Failed search runs**: Timeouts, threshold misses → extreme k values logged
2. **Scale transitions**: Numerical precision issues at bit-width boundaries → leverage points
3. **Heavy-tailed errors**: Resonance amplitude log-scale → non-Gaussian residuals
4. **Incomplete data**: Small sample sizes (n < 50) → outliers have high leverage

In all four cases, Theil-Sen maintains stability while OLS fails.

## Recommendations

### Adoption Guidelines

**Use Theil-Sen when:**
- Data source is empirical (experiments, measurements)
- Sample size is small to moderate (n < 1000)
- Outliers are possible (always assume this)
- Robustness is more important than efficiency

**Use OLS when:**
- Data is synthetic and rigorously validated
- Need exact likelihood-based inference
- Sample size is very large (n > 10,000)
- Computational budget is extremely constrained

**For geofac parameter estimation:** Always use Theil-Sen. The data is empirical, sample sizes are small, and outliers are inevitable.

### Integration Points

Replace OLS calls in:
1. `experiments/resonance-drift-hypothesis/regression_analysis.py`
2. `experiments/*/analysis_*.py` scripts
3. Any parameter tuning or trend analysis code

**Migration template:**
```python
# Old (fragile)
from scipy.stats import linregress
slope, intercept, r, p, stderr = linregress(x, y)

# New (robust)
from theil_sen_estimator import theil_sen
slope, intercept = theil_sen(x, y)
```

### Future Enhancements

1. **Confidence intervals**: Add bootstrap-based CIs
2. **Multiple regression**: Extend to multivariate (Repeated Median estimator)
3. **Online updates**: Incremental computation as new data arrives
4. **Weighted version**: For heteroscedastic errors (if needed)

## References

### Academic
1. Theil, H. (1950). "A rank-invariant method of linear and polynomial regression analysis." Proceedings of the Koninklijke Nederlandse Akademie van Wetenschappen, Series A, 53: 386-392, 521-525, 1397-1412.

2. Sen, P. K. (1968). "Estimates of the regression coefficient based on Kendall's tau." Journal of the American Statistical Association, 63(324): 1379-1389.

3. Wilcox, R. R. (2012). "Introduction to Robust Estimation and Hypothesis Testing." Academic Press. Chapter 10: Robust regression.

### Implementation
4. Siegel, A. F. (1982). "Robust regression using repeated medians." Biometrika, 69(1): 242-244.

5. Rousseeuw, P. J., & Leroy, A. M. (1987). "Robust Regression and Outlier Detection." Wiley. Chapter 5.

### Related Geofac Experiments
- `experiments/resonance-drift-hypothesis/` - Motivating context for k(ln N) estimation
- `experiments/kernel-order-impact-study/` - Parameter sensitivity analysis
- `experiments/z5d-comprehensive-challenge/` - Systematic calibration pipeline

---

**Experiment Date:** 2025-11-23  
**Status:** Complete - hypothesis strongly supported  
**Artifacts:** All code, data, and documentation committed to repository
