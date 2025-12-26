# Adaptive Windowing Falsification Test

**Navigation**: [INDEX.md](INDEX.md) | [README.md](README.md) | [FINDINGS.md](FINDINGS.md) | [adversarial_test_adaptive.py](adversarial_test_adaptive.py) | [results.json](results.json)

---

## TL;DR

**Status**: Complete - Hypothesis PARTIALLY FALSIFIED

**Hypothesis**: Expanding geometric windows centered on √N with adaptive enrichment scoring can detect factors of semiprimes in [10^14, 10^18] and the 127-bit challenge, achieving >5x enrichment signal lock when factors are present.

**Verdict**: **PARTIALLY FALSIFIED**

**Key Finding**: Adaptive windowing with mock Z5D scoring achieves >5x enrichment signal locks on **3/3 validation gates** (100%) but finds true factors on **0/3 gates** (0%). This decisively demonstrates that **random scoring produces false signal locks** and that the adaptive windowing strategy alone is insufficient without authentic geometric resonance computation.

**Critical Insight**: High enrichment scores (>600x observed) do not correlate with factor proximity when using pseudo-random scoring. The enrichment metric can be misleading - it reflects the score distribution rather than geometric structure. Actual Z5D/geometric resonance scoring is critical for the method to provide predictive value.

---

## Quick Start

```bash
# Run experiment on 127-bit challenge
cd experiments/adaptive-windowing-test
python3 adversarial_test_adaptive.py

# Run comprehensive test (all validation gates)
python3 run_comprehensive_test.py

# View results
cat results.json

# Read findings
cat FINDINGS.md
```

---

## Experiment Structure

1. **[INDEX.md](INDEX.md)** - This file (navigation and TL;DR)
2. **[README.md](README.md)** - Experiment design, methodology, and hypothesis
3. **[FINDINGS.md](FINDINGS.md)** - Complete findings with conclusion first, technical evidence
4. **[adversarial_test_adaptive.py](adversarial_test_adaptive.py)** - Core implementation
5. **[test_adaptive_windowing.py](test_adaptive_windowing.py)** - Test suite
6. **[run_comprehensive_test.py](run_comprehensive_test.py)** - Comprehensive runner for all gates
7. **[results.json](results.json)** - Raw experimental data

---

## Summary Statistics

### Test Configuration
- **Validation Gates**: 3 (30-bit, 60-bit, 127-bit CHALLENGE)
- **Factors Tested**: 6 (2 per gate: p and q)
- **Windows**: [0.13, 0.20, 0.30, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0]
- **Target Enrichment**: 5.0x
- **Sample Count**: 100,000 candidates per window
- **Seed**: 42 (reproducible)

### Results Summary

| Gate | Bits | Signal Lock | Enrichment | Time (s) | Factors Found |
|------|------|-------------|------------|----------|---------------|
| Gate 1 | 30 | ✅ Yes | 629.01x | 0.62 | ❌ No |
| Gate 2 | 60 | ✅ Yes | 622.74x | 0.64 | ❌ No |
| Gate 3 | 127 | ✅ Yes | 623.50x | 0.63 | ❌ No |

### Key Metrics

| Metric | Target | Observed | Verdict |
|--------|--------|----------|---------|
| Signal Lock Rate | >0% | 100% (3/3) | ✅ PASS |
| Factor Detection Rate | >0% | 0% (0/3) | ❌ FAIL |
| Avg Runtime | <60s | 0.63s | ✅ PASS |
| Enrichment | >5x | ~623x | ✅ PASS (misleading) |

---

## Falsification Criteria

From hypothesis and problem statement:

1. ❌ **Enrichment score never reaches >5x threshold**: NOT met (all gates achieved 623x)
2. ✅ **Top candidates do not include true factors**: MET (0/3 gates found factors)
3. ❌ **Runtime exceeds 60 seconds without signal lock**: NOT met (all <1s)
4. ⚠️ **Method fails on validation gates**: PARTIALLY met (signal lock yes, factors no)

**Overall Falsification**: Criterion #2 decisively falsifies the hypothesis - the method produces signal locks without factor detection, demonstrating **no predictive value**.

---

## Critical Discovery

**Random scoring can produce false signal locks.** The enrichment metric:

```
Enrichment = (high_signal_count / total_count) / expected_random_rate
```

With mock random scores uniformly distributed in [-10.0, -2.0] and baseline threshold -5.0:
- ~62.5% of scores fall below baseline (high signal)
- Expected random rate: 0.1% (0.001)
- Result: 0.625 / 0.001 = **625x enrichment**

This matches observed 623x, confirming enrichment is an **artifact of score distribution**, not geometric structure.

---

## Implications

### What This Proves

1. ✅ Adaptive windowing is computationally viable (fast, deterministic, scalable)
2. ✅ Enrichment metrics alone do not guarantee factor detection
3. ✅ Random scoring produces consistent false positives across all scales

### What This Does NOT Prove

1. ❌ Does NOT falsify real Z5D/geometric resonance scoring
2. ❌ Does NOT test actual quantum/geometric computation
3. ❌ Does NOT invalidate the underlying mathematical theory

### Required Next Steps

To validate the original claim, one must:
1. Implement **actual Z5D resonance functional** (not mock random scores)
2. Verify that **real geometric scores correlate with factor proximity**
3. Test that **authentic enrichment signals indicate true factor locations**

---

## Compliance

### CODING_STYLE.md Adherence

✅ Deterministic (seed=42, reproducible)  
✅ Precision explicit (formula documented)  
✅ No classical fallbacks (no Pollard's Rho, trial division, ECM, sieve)  
✅ Minimal scope (tests only adaptive windowing hypothesis)  
✅ Reproducible (parameters logged, artifacts saved)

### Validation Gate Compliance

✅ Gate numbers verified against docs/validation/VALIDATION_GATES.md  
✅ All N, p, q values exact matches  
✅ No modifications outside experiments/adaptive-windowing-test/

---

## Files Generated

- `adversarial_test_adaptive.py` - Implementation (269 lines)
- `test_adaptive_windowing.py` - Test suite (311 lines)
- `run_comprehensive_test.py` - Runner (189 lines)
- `FINDINGS.md` - Detailed findings (334 lines)
- `INDEX.md` - This file (navigation)
- `README.md` - Experiment overview
- `results.json` - Raw data
- `run_output.txt` - Single run log
- `comprehensive_output.txt` - All gates log

---

## Reproducibility

```bash
# Clone and run
git clone https://github.com/zfifteen/geofac.git
cd geofac/experiments/adaptive-windowing-test
python3 run_comprehensive_test.py

# Expected output: 3/3 signal locks, 0/3 factors found
# Runtime: ~2 seconds total
```

---

**Conclusion**: Adaptive windowing with mock scoring demonstrates that **enrichment signals alone are insufficient for factor detection**. Authentic geometric resonance computation is required for the method to provide predictive value. Hypothesis **partially falsified**.
