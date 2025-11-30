# Parameter Optimization 127-bit Falsification Experiment

## Purpose

This experiment attempts to falsify the hypothesis that specific parameter optimizations will improve 127-bit factorization over the current scale-adaptive defaults.

## Hypothesis Under Test

The hypothesis claims that for 127-bit numbers, the following parameter values will enable reliable factorization within a 30-minute constraint:

```yaml
geofac.samples=50000              # Increased from default
geofac.m.span=0.3                 # Wider m-range
geofac.m.resolution=200           # Moderate resolution
geofac.k.min=2                    # Start low for fundamental harmonics
geofac.k.max=17                   # Cap at prime to avoid harmonic pollution
geofac.threshold=0.15             # Lower threshold to catch weak resonances
geofac.radius=0.02                # Tighter radius for precision
geofac.adaptive.bump=1.5          # Aggressive precision increases
geofac.adaptive.threshold=0.80    # Earlier adaptation trigger
```

### Specific Claims

1. For 127-bit numbers, resonance peaks are narrow and could be anywhere in (m,k) space
2. Wider initial coverage (larger m.span) is needed
3. Lower threshold (0.15 vs default ~0.82) is critical because Dirichlet kernel peaks may be weaker at 127 bits
4. Shell exclusion creates "dead zones" that might eliminate solutions
5. Wider k-range [2, 17] vs current [0.30, 0.40] is needed to find additional resonances

## Target Number

**127-bit Challenge Semiprime (Whitelisted)**:
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863
- √N ≈ 1.17264 × 10¹⁹

## Current Scale-Adaptive Defaults (for 127-bit)

From `ScaleAdaptiveParams.java`, using base values from `application.yml`:

| Parameter | Base (30-bit) | Scaled (127-bit) | Formula |
|-----------|---------------|------------------|---------|
| samples | 2000 | ~30,517 | base × (bitLength/30)^1.5 |
| m-span | 180 | ~762 | base × (bitLength/30) |
| threshold | 0.95 | ~0.82 | base - log₂(bitLength/30) × attenuation |
| k-lo | 0.25 | ~0.30 | center - (baseWidth / √(bitLength/30)) |
| k-hi | 0.45 | ~0.40 | center + (baseWidth / √(bitLength/30)) |
| timeout | 1,200,000ms | ~21,500,000ms (~6h) | base × (bitLength/30)² |

## Proposed Parameters

From the hypothesis:

| Parameter | Value | Notes |
|-----------|-------|-------|
| samples | 50,000 | Fixed, not scaled |
| m-span | 0.3 (interpreted as m-resolution) | Unclear semantics |
| k-min | 2 | Fractional k vs integer |
| k-max | 17 | Fractional k vs integer |
| threshold | 0.15 | Much lower than default |
| radius | 0.02 | Different from search-radius-percentage |
| adaptive.bump | 1.5 | Not a current parameter |
| adaptive.threshold | 0.80 | Unclear mapping |

## Methodology

### Test Matrix

1. **Control**: Current scale-adaptive defaults
2. **Proposed**: Hypothesis parameter set
3. **Ablation 1**: Default + lower threshold only
4. **Ablation 2**: Default + wider k-range only
5. **Ablation 3**: Default + higher samples only

### Measurements

For each configuration:
- Success/failure in finding factors
- Time to factor (if successful)
- Number of candidates tested
- Peak amplitude observed
- Number of candidates passing threshold

### Falsification Criteria

The hypothesis is **FALSIFIED** if ANY of:

1. Proposed parameters do NOT improve success rate over current defaults
2. Proposed parameters do NOT reduce time-to-factor
3. Proposed parameters cause regressions in smaller-scale tests (30-bit, 60-bit)
4. Lower threshold (0.15) causes excessive false positives without finding factors
5. Wider k-range [2, 17] does not find additional resonances vs [0.30, 0.40]

### Success Criteria

The hypothesis is **SUPPORTED** if ALL of:

1. Proposed parameters achieve higher success rate than defaults
2. Time-to-factor is reduced OR equivalent with higher reliability
3. No regressions at smaller scales
4. Lower threshold finds genuine resonances, not just noise

## Quick Start

```bash
# Navigate to experiment directory
cd experiments/parameter-optimization-127bit-falsification

# Run the experiment
python3 run_experiment.py

# View results
cat EXECUTIVE_SUMMARY.md
```

## File Structure

```
experiments/parameter-optimization-127bit-falsification/
├── README.md                      # This file
├── EXECUTIVE_SUMMARY.md           # Clear verdict and key findings
├── EXPERIMENT_REPORT.md           # Detailed analysis
├── run_experiment.py              # Main experiment runner
└── test_parameter_optimization.py # Test and falsification logic
```

## Dependencies

- Python 3.10+
- mpmath (arbitrary precision)
- subprocess (for Java integration)

## Validation Gates

Per project requirements:
- **Gate 3 (127-bit)**: Primary target, whitelisted
- **Gate 1 (30-bit)**: Regression check
- No classical fallbacks allowed

## Precision

- Uses mpmath with explicit `mp.dps`
- Adaptive: max(100, N.bitLength() × 4 + 200) = 708 decimal places for 127-bit
- All precision choices logged

## Reproducibility

- Seeds pinned where applicable
- All parameters logged
- Results exported to JSON/Markdown

---

**Status**: Ready for execution
**Last Updated**: 2025-11-28
**Experiment**: parameter-optimization-127bit-falsification
