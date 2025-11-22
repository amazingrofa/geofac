# Signed or Scaled Adjustments Experiment

**Navigation**: [INDEX.md](INDEX.md) | [README.md](README.md) | [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md) | [experiment.py](experiment.py) | [results.json](results.json)

---

## TL;DR

**Status**: Complete - Hypothesis DECISIVELY FALSIFIED

**Hypothesis**: Signed or scaled adjustments to the geometric parameter k in θ′(n,k) = φ·((n mod φ)/φ)^k can reduce search iterations in Fermat-style factorization of balanced semiprimes.

**Verdict**: **FALSIFIED**. The hypothesis fails for balanced semiprimes (p ≈ q) where ceil(√n) is already optimal. Positive k-adjustments universally fail (100% failure rate, 0/10 successes across all scales tested). Negative k-adjustments appear to succeed (10/10 successes) but only because the guard clause `a ≥ ceil(√n)` clamps them back to the optimal starting point - they provide no actual improvement over the control (all strategies that reach the optimal point achieve 0 iterations).

**Key Finding**: For balanced semiprimes, θ′(n,k) with k=0.3 produces positive shifts (~1-2 units) that move the starting point AWAY from the optimal ceil(√n), guaranteeing failure. Negative adjustments are corrective only in the sense that they trigger the guard clause; the geometric formula itself provides no useful information for this class of semiprime.

**Critical Insight**: The result validates the original simulation's observation that k=0.3 overshoots, but invalidates the hypothesis that signed/scaled corrections help. The fundamental issue is that θ′(n,k) is designed for prime-density mapping, not for directly computing factorization starting points. For balanced semiprimes, no adjustment strategy outperforms the trivial baseline: start at ceil(√n).

---

## Quick Start

```bash
# Run experiment
python experiment.py

# View results
cat results.json
```

---

## Experiment Structure

1. **[INDEX.md](INDEX.md)** - This file (navigation and TL;DR)
2. **[README.md](README.md)** - Experiment design, methodology, and setup
3. **[EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md)** - Complete findings, analysis, and verdict
4. **[experiment.py](experiment.py)** - Implementation code
5. **[results.json](results.json)** - Raw experimental data

---

## Summary Statistics

### Test Configuration
- **Semiprimes**: 10 balanced semiprimes in [10^14, 10^18]
- **Precision**: mpmath 50 decimal places (target < 1e-16)
- **Seed**: 42 (reproducible)
- **Max iterations**: 100,000 per test

### Strategy Performance

| Strategy | Success Rate | Avg Iterations (All) | Avg Iterations (Successful) |
|----------|--------------|---------------------|----------------------------|
| Control (no adjustment) | 10/10 (100%) | 0.0 | 0.0 |
| Positive k=0.3 (original) | 0/10 (0%) | 100,000.0 | N/A |
| Negative k=0.3 (corrective) | 10/10 (100%) | 0.0 | 0.0 |
| Scaled positive k=0.3×0.1 | 0/10 (0%) | 100,000.0 | N/A |
| Scaled negative k=0.3×0.1 | 10/10 (100%) | 0.0 | 0.0 |
| Scaled positive k=0.3×0.5 | 0/10 (0%) | 100,000.0 | N/A |
| Scaled negative k=0.3×0.5 | 10/10 (100%) | 0.0 | 0.0 |

### Interpretation

- **Positive adjustments**: 100% failure rate regardless of scale (0.1×, 0.5×, 1.0×)
- **Negative adjustments**: 100% success rate at 0 iterations (identical to control)
- **Control group**: Optimal baseline performance (0 iterations)

The negative adjustments succeed not because they improve the search, but because the implementation correctly guards against invalid starting points by clamping `a ≥ ceil(√n)`. This guard effectively converts all negative adjustments into the control strategy.

---

## Falsification Criteria (All Met)

1. ✅ **Positive k-adjustments fail universally**: 0/30 successes across three scale factors
2. ✅ **Negative k-adjustments provide no improvement**: 0 iterations achieved identically to control (no benefit)
3. ✅ **Scaled adjustments show no benefit**: All scales (0.1×, 0.5×, 1.0×) either fail completely or match control
4. ✅ **No consistent improvement pattern**: Only strategies that reach ceil(√n) succeed; geometric adjustment is irrelevant

---

## Implications

### For Balanced Semiprimes (p ≈ q)
- Starting point ceil(√n) is mathematically optimal
- θ′(n,k) provides no useful adjustment signal for this class
- Any strategy that deviates from ceil(√n) will fail

### For Imbalanced Semiprimes (p << q)
- Not tested in this experiment (would require δ >> 1000)
- θ′(n,k) may have different behavior (UNVERIFIED)
- Separate experiment required for imbalanced case

### For GVA/Geometric Resonance Factorization
- This experiment tests Fermat-style iteration, not geometric resonance
- θ′(n,k) may still be useful for geodesic/phase-based methods
- The role of k in GVA's amplitude detection is distinct from Fermat starting points

---

## Related Experiments

- **[z5d-comprehensive-challenge/](../z5d-comprehensive-challenge/)** - Z5D as band/step oracle for 127-bit challenge
- **[deeper-recursion-hypothesis/](../deeper-recursion-hypothesis/)** - Multi-stage recursion falsification
- **[resonance-drift-hypothesis/](../resonance-drift-hypothesis/)** - k-drift untestable (no empirical data)

---

## Citation

```bibtex
@experiment{geofac-signed-scaled-adjustments-2024,
  title={Signed or Scaled Adjustments to Geometric Parameter k: A Falsification Study},
  author={Geofac Experiment Framework},
  year={2024},
  institution={geofac},
  note={Decisively falsified for balanced semiprimes},
  url={https://github.com/zfifteen/geofac/tree/main/experiments/signed-scaled-adjustments}
}
```

---

**Experiment Date**: 2024-11-22  
**Status**: Complete  
**Verdict**: Hypothesis Decisively Falsified
