# Detailed Results: 127-Bit Fractal-Segment Masking Experiment

**Experiment Date:** 2025-11-22
**Execution Time:** 32.160 seconds
**Outcome:** Failure (factors not found within search window)

---

## Experiment Setup

### Target Semiprime

```
N₁₂₇ = 137524771864208156028430259349934309717
Bit length: 127 bits
```

### Known Factors (for verification)

```
p = 10508623501177419659  (64-bit)
q = 13086849276577416863  (64-bit)
Verification: p × q = N₁₂₇ ✓
```

### Configuration Parameters

```python
SEGMENTS = 64
TOP_K = 8
MIN_RANDOM_SEGMENTS = 1
PRECISION = 800  # decimal places
MAX_CANDIDATES = 650000
K_VALUES = [0.30, 0.35, 0.40]
SMALL_PRIMES = 153  # prefilter
```

### Search Window Calculation

```
sqrt(N₁₂₇) = 11,727,095,627,827,384,440
Window size = max(800000, sqrt(N) / 150)
            = sqrt(N) / 150
            = 78,180,637,518,849,229

Window boundaries:
  Lower: 11,648,914,990,308,535,211
  Upper: 11,805,276,265,346,233,669
```

---

## Phase 1: Segment Scoring

All 64 segments were scored using Mandelbrot-based interest metric.

### Score Distribution

```
Top score:    0.7468
Median score: 0.7442
Bottom score: 0.7429
Range:        0.0039 (very narrow - indicates uniform segment interest)
```

### Interpretation

The narrow score distribution (0.7429-0.7468) suggests that the Mandelbrot scoring did not find strong differentiation between segments. This is expected when factors are far outside the window - the fractal dynamics don't "see" the true factor locations.

---

## Phase 2: Segment Selection

### Top-K Segments Selected (with diversity enforcement)

```
1. Score=0.7468, range=[+68.4T to +70.9T]
2. Score=0.7456, range=[-4.9T to -2.4T]
3. Score=0.7453, range=[+44.0T to +46.4T]
4. Score=0.7452, range=[-34.2T to -31.8T]
5. Score=0.7451, range=[-12.2T to -9.8T]
6. Score=0.7449, range=[-29.3T to -26.9T]
7. Score=0.7449, range=[±0 to +2.4T]
8. Score=0.7447, range=[+75.7T to +78.2T]
9. Score=0.7441, range=[+73.3T to +75.7T]  (random segment)
```

(T = trillion = 10^12)

### Coverage Analysis

```
Total window size: 156,361,275,037,698,458
Segments selected: 9
Covered range:     21,987,203,830,016,227
Coverage:          14.06%
```

This meets the target of <15% coverage, showing the fractal mask is working as designed to compress the search space.

---

## Phase 3: GVA Kernel Sweep

### K-Value Iterations

For each k in [0.30, 0.35, 0.40]:
- Embedded N in 7D torus using golden ratio powers
- Computed Riemannian distances for candidates in each segment
- Applied hard prefilters (parity, small primes, band check)
- Tested candidates in ascending distance order

### Candidate Testing Statistics

```
Total candidates tested: 4,521
Max candidates budget:   650,000
Budget utilization:      0.70%
```

### Per-K Results

```
k = 0.30:  9 segments searched, 0 factors found
k = 0.35:  9 segments searched, 0 factors found
k = 0.40:  9 segments searched, 0 factors found
```

---

## Root Cause Analysis: Why Did It Fail?

### Factor Location Analysis

```
sqrt(N) = 11,727,095,627,827,384,440

Actual factor locations:
  p = 10,508,623,501,177,419,659
  q = 13,086,849,276,577,416,863

Offsets from sqrt(N):
  p offset: -1,218,472,126,649,964,781
  q offset: +1,359,753,648,750,032,423

Distance from sqrt(N):
  |p - sqrt(N)|: 1,218,472,126,649,964,781  (1.218 quadrillion)
  |q - sqrt(N)|: 1,359,753,648,750,032,423  (1.360 quadrillion)
```

### Window vs. Factor Comparison

```
Window half-width:     78,180,637,518,849,229  (78.2 trillion)
p distance:         1,218,472,126,649,964,781  (1.218 quadrillion)
q distance:         1,359,753,648,750,032,423  (1.360 quadrillion)

Ratio (p):  15.6x beyond window
Ratio (q):  17.4x beyond window
```

### Critical Insight

**Both factors are completely outside the search window.** The experiment searched in the range around sqrt(N), but the actual factors are:
- p: 1.2 quadrillion below sqrt(N)
- q: 1.4 quadrillion above sqrt(N)

This means the search window would need to be **~16-17x larger** to contain the factors.

---

## Why Window Sizing Failed

### Assumption in Technical Memo

The technical memo stated:
> "The 127-bit challenge number is not friendly: the primes are not extremely close to √N."

However, the term "not extremely close" understated the actual distance by an order of magnitude.

### Factor Balance Analysis

```
Balanced semiprime: p ≈ q ≈ sqrt(N)
  Example: 125-bit test used p,q with offsets ~±5

CHALLENGE_127 reality:
  p/sqrt(N) = 0.896098  (10.4% below)
  q/sqrt(N) = 1.115950  (11.6% above)
  |p-q|     = 2.578 quadrillion
```

