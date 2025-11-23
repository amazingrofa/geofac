# Kernel Order (J) Impact Study

## Quick Navigation

**Start here:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) - Complete findings and verdict

Supporting documents:
- [README.md](README.md) - Experiment design, methodology, and test framework

Code artifacts:
- [kernel_order_experiment.py](kernel_order_experiment.py) - Main experiment implementation

Data artifacts:
- [results.json](results.json) - Experimental results

## TL;DR

**Hypothesis:** The Dirichlet kernel order J=6 (current default) is not optimal for all scales; testing J ∈ {3, 6, 9, 12, 15} will reveal whether higher or lower orders improve factorization success rates.

**Method:** Run controlled factorization attempts on validation gate semiprimes (30-bit, 60-bit) with varying J values, measuring success rate, runtime, and amplitude characteristics.

**Falsification Criteria:**
1. J=6 performs identically to all other tested values (no effect)
2. All J values fail equally (kernel order irrelevant at these scales)
3. Performance variation is within noise margins (±5%)
4. Higher J always fails (parameter only works for small values)

**Status:** Framework implemented, ready for execution

---

Read [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) for complete details (to be populated after execution).
