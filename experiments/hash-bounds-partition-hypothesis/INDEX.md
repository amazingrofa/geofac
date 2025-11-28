# Hash-Bounds Partition Hypothesis Falsification Experiment

## Quick Navigation

**Start here:** [EXPERIMENT_SUMMARY.md](EXPERIMENT_SUMMARY.md) - Complete findings and verdict

Supporting documents:
- [README.md](README.md) - Experiment design, methodology, and test framework

Code artifacts:
- [hash_bounds_sampling.py](hash_bounds_sampling.py) - Core hash-bounds sampling implementation
- [comparison_experiment.py](comparison_experiment.py) - Comparison framework: boundary-focused vs uniform sampling
- [test_hash_bounds.py](test_hash_bounds.py) - Unit tests for hash-bounds components

## TL;DR

**Hypothesis:** Fractional square roots of seed primes (frac(√2), frac(√3), frac(√5), frac(√7), frac(√11), frac(√13)) create natural boundaries that partition the factor search space. Factors preferentially cluster near boundaries at n × frac(√p), and boundary-focused sampling should outperform uniform sampling.

**Method:** Compare uniform Sobol/Halton sampling (baseline GVA) vs. boundary-focused sampling that concentrates points near (m, k) coordinates derived from fractional square roots of seed primes.

**Test Target:** Gate 4 operational range [10^14, 10^18] semiprimes + 127-bit challenge (CHALLENGE_127 = 137524771864208156028430259349934309717).

**Falsification Criteria:**
1. Boundary-focused sampling does NOT find factors faster than uniform sampling
2. Factors do NOT cluster preferentially near hash boundaries
3. No measurable reduction in candidates tested
4. Boundary selection is equivalent to random subspace selection

**Expected Outcome:** The experiment will reveal whether hash-bounds partition theory has empirical support or is falsified by evidence.

---

## Executive Summary

*(To be populated after experiment execution)*

**STATUS: FRAMEWORK COMPLETE, AWAITING EXECUTION**

---

## Files

| File | Purpose |
|------|---------|
| INDEX.md (this file) | Navigation and TL;DR |
| README.md | Experiment design and methodology |
| EXPERIMENT_SUMMARY.md | Complete findings, analysis, and verdict |
| hash_bounds_sampling.py | Core hash-bounds boundary computation and sampling |
| comparison_experiment.py | Full comparison framework with ablation studies |
| test_hash_bounds.py | Unit tests for all components |

---

## Key Concepts

### Fractional Square Roots of Seed Primes

The hypothesis uses the fractional part of square roots of the first seed primes:
- frac(√2) ≈ 0.41421356...
- frac(√3) ≈ 0.73205081...
- frac(√5) ≈ 0.23606798...
- frac(√7) ≈ 0.64575131...
- frac(√11) ≈ 0.31662479...
- frac(√13) ≈ 0.60555128...

These values are claimed to create natural partition boundaries in the factor search space.

### Boundary Regions

For each seed prime p, boundary regions are defined around:
- Center: n × frac(√p) for integer n near √N
- Width: Adaptive based on N's scale

### Integration with GVA

The boundary-focused sampling integrates with:
- 7D torus embedding using golden ratio powers
- Riemannian geodesic distance computation
- Adaptive precision: max(configured, N.bitLength() × 4 + 200)

---

## Reproducibility

To reproduce the experiment:

```bash
cd /home/runner/work/geofac/geofac/experiments/hash-bounds-partition-hypothesis

# Step 1: Run unit tests
pytest test_hash_bounds.py -v

# Step 2: Run comparison experiment
python3 comparison_experiment.py
```

**Note:** All experiments use deterministic seeds, fixed parameters, and export reproducible artifacts.
