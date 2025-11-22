# GVA Curvature Falsification — Experiment Design

## Overview

This experiment tests whether curvature metrics (second-order differences of amplitude or phase) reveal geometric structure in GVA embeddings that raw amplitude misses at distant-factor scales.

**Hypothesis:** Curvature (local Hessian, second differences) of the GVA amplitude or phase surface provides usable gradient information for factor localization when raw amplitude is flat.

**Falsification Criteria:**
1. Curvature surface shows same flatness as raw amplitude (variations < 1e-6)
2. No correlation between curvature magnitude and factor locations
3. Signal-to-noise ratio insufficient for discrimination
4. Peak curvature locations are uniformly distributed (no clustering near factors)

## Target

- **N₁₂₇** = 137524771864208156028430259349934309717
- **Expected factors:**
  - p = 10,508,623,501,177,419,659
  - q = 13,086,849,276,577,416,863
- **Shell S₅:** R₅ = 867,036,556,394,714,496 < |δ| ≤ 1,402,894,617,735,313,152 = R₆
- **Both factors confirmed in S₅** (from shell-geometry-scan-01)

## Method

### Fixed Parameters (from shell-geometry-scan-01)
- **Shell:** S₅ only (where factors are known to reside)
- **N:** CHALLENGE_127 (fixed, no other test cases)
- **δ-band:** [R₅, R₆] as defined by golden-ratio shell spacing
- **k values:** [0.30, 0.35, 0.40] (GVA kernel parameters)
- **Precision:** 800 dps

### Changed Signal: Curvature Instead of Amplitude

#### Amplitude (baseline from previous experiment):
```python
dist = riemannian_distance(N_coords, candidate_coords)
amplitude = 1.0 / (1.0 + dist)
```

#### Curvature (this experiment):
For each candidate c, sample at {c-h, c, c+h} with step h:
```python
A_minus = amplitude(c - h)
A_center = amplitude(c)
A_plus = amplitude(c + h)

# Second-order central difference (discrete Laplacian)
curvature = (A_plus - 2*A_center + A_minus) / h²
```

**Note:** Phase curvature was considered but not implemented since amplitude curvature alone is sufficient to test the hypothesis. If amplitude curvature is flat, phase curvature would provide no additional signal.

### Sampling Strategy

Use adaptive stride to sample ~10,000 points uniformly across S₅:
- Shell width: R₆ - R₅ ≈ 5.36 × 10¹⁴
- Sample stride: ~5.36 × 10¹⁰ (to get ~10k samples)
- For each sample point, compute curvature with h = stride / 10

### Metrics Tracked

Per k-value:
- `curvature_min`, `curvature_max`, `curvature_mean`, `curvature_std`
- `curvature_range` = max - min
- `samples_collected`
- `peak_locations` (top 100 curvature magnitudes)
- `factor_distances` (distance from each peak to nearest factor)

Per shell (S₅ only):
- `max_curvature_overall`
- `curvature_distribution` (histogram)
- `spatial_clustering` (do peaks cluster near factors?)

## Success Criteria

### Clear falsification (proves hypothesis wrong):
1. Curvature range < 1e-6 (effectively flat like amplitude)
2. Curvature peaks uniformly distributed (no clustering at factors)
3. No correlation between |curvature| and distance to factors

### Partial falsification:
1. Curvature shows more structure than amplitude BUT
2. Signal-to-noise insufficient for practical use (range < 1e-4)

### Hypothesis confirmed (would require):
1. Curvature range ≥ 1e-3 (meaningful variation)
2. Strong spatial clustering of high-curvature regions near factors
3. Monotonic or at least directional gradient toward factors

## Implementation Notes

- Reuses GVA embedding functions from `gva_factorization.py`
- Minimal new code: just curvature computation wrapper
- Deterministic: fixed seeds, explicit precision
- Single shell (S₅), single N, fixed budget
- Reproducible: logs exact stride, h, all parameters

## References

- Previous experiment: `../shell-geometry-scan-01/`
- PR #103 findings: Amplitude flat 0.997-0.999, no gradient
- Base GVA: `/home/runner/work/geofac/geofac/gva_factorization.py`
