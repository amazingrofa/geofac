# GVA Curvature Validation 2025 — Detailed Results

**Experiment Date:** November 22, 2025  
**Timestamp:** 2025-11-22T20:02:55+00:00  
**Runtime:** 76.66 seconds

## Hypothesis

"Second-order differences of amplitude (curvature/discrete Laplacian) carry a usable gradient for factor localization where raw amplitude does not."

## Methodology

### Target Semiprime
```
N = 137524771864208156028430259349934309717
  = 10508623501177419659 × 13086849276577416863
  = p × q

Bit length: 127 bits
√N = 11,727,095,627,827,384,320
```

### Factor Positions (as offsets from √N)
```
p offset: -1,218,472,126,649,964,661  (negative, outside Shell S₅)
q offset: +1,359,753,648,750,032,543  (positive, beyond Shell S₅)
```

### Shell Geometry
```
Shell S₅: [√N + R₅, √N + R₆]

R₅ offset = 867,036,556,394,714,496   ≈ 8.67×10¹⁴
R₆ offset = 1,402,894,617,735,313,152 ≈ 1.40×10¹⁵

Absolute range: [12,594,132,184,222,098,816, 13,129,990,245,562,697,472]
Shell width: 535,858,061,340,598,656 ≈ 5.36×10¹⁷
```

**Critical observation:** Both factors lie outside the sampled shell:
- p is 1.22×10¹⁸ below √N (Shell S₅ is above √N)
- q is 1.36×10¹⁸ above √N (Shell S₅ only extends to 1.40×10¹⁵)

### GVA Embedding Parameters
```
Dimensions: 7D torus [0,1)⁷
Embedding: Golden ratio geodesic
  φ = (1 + √5) / 2 ≈ 1.618033988749895
  
For each dimension d ∈ {0..6}:
  coord[d] = (n × φ^(d+1))^k mod 1

K-values tested: [0.30, 0.35, 0.40]
```

### Distance Metric
```
Riemannian geodesic distance on flat torus:
  d(p, q) = √(Σ min(|p[i]-q[i]|, 1-|p[i]-q[i]|)²)

Torus wrapping accounts for periodic boundary conditions.
```

### Amplitude and Curvature
```
Amplitude A(c) = 1 / (1 + distance(N, c))

Curvature curv(c) = (A(c+h) - 2·A(c) + A(c-h)) / h²

This is the discrete Laplacian (second-order central difference).
High |curv(c)| indicates rapid change in local gradient.
```

### Sampling Strategy
```
Target samples per k: 5,000
Actual samples per k: 2,500 (only odd candidates for odd N)

Stride: width / target = 107,171,612,268,119 ≈ 1.07×10¹⁴
Curvature h: stride / 10 = 10,717,161,226,811 ≈ 1.07×10¹³

Sampling rate: ~98 candidates/second
```

### Precision
```
Adaptive precision: max(50, N.bitLength() × 4 + 200)
For 127-bit N: 127 × 4 + 200 = 708 dps

mpmath configuration: mp.workdps(708)
All arithmetic performed at 708 decimal places precision.
```

## Results

### k = 0.30

#### Distribution Statistics
```
Samples collected: 2,500

Curvature:
  Range: [-6.22×10⁻²⁷, +3.85×10⁻²⁷]
  Span:  1.01×10⁻²⁶
  Mean:  -6.00×10⁻²⁹
  Std:   1.77×10⁻²⁷
  CV:    2950%

Amplitude:
  Range: [0.4838, 0.9995]
  Span:  0.5157
  Mean:  0.6244
  Std:   0.0710
  CV:    11.4%
```

#### Peak Analysis (Top 100 by |curvature|)
```
Null model (uniform distribution):
  Expected mean distance to nearest factor: 1.07×10¹⁷

Observed (top 100 curvature peaks):
  Mean distance:   2.26×10¹⁷
  Median distance: 2.06×10¹⁷

Distance ratios:
  Mean ratio:   2.108  [No clustering—anti-clustering]
  Median ratio: 1.920  [No clustering—anti-clustering]

Proximity counts:
  Peaks within 10¹³: 0
  Peaks within 10¹⁴: 0
  Peaks within 10¹⁵: 0
```

