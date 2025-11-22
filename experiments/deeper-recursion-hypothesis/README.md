# Deeper Recursion Hypothesis Experiment

## Objective

Attempt to falsify the hypothesis that extending fractal-recursive geodesic search to 3+ stages with dynamic thresholds can reduce runtime below baseline on 110+ bit semiprimes, overcoming the 2.3× overhead observed in 2-stage prototypes.

## Hypothesis Under Test

**Claimed by analysis of PR #92 and Z-framework correlations:**

> "Deeper recursion (3+ stages) with dynamic thresholds and incremental evaluation can reduce runtime below baseline (< 4.027s) on 110-bit semiprimes by avoiding upfront coarse sweep overhead and adaptively focusing on high-density geodesic regions."

**Specific claims:**
1. **Multi-scale recursion**: 3+ stages allow finer-grained pruning than 2 stages
2. **Dynamic thresholds**: Tune per-stage thresholds based on density profiles from previous runs
3. **Incremental evaluation**: Compute next stage only when current stage shows promise
4. **Runtime improvement**: Achieve runtime < baseline while maintaining ≥50% coverage reduction

## Background: PR #92 Analysis

### Baseline (Standard GVA)
Test case: N = 1296000000000003744000000000001183 (110 bits)
- Factors: p = 36000000000000013, q = 36000000000000091 (gap = 78)
- Runtime: 4.027s
- Sampling: 1403 sampled, 1115 tested candidates
- Coverage: 100% (full window search)
- Geodesic distance: 0.000905

### 2-Stage Coarse-to-Fine
- Stage 1 (Coarse): Score 32 segments, sample 1600 candidates
- Stage 2 (Fine): Search top 16 segments (50%), test 1149 candidates
- Runtime: 9.076s (2.3× slower than baseline ✗)
- Coverage: 50% (as intended ✓)
- Factors: Same as baseline (recovered ✓)

**Key insight**: Fractal structure is exploitable (50% coverage works), but overhead from full coarse sweep negates benefit.

## Experimental Design

### Falsification Criteria

The hypothesis is **FALSIFIED** if any of the following hold:

1. **Runtime criterion**: 3-stage runtime ≥ baseline runtime (≥ 4.027s)
2. **Correctness criterion**: 3-stage fails to recover correct factors
3. **Efficiency criterion**: 3-stage shows no improvement over 2-stage (≥ 9.076s)
4. **Overhead criterion**: Total candidates tested in 3-stage ≥ 2-stage candidates

The hypothesis is **SUPPORTED** if:
- 3-stage runtime < baseline runtime (< 4.027s) ✓
- AND factors recovered correctly ✓
- AND demonstrates measurable efficiency gain over 2-stage ✓

### Test Corpus

