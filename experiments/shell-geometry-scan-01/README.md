# Shell Geometry Scan 01 — Distant-Factor Probe for N₁₂₇

## Overview

This experiment tests whether geometric resonance with golden-ratio shell scanning can locate distant factors in the 127-bit challenge semiprime.

**Hypothesis:** By systematically exploring shells at increasing distances from sqrt(N), using fractal segment scoring for guidance, we can detect geometric signals that indicate factor locations even when factors are far from the "friendly" inner band.

## Target

- **N₁₂₇** = 137524771864208156028430259349934309717
- **Expected factors:**
  - p = 10508623501177419659
  - q = 13086849276577416863

## Method

### 1. Shell Structure

Define shells in δ (offset from sqrt(N)) with golden-ratio spacing:

- **R₀** = 78,180,637,518,849,229 (current "friendly" inner radius)
- **R_{j+1}** = φ·R_j where φ ≈ 1.618 (golden ratio)
- **Shell S_j** = {δ : R_j < |δ| ≤ R_{j+1}}

### 2. Budget & Schedule

- **Global budget:** B_total = 700,000 candidates
- **Per-shell budget:** B_shell ≈ 56,000 candidates (~8% of total)
- **Shell limit:** J_max = 5 (S₀ through S₄)

### 3. Per-Shell Procedure

For each shell S_j:

1. **Segment shell** into M=32 segments in δ space
2. **Score segments** using Mandelbrot fractal metric
3. **Select segments:**
   - K_fractal = 6 highest-scored segments
   - K_uniform = 2 uniformly spaced segments
   - Total: K = 8 segments per shell
4. **GVA sweep** each selected segment:
   - k ∈ {0.30, 0.35, 0.40}
   - Precision = 800 dps
   - Hard stop at B_shell budget

### 4. Metrics Tracked

Per shell:
- shell_index
- R_j, R_{j+1}
- segments_scored, segments_selected
- candidate_budget_used
- max_amplitude_overall
- max_amplitude_per_segment (top 5)
- num_candidates_per_segment
- near_hits (high-amplitude candidates)
- hit_found, factors (if any)

## Success Criteria

### Experiment-level success (even without factoring N):
- **Geometric candidate shell:** At least one shell S_j shows:
  - max_amplitude_overall ≥ friendly reference amplitude floor
  - Multiple high-amplitude candidates cluster in δ
  - → Indicates need for full dense run on that shell

### Factorization success:
- Discover p, q with p·q = N₁₂₇ using ≤ B_total candidates
- → Proves geometry + shelling works for distant factors

### Clear failure:
- All shells S₀..S₄ show:
  - max_amplitude_overall << friendly floor, OR
  - Only isolated spikes (no clusters)
  - → Geometry signal too weak; need different transform

## Running the Experiment

```bash
cd /home/runner/work/geofac/geofac/experiments/shell-geometry-scan-01
python3 run_experiment.py
```

## Output Files

- `results.json` - Complete experiment metrics in JSON format
- `EXECUTIVE_SUMMARY.md` - High-level results and verdict
- `DETAILED_RESULTS.md` - Comprehensive analysis and metrics
- `experiment_output.log` - Complete console output from run

## Implementation Notes

- Reuses GVA geodesic distance functions from `gva_factorization.py`
- Reuses Mandelbrot segment scorer from fractal-recursive-gva
- Minimal code: wraps existing GVA in shell loop with metrics
- Deterministic: fixed seeds, explicit precision, reproducible

## References

- Problem statement: Issue description
- Base GVA: `/home/runner/work/geofac/geofac/gva_factorization.py`
- Fractal scorer: `../fractal-recursive-gva-falsification/fr_gva_implementation.py`
- Previous 127-bit attempt: `../127bit-fractal-mask-challenge/`
