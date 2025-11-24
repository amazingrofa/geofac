# Technical Brief: Geometric Resonance Factorization Non-Convergence Issue

## Project Overview

This project implements a deterministic factorization algorithm using geometric resonance, specifically Dirichlet kernel filtering with golden-ratio QMC sampling and phase-corrected snap heuristics. It targets semiprime factorization without classical fallbacks like Pollard’s Rho or ECM.

- **Repository**: https://github.com/zfifteen/geofac
- **Primary Target**: 127-bit challenge semiprime N = 137524771864208156028430259349934309717
- **Tech Stack**: Java, Spring Boot, BigDecimal for high-precision arithmetic, ch.obermuhlner.math.big for extended math functions.

## Problem Statement

After fixing a double-2π bug in the SnapKernel (which caused invalid p0 values), the algorithm now generates valid factor candidates (~√N for m=0); however, this only resolves the p0 validity issue. The algorithm still fails to converge to the correct factors within the configured computational budget. The issue persists despite extended timeouts and increased samples, suggesting the geometric resonance approach needs refinement beyond the bug fix.

- **Symptoms**: High amplitude peaks detected, but snap projections yield invalid p0 (0 or >> N) before the fix; now valid but no divisibility lock.
- **Hypothesis**: Insufficient computational budget or fundamental flaw in the resonance model/sampling strategy.

## Current Implementation

### Core Algorithm Flow
1. **Initialization**: Compute ln(N), pi, twoPi, phiInv (golden ratio inverse).
2. **Sampling Loop**: For each sample (up to 20,000):
   - Update golden ratio sequence u.
   - Compute k = kLo + (kHi - kLo) * u.
   - For each dm in [-mSpan, mSpan]:
     - theta = twoPi * m / k (where m = m0 + dm, m0=0).
     - Amplitude = DirichletKernel.normalizedAmplitude(theta, J).
      - If amplitude > threshold: p0 = SnapKernel.phaseCorrectedSnap(lnN, theta).
     - Guard: reject p0 <=1 or p0 >=N.
     - Test p0 and neighbors (±1) for divisibility.
3. **Termination**: On success, return factors; else timeout.

### Key Components
- **DirichletKernel**: Computes normalized amplitude for filtering resonant peaks.
- **SnapKernel**: Phase-corrected snap: p̂ = exp((ln(N) - theta)/2), rounded to nearest integer.
- **FactorizerService**: Orchestrates search with diagnostics (amplitude distribution, candidate logs).

## Key Files and Code Snippets

### SnapKernel.java (Fixed)
```java
public static BigInteger phaseCorrectedSnap(BigDecimal lnN, BigDecimal theta, MathContext mc) {
    BigDecimal expo = lnN.subtract(theta, mc).divide(BigDecimal.valueOf(2), mc);
    BigDecimal pHat = BigDecimalMath.exp(expo, mc);
    BigDecimal correctedPHat = applyPhaseCorrection(pHat, mc);
    return roundToBigInteger(correctedPHat, mc.getRoundingMode(), mc);
}
```
- **Fix**: Removed extra 2π multiplication; theta already includes 2π*m/k.

### FactorizerService.java (Search Logic)
```java
BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);
BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, config.J(), mc);
if (amplitude.compareTo(BigDecimal.valueOf(config.threshold())) > 0) {
    BigInteger p0 = SnapKernel.phaseCorrectedSnap(lnN, theta, mc);
    // Guards and testing...
}
```

### factor_one.sh (Test Script)
```bash
java -Dgeofac.precision=708 -Dgeofac.samples=20000 -Dgeofac.m-span=200 -Dgeofac.j=8 -Dgeofac.threshold=0.85 -Dgeofac.k-lo=0.15 -Dgeofac.k-hi=0.65 -Dgeofac.search-timeout-ms=300000 -jar build/libs/geofac-0.1.0-SNAPSHOT.jar factor $TARGET_N
```

## Parameters and Computational Budget
- **Precision**: 708 decimal digits (adaptive: max(configured, N.bitLength()*4 + 200)).
- **Samples**: 20,000 (golden-ratio QMC).
- **m-span**: 200 (search range around m0=0).
- **J**: 8 (Dirichlet kernel parameter).
- **Threshold**: 0.85 (amplitude filter).
- **k-lo/hi**: 0.15/0.65 (fractional exponent range).
- **Timeout**: 300,000 ms (5 min).
- **Diagnostics**: Enabled; logs amplitudes, candidates, failures.

## Diagnostics and Logs
- **Amplitude Distribution**: Mean ~0.127, max=1.0; healthy but many rejections.
- **Candidate Failures**: Primarily snap projection issues (pre-fix: ZERO/OVERFLOW; post-fix: NOT_DIVISIBLE).
- **Sample Processing**: Often <20,000 before timeout; e.g., 141 samples in 90s with old budget.
- **Artifacts**: results/single_run_YYYYMMDD-HHMMSS/ (run.log, factorization.json if success).

## Validation Gates
- **Gate 1**: 30-bit quick sanity check (N=1,073,217,479 = 32,749 × 32,771)
- **Gate 2**: 60-bit scaling validation (N=1,152,921,470,247,108,503 = 1,073,741,789 × 1,073,741,827)
- **Gate 3**: 127-bit challenge verification (no fast-path)
- **Gate 4**: 10^14–10^18 operational range for broader claims
- **Constraints**: Deterministic methods only; no stochastic retries; log precision/reproducibility.

See docs/VALIDATION_GATES.md for complete gate specifications and canonical parameters.

## How to Run and Test
1. **Build**: `./gradlew clean build -x test`
2. **Run**: `./scripts/factor_one.sh` (produces per-run artifacts).
3. **Verify Success**: Check for "SUCCESS" in output, p*q == N.
4. **Reproduce**: Use exact parameters; seed golden ratio at u=0.

## Expected Outcome
- **Success**: Discover p,q for N=137524771864208156028430259349934309717 via geometric resonance only.
- **Metrics**: Runtime <5 min, samples processed ~20,000, valid candidates >1% of total.
- **Artifacts**: factorization.json with status=SUCCESS, p, q, diagnostics.

## Independent Fix Approach
- Analyze diagnostics for amplitude/candidate patterns.
- Refine snap heuristic (e.g., multi-snap quorum, slope-aware rounding).
- Tune parameters (k-range, threshold) or increase budget selectively.
- Ensure changes preserve determinism and validation gates.
- Test on N; commit minimal diffs with reproducibility logs.