**Primary test case** (from PR #92):
- N = 1296000000000003744000000000001183 (110 bits)
- p = 36000000000000013
- q = 36000000000000091
- Balance: p ≈ q ≈ √N (hardest case for factorization)

**Validation range**: [10^14, 10^18] per VALIDATION_GATES.md (if time permits, test on additional cases)

### Implementation

#### Baseline GVA (Control)
From `gva_factorization.py`:
- 7D torus embedding with golden ratio
- Riemannian geodesic distance
- Adaptive sampling with k ∈ [0.30, 0.35, 0.40]
- Single-pass exhaustive search

#### 2-Stage Prototype (PR #92 Simulation)
- **Stage 1 (Coarse)**: Divide search window into segments, score by geodesic density
- **Stage 2 (Fine)**: Search top-K segments exhaustively
- Parameters: 32 segments, top-K=16 (50% coverage)

#### 3-Stage Prototype (Hypothesis Test)
- **Stage 1 (Very Coarse)**: Rough segment scoring, identify promising quadrants
- **Stage 2 (Medium)**: Refine top quadrants into sub-segments, adaptive threshold
- **Stage 3 (Fine)**: Focused geodesic search in highest-density sub-segments
- **Dynamic thresholds**: Tune based on density_profile.json from instrumentation
- **Incremental evaluation**: Skip Stage 3 if Stage 2 score below threshold

#### Instrumentation
`instrument_density.py`:
- Profile geodesic density across segments
- Capture candidate distribution
- Export density_profile.json for threshold tuning
- Log stage-by-stage overhead

### Metrics

1. **Runtime**: Wall-clock time (seconds) - PRIMARY METRIC
2. **Total candidates tested**: Sum across all stages
3. **Coverage**: Percentage of search window explored
4. **Samples per stage**: Breakdown of computational cost
5. **Success rate**: Factor recovery (binary: success/failure)
6. **Speedup ratio**: baseline_time / method_time

### Parameters

#### Baseline GVA
- k_values = [0.30, 0.35, 0.40]
- max_candidates = 50000
- timeout = 60s

#### 2-Stage
- segments_stage1 = 32
- samples_stage1 = 1600
- top_k = 16 (50%)
- max_candidates_stage2 = 50000

#### 3-Stage (Hypothesis)
- segments_stage1 = 8 (coarser)
- samples_stage1 = 400 (reduce overhead)
- top_k_stage1 = 4 (50%)
- segments_stage2_per_region = 4
- samples_stage2 = 800
- top_k_stage2 = 2 (50% again)
- max_candidates_stage3 = 50000
- dynamic_threshold_stage2 = 0.7 (tune via density profile)
- early_exit = True (skip Stage 3 if Stage 2 score low)

### Procedure

1. **Baseline run**: Run standard GVA on N, record runtime and candidates
2. **2-stage run**: Simulate PR #92 approach, verify ~9s runtime
3. **Density profiling**: Run instrumentation, capture density_profile.json
4. **Threshold tuning**: Analyze density profile, set dynamic thresholds
5. **3-stage run**: Execute deeper recursion with tuned parameters
6. **Analysis**: Compare all methods on runtime, candidates, coverage
7. **Verdict**: Support or falsify hypothesis based on criteria

## Methodology Notes

### Precision and Determinism

- Adaptive precision: `max(50, N.bit_length() × 4 + 200)` decimal places
  - For 110-bit N: max(50, 110 × 4 + 200) = 640 dps
- Fixed seeds for QMC sampling (golden ratio deterministic)
- Reproducible test case (known p, q for verification)

### Fair Comparison

- All methods use same precision settings
- All use same geodesic distance computation (from gva_factorization.py)
- All use same candidate validation (divisibility test)
- All run on identical hardware/environment
- Timeout: 60 seconds per method

### Threats to Validity

**Internal validity:**
- Implementation bugs could cause false negatives
  - Mitigation: Test 2-stage against PR #92 numbers first
- Parameter tuning may be suboptimal
  - Mitigation: Use density profiling to guide choices; document sensitivity

**External validity:**
- Single test case (N=110-bit) may not generalize
  - Mitigation: This is a replication of PR #92 baseline; representative of 110+ bit regime
- Balanced semiprimes only (p ≈ q)
  - Mitigation: This is the hardest case; if it works here, promising elsewhere

**Construct validity:**
- "Success" = correct factors with p×q == N verification
- "Runtime" = wall-clock time (includes all Python overhead)
- "Speedup" = baseline_time / method_time (> 1.0 is improvement)

## Barriers and Limitations

### What This Experiment Can Test

✓ Whether 3-stage recursion reduces runtime below baseline on 110-bit case  
✓ Whether dynamic thresholds improve over fixed 2-stage approach  
✓ Whether incremental evaluation reduces overhead  
✓ Quantitative comparison of candidates tested across methods

### What This Experiment Cannot Test

✗ Performance on 127-bit CHALLENGE_127 (outside operational range, too slow)  
✗ Full operational range [10^14, 10^18] (time-limited; can test spot checks if time permits)  
✗ Alternative stage configurations (4+, different splits)  
✗ Optimal threshold values (can tune for one case, not full grid search)

### Computational Constraints

- Runtime budget per method: 60 seconds
- Total experiment time: ~10 minutes
- Precision overhead: 640 dps for 110-bit case (acceptable)

## Expected Outcomes

**If hypothesis is TRUE (supported):**
- 3-stage runtime < 4.027s (baseline)
- 3-stage runtime < 9.076s (2-stage)
- Factors recovered correctly
- Total candidates < 2-stage candidates
- Demonstrates adaptive pruning benefit

**If hypothesis is FALSE (falsified):**
- 3-stage runtime ≥ baseline (no improvement), OR
- 3-stage runtime ≈ 2-stage (no benefit from depth), OR
- Factors not recovered (correctness failure), OR
- Overhead from 3 stages > benefit from pruning

## Related Work

- **PR #92 analysis**: Established 2-stage baseline and identified overhead problem
- **fractal-recursive-gva-falsification**: Prior experiment in this repo, different approach (Mandelbrot, falsified)
- **unified-framework correlations**: Multi-scale conical flows suggest recursion viability
- **z-sandbox**: Kappa/geodesic foundations for segment scoring
- **Gists (kappa_signal_demo.py, output.txt)**: QMC variance reduction techniques

## Conclusion

This experiment provides a rigorous test of the deeper recursion hypothesis on the exact test case analyzed in PR #92. Results will clearly support or falsify the claim that 3+ stages with dynamic thresholds can beat baseline runtime. See [EXPERIMENT_SUMMARY.md](EXPERIMENT_SUMMARY.md) for findings and verdict.