**Verdict:** ✗ HYPOTHESIS NOT SUPPORTED

### k = 0.35

#### Distribution Statistics
```
Samples collected: 2,500

Curvature:
  Range: [-6.62×10⁻²⁷, +4.04×10⁻²⁷]
  Span:  1.07×10⁻²⁶
  Mean:  -6.00×10⁻²⁹
  Std:   1.77×10⁻²⁷
  CV:    2959%

Amplitude:
  Range: [0.4857, 0.9993]
  Span:  0.5136
  Mean:  0.6246
  Std:   0.0738
  CV:    11.8%
```

#### Peak Analysis (Top 100 by |curvature|)
```
Null model: 1.07×10¹⁷

Observed:
  Mean distance:   2.26×10¹⁷
  Median distance: 2.06×10¹⁷

Distance ratios:
  Mean ratio:   2.108
  Median ratio: 1.920

Proximity counts:
  Peaks within 10¹³: 0
  Peaks within 10¹⁴: 0
  Peaks within 10¹⁵: 0
```

**Verdict:** ✗ HYPOTHESIS NOT SUPPORTED

### k = 0.40

#### Distribution Statistics
```
Samples collected: 2,500

Curvature:
  Range: [-6.95×10⁻²⁷, +4.19×10⁻²⁷]
  Span:  1.11×10⁻²⁶
  Mean:  -6.00×10⁻²⁹
  Std:   1.77×10⁻²⁷
  CV:    2955%

Amplitude:
  Range: [0.4928, 0.9989]
  Span:  0.5061
  Mean:  0.6250
  Std:   0.0749
  CV:    12.0%
```

#### Peak Analysis (Top 100 by |curvature|)
```
Null model: 1.07×10¹⁷

Observed:
  Mean distance:   2.26×10¹⁷
  Median distance: 2.06×10¹⁷

Distance ratios:
  Mean ratio:   2.108
  Median ratio: 1.920

Proximity counts:
  Peaks within 10¹³: 0
  Peaks within 10¹⁴: 0
  Peaks within 10¹⁵: 0
```

**Verdict:** ✗ HYPOTHESIS NOT SUPPORTED

## Analysis

### Signal Characteristics

1. **Amplitude is relatively flat:**
   - CV ≈ 12% across all k-values
   - Range spans ~0.5 units from ~0.49 to ~1.00
   - Consistent with prior findings (shell-geometry-scan-01)

2. **Curvature shows high relative variation:**
   - CV ≈ 2950% (massive relative variation)
   - But absolute scale is tiny: 10⁻²⁶ to 10⁻²⁷
   - Mean near zero, suggesting oscillation around flat baseline

3. **Curvature variation is uninformative:**
   - High variation does not correlate with factor proximity
   - Top peaks distributed uniformly or worse
   - No spatial clustering detected

### Null Model Comparison

The null model assumes **uniform random distribution** over shell width W with 2 point targets:
```
E[distance to nearest target] ≈ W / 5 = 5.36×10¹⁷ / 5 = 1.07×10¹⁷
```

**All k-values show distance ratio > 1.9**, meaning observed mean distances are nearly **double** the null expectation. This indicates:
- No clustering around factors
- Possibly anti-clustering (peaks avoid factors)
- Or simply: curvature peaks are unrelated to factorization structure

### Why the hypothesis failed

#### Geographic mismatch
The shell S₅ samples the range [√N + 8.67×10¹⁴, √N + 1.40×10¹⁵], but:
- Factor p is at √N - 1.22×10¹⁸ (far below, negative side)
- Factor q is at √N + 1.36×10¹⁸ (far above, beyond R₆)

**Neither factor is in or near the sampled region.**

Even with torus periodicity, the distance to factors is:
- To p: >10¹⁸ (order of magnitude of N itself)
- To q: ~10¹⁸ (order of magnitude of N)

The embedding may create some periodic structure, but if curvature were a useful gradient, we'd expect:
- Some directional bias in peak distribution
- At minimum, distance ratio < 1.0
- Ideally, distance ratio < 0.5

