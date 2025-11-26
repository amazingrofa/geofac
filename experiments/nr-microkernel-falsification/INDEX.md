# NR Microkernel Falsification Experiment

**Status**: Complete - Hypothesis decisively falsified

## TL;DR

**Hypothesis**: Embedding a Newton-Raphson (NR) microkernel inside QMC iterations improves peak detection by locally refining promising candidates on-the-fly.

**Result**: **FALSIFIED**. NR microkernel adds 60-113% runtime overhead while achieving only 2.2% improvement rate across 91 triggered refinements. The cost-benefit ratio is unacceptable.

## Key Findings

| Metric | NR(1) - 1 step | NR(2) - 2 steps |
|--------|----------------|-----------------|
| Runtime overhead | 60.5% | 113.4% |
| Score lift | 1.73% | 1.73% |
| Improvement rate | 2.2% | 2.2% |
| Success rate | 4/4 | 4/4 |

## Why It Failed

1. **Discrete nature of factor search**: NR is designed for continuous optimization. Factor candidates are integers, and the geodesic distance landscape is highly discontinuous in integer space.

2. **Flat local geometry**: The Riemannian distance function has nearly flat gradients near minima, causing NR updates to be negligible or unstable.

3. **Overhead dominates**: Each NR step requires 3 additional embedding+distance computations, multiplying per-candidate cost significantly.

4. **No geometric correlation**: NR refinement assumes the objective function has smooth, exploitable curvature. The geodesic distance metric lacks this structure near integer factors.

## Files

- `README.md` - Experiment design and hypothesis
- `EXPERIMENT_REPORT.md` - Full results and verdict
- `nr_microkernel_gva.py` - GVA with NR microkernel
- `experiment_runner.py` - A/B comparison framework
- `results.json` - Raw experiment data

## Reproducibility

```bash
cd experiments/nr-microkernel-falsification
python3 experiment_runner.py
```

## Related Experiments

- [fractal-recursive-gva-falsification](../fractal-recursive-gva-falsification/) - FR-GVA falsification
- [deeper-recursion-hypothesis](../deeper-recursion-hypothesis/) - 3-stage recursion falsification
