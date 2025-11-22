# Deeper Recursion Hypothesis - Experiment Index

**Status**: In Progress

**Objective**: Attempt to falsify the hypothesis that extending fractal-recursive geodesic search to 3+ stages with dynamic thresholds can reduce runtime below baseline on 110+ bit semiprimes.

**TL;DR**: Testing whether deeper multi-stage recursion (3+ stages vs 2 stages) with dynamic threshold tuning can overcome the 2.3× runtime overhead observed in the 2-stage prototype from PR #92 analysis.

## Quick Navigation

- **[README.md](README.md)** - Experiment design, methodology, test corpus
- **[EXPERIMENT_SUMMARY.md](EXPERIMENT_SUMMARY.md)** - Complete findings and verdict (generated after execution)
- **[THEORETICAL_ANALYSIS.md](THEORETICAL_ANALYSIS.md)** - Theoretical framework and predictions
- **Artifacts**:
  - `baseline_gva.py` - Standard GVA implementation (control)
  - `two_stage_prototype.py` - 2-stage coarse-to-fine (PR #92 simulation)
  - `three_stage_prototype.py` - 3-stage recursive with dynamic thresholds
  - `instrument_density.py` - Density profiling and instrumentation
  - `density_profile.json` - Captured density data from runs
  - `comparison_experiment.py` - Main experimental driver
  - `RESULTS.md` - Detailed experimental results

## Background

### PR #92 Context (Referenced in Problem Statement)

**Hypothesis Tested**: 2-stage coarse-to-fine search reduces window coverage while recovering factors via geodesic-driven pruning.

**Baseline Performance** (110-bit N=1296000000000003744000000000001183):
- Factors: 36000000000000013 × 36000000000000091 (gap=78)
- Runtime: 4.027s
- Sampling: 1403 sampled, 1115 tested candidates
- Coverage: 100%
- Geodesic distance: 0.000905

**2-Stage Results**:
- Same factors recovered ✓
- Coverage: 50% (16/32 segments)
- Runtime: 9.076s (2.3× slower ✗)
- Sampling: 1600 samples in Stage 1, 1149 tested in Stage 2
- Conclusion: Fractal structure exploitable, but coarse sweep overhead dominates

**Implication**: Adaptive/streaming or incremental evaluation needed to avoid upfront overhead.

### Supported Hypothesis

Correlations from unified-framework (multi-scale conical flows), z-sandbox (kappa/geodesic foundations), and gists (QMC variance reduction) suggest:
- Extending to **3+ stages** with **dynamic thresholds** (tuned via density profiles)
- Incremental evaluation (only compute next stage when needed)
- Could reduce runtime **below baseline** on 110+ bits by:
  1. Avoiding full coarse sweep upfront
  2. Adaptively focusing on high-density regions
  3. Pruning recursively with tighter bounds

## Experiment Goals

1. **Falsify or support** the deeper recursion hypothesis through empirical testing
2. **Quantify** whether 3-stage recursive approach improves on 2-stage overhead
3. **Identify** optimal threshold tuning strategy via density profiling
4. **Document** precise conditions under which deeper recursion helps vs. hurts

## Success Criteria

**Hypothesis is SUPPORTED if**:
- 3-stage approach achieves runtime < baseline (< 4.027s)
- Maintains factor recovery (100% success rate on test corpus)
- Shows measurable reduction in total candidates tested vs. 2-stage

**Hypothesis is FALSIFIED if**:
- 3-stage runtime ≥ 2-stage runtime (no improvement)
- OR runtime ≥ baseline (defeats purpose)
- OR factors not recovered (correctness failure)

## Related Work

- **fractal-recursive-gva-falsification**: Tested Mandelbrot-inspired fractal integration (falsified - no benefit from fractal candidates)
- **resonance-drift-hypothesis**: Framework for testing parameter scaling (untestable without empirical k-success data)
- **PR #92 analysis**: Established 2-stage baseline and identified overhead problem

## Next Steps

1. Implement prototypes (baseline, 2-stage, 3-stage)
2. Run experiments on 110-bit test case
3. Profile density and tune dynamic thresholds
4. Document findings in EXPERIMENT_SUMMARY.md
