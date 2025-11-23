# Geofac Experiments

This directory contains research experiments for the geofac geometric resonance factorization project.

## Current Experiments

### [theil-sen-robust-estimator/](theil-sen-robust-estimator/)

**Status**: Complete - Hypothesis strongly supported

**Objective**: Test whether Theil-Sen median slope estimator provides more robust trend estimates than OLS for parameter optimization when outliers are present.

**Key Finding**: Hypothesis strongly supported. Theil-Sen demonstrates 81.4% average error reduction compared to OLS when outliers are present, with 6× better robustness (MAD metric) on synthetic k-data. Method tolerates up to 29.3% outlier contamination while OLS breaks down with a single bad point. For geofac parameter estimation (k vs ln(N)), Theil-Sen provides stable predictions where OLS fails due to failed search runs or measurement artifacts.

**Critical Insight**: OLS minimizes squared errors, exponentially amplifying outlier influence. Theil-Sen uses median of pairwise slopes, making it immune to extreme values. With negligible computational overhead (< 10ms for n=50) and zero tuning parameters, Theil-Sen should replace OLS as the default estimator in all geofac parameter analysis workflows.

**Start here**: [theil-sen-robust-estimator/INDEX.md](theil-sen-robust-estimator/INDEX.md)

---

### [kernel-order-impact-study/](kernel-order-impact-study/)

**Status**: Complete - Hypothesis decisively falsified

**Objective**: Test whether the Dirichlet kernel order parameter J significantly impacts factorization success, and whether J=6 (current default) is optimal across all semiprime scales.

**Key Finding**: Hypothesis falsified. All J values (3, 6, 9, 12, 15) succeeded on both validation gates (30-bit and 60-bit) with 100% success rate. Kernel order affects computation time (2-4× variation) but not factorization success at these scales. Lower J values (3-9) are faster due to simpler computation. Current default J=6 is adequate.

**Critical Insight**: Threshold (0.92) dominates candidate selection, not kernel sharpness. All J values tested identical candidate counts on 60-bit gate, indicating threshold is the bottleneck. Kernel order is not a critical tuning parameter at validation gate scales.

**Start here**: [kernel-order-impact-study/INDEX.md](kernel-order-impact-study/INDEX.md)

---

### [signed-scaled-adjustments/](signed-scaled-adjustments/)

**Status**: Complete - Hypothesis decisively falsified

**Objective**: Falsify the hypothesis that signed or scaled adjustments to the geometric parameter k in θ'(n,k) can reduce search iterations in Fermat-style factorization of balanced semiprimes.

**Key Finding**: Hypothesis decisively falsified. Positive k-adjustments fail universally (0% success rate, 0/30 trials). Negative k-adjustments appear to succeed but only because the guard clause `a ≥ ceil(√n)` clamps them to the optimal baseline - they provide no actual improvement. For balanced semiprimes (p ≈ q), the optimal starting point is mathematically determined as ceil(√n), and θ'(n,k) provides no useful signal for improving this.

**Critical Insight**: The geometric transformation θ'(n,k) = φ·((n mod φ)/φ)^k is designed for prime-density mapping, not for computing factorization starting points. Its application in Fermat-style iteration is a category error. Negative adjustments "succeed" only by being forced back to the trivial baseline.

**Start here**: [signed-scaled-adjustments/INDEX.md](signed-scaled-adjustments/INDEX.md)

---

### [fractal-recursive-gva-falsification/](fractal-recursive-gva-falsification/)

**Status**: Complete - Hypothesis decisively falsified

**Objective**: Falsify the hypothesis that Fractal-Recursive GVA (Mandelbrot-inspired iterations + recursive subdivision) improves factorization

**Key Finding**: Hypothesis falsified. FR-GVA succeeds only via trial division fallback, not fractal mechanism. Zero fractal candidates find factors. Apparent 88x speedup is artifact of comparing geometric (GVA) vs. classical (trial division) methods.

**Start here**: [fractal-recursive-gva-falsification/INDEX.md](fractal-recursive-gva-falsification/INDEX.md)

---

### [resonance-drift-hypothesis/](resonance-drift-hypothesis/)

**Status**: Complete - Framework ready, hypothesis untestable

