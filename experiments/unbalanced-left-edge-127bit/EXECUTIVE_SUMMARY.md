# Unbalanced Left-Edge Geometry Experiment - Executive Summary

**Date**: 2025-11-25  
**Target**: N = 137524771864208156028430259349934309717 (127-bit challenge)  
**Hypothesis**: Unbalanced semiprimes exhibit a "left-edge cliff" in τ-space that reveals the small factor location via τ''' spikes

## Verdict

**HYPOTHESIS NOT VALIDATED** - The τ-space approach detects signal in the correct bit-range but fails to locate factors within the tested candidate budget.

## Methodology

### τ-Function Design

The experiment defines τ(b) as a log-folded geometric score at scale parameter b (where 2^b represents candidate factor magnitude):

```
τ(b) = log(1 + geometric_score × decay)
```

Components:
- **Modular resonance**: Measures proximity to divisibility (N mod scale)
- **Phase alignment**: Golden ratio phase relationships
- **Decay**: Exponential decay from √N to focus signal

### Derivative Analysis

Higher-order derivatives computed via finite differences:
- τ'(b): First derivative (slope)
- τ''(b): Second derivative (curvature)
- τ'''(b): Third derivative (rate of curvature change - "cliff detector")

### Spike Detection

Spikes identified where |τ'''(b)| > 2.0 × mean(|τ'''|)

## Key Findings

### Finding 1: Signal Detection in Correct Region

The experiment detected 56 τ''' spikes, with the top spikes concentrated near the 63-bit range where the actual factors reside:

| Spike | b* | 2^b* | Actual Factor |
|-------|-----|------|---------------|
| #1 | 63.28 | 1.12×10^19 | p ≈ 2^63.19 |
| #2 | 63.41 | 1.23×10^19 | q ≈ 2^63.50 |

The τ''' method correctly identifies the scale region containing the factors.

### Finding 2: Insufficient Candidate Coverage

The search radius of 3.0 bits around each spike (±8× factor) proved insufficient:

- Distance from spike #1 center to actual p: ~7.2×10^17
- Distance from spike #2 center to actual q: ~8.1×10^17
- Generated candidates per spike: 5,001
- Total candidates tested: 100,020

The factor p = 10508623501177419659 is outside the tested candidate ranges.

### Finding 3: τ-Function Limitations

The τ-function as designed has limited discriminatory power:
- τ range: [0.000000, 0.594877] (narrow dynamic range)
- τ''' range: [-138, 151] (noisy signal)
- Multiple spikes of similar magnitude make precise localization difficult

## Experiment Parameters

```
N = 137524771864208156028430259349934309717
mode = UNBALANCED_LEFT_EDGE
precision_dps = 708
num_scan_points = 500
tau_scan_range = [1.0, 65.35] bits
spike_threshold_factor = 2.0
max_spikes_to_test = 20
search_radius_bits = 3.0
candidates_per_spike = 5000
```

## Results

```
tau_third_derivative_spike_at = None (no spike yielded factor)
candidate_factor_found = None
cofactor = None
verified = False
spikes_tested = 20
total_candidates_tested = 100,020
elapsed_ms = 773.84
```

## Analysis

### Why the Hypothesis Was Not Validated

1. **Scale vs. Precision Trade-off**: The 127-bit challenge factors span ~10^19, requiring either:
   - Much larger candidate budgets (10^7+ candidates)
   - More precise spike localization (sub-0.1 bit accuracy)

2. **Signal-to-Noise Ratio**: The τ''' signal correctly identifies the 63-bit region but cannot pinpoint the exact factor location within that range. The "cliff" signature is diffuse rather than sharp.

3. **Geometric Score Limitations**: The modular resonance component `N mod scale` provides weak signal because:
   - For true factor p, N mod p = 0 (perfect signal)
   - For nearby candidates, N mod (p±ε) ≠ 0 (but may still be relatively small)
   - The discrete nature of divisibility creates many local minima

### What Would Be Needed for Success

1. **Enhanced τ-function**: Incorporate additional geometric invariants (e.g., continued fraction structure, lattice properties)

2. **Hierarchical refinement**: Multi-resolution scanning with progressively finer spike localization

3. **Larger search budgets**: 10^7-10^8 candidates to cover the full bit-range uncertainty

4. **Alternative cliff detection**: Consider τ'' extrema or sign changes instead of τ''' magnitude

## Constraints Satisfied

- ✅ No prior knowledge of factors used in algorithm
- ✅ No classical fallbacks (Pollard, ECM, trial division)
- ✅ Deterministic execution
- ✅ Explicit adaptive precision (708 dps)
- ✅ Only divisibility check is final validation

## Reproducibility

```bash
cd experiments/unbalanced-left-edge-127bit
python3 run_experiment.py
```

All parameters logged. Results in `experiment_results.json`.

## Conclusion

The "unbalanced left-edge" geometry hypothesis shows **partial promise** - the τ''' approach correctly identifies the bit-scale region containing the factors. However, it **fails to achieve sufficient precision** for factor recovery within reasonable computational budgets.

This experiment does not rule out the geometric approach but establishes that the current τ-function formulation requires significant refinement or vastly larger search budgets to succeed on 127-bit semiprimes.

### Recommended Follow-ups

1. Test on smaller unbalanced semiprimes (60-80 bits) to validate the approach at tractable scales
2. Explore alternative τ-function formulations with sharper cliff signatures
3. Investigate multi-scale hierarchical refinement for spike localization
4. Consider hybrid approaches combining geometric localization with focused trial division
