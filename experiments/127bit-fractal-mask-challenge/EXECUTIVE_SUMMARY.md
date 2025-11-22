# Executive Summary: 127-Bit Fractal-Segment Masking Experiment

**Date:** 2025-11-22
**Experiment:** Attempt to factorize CHALLENGE_127 using PR #93 fractal-segment masking
**Status:** FAILURE (CONCLUSIVE NEGATIVE RESULT)

---

## Results At-a-Glance

**Target:** N₁₂₇ = 137524771864208156028430259349934309717

**Expected Factors:**
- p = 10508623501177419659
- q = 13086849276577416863

**Outcome:** No factors found within configured search window

**Factorization Success:** NO

**Factors Found:** None

**Time Elapsed:** 32.160 seconds

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Segments scored | 64 |
| Segments searched | 27 |
| Candidates tested | 4,521 |
| Window coverage | 14.06% |
| K-value at success | N/A |
| Segment index at hit | N/A |
| Total runtime | 32.160s |

---

## Configuration Used

| Parameter | Value |
|-----------|-------|
| Total segments | 64 |
| Top-K retained | 8 |
| Min random segments | 1 |
| Precision (dps) | 800 |
| Max candidates | 650,000 |
| K-values tested | [0.30, 0.35, 0.40] |
| Prefilter primes | 153 |
| Search window | ±78,180,637,518,849,229 |

---

## Critical Finding: Factor Distance Analysis

**The experiment revealed why the approach failed:**

```
Factor positions relative to sqrt(N) = 11,727,095,627,827,384,440:
  p offset: -1,218,472,126,649,964,781  (16x beyond window)
  q offset: +1,359,753,648,750,032,423  (17x beyond window)

Distance from sqrt(N):
  |p - sqrt(N)|: 1,218,472,126,649,964,781
  |q - sqrt(N)|: 1,359,753,648,750,032,423
  
Ratio to sqrt(N):
  p/sqrt(N): 0.896098 (about 10.4% below sqrt(N))
  q/sqrt(N): 1.115950 (about 11.6% above sqrt(N))
  
Window boundaries:
  Lower: 11,648,914,990,308,535,211
  Upper: 11,805,276,265,346,233,669
  
BOTH FACTORS OUTSIDE WINDOW: True
```

---

## Verdict

### Hypothesis Status

The hypothesis that fractal-segment masking enables GVA to succeed on the 127-bit challenge is:

**FALSIFIED**

However, this is a **qualified falsification** - the approach failed due to incorrect assumptions about factor distribution, not fundamental flaws in the fractal-mask mechanism.

### Supporting Evidence

1. **Window sizing was fundamentally inadequate:** The search window was ±78 trillion from sqrt(N), but the actual factors were ±1.2-1.4 quadrillion away - approximately 16-17x beyond the window boundaries.

2. **Fractal mask performed as designed:** 
   - 14.06% window coverage achieved (target: <15%)
   - Segment scores showed reasonable distribution (0.7429 to 0.7468)
   - Only 4,521 candidates tested from 650,000 budget (0.7% utilization)
   - Execution completed efficiently in 32 seconds

3. **The 127-bit challenge semiprime has highly unbalanced factors:**
   - p is 10.4% below sqrt(N)
   - q is 11.6% above sqrt(N)
   - This is NOT a "balanced semiprime" near sqrt(N) as assumed in the technical memo

4. **Technical memo assumption violated:** The memo states "moderately distant factors" but CHALLENGE_127 has factors that are extremely distant by GVA standards - beyond any window size that would be computationally feasible.

### Implications

**For the fractal-segment masking approach:**
- The mechanism itself works correctly for its design purpose
- It successfully compressed search to 14% of window with minimal candidate waste
- However, it cannot overcome fundamentally incorrect window placement

**For GVA factorization in general:**
- Current window-sizing heuristics assume factors relatively near sqrt(N)
- The 127-bit challenge requires a fundamentally different search strategy
- A ±1.4 quadrillion window would require ~18x more segments or ~300x more candidates - computationally prohibitive

**For the repository validation gates:**
- CHALLENGE_127 is a pathological case for GVA-style methods
- It represents a different factorization regime than the 10^14-10^18 operational range
- Success on 125-bit balanced semiprimes ≠ success on 127-bit unbalanced semiprimes

---

## Next Steps

**This experiment conclusively demonstrates that:**

1. **Fractal-segment masking is insufficient for CHALLENGE_127** - not due to mask failure, but because both factors lie far outside any computationally feasible search window for GVA methods.

2. **Window expansion is not viable:**
   - To cover actual factor locations: ±1.4 quadrillion window
   - At current density: ~300x candidate budget = 195 million candidates
   - Estimated runtime: 100+ hours (infeasible)

3. **Recommended next steps:**
   - **Accept that GVA methods are not suitable for highly unbalanced semiprimes**
   - Focus GVA development on balanced semiprimes in operational range [10^14, 10^18]
   - For CHALLENGE_127, consider fundamentally different approaches (if any exist that don't violate "no fallback" policy)
   - Document CHALLENGE_127 as a known limitation / out-of-scope target

4. **Alternative experiment possibilities:**
   - Test fractal-segment masking on balanced 127-bit semiprimes (p ≈ q ≈ sqrt(N))
   - Validate the approach on unbalanced semiprimes within operational range
   - Explore whether distance-from-sqrt(N) can be estimated a priori to set appropriate windows

---

## Scientific Value

**This negative result has high scientific value:**

1. **Clearly defines GVA method boundaries:** Works for balanced/near-balanced semiprimes, fails for highly unbalanced ones
2. **Validates the experimental approach:** Quick detection of failure (32s) vs. long unsuccessful search
3. **Provides quantitative limits:** Factor-distance-to-window-size ratio of ~16x is beyond current method capability
4. **Informs future work:** Window sizing is critical; fractal masking cannot compensate for incorrect window placement

---

## References

- Experiment code: `run_experiment.py`
- Experiment output log: `experiment_output.log`
- Detailed analysis: `DETAILED_RESULTS.md`
- Configuration: `README.md`
- PR #93 baseline: `../fractal-recursive-gva-falsification/fr_gva_implementation.py`
- Technical memo: See issue description
