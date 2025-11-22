# Theoretical Analysis: Deeper Recursion Hypothesis

## Overview

This document provides the theoretical framework for understanding when and why deeper multi-stage recursion might reduce factorization runtime compared to single-pass or shallow (2-stage) approaches.

## Theoretical Foundations

### Geodesic Density and Fractal Structure

**Observation from PR #92**: The 2-stage approach successfully recovered factors with 50% coverage, indicating that factor-bearing regions exhibit higher geodesic density in the 7D torus embedding.

**Mathematical basis**:
- Geodesic distance d(n, √N) on 7D torus measures "closeness" to factors
- Density function ρ(region) = average geodesic score over candidates
- High-density regions cluster near factors (empirically validated)

**Fractal hypothesis**: If density distribution is self-similar across scales, recursive subdivision should maintain signal-to-noise ratio at each stage.

### Multi-Stage Recursion: Complexity Analysis

Let:
- N = semiprime to factor
- W = search window size
- S_i = number of segments at stage i
- K_i = top-K segments selected at stage i
- C_i = candidates sampled per segment at stage i

#### Single-Pass (Baseline)
- Samples: C_total = C_1 × W
- Runtime: O(C_total × t_geodesic + C_total × t_divisibility)

#### 2-Stage
- Stage 1: C_1 × S_1 candidates (coarse scoring)
- Stage 2: C_2 × (W/S_1) × K_1 candidates (fine search in top-K)
- Total: C_1 × S_1 + C_2 × (W/S_1) × K_1
- Runtime: O((C_1 × S_1) × t_geodesic + (C_2 × K_1 × W/S_1) × (t_geodesic + t_divisibility))

**Key issue**: Stage 1 overhead (C_1 × S_1) can dominate if not amortized.

#### 3-Stage with Dynamic Thresholds
- Stage 1: C_1 × S_1 candidates (very coarse, S_1 small)
- Stage 2: C_2 × S_2 × K_1 candidates (medium, in top-K_1 from Stage 1)
- Stage 3: C_3 × (W/(S_1×S_2)) × K_1 × K_2 candidates (fine, in top regions)
- Total: C_1 × S_1 + C_2 × S_2 × K_1 + C_3 × K_1 × K_2 × (W/(S_1×S_2))

**Optimization opportunity**: 
- Make S_1 small (8 vs 32) → reduce Stage 1 overhead
- Use dynamic threshold at Stage 2 → early exit if unpromising
- Only Stage 3 does full geodesic+divisibility tests

**Conditions for speedup**:
```
C_1×S_1 + C_2×S_2×K_1 + C_3×K_1×K_2×(W/(S_1×S_2)) < C_baseline

AND

(early exits reduce effective K_1, K_2 in practice)
```

### Dynamic Threshold Tuning

**Motivation**: Fixed thresholds may over-explore low-density regions.

**Approach**:
1. Profile density distribution from initial runs (baseline or 2-stage)
2. Set threshold τ_i at stage i such that P(density > τ_i | factor_present) ≈ target coverage
3. Early exit: if max(density_stage2) < τ_2, skip Stage 3 entirely

**Expected benefit**:
- Reduce false positives in Stage 2 → fewer Stage 3 invocations
- Concentrate computation on high-signal regions
- Trade coverage for speed (acceptable if factor recovery maintained)

### Incremental Evaluation Strategy

**Lazy computation**: Don't compute Stage i+1 unless Stage i passes threshold.

**Algorithm sketch**:
```
def recursive_gva(N, stage=1, max_stage=3):
    if stage > max_stage:
        return baseline_gva(N)  # fallback
    
    segments = score_segments(N, granularity=stage)
    top_segments = select_top_k(segments, k=K[stage])
    
    if stage < max_stage:
        max_density = max(seg.density for seg in top_segments)
        if max_density < threshold[stage]:
            return None  # early exit, no factor in this branch
    
    for seg in top_segments:
        if stage == max_stage:
            factors = fine_search(seg)  # full geodesic + divisibility
            if factors:
                return factors
        else:
            factors = recursive_gva(seg.range, stage+1, max_stage)
            if factors:
                return factors
    
    return None
```

**Theoretical gain**: 
- Prune exponentially: If P(pass_threshold) = p, expected branches explored = p^(max_stage-1)
- For p = 0.5 (50% at each stage), 3 stages explore ~0.25 of search space vs 0.5 for 2 stages

### Z-Framework Correlations

**Unified-framework insights**:
- Conical flows (dh/dt = -k) show 93× speedups via multi-scale geometry
- 15-20% density boosts from geodesic mapping align with 50% coverage success in PR #92
- Self-similar structures support recursive exploitation

