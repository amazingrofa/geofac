# Signed or Scaled Adjustments Experiment

## Design and Methodology

### Hypothesis Statement

**Primary Hypothesis**: Signed or scaled adjustments to the geometric parameter k in the transformation θ′(n,k) = φ·((n mod φ)/φ)^k can reduce the number of search iterations required in Fermat-style factorization of semiprimes.

**Background**: Original simulation (described in issue #22) tested k=0.3 positive adjustments and found they overshot, increasing iterations to 100,000+ vs. 0-1 for unadjusted. This suggested that:
- Positive adjustments move starting point away from optimal
- Negative (corrective) or scaled adjustments might improve performance

**Falsification Criteria**:
1. Negative k-adjustments fail to reduce iterations vs. control
2. Scaled adjustments (0.1×, 0.5×) show no consistent improvement
3. Any apparent improvement is within noise/variance or due to guard clauses

---

## Experiment Design

### Test Parameters

- **Semiprimes**: 10 test cases generated in operational range [10^14, 10^18]
- **Prime characteristics**: Close primes (balanced semiprimes where p ≈ q)
- **Gap range**: 100 to 10,000 units between p and q
- **Precision**: mpmath with 50 decimal places (target error < 1e-16)
- **Reproducibility**: Fixed seed = 42 for deterministic RNG
- **Iteration limit**: 100,000 iterations per test (timeout)

### Strategies Tested

1. **Control**: No adjustment, start at a = ceil(√n)
2. **Positive k=0.3**: Original adjustment (expected to fail based on prior simulation)
3. **Negative k=0.3**: Corrective adjustment (hypothesis: should improve)
4. **Scaled positive k=0.3×0.1**: Reduced magnitude positive
5. **Scaled negative k=0.3×0.1**: Reduced magnitude corrective
6. **Scaled positive k=0.3×0.5**: Medium magnitude positive
7. **Scaled negative k=0.3×0.5**: Medium magnitude corrective

### Geometric Transformation

The adjustment formula:
```
θ′(n,k) = φ · ((n mod φ) / φ)^k
```

Where:
- φ = golden ratio ≈ 1.618
- n = floor(√N) for semiprime N
- k = 0.3 (geodesic exponent)

Starting point with adjustment:
```
a = ceil(√N + sign × scale × θ′(floor(√N), k))
```

Guard clause enforces:
```
a = max(a, ceil(√N))
```

### Fermat's Factorization Method

For semiprime N = p × q where p ≤ q:

1. Let a = starting point (adjusted or unadjusted)
2. For i = 0, 1, 2, ...:
   - Compute a' = a + i
   - Compute diff = (a')² - N
   - If diff is a perfect square b²:
     - p = a' - b
     - q = a' + b
     - Return (p, q, i) if p × q = N

For balanced semiprimes (p ≈ q), the optimal starting point is a = (p+q)/2 = ceil(√N).

---

## Implementation

### Semiprime Generation

```python
def generate_close_prime_pair(base, min_gap, max_gap, seed):
    # Miller-Rabin primality test for candidate selection
    # Generate p near base
    # Generate q at distance [min_gap, max_gap] from p
    return (p, q)
```

Ensures:
- Primes are genuine (Miller-Rabin with k=10 witnesses)
- Gap is bounded for balanced semiprime characteristics
- Reproducible via seed

### Adjustment Application

```python
def fermat_factorization_with_adjustment(n, k_adjustment, adjustment_sign, adjustment_scale):
    sqrt_n = sqrt(n)
    
    if k_adjustment is None:
        a_start = ceil(sqrt_n)  # Control
    else:
        theta_val = theta_prime(floor(sqrt_n), k_adjustment)
        adjustment = adjustment_sign * adjustment_scale * theta_val
        a_start = ceil(sqrt_n + adjustment)
    
    # Guard: a must be >= ceil(sqrt_n)
    a_start = max(a_start, ceil(sqrt_n))
    
    # Fermat iteration...
```

The guard clause is critical: it prevents starting below the mathematically sound lower bound.

---

## Data Collection

### Per-Test Metrics

For each (semiprime, strategy) pair:
- n: Semiprime value
- expected_p, expected_q: True factors
- found_p, found_q: Discovered factors (if any)
- iterations: Number of Fermat iterations
- success: Boolean (found correct factors)
- elapsed_seconds: Wall-clock time
- k_value, adjustment_sign, adjustment_scale: Strategy parameters

### Aggregate Metrics

For each strategy:
- Total tests
- Success count and rate
- Average iterations (all tests)
- Average iterations (successful tests only)

---

## Precision and Reproducibility

### Precision Management
- `mp.dps = 50` (50 decimal places)
- All sqrt and mod operations use mpmath.mpf
- Singularity epsilon: 10^(-25) for guard clauses
- Target precision error: < 1e-16

### Reproducibility
- Fixed seed: 42
- Deterministic prime generation (seeded RNG)
- Deterministic QMC-style sampling (golden ratio sequence)
- All parameters logged with ISO 8601 timestamps
- Results exported to JSON for verification

---

## Operational Range Compliance

Per CODING_STYLE.md validation gates:
- All semiprimes generated in [10^14, 10^18]
- 127-bit challenge (N = 137524771864208156028430259349934309717) not used
- Focus on operational range validation, not challenge number

Rationale:
- Balanced semiprimes in this range stress-test the adjustment hypothesis
- Computationally feasible (vs. 127-bit which requires extensive time)
- Compliant with validation gate 4 (operational range [10^14, 10^18])

---

## Limitations and Scope

### In Scope
- Balanced semiprimes (p ≈ q)
- Fermat-style iteration starting points
- Signed and scaled k-adjustments
- Operational validation range

### Out of Scope
- Imbalanced semiprimes (p << q) - different optimal starting point
- Geometric resonance amplitude detection - distinct from Fermat iteration
- 127-bit challenge factorization - different scale and characteristics
- Trial division, Pollard's Rho, ECM - excluded per no-fallback policy

### Assumptions
- θ′(n,k) with k=0.3 is representative of geodesic exponent range
- Balanced semiprimes are a valid test case for adjustment strategies
- Guard clause `a ≥ ceil(√n)` is mathematically sound

---

## Running the Experiment

```bash
# Navigate to experiment directory
cd experiments/signed-scaled-adjustments

# Run experiment (requires mpmath)
python experiment.py

# View results
cat results.json

# Or analyze with jq
jq '.strategy_summaries' results.json
```

### Dependencies
- Python 3.8+
- mpmath (install via `pip install mpmath`)

---

## Expected Outcomes

### If Hypothesis is Supported
- Negative k-adjustments reduce iterations vs. control
- Scaled adjustments show consistent improvement
- Clear correlation between adjustment direction/scale and performance

### If Hypothesis is Falsified
- Negative k-adjustments match or underperform control
- Positive adjustments universally fail (as in original simulation)
- No scaling factor improves performance
- Guard clause dominates behavior (all negative adjustments clamp to control)

---

## Safety and Ethics

- No fabricated data: All results are from actual computation
- No synthetic semiprimes: Only proper prime generation via Miller-Rabin
- No cherry-picking: All 10 test cases reported regardless of outcome
- Reproducible: Fixed seed enables independent verification

---

**Design Date**: 2024-11-22  
**Framework**: geofac experiments  
**Compliance**: CODING_STYLE.md, VALIDATION_GATES.md
