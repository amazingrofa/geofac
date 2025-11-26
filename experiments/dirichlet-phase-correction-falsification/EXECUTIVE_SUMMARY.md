# Executive Summary: Dirichlet Phase Correction Falsification

**Date:** 2025-11-25  
**Experiment:** Dirichlet Phase Correction Falsification — Gate 2 Analysis  
**Status:** COMPLETE — Hypothesis partially falsified

---

## Results At-a-Glance

**Hypothesis:** The Dirichlet-kernel phase correction is blocking resonance lock in Gate 2 attempts. Systematic curvature in residual phase Δφ indicates geometric asymmetry correctable via φ_shift = α × ln(N)/e².

**Outcome:** **HYPOTHESIS FALSIFIED** — Curvature can be reduced, but RMS remains unchanged

**Runtime:** 2.98 seconds  
**Samples collected:** 2,001

---

## Key Findings

### 1. Baseline Curvature Analysis

| Metric | Value |
|--------|-------|
| Quadratic coefficient a | -3.92 × 10³⁰ |
| Linear coefficient b | -8.67 × 10¹⁴ |
| Constant c | 0.983 |
| R² fit quality | 0.292 |
| Baseline RMS | 1.814 |

**Interpretation:** Strong quadratic curvature exists in the baseline residual phase, suggesting systematic geometric asymmetry. However, the R² of 0.29 indicates the quadratic fit explains only ~29% of variance.

### 2. Phase Correction Sweep

#### Initial Sweep: α ∈ [-0.5, 0.5]

| α | Curvature |a| | RMS | Notes |
|---|-------------|-----|-----|
| -0.50 | 3.37 × 10³⁰ | 1.814 | Slight curvature reduction |
| 0.00 | 3.92 × 10³⁰ | 1.814 | Baseline |
| 0.42 | **2.84 × 10²⁸** | 1.814 | **Optimal in initial range** |
| 0.50 | 1.44 × 10³⁰ | 1.814 | |

#### Extended Sweep: α ∈ [-2, 2]

| α | Curvature |a| | RMS | Notes |
|---|-------------|-----|-----|
| -1.80 | **2.11 × 10²⁹** | 1.814 | **Optimal overall** |
| 0.42 | 2.84 × 10²⁸ | 1.814 | Best in initial range |

### 3. Optimal Correction

| Metric | Before (α=0) | After (α*=0.42) | After (α*=-1.8) | Change |
|--------|--------------|-----------------|-----------------|--------|
| Curvature |a| | 3.92 × 10³⁰ | 2.84 × 10²⁸ | 2.11 × 10²⁹ | **138× / 18.6×** |
| Residual RMS | 1.8138 | 1.8139 | 1.8139 | **~0× (no change)** |

---

## Verdict

### HYPOTHESIS FALSIFIED

**Acceptance Criteria:**
- ✅ |a| drops by ≥5× after correction (achieved: 138× at α=0.42, 18.6× at α=-1.8)
- ❌ Residual RMS drops by ≥2× after correction (achieved: 1.00×, essentially no change)

**Evidence:**

1. ✅ **Baseline curvature exists:** |a| = 3.92 × 10³⁰ (significant)
2. ✅ **Curvature reduction achieved:** 138× at α=0.42 (far exceeds 5× target)
3. ❌ **RMS reduction failed:** 1.00× (essentially unchanged, far below 2× target)
4. ⚠️ **Optimal α* found but ineffective:** α=0.42 in initial range, α=-1.8 in extended

**Conclusion:**

The phase correction formula φ_shift = α × ln(N)/e² **can reduce curvature** in the residual phase, but this curvature reduction **does not translate to improved resonance quality** (measured by RMS). The residual RMS remains essentially constant (~1.814) regardless of phase correction.

This suggests:
1. The curvature in Δφ is NOT the blocking factor for resonance lock
2. The geometric asymmetry indicated by curvature is not the primary error source
3. Other factors (not captured by this phase model) dominate the residual

---

## Implications

### For Dirichlet-Kernel Phase Correction

The hypothesis that phase correction would unlock resonance is **falsified**. While curvature exists and can be corrected:
- Correcting curvature does not improve overall fit quality
- The dominant error is not addressable via global phase shift
- Other mechanisms are responsible for resonance lock failure

### For Gate 2 Factorization

The 60-bit Gate 2 semiprime (N = 1,152,921,470,247,108,503) shows:
- Systematic curvature exists in the phase residuals
- But phase correction alone cannot improve factor detection
- The search space topology may need fundamentally different approaches

### Scientific Value

This experiment provides:
1. **Partial validation:** Curvature exists and is correctable (≥5× achieved)
2. **Clear falsification:** Correction does not improve RMS (0× vs 2× target)
3. **Definitive conclusion:** Phase correction is not the blocking factor

---

## Configuration

| Parameter | Value |
|-----------|-------|
| Gate | Gate 2 (60-bit) |
| N | 1,152,921,470,247,108,503 |
| sqrt(N) | 1,073,741,807 |
| Expected p | 1,073,741,789 |
| Expected q | 1,073,741,827 |
| Bit length | 60 |
| α sweep range | [-0.5, 0.5] (initial), [-2, 2] (extended) |
| α steps | 101 |
| Sample window | ±1,000 |
| Precision | 440 dps (adaptive) |
| Seed | 42 |

---

## Next Steps

1. **Accept the falsification:** Phase correction is not the solution for Gate 2
2. **Investigate other error sources:** Non-phase factors dominating RMS
3. **Consider alternative hypotheses:** 
   - Higher-order corrections beyond quadratic
   - Non-global (local) phase corrections
   - Different embedding parameters or kernel structures

---

## References

- Experiment design: [README.md](README.md)
- Implementation: [run_experiment.py](run_experiment.py)
- Raw data: [results.json](results.json)
