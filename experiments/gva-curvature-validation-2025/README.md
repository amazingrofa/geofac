# GVA Curvature Validation 2025

**Experiment Date:** November 2025  
**Status:** Active  
**Hypothesis:** Second-order differences of amplitude (curvature/discrete Laplacian) carry a usable gradient for factor localization where raw amplitude does not.

## Motivation

Previous experiments (shell-geometry-scan-01, gva-curvature-falsification) established that:
1. Raw GVA amplitude is relatively flat in Shell S₅ for CHALLENGE_127
2. First-order differences (gradient) show minimal structure
3. The question remains: does curvature (second-order differences) reveal hidden structure?

This experiment tests whether the **discrete Laplacian** of GVA amplitude provides a localization signal for factors, even when raw amplitude appears flat.

## Experimental Design

### Target
- **N:** CHALLENGE_127 = 137524771864208156028430259349934309717
- **Factors:** p = 10508623501177419659, q = 13086849276577416863
- **Bit length:** 127 bits
- **Scale:** Within [10¹⁴, 10¹⁸] validation window

### Shell Geometry
- **Shell:** S₅ (fifth golden-ratio shell around √N)
- **Boundaries:** R₅ = √N × φ⁵, R₆ = √N × φ⁶
- **Computed values:** R₅ ≈ 8.67×10¹⁴, R₆ ≈ 1.40×10¹⁵
- **Width:** ~5.4×10¹⁴

### GVA Parameters
- **K-values:** [0.30, 0.35, 0.40] (geodesic exponents)
- **Embedding:** 7D torus with golden ratio coordinates
- **Distance metric:** Riemannian geodesic on flat torus

### Sampling Strategy
- **Target samples:** ~5000 per k-value
- **Stride:** Computed from shell width to achieve target
- **Curvature h:** stride / 10 (for finite differences)

### Curvature Computation
For each candidate c:
```
A(c) = 1 / (1 + distance(N, c))  [GVA amplitude]

curv(c) = (A(c+h) - 2*A(c) + A(c-h)) / h²  [discrete Laplacian]
```

The discrete Laplacian measures local concavity/convexity. High |curv(c)| indicates rapid change in gradient.

### Analysis Metrics

1. **Distribution statistics:**
   - Curvature: min, max, mean, std, range
   - Amplitude: min, max, mean, std, range
   
2. **Peak analysis:**
   - Track top 100 peaks by |curvature|
   - Compute distance from each peak to nearest factor
   - Compare to null model (uniform distribution)

3. **Null model:**
   - Expected mean distance for uniform distribution over shell width
   - Formula: E[dist] ≈ W / 5 (for 2 targets in width W)

4. **Success criteria:**
   - **Strong support:** distance_ratio < 0.5 (top peaks cluster 2× closer than expected)
   - **Weak support:** distance_ratio < 1.0 (some clustering detected)
   - **No support:** distance_ratio ≥ 1.0 (no clustering, null hypothesis)

### Precision Requirements
- **Adaptive precision:** max(50, N.bitLength() × 4 + 200)
- **For 127-bit N:** 708 decimal places
- **Implementation:** mpmath with explicit mp.workdps()

## Expected Outcomes

### If hypothesis is TRUE:
- Top curvature peaks cluster near factor locations
- Distance ratio < 0.5 for at least one k-value
- Clear separation from null model distribution

### If hypothesis is FALSE:
- Top curvature peaks distributed uniformly (distance ratio ≈ 1.0)
- No spatial clustering near factors
- Null model holds

## Comparison to Prior Work

| Experiment | Signal | Result | Shell |
|------------|--------|--------|-------|
| shell-geometry-scan-01 | Raw amplitude | Flat, no structure | S₅ |
| gva-curvature-falsification | Curvature | Showed variation but no analysis | S₅ |
| **This experiment** | **Curvature + null model** | **TBD** | **S₅** |

## Implementation Details

### Files
- `run_experiment.py` — Main computation script
- `results.json` — Raw data output
- `EXECUTIVE_SUMMARY.md` — Results-first summary
- `DETAILED_RESULTS.md` — Full methodology and data
- `README.md` — This file

### Dependencies
- Python 3.8+
- mpmath (arbitrary precision)
- Standard library only (json, time, statistics)

### Running the Experiment
```bash
cd experiments/gva-curvature-validation-2025
python run_experiment.py
```

Expected runtime: ~10-20 minutes for 5000 samples × 3 k-values

### Output Format
```json
{
  "experiment": "gva-curvature-validation-2025",
  "hypothesis": "...",
  "N": 137524771864208156028430259349934309717,
  "per_k_metrics": [
    {
      "k": 0.30,
      "samples_collected": 5000,
      "curvature_mean": ...,
      "null_model_mean_distance": ...,
      "actual_mean_distance_top_peaks": ...,
      "distance_ratio_mean": ...,
      "peak_locations": [...]
    }
  ]
}
```

## Validation Gates

This experiment satisfies:
- **Gate 1 (127-bit challenge):** Primary target is CHALLENGE_127 ✓
- **Gate 4 (10¹⁴–10¹⁸ range):** All factors in range ✓
- **No classical fallbacks:** Pure geometric method ✓
- **Deterministic:** Fixed seeds, reproducible ✓
- **Explicit precision:** 708 dps logged ✓

## References

1. shell-geometry-scan-01 — Established S₅ shell boundaries
2. gva-curvature-falsification — Initial curvature exploration
3. CODING_STYLE.md — Invariants and validation gates
4. VALIDATION_GATES.md — Scale requirements
5. gva_factorization.py — Core GVA implementation

## Success Criteria

**Hypothesis validated if:**
- At least one k-value shows distance_ratio < 0.5
- Top peaks cluster significantly closer to factors than null model
- Results reproducible with fixed seed

**Hypothesis falsified if:**
- All k-values show distance_ratio ≥ 1.0
- No significant clustering detected
- Peak distribution matches uniform null model

## Next Steps

After experiment completion:
1. Review EXECUTIVE_SUMMARY.md for verdict
2. Analyze clustering patterns in results.json
3. If validated: test on additional RSA challenge numbers
4. If falsified: document failure mode and pivot to alternative approaches
