# Hash-Bounds Prior Falsification Experiment

## **HYPOTHESIS FALSIFIED** — The v1 Hash-Bounds Predictor Shows Performance Worse Than Random

The Hash-Bounds hypothesis claims that Z5D prime structure combined with √p fractional parts can predict a probabilistic band on `frac(√d)` or `d/√N` for a factor `d` of semiprime N, with 50-80% coverage at width 0.155.

**Observed results**: 10.7% hit rate (3/28 checks) versus 15.5% random baseline.

| Metric | Hypothesis Claim | Observed | Verdict |
|--------|-----------------|----------|---------|
| Overall coverage | 50% - 80% | 10.7% | ❌ FALSIFIED |
| vs Random (15.5%) | Outperform | Underperform | ❌ FALSIFIED |
| fracSqrt strategy | ~50% | 21.4% | ❌ Below minimum |
| dOverSqrtN strategy | ~50% | 0.0% | ❌ Complete miss |

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Hypothesis Under Test](#hypothesis-under-test)
3. [Predictor Implementation](#predictor-implementation)
4. [Test Methodology](#test-methodology)
5. [Results](#results)
6. [Falsification Analysis](#falsification-analysis)
7. [Discussion](#discussion)
8. [Reproducibility](#reproducibility)
9. [Files](#files)

---

## Executive Summary

This experiment implements and tests a v1 Hash-Bounds predictor to falsify the hypothesis that Z5D prime structure + √p fractional parts can predict a probabilistic band on `frac(√d)` or `d/√N` for factor discovery.

### Key Findings

1. **Overall hit rate: 10.7%** — Significantly below the claimed 50% minimum
2. **Random baseline: 15.5%** — The predictor performs *worse* than random chance
3. **fracSqrt strategy: 21.4%** — Shows some structure but far below hypothesis claims
4. **dOverSqrtN strategy: 0.0%** — Complete failure with zero hits across all tests
5. **127-bit challenge: 1/4 hits (25%)** — Only p_fracSqrt landed in band

### Conclusion

**The v1 Hash-Bounds predictor as implemented is FALSIFIED.** The observed performance is:
- Below the claimed 50-80% coverage range
- Worse than random chance (width-based baseline)
- Asymmetric between strategies (fracSqrt vs dOverSqrtN)

This does not definitively falsify the underlying hypothesis — the v1 predictor may be a poor proxy for the full Z5D-based hash-bounds theory. Further investigation with refined predictors is warranted.

---

## Hypothesis Under Test

**Hash-Bounds Hypothesis:**

> Z5D prime structure + √p fractional parts can be turned into a probabilistic band on `frac(√d)` (or `d/√N`) for a factor `d` of a semiprime N.

### Claimed Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Mean relative error | ≈ 22,126 ppm | Prediction error in parts per million |
| Average fractional error | ≈ 0.237 | Error in [0,1) band |
| Width factor | ≈ 0.155 | Band width for ~51.5% coverage |
| Coverage | 50-80% | Hit rate in older experiments |

### Critical Distinction

This is **NOT** a deterministic bound. It's a prior window that allegedly hits factors in approximately 50-80% of cases.

---

## Predictor Implementation

### v1 Hash-Bounds Predictor Pipeline

```
1. Input selection:
   x = floor(√N)  [or x = N for alternate mode]

2. Prime index approximation (PNT proxy):
   m ≈ x / ln(x)

3. Predicted prime location:
   p_pred ≈ m × ln(m)

4. Fractional part:
   f_pred = frac(√p_pred) ∈ [0,1)

5. Band construction:
   center = f_pred
   width = 0.155 (adjustable)
   lower = center - width/2
   upper = center + width/2
   [with wrap-around in [0,1)]
```

### Strategies for Factor Checking

| Strategy | Formula | Description |
|----------|---------|-------------|
| `fracSqrt` | g(d) = frac(√d) | Fractional part of square root of factor |
| `dOverSqrtN` | g(d) = frac(d/√N) | Fractional part of factor divided by √N |

A factor is considered "in band" if its g(d) value falls within [lower, upper], handling wrap-around.

### Precision

Adaptive precision using mpmath:
```
dps = max(100, bit_length × 4 + 200)
```

For 127-bit challenge: 708 decimal places.

---

## Test Methodology

### Test Suite

1. **127-bit Challenge** (whitelisted):
   - N = 137524771864208156028430259349934309717
   - p = 10508623501177419659
   - q = 13086849276577416863

2. **Semiprimes in [10^14, 10^18]**:
   - 100000007 × 1000000007 = 100000007700000049 (~10^17)
   - 10000019 × 10000079 = 100000980001501 (~10^14)
   - 100003 × 1000000007 = 100003000700021 (~10^14)

3. **Generated balanced semiprimes**:
   - 50-bit: 618065584371421 (seed=20251129)
   - 55-bit: 8362822623568939 (seed=20251130)
   - 58-bit: 127654898013390029 (seed=20251131)

### Checks Per Semiprime

For each semiprime N with factors (p, q):
- p with fracSqrt strategy
- p with dOverSqrtN strategy
- q with fracSqrt strategy
- q with dOverSqrtN strategy

**Total: 4 checks per semiprime × 7 semiprimes = 28 checks**

### Falsification Criteria

1. If coverage drops significantly below 50% consistently → **WEAKENED**
2. If predictor shows no better than random (width ≈ 15.5% for 0.155) → **FALSIFIED**
3. If coverage is within 50-80% → **NOT FALSIFIED**

---

## Results

### Per-Semiprime Results

| Semiprime | Bits | Band | Hits | Rate |
|-----------|------|------|------|------|
| 127-bit challenge | 127 | [0.148, 0.308] | 1/4 | 25% |
| 10^17 scale | 57 | [0.964, 0.119]* | 1/4 | 25% |
| 10^14 scale | 47 | [0.606, 0.761] | 0/4 | 0% |
| Mixed ~10^14 | 47 | [0.620, 0.775] | 0/4 | 0% |
| 50-bit generated | 50 | [0.081, 0.236] | 0/4 | 0% |
| 55-bit generated | 53 | [0.377, 0.532] | 0/4 | 0% |
| 58-bit generated | 57 | [0.123, 0.278] | 1/4 | 25% |

*Band wraps around at 0/1 boundary

### Detailed Check Results

#### 127-bit Challenge
| Check | Factor Value | Band | In Band |
|-------|--------------|------|---------|
| p_fracSqrt | 0.228200 | [0.148, 0.308] | ✓ |
| p_dOverSqrtN | 0.896098 | [0.148, 0.308] | ✗ |
| q_fracSqrt | 0.726221 | [0.148, 0.308] | ✗ |
| q_dOverSqrtN | 0.115950 | [0.148, 0.308] | ✗ |

### Aggregate Statistics

| Metric | Value |
|--------|-------|
| Total semiprimes | 7 |
| Total checks | 28 |
| Total hits | 3 |
| Overall hit rate | **10.7%** |

### Strategy Breakdown

| Strategy | Hits | Checks | Rate |
|----------|------|--------|------|
| fracSqrt | 3 | 14 | **21.4%** |
| dOverSqrtN | 0 | 14 | **0.0%** |

### Factor Breakdown

| Factor | Hits | Checks | Rate |
|--------|------|--------|------|
| p (smaller) | 2 | 14 | 14.3% |
| q (larger) | 1 | 14 | 7.1% |

---

## Falsification Analysis

### Key Comparisons

| Comparison | Expected | Observed | Outcome |
|------------|----------|----------|---------|
| vs Hypothesis minimum (50%) | ≥50% | 10.7% | **FAIL** |
| vs Random baseline (15.5%) | >15.5% | 10.7% | **FAIL** |
| fracSqrt vs claim | ~50% | 21.4% | **FAIL** |
| dOverSqrtN vs claim | ~50% | 0.0% | **FAIL** |

### Conclusion

**FALSIFIED** — Strong evidence against the v1 Hash-Bounds predictor.

The performance is:
1. **69% below** the claimed 50% minimum (10.7% vs 50%)
2. **31% below** random chance (10.7% vs 15.5%)
3. Exhibits **complete failure** on dOverSqrtN strategy (0% hits)

### Evidence Strength

**Strong** — The predictor performs worse than random chance would suggest.

---

## Discussion

### Why Did the Predictor Fail?

Several possibilities:

1. **Oversimplified proxy**: The PNT-based prime index approximation may be too crude. Real Z5D uses more sophisticated prime structure.

2. **Wrong mapping**: The mapping x → m → p_pred → f_pred may not capture the actual relationship claimed by the hypothesis.

3. **Strategy mismatch**: The dOverSqrtN strategy shows 0% hits, suggesting it may be fundamentally incompatible with this predictor design.

4. **Width insufficient**: At 0.155 width, random baseline is 15.5%. The predictor needs to significantly outperform this, which it doesn't.

### What This Doesn't Falsify

- The underlying Z5D prime structure theory
- More sophisticated hash-bounds implementations
- Adaptive width or curvature-corrected predictors
- Factor-specific (p vs q) targeting strategies

### Next Steps

1. **Refine the predictor**: Incorporate actual Z5D density estimates
2. **Adjust width**: Test larger widths (0.25, 0.35, 0.50)
3. **Strategy investigation**: Why does fracSqrt partially work (21.4%) while dOverSqrtN completely fails (0%)?
4. **Curvature terms**: Add κ(n) corrections as mentioned in hypothesis
5. **Scale effects**: Investigate bit-length dependence more rigorously

---

## Reproducibility

### Configuration

```json
{
  "width": 0.155,
  "use_sqrt_N": true,
  "bit_length_scaling": true,
  "strategies": ["fracSqrt", "dOverSqrtN"],
  "random_seed": 20251128,
  "timestamp": "2025-11-28T12:41:51.041213Z"
}
```

### Seeds

| Purpose | Seed |
|---------|------|
| Main experiment | 20251128 |
| 50-bit generation | 20251129 |
| 55-bit generation | 20251130 |
| 58-bit generation | 20251131 |

### Precision

All computations use mpmath with adaptive decimal places:
```
dps = max(100, bit_length × 4 + 200)
```

### Running the Experiment

```bash
cd experiments/hash-bounds-prior-falsification

# Run tests
python3 -m pytest test_hash_bounds.py -v

# Run experiment
python3 run_experiment.py

# View results
cat run_log.json
```

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This document — executive summary and experiment details |
| `hash_bounds_predictor.py` | v1 Hash-Bounds predictor implementation |
| `run_experiment.py` | Main experiment runner |
| `test_hash_bounds.py` | Pytest unit tests (28 tests) |
| `run_log.json` | Experiment results with all diagnostic data |

---

## Validation Gates

This experiment adheres to the geofac validation gates:

- ✅ **127-bit challenge** (N = 137524771864208156028430259349934309717) — tested
- ✅ **[10^14, 10^18] operational range** — multiple semiprimes tested
- ✅ **No classical fallbacks** — pure geometric/probabilistic approach
- ✅ **Precision logged** — adaptive mpmath precision used
- ✅ **Reproducibility** — seeds pinned, parameters logged

---

## References

- Project `README.md` — Repository overview
- Project `docs/VALIDATION_GATES.md` — Gate specifications
- `experiments/z5d-comprehensive-challenge/` — Related Z5D experiment

---

**Status**: Experiment complete — **HYPOTHESIS FALSIFIED**  
**Last Updated**: 2025-11-28  
**Experiment**: hash-bounds-prior-falsification
