# **HYPOTHESIS FALSIFIED**

**Experiment:** GVA Curvature Validation 2025  
**Date:** November 22, 2025  
**Runtime:** 77 seconds  
**Target:** CHALLENGE_127 (127-bit semiprime)

## Conclusion

Second-order differences (curvature/discrete Laplacian) of GVA amplitude **do NOT provide a usable gradient for factor localization** in Shell S₅ for the 127-bit challenge number.

**All three k-values tested (0.30, 0.35, 0.40) show distance ratios > 1.9**, meaning top curvature peaks are **nearly 2× farther from factors** than expected under a uniform null distribution. This is the opposite of clustering—it indicates **anti-clustering** or uniform distribution with noise.

## Key Results

### Samples Collected
- **k=0.30:** 2,500 samples
- **k=0.35:** 2,500 samples  
- **k=0.40:** 2,500 samples

### Distance Ratios (Top 100 Peaks)
| k-value | Mean Ratio | Median Ratio | Verdict |
|---------|------------|--------------|---------|
| 0.30 | 2.108 | 1.920 | ✗ Anti-clustering |
| 0.35 | 2.108 | 1.920 | ✗ Anti-clustering |
| 0.40 | 2.108 | 1.920 | ✗ Anti-clustering |

**Distance ratio < 0.5:** Strong clustering (would support hypothesis)  
**Distance ratio < 1.0:** Weak clustering (might support hypothesis)  
**Distance ratio ≥ 1.0:** No clustering (falsifies hypothesis)  
**Distance ratio > 1.5:** Anti-clustering (strong falsification)

### Peaks Near Factors
**No peaks within 10¹⁵ of either factor** for any k-value tested.
- Peaks within 10¹³: **0**
- Peaks within 10¹⁴: **0**
- Peaks within 10¹⁵: **0**

The shell width is 5.36×10¹⁷, and factors are at offsets -1.22×10¹⁸ (p) and +1.36×10¹⁸ (q) from √N—**both factors lie far outside Shell S₅**.

## Interpretation

### Why the hypothesis failed

1. **Shell S₅ doesn't contain the factors:** Both p and q are located far from the sampled region
   - p offset: -1.22×10¹⁸ (negative, outside shell)
   - q offset: +1.36×10¹⁸ (positive, but beyond R₆ = 1.40×10¹⁵)
   - Sampled range: [8.67×10¹⁴, 1.40×10¹⁵] offsets

2. **Curvature shows no long-range structure:** Even though factors are "visible" to the embedding (through torus periodicity), curvature peaks don't point toward them.

3. **Signal is too weak or non-existent:** The curvature range (10⁻²⁷ scale) shows variation, but this variation is not spatially correlated with factor locations.

### Comparison to amplitude

| Metric | Amplitude | Curvature |
|--------|-----------|-----------|
| Range | 0.51 | 1.1×10⁻²⁶ |
| Coefficient of variation | 12% | 2956% |
| Clustering near factors | None | None (worse than null) |

Amplitude is relatively flat (12% CV). Curvature has high relative variation (2956% CV) but this variation is **not informative**—it's noise or structure unrelated to factorization.

## Recommendations

### Do NOT pursue:
- ✗ Higher-order differences (third, fourth derivatives)
- ✗ Different shell geometries with current curvature metric
- ✗ More k-values with current approach

### Consider investigating:
- ✓ Shell S₀ or shells that actually contain the factors
- ✓ Different distance metrics or embedding dimensions
- ✓ Spectral methods (FFT of amplitude profile)
- ✓ Discrete wavelet transforms instead of Laplacian
- ✓ Correlation with known factor structure rather than absolute position

## Validation Gates Status

✓ **Gate 1 (127-bit challenge):** Used CHALLENGE_127 as primary target  
✓ **Gate 4 (10¹⁴–10¹⁸ range):** All measurements in valid scale range  
✓ **No classical fallbacks:** Pure geometric method  
✓ **Deterministic:** Reproducible with fixed parameters  
✓ **Explicit precision:** 708 dps logged and used

## Reproducibility

```bash
cd experiments/gva-curvature-validation-2025
python3 run_experiment.py
```

**Parameters:**
- N = 137524771864208156028430259349934309717
- Shell S₅: [√N + 8.67×10¹⁴, √N + 1.40×10¹⁵]
- k-values: [0.30, 0.35, 0.40]
- Samples: 2,500 per k (5,000 attempted, 2,500 odd)
- Curvature h: stride / 10 = 1.07×10¹³
- Precision: 708 dps (adaptive)

## Conclusion Summary

**The hypothesis that "second-order differences of amplitude carry a usable gradient for factor localization" is FALSIFIED for Shell S₅ geometry on CHALLENGE_127.**

The experiment demonstrates:
1. Curvature varies (it's not constant)
2. Curvature variation is NOT correlated with factor locations
3. Top curvature peaks are distributed uniformly or anti-cluster relative to factors
4. This approach provides no advantage over random search

**Next steps:** Pivot to alternative signal processing methods or investigate shells that actually contain the factors.
