# Newton-Raphson Microkernel Falsification Experiment

**Status**: In Progress

**Date**: 2025-11-25

## Objective

Attempt to falsify the hypothesis that embedding a Newton-Raphson (NR) microkernel directly inside each QMC iteration improves resonance scan peak detection by locally refining promising peaks on-the-fly, instead of in a separate post-phase.

## Hypothesis (to falsify)

The hypothesis claims:
1. **Peak sharpening**: NR refinement during QMC sampling produces fewer ties and cleaner best-of lists
2. **Stability**: Less flip-flop across neighboring tiles/windows  
3. **Less post-processing**: Many "nearly there" peaks self-correct in-loop
4. **Speed/convergence tradeoff**: Small speed cost for smoother convergence and fewer false highs

## Falsification Criteria

The hypothesis is considered **falsified** if:
1. NR refinement shows no statistically significant improvement in top-N score lift
2. Rank stability does not improve (or worsens)
3. Hit rate does not increase (or false positive rate increases)
4. Runtime penalty exceeds claimed "little speed" cost (>15% overhead)
5. At least 2/3 of test cases show no benefit

The hypothesis is considered **supported** if:
1. Measurable peak sharpening observed
2. Rank stability improves across windows
3. Hit/false-positive ratio improves
4. Runtime overhead is modest (<15%)

## Experiment Design

### Algorithm Integration

Per the hypothesis, the NR microkernel is integrated into the GVA geodesic scoring loop:

```python
# After computing score S at sampled (k, candidate):
if do_nr and S >= nr_trigger:
    x = candidate  # or k, depending on objective
    for i in range(nr_steps):
        f = objective(x)      # phase-error or amplitude residual
        fp = objective_deriv(x)
        if abs(fp) < epsilon:
            break
        nx = x - f / fp
        if nx < k_min or nx > k_max:
            break
        x = nx
    Sn = score(x)
    if Sn > S:
        candidate = x
        S = Sn
```

### Parameters (per hypothesis defaults)

- **Trigger**: Top 5% per tile OR S ≥ μ + 1.5σ
- **NR steps**: 1 by default, allow 2 for best candidates
- **Tolerance**: Stop early if relative improvement < 1e-6
- **Budget**: Cap refines per batch (top 64 samples)

### Test Cases

1. Gate 1 (30-bit): Quick sanity check
2. Gate 2 (60-bit): Scaling validation
3. Operational range samples: 50-bit, 64-bit

### Metrics

For each test case, compare QMC-only vs QMC+NR(1) vs QMC+NR(2):

- **Score lift**: Top-N score improvement
- **Rank stability**: Correlation of rankings across seeds
- **Hit rate**: Factor found within budget
- **Runtime**: Total time and NR overhead

## Key Constraints

1. **No classical fallbacks**: Pure geometric resonance only
2. **Deterministic**: Fixed seeds, fixed NR step budget
3. **Same precision path**: NR uses same high-precision as main score
4. **Guardrails**: Safety stops if |f'| < ε or update escapes scan band

## Files

- `README.md` - This file
- `nr_microkernel_gva.py` - GVA with NR microkernel integration
- `experiment_runner.py` - A/B comparison framework
- `EXPERIMENT_REPORT.md` - Final findings and verdict