**None of these conditions are met.**

#### Signal weakness
Even if factors were "visible" through torus wrapping:
- Curvature magnitude is 10⁻²⁶ to 10⁻²⁷
- This is ~10 orders of magnitude smaller than amplitude (~1)
- Noise and numerical precision may dominate at this scale

#### Structural interpretation
Curvature measures **local concavity** of the amplitude surface. For curvature to guide factor search:
- Amplitude must have non-flat structure (it does, slightly)
- Curvature peaks must spatially correlate with factors (they don't)
- The correlation must be stronger than random (it's worse than random)

**The data shows curvature is not a useful localization signal.**

## Comparison to Prior Experiments

| Experiment | Metric | Shell | Result | Distance Ratio |
|------------|--------|-------|--------|----------------|
| shell-geometry-scan-01 | Raw amplitude | S₅ | Flat, no peaks | N/A |
| gva-curvature-falsification | Curvature | S₅ | Variation but no analysis | N/A |
| **This experiment** | **Curvature + null model** | **S₅** | **Anti-clustering** | **2.1** |

Previous work established that S₅ amplitude is flat. This experiment confirms:
1. Curvature varies (not constant like amplitude)
2. Variation is not informative for factorization
3. Peaks are uniformly distributed, not clustered near factors

## Computational Notes

### Performance
```
Total runtime: 76.66 seconds
Samples computed: 7,500 (2,500 per k × 3 k-values)
Rate: ~98 samples/second

Curvature computation requires 3 amplitude evaluations per sample:
  - A(c-h), A(c), A(c+h)
  
Effective rate: ~33 curvature samples/second
```

### Precision Impact
With 708 dps:
- Curvature values are numerically stable at 10⁻²⁶ scale
- No underflow or precision loss detected
- Results reproducible to full precision

### Memory
```
Peak tracking: 100 peaks × 3 k-values = 300 peak records
Each record: ~200 bytes
Total peak memory: ~60 KB (negligible)
```

## Validation

### Gates Satisfied
✓ **Gate 1:** CHALLENGE_127 used as primary target  
✓ **Gate 4:** All measurements in [10¹⁴, 10¹⁸] range  
✓ **No classical fallbacks:** Pure geometric resonance method  
✓ **Deterministic:** Fixed seeds (implicit in stride-based sampling)  
✓ **Explicit precision:** 708 dps declared and used

### Reproducibility
```bash
cd experiments/gva-curvature-validation-2025
python3 run_experiment.py
```

Output includes:
- `results.json` — Full data (7,500 samples, 300 peaks)
- Console output — Summary statistics
- This document — Detailed analysis

## Conclusion

**Hypothesis falsified.** Second-order differences (curvature) of GVA amplitude do not provide a usable gradient for factor localization in Shell S₅ for CHALLENGE_127.

**Evidence:**
1. Distance ratios > 1.9 for all k-values (worse than uniform random)
2. Zero peaks within 10¹⁵ of either factor
3. No spatial correlation between curvature and factor locations
4. Consistent failure across all three k-values tested

**Implications:**
- Curvature-based localization is not viable for this geometry
- Shell S₅ may be inappropriate (factors not present in shell)
- Alternative signal processing methods needed
- Consider shells that contain the factors (S₀ or negative shells)

## Raw Data

Full results available in `results.json` with structure:
```json
{
  "experiment": "gva-curvature-validation-2025",
  "N": 137524771864208156028430259349934309717,
  "per_k_metrics": [
    {
      "k": 0.30,
      "samples_collected": 2500,
      "curvature_values": [...],  // 2500 values
      "amplitude_values": [...],   // 2500 values
      "candidates": [...],         // 2500 candidates
      "peak_locations": [...]      // Top 100 peaks with distances
    },
    // ... k=0.35, k=0.40
  ]
}
```

Each peak record includes:
- `candidate`: absolute value
- `delta`: offset from √N
- `curvature`: signed curvature value
- `abs_curvature`: |curvature| (ranking metric)
- `amplitude`: GVA amplitude at candidate
- `distance_to_nearest_factor`: min(|delta - p_offset|, |delta - q_offset|)
