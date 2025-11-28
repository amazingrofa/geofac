# Hash-Bounds Integration Experiment

## Objective

**Rigorously test** the hypothesis that SHA256-based "hash-bounds" can improve factor prediction in geofac.

## Result

**HYPOTHESIS PARTIALLY VALIDATED BUT INEFFECTIVE**: The mathematical calculations in the hypothesis are correct, but the hash-adjustment does NOT improve predictions for the 127-bit challenge. In fact, it WORSENS the prediction.

## Hypothesis Under Test

The hypothesis claims:

1. **Hash Fraction**: Compute `frac_hash = SHA256(str(N))` normalized to [0,1]
2. **Z5D-like Prediction**: Compute `f = {sqrt((sqrt(N)/ln(sqrt(N))) * ln((sqrt(N)/ln(sqrt(N)))))}` where `{x}` denotes fractional part
3. **Adjustment**: `f_adjusted = f + (frac_hash - 0.5) * attenuation` where attenuation is bit-length dependent (e.g., 0.01 for 127-bit)
4. **Claim**: This adjusted prediction allegedly narrows k-sampling range and improves factor detection

### Claimed Values for 127-bit Challenge

| Claimed | Value | Verified |
|---------|-------|----------|
| frac_hash | ≈ 0.4253 | ✅ CORRECT |
| Z5D prediction | ~0.2278 | ✅ CORRECT |
| Actual {sqrt(p)} | ~0.2282 | ✅ CORRECT |
| Error | ~0.00042 | ✅ CORRECT |

**All calculation claims verified.** However, the adjustment WORSENS the prediction.

## Methodology

### 1. Verify SHA256 Calculations

Independent computation of SHA256(str(N)) for all test cases to verify claimed hash values.

### 2. Verify Z5D-like Prediction Formula

Compute the formula exactly as specified and compare to claimed values.

### 3. Compare Against Baseline

Test whether hash-adjusted predictions outperform:
- Unadjusted Z5D predictions
- Random predictions
- Null model (predict 0.5)

### 4. Test on Multiple Cases

- **127-bit Challenge**: N = 137524771864208156028430259349934309717
- **RSA-100**: N = 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
- **Gate 1 (30-bit)**: N = 1073217479
- **Gate 2 (60-bit)**: N = 1152921470247108503

### 5. Statistical Analysis

Compute:
- Mean absolute error for each method
- Correlation between hash values and factor locations
- Statistical significance tests

## Precision Requirements

Following repository standards:
- `precision = max(configured, N.bitLength() × 4 + 200)`
- For 127-bit: `precision = max(100, 127 × 4 + 200) = 708` decimal places
- Use mpmath with explicit `mp.dps` setting

## Test Cases

| Case | N | p | q | Bit-length |
|------|---|---|---|------------|
| Challenge | 137524771864208156028430259349934309717 | 10508623501177419659 | 13086849276577416863 | 127 |
| RSA-100 | (see EXPERIMENT_REPORT.md) | (known) | (known) | 330 |
| Gate 1 | 1073217479 | 32749 | 32771 | 30 |
| Gate 2 | 1152921470247108503 | 1073741789 | 1073741827 | 60 |

## Expected Outcomes

### What We Found

| Outcome | Result |
|---------|--------|
| Calculation claims match | ✅ YES - All verified |
| Adjustment improves 127-bit | ❌ NO - Error increased 2.8x |
| Consistent improvement | ❌ NO - Only 3/4 cases helped |
| Statistical significance | ❌ NO - Avg improvement only 0.003 |

## Key Finding

**The baseline Z5D prediction (without hash adjustment) is already remarkably accurate for the 127-bit challenge**, with an error of only 0.000421. Applying the hash-based adjustment INCREASES the error to 0.001167.

## Files

- `hash_bounds_test.py` - Main implementation
- `test_hash_bounds.py` - pytest test suite
- `EXPERIMENT_REPORT.md` - Detailed findings
- `INDEX.md` - Quick navigation

## Reproducibility

All calculations are deterministic:
- SHA256 is deterministic
- mpmath precision is pinned
- No random sampling used

Run tests with:
```bash
cd experiments/hash-bounds-integration
pytest test_hash_bounds.py -v
python3 hash_bounds_test.py
```

## Compliance

✅ Works on validation gate numbers and 127-bit whitelist  
✅ No classical fallbacks  
✅ Deterministic methods only  
✅ Explicit precision with mpmath  
✅ All parameters logged  

---

*Experiment designed to rigorously falsify the hash-bounds hypothesis.*
