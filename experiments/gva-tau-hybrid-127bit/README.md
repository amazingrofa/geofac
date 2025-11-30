# GVA-τ''' Hybrid Falsification Experiment

Falsification experiment testing whether integrating Z-Framework GVA (7D torus embedding) with τ''' spike ranking can recover factors of the 127-bit challenge using only geometric signals.

## Hypothesis

**Claim**: Integrating Z-Framework GVA (7D torus embedding, geodesic scanning near b=63.28–63.50 bits) with refined τ''' spike ranking can recover factors of N=137524771864208156028430259349934309717 (127-bit challenge) using only geometric signals, no classical methods.

**Status**: ❌ **FALSIFIED**

## Background

### PR #132 Baseline

Previous work (PR #132) using Richardson extrapolation + Sobol QMC achieved:
- 0.026-bit spike accuracy (best spike was 0.026 bits from actual q ≈ 2^63.50)
- 993k candidates tested
- **Failure**: closest spike ranked 10th by confidence metric (|τ'''|/error), not 1st
- **Root cause**: ranking metric inversely correlates with factor proximity

### Proposed Improvements

This experiment tested three refinements:

1. **Spike Ranking Upgrade**: Score = error⁻¹ · log(|τ'''|) instead of |τ'''|/error
2. **GVA Integration**: 7D torus embedding with geodesic distance scoring
3. **QMC Enhancement**: Sobol with Owen scrambling, focused in [63.3, 63.7] bit range

## Methodology

### Phase 1: QMC Sampling

Generate 50,000 Sobol QMC samples in bit range [63.30, 63.70]:
- Owen scrambling for improved coverage
- Seed pinned at 42 for reproducibility

### Phase 2: τ''' Spike Computation

For each bit position b:
1. Compute τ(b) = N - 2^b · floor(N / 2^b)
2. Apply Richardson extrapolation to compute τ'''(b)
3. Estimate error from coarse/fine difference
4. Score using: Score = error⁻¹ · log(|τ'''|)

### Phase 3: GVA Geodesic Scoring

For each candidate:
1. Embed N and candidate in 7D torus using golden ratio mapping
2. Compute Riemannian geodesic distance with periodic boundaries
3. Combine with spike score: combined_score = spike_score + α · (1/geodesic_distance)
4. α = 0.1 to weight geodesic contribution

### Phase 4: Candidate Testing

1. Rank all candidates by combined score (descending)
2. Test each candidate with N % c == 0
3. Record first successful factor or exhaustion

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| N | 137524771864208156028430259349934309717 | 127-bit challenge |
| Precision | 708 dps (100 working) | max(50, 127×4+200) |
| Bit range | [63.30, 63.70] | q ≈ 2^63.505 |
| Samples | 50,000 | Balance coverage vs runtime |
| k values | [0.30, 0.35, 0.40] | Standard GVA exponents |
| h step | 0.001 | Richardson step size |
| Timeout | 60s | Per hypothesis spec |
| Seed | 42 | Reproducibility |

## Results

### Summary

| Metric | Result |
|--------|--------|
| **Factors found** | ❌ No |
| **Best proximity** | 0.000003 bits |
| **Best rank** | 46,013 / 50,000 |
| **Baseline rank** | 10 (PR #132) |
| **Improved?** | ❌ WORSE |

### Phase Timings

| Phase | Duration |
|-------|----------|
| QMC sampling | 0.02s |
| τ''' computation | 16.40s |
| Geodesic scoring | 43.58s |
| Candidate testing | 0.05s |
| **Total** | 60.05s |

### Key Findings

1. **Detection excellent**: Found spike within 0.000003 bits of q
2. **Ranking terrible**: Best spike ranked 46,013th (vs 10th in PR #132)
3. **New formula worse**: log scaling backfired
4. **GVA no help**: Geodesic distances uncorrelated at this scale

## Files

- `run_experiment.py` - Main experiment code
- `results.json` - Complete results with all spike data
- `EXECUTIVE_SUMMARY.md` - Results-first summary
- `README.md` - This documentation

## Reproducing

```bash
cd experiments/gva-tau-hybrid-127bit
python3 run_experiment.py
```

Requirements:
- Python 3.12+
- mpmath 1.3.0+
- scipy 1.7.0+ (qmc module)
- numpy 2.0+

## Validation Gate Compliance

- ✅ Target: CHALLENGE_127 = 137524771864208156028430259349934309717
- ✅ No classical fallbacks (Pollard's Rho, trial division, ECM, sieves)
- ✅ Deterministic/quasi-deterministic methods only (Sobol sampling)
- ✅ Precision: max(50, N.bit_length() × 4 + 200) = 708 dps
- ✅ Seeds pinned, parameters logged

## Conclusions

The hypothesis is **FALSIFIED**:

1. τ''' spike detection works but ranking fails catastrophically
2. The new Score = error⁻¹ · log(|τ'''|) formula performed worse than baseline
3. GVA geodesic integration provides no benefit at 127-bit scale
4. The fundamental problem is ranking, not spike detection

## Next Steps

This experiment rules out the specific combination of:
- τ''' spike ranking with log-scaled error weighting
- 7D torus geodesic guidance
- Sobol QMC sampling in narrow bit range

Future work should explore:
- Alternative ranking metrics not based on τ''' error estimates
- Different geometric frameworks beyond torus embedding
- Abandoning spike-based approaches entirely

## References

- `gva_factorization.py` - Core GVA implementation
- `experiments/gva-root-cause-analysis/` - Previous GVA analysis
- `docs/VALIDATION_GATES.md` - Gate specifications
