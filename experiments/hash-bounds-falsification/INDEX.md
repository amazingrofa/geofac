# Hash-Bounds Falsification Experiment

**Navigation**: [INDEX.md](INDEX.md) | [README.md](README.md) | [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md) | [hash_bounds_test.py](hash_bounds_test.py) | [results.json](results.json)

---

## TL;DR

**Status**: Complete - Hypothesis DECISIVELY FALSIFIED

**Hypothesis**: Hash-bounds derived from Z5D fractional part predictions {√(m·ln(m))} can predict bounds for factor location in semiprime N = p × q, with claimed ~51.5% coverage using width factor 0.155.

**Verdict**: **FALSIFIED**

**Key Finding**: The hash-bounds method achieves **0% coverage** (0/6 factors) across all three validation gates. This is significantly below both the claimed 51.5% coverage and even the random baseline of 15.5%. The Z5D fractional part prediction systematically misses actual factor positions by large margins (average error 0.457 vs claimed ~0.237).

**Critical Insight**: The Z5D prediction formula {√(m·ln(m))} where m ≈ p/ln(p) bears no meaningful relationship to actual {√p}. For CHALLENGE_127, the prediction is ~0.879 while actual is ~0.228—a complete miss. The hypothesis is based on mathematical structures that do not actually correlate with factor locations.

---

## Quick Start

```bash
# Run experiment
cd experiments/hash-bounds-falsification
python hash_bounds_test.py

# Run tests
python -m pytest test_hash_bounds.py -v

# View results
cat results.json
```

---

## Experiment Structure

1. **[INDEX.md](INDEX.md)** - This file (navigation and TL;DR)
2. **[README.md](README.md)** - Experiment design, methodology, and setup
3. **[EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md)** - Complete findings, analysis, and verdict
4. **[hash_bounds_test.py](hash_bounds_test.py)** - Implementation code
5. **[test_hash_bounds.py](test_hash_bounds.py)** - Pytest test suite (26 tests)
6. **[results.json](results.json)** - Raw experimental data

---

## Summary Statistics

### Test Configuration
- **Validation Gates**: 3 (30-bit, 60-bit, 127-bit CHALLENGE)
- **Factors Tested**: 6 (2 per gate)
- **Width Factor**: 0.155 (from hypothesis)
- **Precision**: Adaptive (max(configured, N.bit_length() × 4 + 200))
- **Seed**: 42 (reproducible)

### Coverage Results

| Gate | N (bit-length) | Actual {√p} | Z5D Pred | Error | p in bounds |
|------|----------------|-------------|----------|-------|-------------|
| Gate 1 (30-bit) | 30 | 0.967 | 0.290 | 0.676 | ❌ No |
| Gate 2 (60-bit) | 60 | 0.999 | 0.712 | 0.288 | ❌ No |
| Gate 3 (127-bit) | 127 | 0.228 | 0.879 | 0.651 | ❌ No |

### Key Metrics

| Metric | Claimed | Observed | Verdict |
|--------|---------|----------|---------|
| Coverage Rate | 51.5% | 0.0% | ❌ FAIL |
| Avg Fractional Error | ~0.237 | 0.457 | ❌ FAIL |
| Mean Relative Error | 22,126 ppm | 456,703 ppm | ❌ FAIL |
| Factors in Bounds | 3/6 expected | 0/6 actual | ❌ FAIL |

---

## Falsification Criteria (All Met)

1. ✅ **Proposed bounds systematically miss actual factor's fractional part**: 0/6 factors captured
2. ✅ **Coverage rate < 30%**: Achieved 0% (significantly below 30% threshold)
3. ✅ **Method provides no predictive signal vs random baseline**: Random would expect 15.5% coverage; observed 0%
4. ✅ **Average error exceeds claimed calibration**: 0.457 vs claimed 0.237 (93% worse)

---

## Implications

### For Hash-Bounds Hypothesis
- The Z5D prediction formula {√(m·ln(m))} does not predict {√p}
- Fractional part bounds provide no useful factor location information
- The claimed calibration metrics are not reproducible

### For CHALLENGE_127
- The specific prediction for p=10508623501177419659 misses by ~0.65
- Bounds [0.801, 0.956] completely miss actual {√p} ≈ 0.228
- Hash-bounds cannot narrow the search window for this number

### For Geofac Project
- Hash-bounds should not be integrated into geometric resonance methods
- Factor location via fractional part analysis is not a viable strategy
- Resources should focus on proven geometric ranking approaches

---

## Related Experiments

- **[signed-scaled-adjustments/](../signed-scaled-adjustments/)** - Tests θ'(n,k) adjustments (falsified)
- **[z5d-comprehensive-challenge/](../z5d-comprehensive-challenge/)** - Z5D as band/step oracle

---

## Citation

```bibtex
@experiment{geofac-hash-bounds-falsification-2025,
  title={Hash-Bounds Falsification: Testing Z5D Fractional Part Predictions},
  author={Geofac Experiment Framework},
  year={2025},
  institution={geofac},
  note={Decisively falsified with 0% coverage across all validation gates},
  url={https://github.com/zfifteen/geofac/tree/main/experiments/hash-bounds-falsification}
}
```

---

**Experiment Date**: 2025-11-28  
**Status**: Complete  
**Verdict**: Hypothesis Decisively Falsified
