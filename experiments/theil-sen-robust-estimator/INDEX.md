# Theil-Sen Robust Estimator Experiment

## Quick Navigation

**Start here:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) - Clear verdict and key findings

Supporting documents:
- **[README.md](README.md)** - Detailed methodology and experiment design
- **[METHODOLOGY.md](METHODOLOGY.md)** - Mathematical foundations and implementation details

Code artifacts:
- **[theil_sen_estimator.py](theil_sen_estimator.py)** - Core implementation
- **[compare_estimators.py](compare_estimators.py)** - Theil-Sen vs OLS comparison
- **[apply_to_resonance.py](apply_to_resonance.py)** - Application to k_opt(ln N) estimation
- **[test_theil_sen.py](test_theil_sen.py)** - Unit tests validating correctness and robustness

Data files:
- **[comparison_results.json](comparison_results.json)** - Detailed comparison metrics
- **[resonance_application_results.json](resonance_application_results.json)** - Resonance parameter predictions

## TL;DR

**Hypothesis**: Theil-Sen median slope estimator is more robust than OLS for parameter trend estimation with outliers

**Result**: **STRONGLY SUPPORTED** - 81.4% error reduction, 6× better robustness

**Key Finding**: Theil-Sen tolerates up to 29% outliers while OLS fails with a single bad point

**Impact**: Use Theil-Sen for all geofac parameter regression (k vs ln(N), threshold tuning, etc.)

**Recommendation**: Replace OLS with Theil-Sen as default estimator in parameter analysis scripts

## Experiment Overview

This experiment implements and validates the Theil-Sen robust regression estimator as an alternative to Ordinary Least Squares (OLS) for parameter optimization in geofac.

### What Was Tested

1. **Synthetic comparison**: 4 scenarios with varying outlier contamination
2. **Resonance application**: Estimate k_opt(ln N) with synthetic k-success data
3. **Robustness metrics**: MAD, slope error, SSR across methods

### Key Results

| Metric | Theil-Sen | OLS | Winner |
|--------|-----------|-----|--------|
| Average slope error | 0.007 | 0.040 | **Theil-Sen (81% better)** |
| MAD (robustness) | 0.550 | 0.825 | **Theil-Sen (50% better)** |
| Breakdown point | 29.3% | 0% | **Theil-Sen** |
| Complexity | O(n²) | O(n) | OLS (negligible for n<100) |

### Verdict Summary

**Supported** - Theil-Sen decisively outperforms OLS in all outlier scenarios while matching OLS on clean data. No falsification criteria met.

**Practical Impact** - For geofac parameter estimation with incomplete or noisy data, Theil-Sen provides stable predictions where OLS fails.

---

Read [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) for complete findings and recommendations.
