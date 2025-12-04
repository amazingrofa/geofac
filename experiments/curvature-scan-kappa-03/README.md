# Narrow-Band Curvature Scan around κ ≈ 0.3

**Experiment Date:** December 2025  
**Status:** Active  
**Hypothesis:** Dirichlet-kernel peaks at κ ≈ 0.3 are stable and gateworthy for scaling to Gate-4.

## Motivation

This experiment performs a high-resolution curvature sweep to characterize the Dirichlet-kernel amplitude response across a narrow band centered at κ₀ = 0.3. The goal is to determine if this curvature value produces stable, reproducible peaks that persist across kernel orders, supporting the hypothesis that κ ≈ 0.3 is optimal for geometric resonance factorization.

## Experimental Design

### Target

- **Primary:** CHALLENGE_127 = 137524771864208156028430259349934309717 (Gate-3, 127-bit)
- **Factors:** p = 10508623501177419659, q = 13086849276577416863
- **Scale:** Within [10¹⁴, 10¹⁸] validation window

### Curvature Band

| Parameter | Value |
|-----------|-------|
| Center (κ₀) | 0.3000 |
| Half-width (Δκ) | 0.0100 |
| Range | [0.2900, 0.3100] |
| Resolution (δκ) | 1e-5 (≈ 2,001 points) |

*Note: For practical runtime, initial scans may use coarser resolution (5e-5) then refine around peaks.*

### Dirichlet Kernel Orders

| Order (J) | Notes |
|-----------|-------|
| 257 | Baseline order |
| 513 | Primary test (odd) |
| 1025 | Extended order |

Testing multiple J values validates peak persistence across kernel sharpness.

### Sampling Strategy

- **Sample count:** M = 100,000 (reduced from 1e6 for practical runtime)
- **Seed:** 1729 (deterministic)
- **Method:** Sobol sequence for quasi-random sampling
- **Lattice:** Identical candidates across all κ values to isolate κ-effect
- **Window:** Centered on √N with adaptive sizing

### Computed Metrics (per κ)

1. **Geometric signal:** s_κ(m) = 1 / (1 + distance(N, m))
2. **Dirichlet amplitude:** A(κ) = max_ω |D_J(ω; s_κ)|
3. **Top-K ranks:** R_K(κ) for K ∈ {10, 100, 1000}
4. **Peak characteristics:** FWHM, SNR, peak frequency ω*

## Acceptance Gates

### Gate 1: Peak Persistence
- **Criterion:** Same primary peak location κ* stays within ±3δκ when changing J (257 ↔ 1025)
- **Threshold:** max|Δκ*| ≤ 3 × 1e-5 = 3e-5

### Gate 2: Peak Width (FWHM)
- **Criterion:** Primary peak FWHM ≤ 40δκ
- **Threshold:** FWHM ≤ 4e-4 (sharp enough to be targetable)

### Gate 3: Signal-to-Noise Ratio
- **Criterion:** Peak amplitude at least 8× the local median absolute deviation
- **Threshold:** SNR ≥ 8

### Gate 4: Rank Stability
- **Criterion:** Jaccard(top-100 at κ₀, top-100 at κ₀±5δκ) ≥ 0.75
- **Threshold:** Jaccard index ≥ 0.75 (high overlap in top candidates)

### Gate 5: Skew Test
- **Criterion:** On a skewed semiprime of similar size, still observe a primary peak within ±0.002 of κ₀
- **Threshold:** |κ* - κ₀| ≤ 0.002

## Output Artifacts

### Configuration
- `scan_config.json` — Full configuration with κ₀, Δκ, δκ, J values, M, seed, N

### Data Files
- `curvature_scan.csv` — Columns: [kappa, J, amplitude, peak_freq, fwhm, snr, topK_hash]
- `topK/*.json` — Actual top-K indices for each κ value (K=10/100/1000)
- `results.json` — Complete results with all metrics

### Environment & Logs
- `env.txt` — Python version, CPU, mpmath version, timestamps
- `log.txt` — Timings and gate results

### Reproducibility Verification
- Lattice hash recorded to prove identical samples across κ

## Running the Experiment

### Prerequisites
- Python 3.8+
- mpmath (arbitrary precision)
- Standard library only (json, time, hashlib)

### Execution

```bash
cd experiments/curvature-scan-kappa-03
python curvature_scan.py
```

### Expected Runtime
- Coarse resolution (5e-5): ~10-30 minutes
- Fine resolution (1e-5): ~1-2 hours
- Full specification (1e-5, 1e6 samples): ~8-12 hours

## Precision Requirements

- **Adaptive precision:** max(50, N.bitLength() × 4 + 200)
- **For 127-bit N:** 708 decimal places
- **Implementation:** mpmath with explicit mp.workdps()

## Validation Gates Compliance

| Gate | Status |
|------|--------|
| Gate-3 (127-bit challenge) | Primary target ✓ |
| Gate-4 (10¹⁴–10¹⁸ range) | All factors in range ✓ |
| No classical fallbacks | Pure geometric method ✓ |
| Deterministic | Fixed seed (1729) ✓ |
| Explicit precision | 708 dps logged ✓ |

## Expected Outcomes

### If hypothesis is TRUE (scale to Gate-4):
- All 5 acceptance gates pass
- Primary peak κ* stable within ±3δκ across J values
- Sharp, high-SNR peaks at κ ≈ 0.3
- High rank stability (Jaccard ≥ 0.75)
- Skew test shows similar behavior

### If hypothesis is FALSE (hold):
- One or more gates fail
- Peaks drift or split with changing J
- Low SNR or broad FWHM
- Rank instability at nearby κ values
- Skew test shows different optimal κ

## Analysis Workflow

After running:

1. **Review `log.txt`** for gate pass/fail summary
2. **Examine `curvature_scan.csv`** for raw amplitude data
3. **Plot A(κ) curves** for each J value
4. **Analyze peak zoom windows** around local maxima
5. **Compute Jaccard stability strips** for K = 10, 100, 1000

## References

1. `gva_factorization.py` — Core GVA implementation
2. `experiments/gva-curvature-validation-2025/` — Prior curvature experiment
3. `experiments/kernel-order-impact-study/` — J parameter analysis
4. `experiments/dirichlet-phase-correction-falsification/` — Phase analysis

## Decision Matrix

| Result | Action |
|--------|--------|
| All gates pass | Proceed to Gate-4 validation |
| 4/5 gates pass | Investigate failing gate, consider parameter adjustment |
| 3/5 gates pass | Major investigation needed |
| <3 gates pass | Hypothesis falsified, explore alternative κ values |

## Contact

This experiment is part of the geofac geometric resonance factorization project.
See the main README.md for project context and goals.
