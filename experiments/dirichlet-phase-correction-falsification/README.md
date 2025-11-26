# Dirichlet Phase Correction Falsification — Experiment Design

## Overview

This experiment tests whether the Dirichlet-kernel phase correction is blocking resonance lock in Gate 2 attempts. The hypothesis is that systematic curvature in the residual phase indicates geometric asymmetry that can be corrected with a global phase shift.

**Hypothesis:** The residual phase Δφ = φ_meas - φ_pred shows systematic curvature (convex/concave drift) that can be reduced by applying a global phase shift φ_shift = α × ln(N)/e².

**Falsification Criteria:**
1. Δφ(m/N) shows no systematic curvature (looks like noise around 0) → current correction is fine
2. Curvature exists but phase correction does not reduce it by ≥5× → hypothesis is false
3. Residual RMS does not drop by ≥2× after correction → hypothesis is false

## Target

- **Gate 2:** N = 1,152,921,470,247,108,503 (60-bit semiprime)
- **Expected factors:**
  - p = 1,073,741,789
  - q = 1,073,741,827
- **sqrt(N) ≈** 1,073,741,808

## Method

### Phase Measurement via 7D Torus Embedding

Following GVA methodology from `gva_factorization.py`:

1. **Embed N** in 7D torus using golden ratio:
   ```python
   phi = (1 + sqrt(5)) / 2
   for d in 0..6:
       coord[d] = frac(n * phi^(d+1))
   ```

2. **For each candidate m** around √N:
   - Compute torus embedding coordinates
   - Measure "phase" from geodesic structure in embedding

3. **Compute residual phase:**
   ```python
   dphi = wrap_to_pi(phi_meas - phi_pred)
   ```
   where `wrap_to_pi(a) = (a + π) % (2π) - π`

### Phase Correction Model

The hypothesis proposes that geometric asymmetry introduces systematic phase drift:

```python
phi_shift = alpha * math.log(N) / (math.e ** 2)
dphi_corrected = wrap_to_pi((phi_meas + phi_shift) - phi_pred)
```

### Metrics

1. **Curvature coefficient (a):** Fit Δφ(x) ≈ ax² + bx + c where x = m/N
2. **Baseline curvature:** |a| before correction
3. **Optimal α*:** Value in [-0.5, 0.5] that minimizes |a|
4. **Corrected curvature:** |a*| after applying optimal phase shift
5. **Residual RMS:** sqrt(mean(Δφ²)) before and after correction

### Sampling Strategy

- Sample window: ±1000 candidates around √N
- Normalized index: x = m/N
- Total samples: 2001 (or as determined by step size)

## Success Criteria

### Clear falsification (proves hypothesis wrong):
1. Baseline curvature is negligible (|a| < 1e-6)
2. Phase shift provides no meaningful improvement (|a| reduction < 5×)
3. RMS reduction < 2×, confirming no systematic drift

### Partial falsification:
1. Curvature exists but is not correctable with proposed shift formula
2. Optimal α* is outside reasonable range
3. Correction improves fit but not enough to be useful

### Hypothesis confirmed (would require):
1. Clear baseline curvature (|a| > 1e-4)
2. |a| reduction ≥ 5× after correction
3. RMS reduction ≥ 2× after correction
4. Optimal α* in [-0.5, 0.5] range

### Extended Search

If initial sweep fails to find improvement:
- Expand α range to [-2, 2]
- If still no improvement, hypothesis is definitively falsified

## Implementation Notes

- Reuses GVA embedding functions from `gva_factorization.py`
- Precision: max(50, N.bitLength() × 4 + 200) = max(50, 60×4+200) = 440 dps
- Fixed seed for reproducibility
- All parameters logged with timestamps
- Outputs to results.json for automated analysis

## Validation Gate Compliance

- **Gate:** Gate 2 (60-bit)
- **N:** 1152921470247108503
- **Known factors:** p = 1073741789, q = 1073741827
- **Precision:** Adaptive, minimum 440 dps
- **Method:** Pure geometric measurement, no classical fallbacks

## References

- Previous experiment: [../gva-curvature-falsification/](../gva-curvature-falsification/)
- Base GVA: [/home/runner/work/geofac/geofac/gva_factorization.py](../../gva_factorization.py)
- Validation Gates: [docs/VALIDATION_GATES.md](../../docs/VALIDATION_GATES.md)
