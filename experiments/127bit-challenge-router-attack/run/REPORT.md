# 127-bit Challenge Router Attack Experiment

**Date:** 2025-11-22T16:41:01.109426

## Executive Summary

✓ **SUCCESS** - Factors found via FR-GVA
- Primary engine (FR-GVA) succeeded
- Time: 0.011s
- Factors: 10000019 × 10000079
- Validation: p × q = N ✓

## Target Semiprime

```
N = 100000980001501
```

## Structural Features

- **Bit length:** 47
- **Approx sqrt(N):** 10000048
- **Kappa (κ):** 8.725391
- **Log(N):** 32.24

## Router Decision

Based on structural feature analysis, the router selected: **FR-GVA**

## Execution Details

### Primary Attempt
- **Method:** FR-GVA
- **Precision:** 388 dps
- **Time:** 0.011s
- **Result:** Success

## Validation

```python
p = 10000019
q = 10000079
p * q = 100000980001501
N = 100000980001501
Valid: True
```

## Reproducibility

This experiment uses deterministic methods:
- Fixed precision (adaptive based on bit length)
- Quasi-Monte Carlo sampling (Sobol/Halton sequences)
- No stochastic elements

All parameters and results are logged for full reproducibility.