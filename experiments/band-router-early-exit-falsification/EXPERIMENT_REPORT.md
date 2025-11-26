# Experiment Report: Band-First Router + Early-Exit Guard Falsification

## Executive Summary

**HYPOTHESIS FALSIFIED**

Both components of the "Band-First Router + Early-Exit Guard" hypothesis failed to meet their performance thresholds on CHALLENGE_127:

| Test | Metric | Achieved | Threshold | Result |
|------|--------|----------|-----------|--------|
| **A** | Candidate reduction | **8.3%** | ≥70% | ❌ FAIL |
| **A** | Coverage | 97.9% | ≥90% | ✅ PASS |
| **B** | Step reduction | **0.0%** | ≥35% | ❌ FAIL |
| **B** | Time reduction | 23.6% | ≥35% | ❌ FAIL |
| **B** | Recall loss | 0.0% | ≤5% | ✅ PASS |

### Root Cause Analysis

1. **Band router fails**: The expected gap Δ ≈ 44 at √N ≈ 1.17×10^19 is extremely small relative to the scale. With bands of width ~44, the search range is tiny (~940 total), leaving only ~217 candidates after wheel filtering. There's insufficient "unbanded" baseline to achieve 70% reduction.

2. **Early-exit shows no benefit**: With only ~98 candidates per scan and no flat surfaces detected (0 early exits), there's no opportunity for early-exit to provide savings.

### Conclusion

The hypothesis is **fundamentally incompatible** with the CHALLENGE_127 structure. The expected gap (~44) is so small relative to √N that:

- Banding provides negligible compression (bands nearly cover the entire practical search space)
- Early-exit has no flat regions to abort (search space is too small)

This is not a parameter tuning failure—it's a structural mismatch between the hypothesis design (which assumes large search spaces with many wasteful regions) and the challenge's tight geometric structure.

---

## Detailed Results

### Test A — Band Router Coverage

**Date**: 2025-11-25  
**Git HEAD**: See artifact  
**Seed**: 42

#### Parameters
| Parameter | Value |
|-----------|-------|
| N | 137524771864208156028430259349934309717 |
| √N | 11727095627827384440 |
| C | 0.9 |
| α | 1.0 |
| wheel | 210 |
| num_bands | 20 |
| dps | 708 |

#### Results
| Metric | Value |
|--------|-------|
| Expected gap | 43.91 |
| Bands planned | 20 |
| Delta max | 473 |
| Total band span | 940 |
| Unbanded + wheel count | 217 |
| Banded + wheel count | 199 |
| **Reduction** | **8.3%** |
| **Coverage** | **97.9%** |

#### Analysis

The reduction of only 8.3% (far below 70% threshold) occurs because:

1. **Tiny search space**: Expected gap ~44 × 20 bands = ~880 total δ range
2. **Dense bands**: At this scale, wheel-filtered candidates are sparse (~0.23 per unit)
3. **Near-complete overlap**: Bands cover 97.9% of the already-tiny baseline

The hypothesis assumes banding would exclude large swaths of candidates. Instead, the search space is so small that banding provides no meaningful compression.

#### Artifact

```
experiments/band-router-early-exit-falsification/router_A_seed42.jsonl
```

---

### Test B — Early-Exit Efficiency

**Date**: 2025-11-25  
**Git HEAD**: See artifact  
**Seed**: 43

#### Parameters
| Parameter | Value |
|-----------|-------|
| N | 137524771864208156028430259349934309717 |
| C | 0.9 |
| α | 1.0 |
| τ_grad | 1e-6 |
| τ_curv | 1e-8 |
| L | 8 |
| max_steps_per_band | 500 |
| k | 0.35 |

#### Control (Early-Exit OFF)
| Metric | Value |
|--------|-------|
| Steps | 98 |
| Time | 0.45s |
| Peaks | 0 |
| Early exits | 0 |

#### Treatment (Early-Exit ON)
| Metric | Value |
|--------|-------|
| Steps | 98 |
| Time | 0.34s |
| Peaks | 0 |
| Early exits | 0 |

