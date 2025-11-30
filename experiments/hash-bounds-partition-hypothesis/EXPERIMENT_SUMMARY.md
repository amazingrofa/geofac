# Hash-Bounds Partition Hypothesis: Experiment Summary

## Executive Summary

**STATUS: FRAMEWORK COMPLETE, AWAITING EXECUTION**

The experiment framework is fully implemented and ready to execute. Results will be populated after running the comparison experiments.

---

## Hypothesis

**Claimed:** Fractional square roots of seed primes (frac(√2), frac(√3), frac(√5), frac(√7), frac(√11), frac(√13)) create natural boundaries that partition the factor search space. Factors preferentially cluster near boundaries at n × frac(√p), and boundary-focused sampling should outperform uniform sampling.

**Seed Prime Fractional Roots:**
- frac(√2) ≈ 0.41421356237
- frac(√3) ≈ 0.73205080757
- frac(√5) ≈ 0.23606797750
- frac(√7) ≈ 0.64575131106
- frac(√11) ≈ 0.31662479036
- frac(√13) ≈ 0.60555127546

---

## Experimental Design

### Falsification Criteria

The hypothesis is falsified if any of the following hold:

1. **Criterion 1:** Boundary-focused sampling does NOT find factors faster than uniform sampling on average
2. **Criterion 2:** Factors do NOT cluster measurably near hash boundaries (uniform distribution is indistinguishable)
3. **Criterion 3:** No improvement in success rate when using boundary-focused sampling
4. **Criterion 4:** Boundary selection performs no better than random subspace selection of equal size

### Test Targets

**Primary:** Gate 4 operational range [10^14, 10^18] semiprimes
- 60-bit: 1152921470247108503 = 1073741789 × 1073741827
- 64-bit: 18446736050711510819 = 4294966297 × 4294966427

**Secondary:** 127-bit challenge semiprime (Gate 3)
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863

### Experimental Framework

| Experiment | Boundary Focus | Proximity Weight | Purpose |
|------------|----------------|------------------|---------|
| 1. Uniform GVA | ✗ | ✗ | Control baseline |
| 2. Hash-Bounds (default) | ✓ (0.7) | ✓ (0.1) | Test full hypothesis |
| 3. Hash-Bounds (bw=0.3) | ✓ (0.3) | ✓ (0.1) | Ablation: less focus |
| 4. Hash-Bounds (bw=0.9) | ✓ (0.9) | ✓ (0.1) | Ablation: more focus |
| 5. Hash-Bounds (pw=0.0) | ✓ (0.7) | ✗ (0.0) | Ablation: no proximity |
| 6. Hash-Bounds (pw=0.5) | ✓ (0.7) | ✓ (0.5) | Ablation: high proximity |

---

## Implementation Details

### Boundary-Focused Sampling

**Key innovation:** Instead of uniform Sobol/Halton sampling across the full window, concentrate samples near positions where n × frac(√p) aligns with factor search space.

**Combined Scoring:**
```
score = (1 - β) × (-geodesic_distance) + β × boundary_proximity
```

Where:
- `geodesic_distance`: Riemannian distance in 7D torus (lower = better)
- `boundary_proximity`: Exponential decay from nearest hash boundary (higher = closer)
- `β`: Boundary proximity weight (default 0.1)

**Sampling Strategy:**
- `boundary_weight` fraction of samples clustered near boundary centers
- Remaining samples use uniform golden ratio QMC
- Local QMC within boundary regions for fine coverage

### Parameters

- **k = 0.35:** Geodesic exponent for torus embedding
- **max_candidates:** Varies by scale (3000-10000)
- **delta_window:** ±30,000 to ±100,000 around √N
- **boundary_weight:** 0.7 default (70% boundary-focused)
- **boundary_proximity_weight:** 0.1 default (10% weight in scoring)
- **seed:** 42 (deterministic)
- **precision:** Adaptive: max(50, N.bitLength() × 4 + 200)

---

## Preliminary Analysis

### Fractional Root Properties

The fractional parts of √p for seed primes are irrational, creating quasi-periodic boundary patterns:

| Prime | frac(√p) | Approximate Period |
|-------|----------|-------------------|
| 2 | 0.414... | 2.414... |
| 3 | 0.732... | 1.366... |
| 5 | 0.236... | 4.236... |
| 7 | 0.646... | 1.549... |
| 11 | 0.317... | 3.158... |
| 13 | 0.606... | 1.651... |

These create overlapping boundary patterns that partition the search space non-uniformly.

### Theoretical Considerations

**Supporting arguments:**
1. Golden ratio (φ) already used in GVA suggests irrational boundaries may have significance
2. Fractional parts create equidistributed sequences (Weyl's theorem)
3. Boundary focusing reduces effective search space

**Critical objections:**
1. No known connection between factorization and fractional roots of arbitrary primes
2. Boundary structure may be arbitrary (no worse than random partitioning)
3. GVA's geodesic signal may dominate any boundary effect

---

## Results

*(To be populated after experiment execution)*

### Comparison Summary

| Experiment | Success | Time (s) | Candidates | Notes |
|------------|---------|----------|------------|-------|
| Uniform GVA | - | - | - | Pending |
| Hash-Bounds (default) | - | - | - | Pending |
| Hash-Bounds (bw=0.3) | - | - | - | Pending |
| Hash-Bounds (bw=0.9) | - | - | - | Pending |
| Hash-Bounds (pw=0.0) | - | - | - | Pending |
| Hash-Bounds (pw=0.5) | - | - | - | Pending |

### Factor Clustering Analysis

| Test | p Proximity | q Proximity | Clusters Near Boundary? |
|------|-------------|-------------|------------------------|
| 60-bit | - | - | - |
| 64-bit | - | - | - |
| 127-bit | - | - | - |

---

## Verdict

*(To be determined after experiment execution)*

### Falsification Criteria Status

- [ ] **Criterion 1:** Performance comparison (faster/slower)
- [ ] **Criterion 2:** Clustering analysis (cluster/uniform)
- [ ] **Criterion 3:** Success rate comparison (better/worse)
- [ ] **Criterion 4:** Boundary vs. random (structured/random)

**Final Verdict:** PENDING

---

## Reproducibility

To reproduce this experiment:

```bash
cd /home/runner/work/geofac/geofac/experiments/hash-bounds-partition-hypothesis

# Step 1: Run unit tests
pytest test_hash_bounds.py -v

# Step 2: Run comparison experiment
python3 comparison_experiment.py

# Step 3: Review results
cat comparison_results.json
```

**Artifacts:**
- `comparison_results.json`: Machine-readable experiment results
- Test logs in stdout

---

## Notes

This experiment follows the repository's validation gates and coding philosophy:
- Operates only on semiprimes in [10^14, 10^18] and CHALLENGE_127
- No classical fallbacks (Pollard's Rho, ECM, trial division)
- Deterministic methods only (Sobol/Halton sampling, golden ratio QMC)
- Adaptive precision: max(configured, N.bitLength() × 4 + 200)
- All seeds pinned, all parameters logged

The framework is designed for falsification: specific predictions that can be definitively tested.
