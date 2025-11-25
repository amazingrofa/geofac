# τ''' Spike Refinement Experiment

**Status**: Completed (Hypothesis Not Validated)  
**Target**: 127-bit challenge N = 137524771864208156028430259349934309717  
**Predecessor**: PR #131 (experiments/unbalanced-left-edge-127bit)

## Overview

This experiment tests whether improvements to PR #131's τ''' spike detection can achieve factor recovery for the 127-bit challenge. PR #131 correctly detected the scale region (b≈63.28 aligning with actual factors at ~63.19 and ~63.50 bits) but failed to recover factors within 100k candidates.

### Problem Statement from PR #131

1. **Mapping offset**: Center from b=63.28 is ≈1.119×10¹⁹, but actual p is ≈1.051×10¹⁹—offset exceeding inner search windows.
2. **Sampling inefficiency**: Inner dense search covers negligible fraction of range.
3. **Precision limits**: Finite differences may introduce spike location error.

### Improvements Tested

1. **Richardson extrapolation** for sub-bit spike localization
2. **Sobol QMC sampling** with 80% budget in ±0.1 bit inner region
3. **Increased candidate budget** (1M total vs 100k)

## Methodology

### Richardson Extrapolation for Third Derivative

Standard finite difference:
```
τ'''(b) ≈ (τ(b+2h) - 2τ(b+h) + 2τ(b-h) - τ(b-2h)) / (2h³)
```

Richardson extrapolation combines estimates at h and h/2 to eliminate O(h²) error:
```
D_refined = (4 × D_{h/2} - D_h) / 3
```

This provides sub-bit accuracy in spike localization.

### Sobol QMC Sampling Strategy

Budget allocation:
- **80%** of candidates in ±0.1 bit inner region (quasi-random via Sobol)
- **20%** in ±2.0 bit outer region (logarithmic coverage)

The hypothesis is that improved spike localization places factors within the ±0.1 bit inner region, where dense sampling can find them.

### Spike Confidence Metric

Spikes are ranked by signal/noise ratio:
```
confidence = |τ'''(b)| / error_estimate
```

where `error_estimate` comes from Richardson extrapolation.

## Algorithm

```
1. Set precision: max(50, N.bit_length() × 4 + 200) = 708 dps
2. Compute τ(b) for b ∈ [1, sqrt_N_bits + 2] with 1000 points
3. Apply Richardson extrapolation for τ'''(b) and error estimates
4. Rank spikes by confidence (|τ'''| / error)
5. For top 10 spikes:
   a. Generate candidates via Sobol QMC (80% inner, 20% outer)
   b. Test candidates: if N % c == 0, return (c, N/c)
6. Report success or failure with post-hoc analysis
```

## Results Summary

| Metric | Value |
|--------|-------|
| Spikes detected | 118 |
| Spikes tested | 10 |
| Total candidates | 992,599 |
| Elapsed time | 11.9 seconds |
| Factor found | **No** |

### Key Result: Spike #10 Was 0.026 Bits From q

Post-hoc analysis revealed:

| Spike Rank | b* | Closest Factor | Bit Distance |
|------------|-----|----------------|--------------|
| 1 | 62.64 | p | 0.547 bits |
| 5 | 63.61 | q | 0.103 bits |
| **10** | **63.48** | **q** | **0.026 bits** |

The τ''' detection correctly identified a spike within 0.026 bits of factor q, but this spike ranked 10th by confidence.

## Analysis

### Why It Failed

1. **Confidence ranking inversion**: The closest spike to a factor (0.026 bits) ranked 10th, not 1st.

2. **Factor outside inner window**: Even for spike #10:
   - Inner region: 1.275×10¹⁹ to 1.295×10¹⁹
   - Actual q: 1.309×10¹⁹
   - Factor q fell outside the ±0.1 bit inner window

3. **Scale fundamentals**: At 10¹⁹ scale, 0.026 bits = 2.35×10¹⁷ integers—far exceeding any practical search budget.

### Comparison to PR #131

| Aspect | PR #131 | This Experiment |
|--------|---------|-----------------|
| Best spike accuracy | ~0.09 bits | ~0.026 bits |
| Richardson extrapolation | No | Yes |
| Sobol QMC | No | Yes |
| Candidates tested | 100,020 | 992,599 |
| Outcome | Not validated | Not validated |

Richardson extrapolation improved accuracy by ~3.5×, but this did not achieve factor recovery.

## Constraints Satisfied

- ✅ No prior knowledge of factors used in algorithm
- ✅ No classical fallbacks (Pollard, ECM, trial division, sieves)
- ✅ Deterministic/quasi-deterministic methods only (Sobol sequences)
- ✅ Explicit adaptive precision (708 dps)
- ✅ Reproducible execution

## Running the Experiment

```bash
cd experiments/tau-spike-refinement-127bit
pip install mpmath scipy
python3 run_experiment.py
```

### Output Files

- `experiment_results.json` — Full structured results including post-hoc analysis
- `EXECUTIVE_SUMMARY.md` — Human-readable summary with conclusions

### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `num_scan_points` | 1000 | Points in τ scan (2× PR #131) |
| `spike_threshold_factor` | 2.0 | Spikes > 2× mean |τ'''| |
| `max_spikes_to_test` | 10 | Top spikes to investigate |
| `outer_radius_bits` | 2.0 | Outer search region (±4×) |
| `inner_radius_bits` | 0.1 | Inner dense region (±7%) |
| `inner_fraction` | 0.8 | Budget for inner region |
| `candidates_per_spike` | 100,000 | Candidates per spike |

## Falsification Criteria

The hypothesis is **falsified** because:

1. ❌ Factor recovery not achieved within 1M candidate budget
2. ❌ Confidence ranking failed to prioritize closest spike
3. ❌ Even best spike (0.026 bits) produced offset exceeding inner search window

The hypothesis **would have been validated** if:

1. ✅ A clear τ''' spike appeared at factor scale
2. ✅ Confidence ranking surfaced the correct spike
3. ✅ Candidates from the spike location yielded the factor

## Conclusions

1. **τ''' signal exists and is more accurate with Richardson extrapolation** — best spike was 0.026 bits from q.

2. **Confidence metric is flawed** — closest spike ranked 10th instead of 1st.

3. **Sampling strategy is sound but requires better spike ranking** — 80% of budget on ±0.1 bit would work if the top-ranked spike were actually closest.

4. **Scale remains the fundamental challenge** — at 10¹⁹, even sub-0.1 bit accuracy produces intractable search spaces.

## Recommended Follow-ups

1. **Improve confidence metric**: Design a ranking that correlates with factor proximity (e.g., local τ curvature, phase coherence).

2. **Multi-resolution refinement**: Use coarse scan to identify region, then fine scan within region to refine spike location.

3. **Test all spikes**: With 118 spikes and 100k candidates each, full coverage would require ~12M candidates—tractable for a dedicated run.

4. **Alternative τ-function**: Explore τ formulations with sharper discriminatory power.

## References

- [PR #131 Experiment](../unbalanced-left-edge-127bit/README.md)
- [Validation Gates](../../docs/validation/VALIDATION_GATES.md)
- [Coding Style](../../docs/implementation/CODING_STYLE.md)
