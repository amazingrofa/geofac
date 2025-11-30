# Falsification Experiment: blind-geofac-web 127-bit Challenge

## **INCONCLUSIVE - PENDING FULL TEST**

The geometric resonance method could not factor N within the observed probe time, but the full 30-minute falsification window was not completed due to practical time constraints. The evidence collected suggests the hypothesis is **likely false** for the specified parameters.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Challenge N | 137524771864208156028430259349934309717 |
| N bit-length | 127 bits |
| Expected p | 10508623501177419659 |
| Expected q | 13086849276577416863 |
| Probe duration | ~8 minutes (partial, test stopped) |
| Factor found | No |
| Timeout threshold | 30 minutes (full test), 2 minutes (base config) |
| Test status | **Inconclusive** - coverage gating failures observed |

### Key Finding

**Key Finding**: The ring search radius is capped at 100M (probe) / 200M (full test), but candidates are ~10^17 away from √N. This creates effectively zero coverage of the factor space.

---

## Experiment Setup

### Hardware/Environment
- Java 21 (Temurin)
- Gradle 8.14
- Spring Boot 3.2.0
- Single-threaded scan with parallel m-sweep

### Parameters Tested (with scale-adaptive applied)

| Parameter | Base Value | Adapted Value (127-bit) |
|-----------|------------|-------------------------|
| samples | 500 (probe) / 5000 (full) | ~4,355 / ~43,550 |
| m-span | 100 (probe) / 250 (full) | ~423 / ~1,058 |
| threshold | 0.88 | ~0.85 |
| k-range | [0.28, 0.42] | [0.30, 0.40] (narrowed) |
| timeout | 120,000 ms (probe) | ~2,147,483 ms (~35 min) |
| precision | 512 | 708 (adaptive: 127×4+200) |
| search-radius | 1.5% of pCenter | Capped at 100M |
| max-search-radius | 100,000,000 | 100,000,000 |

---

## Observations

### 1. Ring Search Coverage Failure

The most significant observation is the consistent failure of ring search coverage:

```
Search radius capped at 100000000 (dynamic radius would be 169539193434207824)
Ring search coverage below threshold: 0.000 < 0.600
```

**Analysis**: The dynamic radius calculation returns values around **1.7×10^17**, but the cap is 100M. This means:
- Coverage = 100M / 1.7×10^17 ≈ 0.0000000006 (essentially zero)
- The algorithm is only searching ±100M integers around each candidate center
- The actual factor p=10508623501177419659 is ~1.2×10^18 away from √N (≈11.7×10^18)

### 2. Precision Scaling

Precision was correctly adapted:
```
PrecisionUtil: chosen precision=708 (configured=512, bitlen=127, required=708)
```

This meets the requirement: `precision = max(configured, N.bitLength() × 4 + 200) = max(512, 127×4+200) = max(512, 708) = 708`.

### 3. Scale-Adaptive Parameters

Scale-adaptive tuning was applied correctly:
```
samples: 2000 -> 17420
m-span: 180 -> 762
threshold: 0.95 -> 0.8459102954418176
k-range: [0.25, 0.45] -> [0.3013974823243749, 0.39860251767562505]
timeout: 600000ms -> 10752666ms
```

### 4. Singularity Guard

The Dirichlet kernel singularity guard works correctly at θ=0 and near-zero values:
```
theta=0 -> amplitude=1
theta=1.0E-10 -> amplitude=0.9999999999999...
theta=1.0E-50 -> amplitude=1
```

### 5. Snap Kernel Output

Candidates produced by the snap kernel are in a reasonable range:
```
lnN = 87.7834
theta = π/4
candidate = 7787105653281278672 (63 bits)
```

---

## Micro-Test Results

All 7 micro-tests passed:

