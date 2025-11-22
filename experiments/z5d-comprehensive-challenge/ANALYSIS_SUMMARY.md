# Z5D Comprehensive Challenge: Executive Summary

======================================================================


## Result: ✗ FAILURE


## Challenge
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863
- Bit-length: 127

## Parameters
- Total budget: 17,560
- δ_max: 38,418
- Bands: 10
- k-value: 0.35
- ε: 0.7433

## Execution
- Candidates tested: 4,388
- Time elapsed: 14.96s
- Rate: 293 candidates/sec

## Band Coverage Analysis
- δ-range covered: [4,373, 17,503]
- δ_p (true): -1,218,472,126,649,964,781
- δ_q (true): 1,359,753,648,750,032,423
- p in range: False
- q in range: False
- Bands covered: 4 / 10

## Diagnosis
- Failure mode: **BAND_MISS**
- Factors were outside searched δ-range
- Recommendation: Increase δ_max or adjust ε parameter

## Key Findings

1. **Z5D Oracle Performance**
   - The PNT-based Z5D approximation provided band estimates
   - Band coverage: 4 bands explored

2. **Pipeline Efficiency**
   - 210-wheel filter: 77% pruning rate
   - Z5D adaptive stepping: variable step sizes by density
   - FR-GVA ranking: geodesic distance scoring

3. **Scale Challenge**
   - 127-bit challenge represents ~10^38 search space
   - Factors near √N ≈ 1.17×10^19
   - Expected gap: ~44 units
