# **HYPOTHESIS FALSIFIED**: GVA-τ''' Hybrid Cannot Recover 127-bit Factors

## Verdict

**HYPOTHESIS FALSIFIED** — The GVA-τ''' hybrid method fails to rank factor-proximate spikes highly enough to recover factors within budget.

## Key Results

| Metric | Value |
|--------|-------|
| **Success** | ❌ No factors found |
| **Best spike proximity to q** | 0.000003 bits |
| **Best spike rank** | 46,013 / 50,000 |
| **PR #132 baseline rank** | 10th |
| **Ranking improvement** | ❌ WORSE (46,013 vs 10) |
| **Total runtime** | 60.05s |

## What Happened

1. **Spike Detection Works**: The experiment found a spike within 0.000003 bits of the actual factor q ≈ 2^63.505
2. **Ranking Fails**: This excellent spike ranked 46,013th out of 50,000 candidates
3. **New Score Formula Backfired**: The Score = error⁻¹ · log(|τ'''|) formula performed *worse* than the original |τ'''|/error metric

## Top 10 Ranked Spikes

| Rank | Bit Position | Combined Score | Bit Error from q |
|------|-------------|----------------|------------------|
| 1 | 63.647 | 252.31 | 0.142 |
| 2 | 63.535 | 242.70 | 0.030 |
| 3 | 63.439 | 203.82 | 0.066 |
| 4 | 63.586 | 160.65 | 0.081 |
| 5 | 63.482 | 145.29 | 0.023 |
| 6 | 63.616 | 105.59 | 0.111 |
| 7 | 63.576 | 85.24 | 0.071 |
| 8 | 63.314 | 51.91 | 0.191 |
| 9 | 63.588 | 47.21 | 0.084 |
| 10 | 63.333 | 40.69 | 0.172 |

**Note**: The 2nd-ranked spike (b=63.535, 0.030 bit error) was reasonably close, but still not the factor.

## Root Cause Analysis

### Why New Ranking Failed

The hypothesis that `Score = error⁻¹ · log(|τ'''|)` would fix the inverse correlation between confidence and factor proximity was **incorrect**.

**Finding**: The log scaling actually made ranking worse because:
1. Large τ''' values near discontinuities dominate even with log scaling
2. The error estimate from Richardson extrapolation is not correlated with factor proximity
3. GVA geodesic contribution (α=0.1) was too weak to influence ranking

### GVA Geodesic Distance Not Helpful

The 7D torus geodesic distances showed no correlation with factor proximity at this scale. This confirms previous root-cause analysis findings that GVA methods do not scale beyond ~40 bits.

## Experimental Parameters

| Parameter | Value |
|-----------|-------|
| N | 137524771864208156028430259349934309717 |
| Bit length | 127 |
| Precision | 708 dps (708 dps logged, 100 dps working) |
| Bit scan range | [63.30, 63.70] |
| QMC samples | 50,000 |
| k values | [0.30, 0.35, 0.40] |
| h step | 0.001 |
| Seed | 42 |

## Conclusions

1. **τ''' spike detection** achieves excellent bit-level accuracy (0.000003 bits)
2. **Spike ranking** remains the fundamental problem — no combination of error weighting and log scaling recovers correct ranking
3. **GVA geodesic guidance** provides no benefit at 127-bit scale
4. **Alternative ranking methods** needed — current mathematical formulations all fail

## Implications

This falsification experiment demonstrates that:

- **Geometric signal alone is insufficient**: Even with 7D torus embedding and τ''' analysis, the ranking metric fails
- **The PR #132 failure mode persists**: Best-proximity spikes rank poorly regardless of scoring formula
- **New approaches needed**: Further refinement of spike ranking within this framework is unlikely to succeed

## Reproducibility

```bash
cd experiments/gva-tau-hybrid-127bit
python3 run_experiment.py
```

Results saved to `results.json` with complete phase timings, spike data, and metadata.

---

*Experiment conducted: 2025-11-25T16:18:00.865092*
*Status: FALSIFIED*
