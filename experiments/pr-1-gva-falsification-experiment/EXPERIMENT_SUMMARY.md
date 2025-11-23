# GVA 5D Falsification Experiment - Summary

**Status:** 🔄 Pending Execution

This document will be populated with complete results and analysis after the experiment is executed.

---

## Experiment Overview

**Hypothesis:** GVA (Geodesic Validation Assault) can efficiently factor RSA moduli using 5D toroidal embedding, Riemannian geodesic distance, and Jacobian-weighted QMC sampling, achieving 15-20% density enhancement and 100x speedup.

**Falsification Targets:**
- RSA-100 (330 bits): Primary test
- RSA-129 (427 bits): Stretch goal
- CHALLENGE_127 (127 bits): Positive control

**Expected Outcome:** Falsification - GVA will not factor RSA-100 within 10^6 QMC samples.

---

## Execution Instructions

To generate results for this summary:

```bash
cd /home/runner/work/geofac/geofac/experiments/pr-1-gva-falsification-experiment

# Quick test on CHALLENGE_127 (~5 minutes)
python3 gva_5d_falsification.py --target CHALLENGE_127 --samples 100000

# Full RSA-100 falsification (~8 hours)
python3 gva_5d_falsification.py --target RSA-100 --samples 1000000

# RSA-129 stretch goal (~80 hours)
python3 gva_5d_falsification.py --target RSA-129 --samples 10000000
```

Results will be saved to `results_{target}_{timestamp}.json` and should be analyzed to populate this document.

---

## Results Template

### RSA-100 Test Results

**Target:** N = 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139

**Configuration:**
- Max samples per k: 1,000,000
- k values tested: [0.30, 0.35, 0.40]
- Jacobian weighting: Enabled
- Geodesic guidance: Enabled
- Random seed: 42
- Precision: 1,520 dps

**Results:**
- Success: [TO BE FILLED]
- Factors found: [TO BE FILLED]
- Total candidates tested: [TO BE FILLED]
- Total time: [TO BE FILLED]
- Density enhancement: [TO BE FILLED]
- Distance correlation: [TO BE FILLED]

**Verdict:** [TO BE FILLED]

---

### CHALLENGE_127 Test Results

**Target:** N = 137524771864208156028430259349934309717

**Configuration:**
- Max samples per k: 100,000
- k values tested: [0.30, 0.35, 0.40]
- Jacobian weighting: Enabled
- Geodesic guidance: Enabled
- Random seed: 42
- Precision: 708 dps

**Results:**
- Success: [TO BE FILLED]
- Factors found: [TO BE FILLED]
- Total candidates tested: [TO BE FILLED]
- Total time: [TO BE FILLED]
- Density enhancement: [TO BE FILLED]
- Distance correlation: [TO BE FILLED]

**Verdict:** [TO BE FILLED]

---

### Metrics Summary

| Metric | CHALLENGE_127 | RSA-100 | RSA-129 |
|--------|---------------|---------|---------|
| Success | [TBF] | [TBF] | [TBF] |
| Candidates Tested | [TBF] | [TBF] | [TBF] |
| Elapsed Time (s) | [TBF] | [TBF] | [TBF] |
| Density Enhancement | [TBF] | [TBF] | [TBF] |
| Variance Reduction | [TBF] | [TBF] | [TBF] |
| Min Geodesic Distance | [TBF] | [TBF] | [TBF] |
| Distance Correlation | [TBF] | [TBF] | [TBF] |
| Bootstrap CI (95%) | [TBF] | [TBF] | [TBF] |

---

## Analysis

### Density Enhancement

[TO BE FILLED after execution]

**Expected:** < 10%, possibly negative (far below claimed 15-20%)

### Geodesic Distance Correlation

[TO BE FILLED after execution]

**Expected:** r ≈ 0 (no correlation between distance minima and factors)

### Variance Reduction

[TO BE FILLED after execution]

**Expected:** Minimal or none (< 50%)

### Bootstrap Confidence Intervals

[TO BE FILLED after execution]

**Expected:** 95% CI includes zero, indicating no reliable enhancement

---

## Falsification Verdict

**Overall Verdict:** [TO BE FILLED]

### Criteria Evaluation

| Criterion | Threshold | Observed | Status |
|-----------|-----------|----------|--------|
| RSA-100 factored within 10^6 samples | Must succeed | [TBF] | [TBF] |
| Density enhancement | > 15% | [TBF] | [TBF] |
| Distance correlation | > 0.5 | [TBF] | [TBF] |
| Speedup vs baseline | > 10x | [TBF] | [TBF] |

**Falsification Status:**
- ✓ FALSIFIED: GVA hypothesis does not hold at cryptographic scales
- ✗ NOT YET FALSIFIED: GVA claims supported by experimental evidence

[TO BE DETERMINED after execution]

---

## Interpretation

[TO BE FILLED after execution]

### Key Findings

1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

### Implications

[Discuss what the results mean for the GVA hypothesis]

### Limitations

[Discuss any limitations of the experiment]

---

## Conclusion

[TO BE FILLED after execution]

**Summary in one sentence:** [TBF]

**Recommendation:** [Continue/Abandon GVA approach based on results]

---

## Artifacts

Results saved to:
- `results_CHALLENGE_127_{timestamp}.json`
- `results_RSA-100_{timestamp}.json`
- `results_RSA-129_{timestamp}.json` (if executed)

See [README.md](README.md) for execution instructions and [falsification_design_spec.md](falsification_design_spec.md) for complete technical details.

---

**Note:** This document is a template. Execute the experiment using the commands above to populate it with actual results and analysis.