**Objective**: Test whether optimal resonance parameter k scales with N or remains constant

**Key Finding**: Cannot be falsified due to lack of empirical k-success data. Current k ∈ [0.25, 0.45] is an unvalidated assumption.

**Start here**: [resonance-drift-hypothesis/INDEX.md](resonance-drift-hypothesis/INDEX.md)

---

### [deeper-recursion-hypothesis/](deeper-recursion-hypothesis/)

**Status**: Complete - Hypothesis decisively falsified

**Objective**: Test whether 3-stage recursion with dynamic thresholds can reduce runtime below baseline on 110-bit semiprimes while maintaining factor recovery

**Key Finding**: Hypothesis falsified. 3-stage achieved 1.19× speedup (3.40s vs 4.07s) but failed to recover factors. Multi-stage uniform segmentation is fundamentally incompatible with ultra-localized geodesic signals - adaptive sampling near √N is a necessity, not an optimization.

**Start here**: [deeper-recursion-hypothesis/INDEX.md](deeper-recursion-hypothesis/INDEX.md)

---

### [z5d-informed-gva/](z5d-informed-gva/)

**Status**: Framework complete - Ready for execution

**Objective**: Attempt to falsify the hypothesis that integrating Z5D Prime Predictor insights (density oracle, wheel filtering, gap rules, variable stepping) into FR-GVA improves factorization performance on the 127-bit challenge.

**Key Components**:
- Z5D prime density simulation (PNT-based with realistic clustering)
- Wheel residue filtering mod 210 (~77% deterministic pruning)
- Window×wheel gap coverage validation
- Z5D-shaped variable δ-stepping
- Comparison framework with 4 ablation experiments

**Hypothesis**: "Fractals × Z5D prior" creates synergy that outperforms either approach alone.

**Falsification Criteria**:
1. Z5D density doesn't change segment selection
2. No correlation between amplitude and density
3. No performance improvement vs. baseline
4. All improvements attributable to wheel filter alone

**Start here**: [z5d-informed-gva/INDEX.md](z5d-informed-gva/INDEX.md)

---

### [z5d-comprehensive-challenge/](z5d-comprehensive-challenge/)

**Status**: Complete - Implementation successful, hypothesis supported (architecture)

**Objective**: Implement comprehensive 6-step plan using Z5D as band/step oracle (not score term) to attempt factorization of 127-bit challenge with systematic calibration and clear failure mode diagnosis.

**Key Finding**: Architecture strongly validated. Z5D as band/step oracle (strategy), 210-wheel as hard filter (pruning), FR-GVA as ranking (scoring) provides clean separation of concerns and precise diagnostics. Calibration successful (ε curve R² > 0.99). However, 127-bit challenge has highly imbalanced factors (δ ~ 10^18 from √N), making it non-representative of balanced semiprimes that Z5D targets.

**Innovation**: First systematic calibration-driven pipeline with complete instrumentation and post-mortem analysis capability. Demonstrated that architectural separation enables precise failure mode diagnosis (band miss vs budget miss vs ranking miss).

**Test Results**: 16/16 tests passing. All 6 steps functional. Production rate: 293 candidates/sec with full instrumentation.

**Start here**: [z5d-comprehensive-challenge/EXPERIMENT_REPORT.md](z5d-comprehensive-challenge/EXPERIMENT_REPORT.md)

---

### [weyl-law-remainder-oscillations/](weyl-law-remainder-oscillations/)

**Status**: (Pre-existing experiment)

---

## Experiment Guidelines

Each experiment should include:
1. **INDEX.md** - Navigation guide and TL;DR
2. **EXPERIMENT_SUMMARY.md** - Complete findings and verdict
3. **README.md** - Design, methodology, and setup
4. **Code artifacts** - Implementation (Java/Python/etc.)
5. **Data files** - Results, logs, or placeholders if infeasible
6. **Theoretical analysis** - When empirical validation is blocked

## Adding New Experiments

```bash
mkdir experiments/your-experiment-name
cd experiments/your-experiment-name
# Create INDEX.md, README.md, etc.
```

Follow the structure established by `resonance-drift-hypothesis/` for consistency.
