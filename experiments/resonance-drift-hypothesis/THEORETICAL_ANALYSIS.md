# Theoretical Analysis: Resonance Drift Hypothesis

## The Claim

From the problem statement:
> "If the 'Geometric Resonance' theory holds, the resonance frequency (k) should not be random. It should scale logarithmically or geometrically with the modulus N."

Proposed formula: **k_opt = k_base × (ln(N) / ln(N_base))^S**

Where:
- k_opt: predicted optimal k for target N
- k_base: calibrated k from smaller successful factorization
- S: scaling exponent (the "Z-correction factor")
- N_base: baseline semiprime where k_base was determined

## Evaluation Framework

### Test 1: Dimensional Analysis

**Question**: Is the scaling formula dimensionally consistent?

k is dimensionless (fractional parameter in [0, 1])
ln(N) has units of "nats" (natural log units)
ln(N)/ln(N_base) is dimensionless ratio

**Result**: ✓ Dimensionally consistent

### Test 2: Boundary Behavior

**Question**: What happens at extremes?

- When N = N_base: k_opt = k_base × (1)^S = k_base ✓
- When N → ∞: k_opt → ∞ if S > 0 ✗
- When N → 0: k_opt → 0 if S > 0 ✗

**Result**: ✗ Formula unbounded - violates k ∈ [0, 1] constraint

### Test 3: Physical Interpretation

**Question**: Does k have a resonance interpretation?

From FactorizerService.java:
```java
BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);
```

k appears in denominator of angular parameter θ = 2πm/k.

Physical analogy: k ~ wavelength or period of resonance pattern
- Smaller k → longer wavelength → coarser resonance structure
- Larger k → shorter wavelength → finer resonance structure

**Expectation**: Larger N (more bits) might require finer resolution (larger k)?

**Result**: ⚠️ Plausible but requires empirical validation

### Test 4: Alternative Model

**Question**: Could k be constant (null hypothesis)?

Null hypothesis: k_opt is independent of N, optimal window is fixed [0.25, 0.45]

Evidence supporting null:
- Dirichlet kernel filtering adapts to N via lnN computation
- Snap epsilon scales with precision (which scales with bitLength)
- QMC sampling is scale-invariant by construction

Evidence against null:
- No systematic validation across operational range
- Gate 3 (127-bit) failures suggest parameter mismatch
- Current k-window chosen empirically, not theoretically

**Result**: ⚠️ Both hypotheses lack empirical validation

## Critical Missing Data

To distinguish between drift hypothesis and null hypothesis, need:

1. **k-success values from multiple scales**
   - Minimum 5-10 data points from 30-bit to 60-bit range
   - Each with: (N, ln(N), bitLength, k_optimal)

2. **Variance quantification**
   - Is k_optimal tightly clustered or widely distributed?
   - Does variance increase or decrease with N?

3. **Threshold behavior**
   - How does amplitude threshold (0.92) interact with k choice?
   - Is threshold scale-dependent?

## Synthetic Validation Attempt

**Approach**: Can we infer k scaling from code structure?

From search loop:
```java
BigDecimal k = BigDecimal.valueOf(config.kLo())
               .add(kWidth.multiply(u, mc), mc);
BigInteger m0 = BigInteger.ZERO;
BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);
```

For balanced semiprime: m ≈ 0, so θ ≈ 0.
Dirichlet kernel peaks near θ = 0 (constructive interference).

**Key insight**: k determines spacing of resonance peaks in m-space.
- θ = 2πm/k → peaks occur when θ = 2πn (n integer)
- Peak spacing: Δm = k

Larger k → wider m-spacing → fewer candidates tested per k-sample.
Smaller k → tighter m-spacing → more candidates per k-sample.

**Implication**: Optimal k might depend on:
- Search radius (currently dynamic based on N)
- m-span (currently fixed at 180)
- Threshold sensitivity (how many false positives to tolerate)

**Result**: ⚠️ Relationship unclear without experiments

## Falsification Criteria

The hypothesis WOULD BE FALSIFIED if:

1. **No correlation found**: Regression R² < 0.3 for all models
2. **Wrong direction**: Best-fit slope is negative (k decreases as N increases)
3. **Constant k wins**: Variance in k-success across scales is negligible (σ/μ < 0.05)
4. **127-bit prediction fails**: Predicted k-window yields worse results than baseline

The hypothesis WOULD BE SUPPORTED if:

1. **Strong correlation**: R² > 0.7 for k vs ln(N) or k vs bitLength
2. **Predictive power**: 127-bit factorization succeeds with predicted k-window
3. **Systematic trend**: k_optimal increases monotonically with N
4. **Reduced search time**: Narrow k-window based on prediction outperforms wide baseline

## Current Status: Untestable

**Barrier 1**: No historical k-success data
- Gate 1/2 use fast-path (no search performed)
- No logs from operational range successes
- No instrumentation to capture k when factors found

**Barrier 2**: Computational cost prohibitive
- Operational range factorization attempts exceed 5+ minutes
- Need 10-20 successful runs across scales
- Total runtime: 50-100 minutes minimum

**Barrier 3**: Validation gate restrictions
- Custom config only accepts Gate 3 or Gate 4 range
- Cannot use Gates 1-2 for k-window experiments
- Cannot easily generate new calibration semiprimes

## Conclusion

**The resonance drift hypothesis cannot be falsified with available data and infrastructure.**

The experimental framework (ResonanceDriftExperiment.java, regression_analysis.py) is sound, but:
- Data collection requires instrumentation changes (log k-success values)
- Empirical validation requires long-duration runs (hours, not minutes)
- Current validation gates prevent historical analysis of known successes

**Recommendation**: If this hypothesis is important, invest in:
1. Persistent k-logging in FactorizerService
2. Overnight validation runs on operational range
3. Dedicated parameter sweep infrastructure
4. Relaxed validation gates for research mode

Otherwise, proceed with current static k-window [0.25, 0.45] and acknowledge it as an **unvalidated assumption**.
