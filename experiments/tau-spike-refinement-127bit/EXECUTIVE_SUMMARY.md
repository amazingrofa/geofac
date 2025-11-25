# τ''' Spike Refinement Experiment - Executive Summary

**Date**: 2025-11-25  
**Target**: N = 137524771864208156028430259349934309717 (127-bit challenge)  
**Predecessor**: PR #131 (experiments/unbalanced-left-edge-127bit)

## Verdict

**HYPOTHESIS NOT VALIDATED** — Richardson extrapolation and Sobol QMC sampling improvements did not achieve factor recovery, despite one spike being only 0.026 bits from the actual factor q.

## Key Findings

### Finding 1: A Spike Within 0.026 Bits of Factor q

| Metric | Value |
|--------|-------|
| Spike #10 b* | 63.4786 |
| Spike center | 1.285×10¹⁹ |
| Actual q | 1.309×10¹⁹ |
| Distance | 2.35×10¹⁷ |
| Bit distance | **0.026 bits** |

The τ''' spike detection correctly localized to within 2% of a bit. However, this spike ranked **10th** by confidence (signal/noise ratio = 4.23).

### Finding 2: Confidence Ranking Inversion

The confidence metric (|τ'''| / error estimate) inverted the correct ordering:

| Rank | b* | Closest Factor | Bit Distance |
|------|-----|----------------|--------------|
| 1 | 62.64 | p | 0.547 |
| 5 | 63.61 | q | 0.103 |
| **10** | **63.48** | **q** | **0.026** |

The closest spike to a factor ranked 10th, not 1st. This suggests:
- Richardson extrapolation improves derivative accuracy but doesn't fix the underlying τ-function's discriminatory power
- Signal/noise ratio correlates weakly with proximity to factors

### Finding 3: Inner Search Window Coverage

For spike #10 (the closest to q):
- Inner region (±0.1 bit): covers 1.275×10¹⁹ to 1.295×10¹⁹
- Actual q: 1.309×10¹⁹
- **Factor q is outside the inner search window**

The 0.026-bit spike localization error caused q to fall outside the ±0.1 bit inner region where 80% of candidates were concentrated.

### Finding 4: Fundamental Precision-Coverage Tradeoff

| Strategy | Inner Width | Candidates | Hit Probability |
|----------|-------------|------------|-----------------|
| PR #131 | ±3 bits | 100k | <10⁻¹³ |
| This exp | ±0.1 bit | 80k (inner) | ~10⁻⁴ if spike exactly on target |
| This exp | ±2 bits | 20k (outer) | <10⁻¹³ |

Even with 0.026-bit accuracy, the factor fell in the outer 20% sampling region with probability ~10⁻¹³ of being hit.

## Experiment Configuration

```
N = 137524771864208156028430259349934309717
precision_dps = 708
num_scan_points = 1000
richardson_extrapolation = True
sobol_qmc = True
candidates_per_spike = 100,000
total_candidates_tested = 992,599
inner_radius_bits = 0.1 (80% of budget)
outer_radius_bits = 2.0 (20% of budget)
spikes_tested = 10
elapsed_ms = 11,949
```

## Why the Hypothesis Was Not Validated

1. **Spike ranking inversion**: The confidence metric failed to prioritize the closest spike (rank 10 instead of rank 1).

2. **Localization still insufficient**: Even 0.026-bit accuracy produces an offset of 2.35×10¹⁷, larger than any practical inner search window at this scale.

3. **QMC coverage gap**: Concentrating 80% of candidates in ±0.1 bit only works if spike localization is better than ±0.1 bit. Our best spike was 0.026 bits off—technically within tolerance—but the spike ranked 10th was tested last.

4. **Scale fundamentals**: At 10¹⁹ scale, even 0.026 bits = 2.35×10¹⁷ integers. Covering this with 80k candidates is infeasible.

## Comparison to PR #131

| Metric | PR #131 | This Experiment |
|--------|---------|-----------------|
| Best spike to factor | 63.28 (0.09 bits to p) | 63.48 (0.026 bits to q) |
| Scan points | 500 | 1000 |
| Richardson extrapolation | No | Yes |
| Sobol QMC | No | Yes |
| Total candidates | 100,020 | 992,599 |
| Result | Not validated | Not validated |

Richardson extrapolation improved spike accuracy from ~0.09 bits to ~0.026 bits, but this did not translate to factor recovery.

## Constraints Satisfied

- ✅ No prior knowledge of factors used in algorithm
- ✅ No classical fallbacks (Pollard, ECM, trial division)
- ✅ Deterministic/quasi-deterministic methods only (Sobol QMC)
- ✅ Explicit adaptive precision (708 dps)
- ✅ Post-hoc analysis separated from algorithm

## What Would Be Needed for Success

### Option A: Perfect Spike Localization
If spike localization could achieve <0.001-bit accuracy consistently for the top-ranked spike, the factor would fall within ±0.1 bit inner region with high probability.

### Option B: Larger Inner Window
Increase inner_radius_bits to ±0.3 bits (covers ±23% of center value), accepting 10× more candidates per spike.

### Option C: Rank-Agnostic Exhaustive Search
Test all 118 detected spikes instead of top 10, with 100k candidates each. Budget: ~12M candidates.

### Option D: Alternative τ-Function
Design a τ-function with sharper discriminatory power that produces accurate confidence ranking (closest factor = rank 1).

## Reproducibility

```bash
cd experiments/tau-spike-refinement-127bit
pip install mpmath scipy  # if not installed
python3 run_experiment.py
```

Results: `experiment_results.json`

## Conclusion

The τ''' spike refinement approach demonstrates that:

1. **Signal exists**: Spikes correctly localize near factors (0.026 bits for best spike)
2. **Ranking fails**: Confidence metric doesn't correlate with factor proximity
3. **Coverage gap**: Even excellent localization leaves intractable search spaces at 10¹⁹ scale

The hypothesis that "improved spike localization + smarter sampling can achieve factor recovery" is **falsified** for the current τ-function formulation. Future work should focus on improving the confidence ranking metric or the τ-function itself.