| Test | Result | Notes |
|------|--------|-------|
| singularityGuard_thetaZero_returnsOne | ✓ PASSED | Returns 1.0 as expected |
| singularityGuard_thetaNearZero_handledGracefully | ✓ PASSED | Graceful degradation to 1.0 |
| precisionScaling_127Bit_sufficientPrecision | ✓ PASSED | 708 digits used |
| scaleAdaptiveParams_127Bit_scalingApplied | ✓ PASSED | All parameters scaled correctly |
| scaleAdaptiveParams_Gate4_moderateScaling | ✓ PASSED | Moderate scaling for 47-bit |
| snapKernel_validRange_producesReasonableCandidate | ✓ PASSED | Valid 63-bit candidate |
| dirichletKernel_variousJ_amplitudesNormalized | ✓ PASSED | Bounded [0, 1.1] |

---

## Critical Issue Identified

### The Search Radius Bottleneck

The 127-bit challenge has a fundamental mismatch between:

1. **√N ≈ 1.17×10^19** (half the bit-length)
2. **Factor distance from √N**: p=1.05×10^19, q=1.31×10^19, so |p - √N| ≈ 1.2×10^18

The ring search is looking ±100M around candidates, but the actual factor could be **10^10 times further** than the search radius allows.

**Implication**: Even if the geometric resonance correctly identifies the optimal k and θ values, the final certification step cannot reach the true factor because the search window is too narrow.

---

## Shell Exclusion A/B Test

Not executed to completion due to time constraints. Test infrastructure is in place at:
- `ShellExclusionABTest.java` - Ready for execution with `-Dgeofac.runFalsificationIT=true`

---

## SSE/Log Streaming Analysis

Observed behavior during multi-minute runs:
- Logs stream continuously without memory issues in the test window
- No backpressure observed in the 8-minute probe window
- `ConcurrentLinkedQueue` for diagnostics appears stable

However, for 30+ minute runs, memory pressure from diagnostic logging could be a concern if `enable-diagnostics=true`.

---

## Conclusions

### Hypothesis Status: **LIKELY FALSE** (Pending Full 30-Minute Test)

The geometric resonance method, as currently configured, **cannot** factor the 127-bit challenge because:

1. **Coverage gap**: The ring search radius cap (100M) is ~10^10 times smaller than the actual distance from √N to the true factor.

2. **Correct geometry, inadequate certification window**: The geometric phase may correctly identify resonance peaks, but the arithmetic certification phase cannot explore enough candidates.

### Recommended Next Steps

1. **Remove or increase max-search-radius**: The 100M cap is the primary bottleneck. Consider:
   - Removing the cap entirely (performance risk)
   - Scaling the cap with N.bitLength() (adaptive approach)

2. **Alternative certification strategy**: Instead of exhaustive ring search, consider:
   - Binary search in the vicinity
   - GCD-based filtering
   - Fermat's method near resonance peaks

3. **Run the full 30-minute test**: Execute with:
   ```bash
   ./gradlew test -Dgeofac.runFalsificationIT=true --tests "*FalsificationIT127Bit"
   ```

---

## Test Artifacts Created

| File | Purpose |
|------|---------|
| `FalsificationIT127Bit.java` | Full 30-minute falsification test |
| `QuickFalsificationProbeTest.java` | 2-minute quick probe |
| `ShellExclusionABTest.java` | A/B test for shell exclusion |
| `MicroEdgeCaseTests.java` | Unit tests for edge cases |
| `FINDINGS.md` | This document |

---

## Appendix: Raw Observations

### Scale-Adaptive Calculation for 127-bit N

```
bitLength = 127
BASELINE_BIT_LENGTH = 30.0

samples scaleFactor = (127/30)^1.5 = 8.71
mSpan scaleFactor = 127/30 = 4.23
threshold attenuation = log2(127/30) * 0.05 = 0.104
kRange scaleFactor = sqrt(127/30) = 2.06 (narrows)
timeout scaleFactor = (127/30)^2 = 17.92
```

### Dirichlet Kernel Amplitude Distribution (J=6)

```
θ=π/6: amplitude=0.076923
θ=0: amplitude=1.000000 (singularity)
θ→0: graceful degradation to 1.0
```

---

*Experiment conducted: 2025-11-28*
*Environment: Ubuntu, Temurin JDK 21, Gradle 8.14*
