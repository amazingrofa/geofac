# Geofac Experiments

This directory contains research experiments for the geofac geometric resonance factorization project.

## Current Experiments

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

### [shell-geometry-scan-01/](shell-geometry-scan-01/)

**Status**: Complete - Hypothesis partially confirmed, method limitation exposed

**Objective**: Test whether geometric resonance with golden-ratio shell scanning can locate distant factors in the 127-bit challenge semiprime.

**Key Finding**: φ-shells correctly identified S₅ as factor-containing shell (geometry works), but GVA amplitude is flat (0.997-0.999) with no usable gradient. Proves GVA unsuitable for factors >10% from √N.

**Start here**: [shell-geometry-scan-01/INDEX.md](shell-geometry-scan-01/INDEX.md)

---

### [gva-curvature-falsification/](gva-curvature-falsification/)

**Status**: Complete - Hypothesis decisively falsified

**Objective**: Test whether curvature (second-order differences) of GVA amplitude reveals geometric structure for distant-factor localization where raw amplitude is flat.

**Key Finding**: Hypothesis decisively falsified. Curvature is numerical noise (~10⁻²⁶), peak locations are 1,340× farther from factors than random, no spatial clustering. Proves GVA kernel family encodes no distant-factor structure at any derivative order.

**Implication**: Hard boundary established: GVA only admissible for local band near √N. Method should detect distant-factor condition and exit early rather than burning budget.

**Start here**: [gva-curvature-falsification/INDEX.md](gva-curvature-falsification/INDEX.md)

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