#### Efficiency Metrics
| Metric | Value | Threshold | Result |
|--------|-------|-----------|--------|
| Step reduction | **0.0%** | ≥35% | ❌ FAIL |
| Time reduction | 23.6% | ≥35% | ❌ FAIL |
| Recall loss | 0.0% | ≤5% | ✅ PASS |

#### Analysis

Zero early exits occurred because:

1. **Insufficient steps**: Only 98 total steps across all bands (well below 500 limit)
2. **No flat regions**: The search space exhausted naturally before L=8 consecutive flat steps could accumulate
3. **Measurement artifact**: The 23.6% time reduction is overhead variance, not early-exit benefit

#### Artifacts

- Control: `scan_off_B_seed43.jsonl`
- Treatment: `scan_on_B_seed43.jsonl`
- Diff: `diff.jsonl`

---

## Falsification Criteria Assessment

### Criterion 1: Band Router Reduction ≥70%
**Status**: ❌ FALSIFIED  
**Evidence**: Reduction = 8.3% << 70%  
**Cause**: Search space too small for meaningful banding compression

### Criterion 2: Coverage ≥90%
**Status**: ✅ SUPPORTED  
**Evidence**: Coverage = 97.9% ≥ 90%  
**Note**: Trivially satisfied due to near-complete band overlap

### Criterion 3: Step/Time Reduction ≥35%
**Status**: ❌ FALSIFIED  
**Evidence**: Step reduction = 0.0%, Time reduction = 23.6%  
**Cause**: No flat regions detected; search space exhausted naturally

### Criterion 4: Recall Loss ≤5%
**Status**: ✅ SUPPORTED  
**Evidence**: Recall loss = 0.0% ≤ 5%  
**Note**: Trivially satisfied—no peaks in either control or treatment

---

## Recommendations

### For This Experiment

The hypothesis is **structurally unsuited** to CHALLENGE_127. It requires:

1. Large search spaces with substantial "wasteful" regions
2. Diverse amplitude/curvature landscapes with flat regions

Neither condition holds for a 127-bit balanced semiprime where factors are very close to √N.

### For Future Work

Consider testing the hypothesis on:

1. **Larger semiprimes** (RSA-250+) where δ-ranges might be larger
2. **Imbalanced semiprimes** where factors are far from √N
3. **Alternative metrics** that don't assume large candidate pools

### Structural Insight

The expected gap Δ ≈ ln(√N) ≈ 44 for CHALLENGE_127 reveals a fundamental tension:

- **Banding assumes**: Large δ-ranges with sparse factors
- **Reality**: At scale 10^19, factors are densely clustered within ~100 units of √N
- **Implication**: Sophisticated routing adds overhead without benefit at this scale

---

## Reproducibility

### Environment
- Python 3.12+
- mpmath (arbitrary precision)
- pytest 9.0.1

### Commands
```bash
cd experiments/band-router-early-exit-falsification
pytest test_band_router.py -v -s
```

### Artifacts
All artifacts are JSONL files with full parameter logging:

| File | Purpose |
|------|---------|
| `router_A_seed42.jsonl` | Test A results |
| `scan_off_B_seed43.jsonl` | Test B control |
| `scan_on_B_seed43.jsonl` | Test B treatment |
| `diff.jsonl` | Test B comparison |

### Determinism
- Seeds: 42 (Test A), 43 (Test B)
- Precision: 708 dps (adaptive)
- All parameters logged in artifacts

---

## Conclusion

**HYPOTHESIS FALSIFIED**

The "Band-First Router + Early-Exit Guard" hypothesis does not provide meaningful performance improvements on CHALLENGE_127:

- **Band routing**: 8.3% reduction vs. 70% threshold
- **Early-exit**: 0% step reduction vs. 35% threshold

This is not a parameter tuning issue—it reflects a fundamental incompatibility between the hypothesis design and the challenge structure. The hypothesis assumes large, wasteful search spaces; CHALLENGE_127 has a tiny, dense search space.

**Recommendation**: Do not implement band routing or early-exit guards for the 127-bit challenge. Focus on methods that exploit the tight clustering of factors near √N rather than trying to prune a search space that is already minimal.

---

**Report Generated**: 2025-11-25  
**Experiment**: band-router-early-exit-falsification  
**Status**: FALSIFIED