**Z-sandbox kappa foundations**:
- κ(n) signal provides segment scoring mechanism
- Batch κ computation with QMC variance reduction (from kappa_signal_demo.py)
- Multi-scale Z5D reaches 10^18 with <1 ppm error → recursion is scale-appropriate

**Gists QMC methods**:
- Sobol sampling on N=899 (output.txt) demonstrates low-discrepancy benefit
- Variance reduction techniques applicable to segment scoring (reduce C_1, C_2)

## Predictions

### Quantitative Predictions for 110-bit N=1296000000000003744000000000001183

**Baseline**: 4.027s, 1403 samples, 1115 tested
**2-stage**: 9.076s, 1600 + 1149 = 2749 samples

**3-stage predictions** (with optimized parameters):

**Pessimistic scenario** (no benefit):
- Runtime: ≥9s (no improvement over 2-stage)
- Overhead from 3 stages overwhelms pruning benefit
- Hypothesis FALSIFIED

**Optimistic scenario** (hypothesis supported):
- Runtime: 3.0-3.5s (< baseline)
- Stage 1: 400 samples (8 segments × 50 samples each)
- Stage 2: 800 samples (4 top segments × 4 sub-segments × 50 samples)
- Stage 3: ~600 samples (early exit reduces invocations)
- Total: ~1800 samples (< 2749 for 2-stage, < 2518 for baseline effective)
- Coverage: ~25% (50% × 50% = 25%, vs 50% for 2-stage)
- Hypothesis SUPPORTED if factors still recovered

**Realistic scenario** (marginal benefit):
- Runtime: 4.5-5.5s (between baseline and 2-stage)
- Partial pruning benefit, but setup overhead still significant
- Hypothesis FALSIFIED (no improvement over baseline)

### Conditions Favoring Deeper Recursion

**Favorable**:
- High self-similarity in density distribution (fractal structure validated)
- Large search windows (W >> S_1 × S_2, amortizes overhead)
- Accurate density estimators (low noise in segment scoring)
- Effective early exit (high true negative rate)

**Unfavorable**:
- Uniform density distribution (no signal for pruning)
- Small search windows (overhead not amortized)
- Noisy density estimates (false negatives skip factors)
- Many false positives (early exit rarely triggered)

### Sensitivity Analysis

**Key parameters to test**:
1. **S_1 (stage 1 segments)**: 4, 8, 16 (hypothesis uses 8)
2. **Threshold τ_2**: 0.5, 0.7, 0.9 (hypothesis uses 0.7)
3. **K_1, K_2 (top-K at each stage)**: 50%, 33%, 25%

**Expected sensitivities**:
- S_1 too large → Stage 1 overhead kills speedup (2-stage problem)
- S_1 too small → coarse scoring misses factors (false negatives)
- τ_2 too high → false negatives (miss factors)
- τ_2 too low → false positives (no early exit benefit)

## Falsifiability

This hypothesis is **highly falsifiable**:

1. **Clear runtime threshold**: If 3-stage ≥ baseline, hypothesis rejected
2. **Measurable metrics**: Runtime, candidates tested, coverage (objective)
3. **Reproducible test case**: N=110-bit with known factors
4. **Comparison baseline**: 2-stage and baseline both measured on same hardware

**No escape hatches**:
- Can't blame hardware (all methods on same system)
- Can't blame parameters (document and tune systematically)
- Can't blame test case (same as PR #92 validation)

## Theoretical Verdict (Pre-Experiment)

**Prior probability assessment**:

**Against hypothesis (falsification likely)**:
- PR #92 already showed overhead dominates for 2-stage
- Adding another stage adds more overhead
- 110-bit case may not have enough scale for amortization
- Empirical baseline (4.027s) is already quite fast

**For hypothesis (support possible)**:
- Smaller S_1 (8 vs 32) could reduce overhead significantly
- Dynamic thresholds + early exit could prune aggressively
- If density truly fractal, signal should persist at Stage 3
- QMC variance reduction might make small S_1 viable

**Estimated outcome**: 40% chance hypothesis supported, 60% chance falsified.

**Reasoning**: The 2-stage overhead problem is real, and adding depth without addressing root cause (upfront coarse sweep cost) is risky. However, the proposed mitigations (small S_1, dynamic thresholds, early exit) are theoretically sound and might just work.

## Next Steps

1. Implement prototypes and measure empirically
2. If hypothesis falsified, investigate why (profiling data)
3. If hypothesis supported, identify key parameters and scaling limits
4. Document findings precisely for future work
