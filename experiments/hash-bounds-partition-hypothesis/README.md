# Hash-Bounds Partition Hypothesis Falsification Experiment

## Objective

Attempt to falsify the hypothesis that fractional square roots of seed primes create natural boundaries that partition the factor search space, enabling more efficient factor detection through boundary-focused sampling.

## Hypothesis Under Test

**Claimed:**

> "Fractional square roots of seed primes (frac(√2), frac(√3), frac(√5), frac(√7), etc.) create natural boundaries that partition the factor search space. Instead of arbitrary shell-exclusion, factors preferentially cluster near boundaries at n × frac(√p). Current uniform sampling misses factors because resonances are concentrated at these geometrically-significant boundaries rather than randomly distributed."

**Specific claims:**
1. **Boundary structure:** The fractional parts frac(√2), frac(√3), frac(√5), frac(√7), frac(√11), frac(√13) define geometrically significant boundaries
2. **Factor clustering:** True factors cluster preferentially near n × frac(√p) boundaries
3. **Sampling improvement:** Concentrating Sobol/Halton points near these boundaries improves factor detection
4. **GVA integration:** Mapping boundary coordinates to (m, k) candidates near √N enhances geodesic search

## Experimental Design

### Falsification Criteria

The hypothesis is falsified if any of the following hold:

1. **Criterion 1:** Boundary-focused sampling does NOT find factors faster than uniform sampling on average
2. **Criterion 2:** Factors do NOT cluster measurably near hash boundaries (uniform distribution is indistinguishable)
3. **Criterion 3:** No reduction in candidates tested when using boundary-focused sampling
4. **Criterion 4:** Boundary selection performs no better than random subspace selection of equal size

At least one falsification criterion must be violated for the hypothesis to be considered supported.

### Test Targets

**Primary Target:** Gate 4 operational range [10^14, 10^18] semiprimes

Specific test semiprimes:
- 60-bit: 1152921470247108503 = 1073741789 × 1073741827
- 64-bit: 18446736050711510819 = 4294966297 × 4294966427
- Additional semiprimes in operational range

**Secondary Target:** 127-bit challenge semiprime (Gate 3)
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863

### Key Components

#### 1. Fractional Square Root Boundaries

Compute fractional parts of square roots of seed primes:

```python
SEED_PRIMES = [2, 3, 5, 7, 11, 13]

# Fractional parts (high precision)
FRAC_SQRT = {
    2:  0.41421356237309504880168872420969807856967187537694...,
    3:  0.73205080756887729352744634150587236694280525381038...,
    5:  0.23606797749978969640917366873127623544061835961152...,
    7:  0.64575131106459059050161575363926042571025918308245...,
    11: 0.31662479035539984359806544102557426130432849155867...,
    13: 0.60555127546398929311922126747049594625129657384524...,
}
```

#### 2. Boundary Region Definition

For each seed prime p and √N:
- Boundary centers: floor(√N × frac(√p) × n) for relevant integers n
- Boundary width: Adaptive based on scale (log(√N) or similar)

#### 3. Boundary-Focused Sampling

Instead of uniform Sobol/Halton sampling across the full window:
- Identify boundary regions for each seed prime
- Concentrate sampling points near boundary centers
- Use distance-weighted sampling (denser near boundaries)

#### 4. GVA Integration

Map boundary coordinates to GVA's (m, k) candidate space:
- Embed candidates in 7D torus using golden ratio powers
- Compute Riemannian geodesic distance
- Rank candidates by distance + boundary proximity

### Implementation

#### Baseline: Uniform GVA Sampling
- Standard GVA with uniform Sobol/Halton δ-sampling
- No boundary weighting
- Equal probability across entire search window

#### Treatment: Hash-Bounds Focused Sampling
- Same GVA core
- **+ Fractional root boundary computation**
- **+ Boundary-focused sampling (concentrated near frac(√p) multiples)**
- **+ Combined scoring: geodesic distance + boundary proximity**

#### Scoring Function

Baseline score:
```
score_baseline = -geodesic_distance(candidate, N)
```

Enhanced score with boundary proximity:
```
score_enhanced = α × (-geodesic_distance) + β × boundary_proximity(candidate)
```

Where boundary_proximity measures minimum distance to any hash boundary.

### Metrics

1. **Factor Discovery:**
   - Candidates tested to find factor
   - Success rate within budget
   - Time to first factor

2. **Boundary Clustering:**
   - Distribution of actual factors relative to hash boundaries
   - Statistical test: are factors closer to boundaries than random?

3. **Sampling Efficiency:**
   - Coverage of search space
   - Redundancy in sampled regions

4. **Ablation Analysis:**
   - Each seed prime individually (√2 only, √3 only, etc.)
   - Combined boundaries vs. best single boundary
   - Boundary proximity weight sensitivity (β = 0.01, 0.1, 0.5, 1.0)

## Reproducibility

### Run Experiment

```bash
# Unit tests
pytest test_hash_bounds.py -v

# Full comparison
python3 comparison_experiment.py
```

All experiments use deterministic parameters, fixed seeds, and export artifacts.

## Files

| File | Purpose |
|------|---------|
| INDEX.md | Navigation and TL;DR |
| README.md (this file) | Experiment design and methodology |
| EXPERIMENT_SUMMARY.md | Complete findings and verdict |
| hash_bounds_sampling.py | Core hash-bounds computation and sampling |
| comparison_experiment.py | Test suite and analysis framework |
| test_hash_bounds.py | Unit tests for components |

## Expected Outcomes

### If Hypothesis is Supported
- Boundary-focused sampling finds factors with fewer candidates tested (≥20% improvement)
- Actual factors are statistically closer to hash boundaries than random expectation
- Multiple seed primes contribute independently (not redundant)
- Improvement holds across different N scales in operational range

### If Hypothesis is Falsified
- Uniform sampling performs equally well or better
- Factor locations are uniformly distributed (no boundary clustering)
- Boundary-focused sampling wastes computation on arbitrary regions
- Any observed improvement is attributable to reduced search space (not boundary structure)
