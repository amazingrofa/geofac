# Kernel Order (J) Impact Study - Quick Summary

**Date:** 2025-11-23  
**Status:** ✅ COMPLETE  
**Verdict:** ❌ HYPOTHESIS FALSIFIED

## One-Line Result

All J values (3, 6, 9, 12, 15) succeeded on validation gates; kernel order affects runtime (2-4×) but not success.

## Test Matrix

| Test Case | J=3 | J=6 | J=9 | J=12 | J=15 |
|-----------|-----|-----|-----|------|------|
| Gate 1 (30-bit) | ✅ 0.54s | ✅ 0.52s | ✅ 0.51s | ✅ 1.48s | ✅ 1.51s |
| Gate 2 (60-bit) | ✅ 0.78s | ✅ 1.62s | ✅ 1.62s | ✅ 2.89s | ✅ 2.88s |

## Key Findings

1. **100% success rate** regardless of J
2. **Lower J is faster** (2-4× speedup)
3. **J=6 default is adequate** (not optimal but acceptable)
4. **Threshold dominates** candidate selection, not kernel sharpness

## Files

- `EXECUTIVE_SUMMARY.md` — Complete analysis (8 KB)
- `README.md` — Methodology (6 KB)
- `kernel_order_experiment.py` — Implementation (8 KB)
- `results.json` — Raw data (4 KB)

## Reproduction

```bash
cd experiments/kernel-order-impact-study
python3 kernel_order_experiment.py
```

**Runtime:** ~10 seconds  
**Dependencies:** Python 3.12+, mpmath 1.3.0+
