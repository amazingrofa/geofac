# Hash-Bounds Integration Experiment

## Objective

**Rigorously test** the hypothesis that SHA256-based "hash-bounds" can improve factor prediction in geofac, using the "better than random" criterion.

## Result

**MIXED RESULT**: 
- ✅ **127-bit challenge SUCCESS** — p is captured in the prediction band
- ⚠️ **Per-N rate marginally below baseline** — 14.3% vs 15.5% random baseline

## Success Criterion: "Better Than Random"

Per user reassessment (Nov 28, 2025):
- **Random baseline**: 15.5% capture probability (band width = 0.155)
- **Per-N success**: At least one factor (p or q) captured in the prediction band
- **Primary target**: 127-bit challenge

## Hypothesis Under Test

The hypothesis claims:

1. **Hash Fraction**: Compute `frac_hash = SHA256(str(N))` normalized to [0,1]
2. **Z5D-like Prediction**: Compute `f = {sqrt((sqrt(N)/ln(sqrt(N))) * ln((sqrt(N)/ln(sqrt(N)))))}` where `{x}` denotes fractional part
3. **Band**: Create band `[f - 0.0775, f + 0.0775]` (width = 0.155)
4. **Success**: Factor p or q's {sqrt} value falls within the band

### Verified Values for 127-bit Challenge

| Metric | Value | Status |
|--------|-------|--------|
| frac_hash | 0.4253 | ✅ VERIFIED |
| Z5D prediction | 0.2278 | ✅ VERIFIED |
| Band | [0.1503, 0.3053] | ✅ COMPUTED |
| Actual {sqrt(p)} | 0.2282 | ✅ IN BAND |
| Error | 0.000421 | ✅ VERIFIED |

## Test Cases

| Case | N | p | q | Bit-length | p in band? |
|------|---|---|---|------------|------------|
| Challenge | 137524771864208156028430259349934309717 | 10508623501177419659 | 13086849276577416863 | 127 | ✅ YES |
| 10^17 Scale | 100006904456937509 | 317000027 | 315479167 | 57 | ❌ |
| 10^14 Scale | 100000980001501 | 10000019 | 10000079 | 47 | ❌ |
| 58-bit | 288230356824359011 | 536870909 | 536870879 | 58 | ❌ |
| Gate 1 | 1073217479 | 32749 | 32771 | 30 | ❌ |
| Gate 2 | 1152921470247108503 | 1073741789 | 1073741827 | 60 | ❌ |
| RSA-100 | (see EXPERIMENT_REPORT.md) | (known) | (known) | 330 | ❌ |

## Key Findings

| Metric | Value |
|--------|-------|
| Per-N capture rate | 14.3% (1/7) |
| Random baseline | 15.5% |
| 127-bit challenge success | ✅ YES |
| Hash adjustment helps error | 71.4% of cases |

## Methodology

### 1. Verify SHA256 Calculations
Independent computation of SHA256(str(N)) for all test cases.

### 2. Compute Z5D Prediction and Band
Apply the formula to get prediction center, then create band [center - 0.0775, center + 0.0775].

### 3. Check Band Capture
For each semiprime, check if {sqrt(p)} or {sqrt(q)} falls within the band.

### 4. Compare to Random Baseline
Random baseline = 15.5% (band width as fraction of [0,1] interval).

## Precision Requirements

Following repository standards:
- `precision = max(configured, N.bitLength() × 4 + 200)`
- For 127-bit: `precision = max(100, 127 × 4 + 200) = 708` decimal places
- Use mpmath with explicit `mp.dps` setting

## Files

- `hash_bounds_test.py` - Main implementation (with band capture analysis)
- `test_hash_bounds.py` - pytest test suite (38 tests)
- `EXPERIMENT_REPORT.md` - Detailed findings with executive summary
- `INDEX.md` - Quick navigation

## Reproducibility

All calculations are deterministic:
- SHA256 is deterministic
- mpmath precision is pinned
- No random sampling used

Run tests with:
```bash
cd experiments/hash-bounds-integration
pip install pytest mpmath
pytest test_hash_bounds.py -v
python3 hash_bounds_test.py
```

## Compliance

✅ Works on validation gate numbers and 127-bit whitelist  
✅ No classical fallbacks  
✅ Deterministic methods only  
✅ Explicit precision with mpmath  
✅ All parameters logged  

---

*Experiment tests hash-bounds hypothesis using "better than random" criterion.*
