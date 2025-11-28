# Hash-Bounds Integration Experiment - Index

## Status: **HYPOTHESIS PARTIALLY VALIDATED, BUT INEFFECTIVE**

## TL;DR

The hash-bounds hypothesis claims that SHA256-based adjustments can improve Z5D predictions for factor locations. This experiment finds:

1. **Claimed calculations are CORRECT** — The SHA256 hash values and Z5D predictions match the hypothesis claims
2. **Hash-adjustment WORSENS prediction for 127-bit challenge** — Error increases from 0.000421 to 0.001167
3. **No consistent benefit** — Hash-adjustment helps in only 3/4 cases, and improvements are tiny
4. **Z5D unadjusted is already good** — The baseline Z5D prediction for 127-bit has remarkably low error

## Conclusion

**The hash-bounds adjustment provides NO practical benefit.** While the mathematical claims verify, the adjustment actually HARMS prediction accuracy for the primary 127-bit challenge case.

## Quick Navigation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Experimental design and methodology |
| [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md) | Complete findings with executive summary |
| [hash_bounds_test.py](hash_bounds_test.py) | Python implementation |
| [test_hash_bounds.py](test_hash_bounds.py) | pytest test suite |

## Key Findings

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Claimed frac_hash | 0.4253 | ✅ VERIFIED (actual: 0.4253) |
| Claimed Z5D pred | 0.2278 | ✅ VERIFIED (actual: 0.2278) |
| Error (Z5D baseline) | 0.000421 | Already very low |
| Error (after adjustment) | 0.001167 | **WORSENED by 2.8x** |
| 127-bit adjustment helped | NO | Hash-bounds HARMFUL for challenge |

## Test Cases Summary

| Case | Bit-length | Z5D Error | Adjusted Error | Helped? |
|------|------------|-----------|----------------|---------|
| 127-bit Challenge | 127 | 0.000421 | 0.001167 | ❌ NO |
| RSA-100 | 330 | 0.0840 | 0.0834 | ✅ Yes (tiny) |
| Gate 1 | 30 | 0.6493 | 0.6399 | ✅ Yes (tiny) |
| Gate 2 | 60 | 0.2876 | 0.2836 | ✅ Yes (tiny) |

## Verdict

**HYPOTHESIS PARTIALLY VALIDATED BUT INEFFECTIVE:**
- ✅ Mathematical calculations are correct
- ❌ Hash-adjustment does not improve 127-bit challenge prediction
- ❌ Average improvement is only 0.0033 (negligible)
- ❌ Primary use case (127-bit challenge) is HARMED by adjustment

---

*Experiment Date: 2025-11-28*  
*Status: COMPLETE*