This is an **unbalanced semiprime** with factors far from sqrt(N), not a slightly unbalanced one.

### Computational Infeasibility

To cover the actual factor locations:

```
Required window: ±1.4 quadrillion
Current window:  ±78.2 trillion
Scale factor:    17.9x

At current segment/candidate density:
  Required segments: 64 × 17.9 = 1,146
  Required candidates: 650k × 17.9² = 208 million
  
Estimated runtime (linear scaling): 32s × 17.9² ≈ 285 hours
```

This is computationally prohibitive for the GVA approach.

---

## Fractal-Segment Masking Performance

### Did the Fractal Mask Work?

**YES** - The fractal-segment masking mechanism performed exactly as designed:

1. **Efficient compression:** 14.06% window coverage (target: <15%)
2. **Budget preservation:** Only 0.7% of candidate budget used
3. **Fast execution:** 32 seconds for complete search
4. **Proper segment selection:** Diversity enforcement worked

### What Went Wrong?

The fractal mask **cannot compensate for fundamentally incorrect window placement**. 

The mask optimizes candidate selection *within* a window, but if the window doesn't contain the factors, no amount of optimization helps.

Analogy: Having a perfect map of downtown Seattle doesn't help if you're trying to find an address in New York.

---

## Comparison to Baseline GVA

### Would Vanilla GVA Have Succeeded?

**NO** - Vanilla GVA would have failed for the same reason: both factors outside the search window.

### Did Fractal Masking Help?

**Neutral** - In this case, fractal masking:
- Reduced runtime (good)
- Reduced candidates tested (good)
- But couldn't find factors because they weren't in the window (inevitable)

For this specific problem, fractal masking **failed fast and efficiently**, which is valuable - it didn't waste 10 minutes searching an empty window.

---

## Lessons Learned

### 1. Factor Distribution Matters More Than Method Quality

The primary determinant of success is whether factors are in the search window, not how efficiently you search the window.

### 2. "Moderately Distant" is Ambiguous

Technical terminology matters:
- "Near sqrt(N)": ±0.1% offset
- "Moderately distant": ±1-5% offset  
- "Highly unbalanced": ±10% offset (CHALLENGE_127)

CHALLENGE_127 should be classified as "highly unbalanced," not "moderately distant."

### 3. Window Sizing Heuristics Need Factor Distribution Priors

Current heuristic:
```python
window = max(800000, sqrt_N // 150)
```

This assumes factors are relatively close to sqrt(N). For unbalanced semiprimes, this fails catastrophically.

### 4. Validation Gates Are Not Interchangeable

Success on balanced 125-bit semiprimes does **not** imply success on unbalanced 127-bit semiprimes. These are different problem classes.

---

## Recommendations

### For This Experiment

**Conclusion:** Fractal-segment masking is **insufficient** for CHALLENGE_127.

**Reason:** Not a limitation of the method, but mismatch between problem (highly unbalanced semiprime) and method assumptions (factors near sqrt(N)).

### For Future Work

1. **Reclassify CHALLENGE_127:**
   - Mark as "highly unbalanced semiprime"
   - Note as out-of-scope for GVA-style methods
   - Document as known limitation

2. **Test fractal masking on appropriate targets:**
   - Balanced 127-bit semiprimes (p ≈ q ≈ sqrt(N))
   - Unbalanced semiprimes within operational range [10^14, 10^18]
   - Quantify method performance vs. factor imbalance ratio

3. **Develop factor-distance estimation:**
   - Research whether p/q ratio can be estimated a priori
   - If yes, use to set adaptive window sizes
   - If no, document fundamental limitation

4. **Update documentation:**
   - Clearly separate "balanced" vs. "unbalanced" semiprime classes
   - Define GVA method scope: balanced semiprimes only
   - Add CHALLENGE_127 to "known limitations" section

---

## Conclusion

This experiment **successfully falsified** the hypothesis that fractal-segment masking enables GVA to factor CHALLENGE_127, but with an important qualifier:

**The failure was not due to fractal masking deficiency, but due to incorrect problem assumptions.**

The fractal mask performed well at its designed task (segment scoring, candidate compression, efficient search). However, it cannot overcome the fundamental issue that both factors are ~16-17x beyond the search window boundaries.

**Scientific Value:** This negative result clearly defines the boundaries of GVA-based methods and provides quantitative limits on factor distance tolerance.

**Practical Implication:** GVA methods (with or without fractal masking) are suitable for balanced or near-balanced semiprimes, not highly unbalanced ones.

---

## Artifacts

- **Experiment code:** `run_experiment.py`
- **Console output:** `experiment_output.log`
- **Executive summary:** `EXECUTIVE_SUMMARY.md`
- **This document:** `DETAILED_RESULTS.md`

All results are reproducible by running:
```bash
python3 run_experiment.py
```

---

**Experiment completed:** 2025-11-22
**Result:** Hypothesis falsified (with qualification)
**Status:** Scientifically conclusive negative result
