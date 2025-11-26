# Z5D-GVA Band Oracle Falsification Experiment

## Executive Summary

**HYPOTHESIS FALSIFIED**

The Z5D-informed GVA upgrade hypothesis proposes that band oracles, density weighting, wheel masks (mod 2310), and short-circuit mechanisms can improve factorization of the 127-bit challenge. This experiment tests that hypothesis through rigorous falsification criteria.

### Key Findings

1. **All methods failed** to factor the 127-bit challenge within the test budget
2. **Fundamental structural limitation**: The 127-bit challenge factors (p, q) are located ~10^18 away from √N, not near it as assumed by the band oracle design
3. **Density weighting toggle** (A/B test) showed no measurable difference
4. **Short-circuit mechanism** did not trigger (no distant shells detected)
5. **Wheel mask** correctly admits both known factors but provides only pruning benefit

### Critical Insight

The 127-bit challenge is an **unbalanced semiprime**:
- √N ≈ 1.17 × 10^19
- p = 10,508,623,501,177,419,659 (smaller factor)
- q = 13,086,849,276,577,416,863 (larger factor)
- δ_p = p - √N = **-1.22 × 10^18** (!)
- δ_q = q - √N = **+1.36 × 10^18** (!)

The band oracle design assumes factors are near √N with δ on the order of 10^6 to 10^7. The actual factors are ~10^11 times farther away than the search window covers.

## Validation Gates

- **Gate 3**: 127-bit challenge: N = 137524771864208156028430259349934309717
- **Factors**: p = 10508623501177419659, q = 13086849276577416863
- **Operational range**: [10^14, 10^18]

## Methodology

### Components Implemented

1. **Band Oracle** (`z5d_band_oracle.py`): Generates `bands.jsonl` with inner bands around √N using exponentially increasing widths
2. **Bin Export** (`band_constrained_gva.py`): Quantizes k/m grid into `bins.json`
3. **Wheel Mask** (`mask_generator.py`): Mod 2310 (2×3×5×7×11) residue filter → `mask.json` with 480 allowed residues
4. **A/B Density Toggle**: `use_density_weight` parameter (default False)
5. **Short-Circuit**: Variance < τ₁ and curvature < τ₂ for T consecutive steps
6. **Acceptance Criterion**: SNR > τ, Newton ≤ K steps, residual < ε, mask holds

### Experiments Run

| Experiment | Config | Result | Time |
|------------|--------|--------|------|
| Baseline GVA | 50K candidates, ±500K δ-window | FAILURE | 0.04s |
| Z5D Band Oracle (no density) | 29 bands, 1K/band, mod 2310 mask | FAILURE | 104.7s |
| Z5D Band Oracle (with density) | Same + density weighting | FAILURE | 104.4s |

### Falsification Criteria Results

| Criterion | Result |
|-----------|--------|
| Z5D improves over baseline | ✗ FALSE |
| Density toggle changes outcome | ✗ FALSE |
| Short-circuit reduces computation | ✗ FALSE |
| Improvements not just wheel mask | ✗ FALSE |

## Artifacts

| File | Description |
|------|-------------|
| `mask.json` | Wheel residue mask (mod 2310): 480 admissible residues |
| `bands.jsonl` | Band oracle output: 29 bands with priorities and coverage |
| `bins.json` | Quantized k/m grid: 200 bins (10 k × 20 m) |
| `peaks.jsonl` | Candidate peaks found during search (~30K records) |
| `run_log.json` | Full reproducibility log with timestamps and parameters |

## Interpretation

The Z5D-informed GVA upgrade does NOT demonstrably improve factorization of the 127-bit challenge. The fundamental issue is **structural**:

1. **Band Oracle Assumption Violated**: The band oracle assumes factors cluster near √N. For the 127-bit challenge, factors are 10^18 away from √N, completely outside any reasonable search window.

2. **Wheel Mask is Necessary but Not Sufficient**: The mod 2310 wheel correctly filters candidates (both p and q pass the mask), but filtering alone cannot find factors that are outside the search space.

3. **Density Weighting Irrelevant**: Since no candidates near the actual factors were explored, density weighting had no opportunity to improve targeting.

4. **Short-Circuit Did Not Activate**: The search explored all bands without detecting the "distant shell" pattern the short-circuit was designed for.

## Recommendations for Future Work

1. **Reframe the Problem**: The 127-bit challenge requires methods that don't assume p ≈ q ≈ √N. Consider imbalance-aware approaches.

2. **Scale Analysis First**: Before designing search strategies, analyze the expected factor distribution for the target N.

3. **Alternative Approaches**: 
   - Lattice-based methods that handle imbalanced factors
   - Fermat-style methods starting from larger search bases
   - Hybrid approaches that combine geometric insights with classical bounds

## Reproducibility

```bash
# Run the experiment
cd experiments/z5d-gva-band-oracle-falsification
python3 run_experiment.py

# View results
cat run_log.json | python3 -m json.tool
```

### Environment

- Python 3.x with mpmath for arbitrary precision
- All random elements use deterministic seeds (seed=42)
- Timestamps in ISO 8601 UTC format

## Files

| File | Purpose |
|------|---------|
| `README.md` | This document |
| `run_experiment.py` | Main experiment runner |
| `z5d_band_oracle.py` | Band oracle implementation |
| `band_constrained_gva.py` | Band-constrained GVA with all Z5D enhancements |
| `mask_generator.py` | Wheel mask (mod 2310) generator |
| `mask.json` | Generated wheel mask artifact |
| `bands.jsonl` | Generated bands artifact |
| `bins.json` | Generated k/m bins artifact |
| `peaks.jsonl` | Peaks found during search |
| `run_log.json` | Full experiment log with reproducibility data |

## Conclusion

**The hypothesis that Z5D-informed GVA upgrades can improve factorization of the 127-bit challenge is FALSIFIED.**

The failure is not due to implementation issues but to a fundamental mismatch between the method's assumptions (factors near √N) and the target's structure (factors ~10^18 away from √N). Any future approach must account for this extreme imbalance in the 127-bit challenge's factor distribution.
