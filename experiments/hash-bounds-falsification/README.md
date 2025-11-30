# Hash-Bounds Falsification Experiment

## Design and Methodology

### Hypothesis Statement

**Primary Hypothesis**: Hash-bounds derived from Z5D fractional part predictions can predict useful bounds for locating the factor d in semiprime N = p × q.

**Specific Claims from Issue**:
1. SHA-256-like constants derived from bounded fractional parts {√p} can predict bounds for the factor d
2. Z5D prime predictions establish geometric bounds on fractional parts of square roots of primes
3. Calibrated metrics: mean relative error ~22,126 ppm, average fractional errors ~0.237, width factor 0.155 yields ~51.5% coverage
4. For CHALLENGE_127 (N=137524771864208156028430259349934309717), predictions claim to narrow the search window via fractional part {√p}

**Key Values from Hypothesis**:
- Actual {√p} ≈ 0.228200298... for p=10508623501177419659
- Mock Z5D prediction {√(m·ln(m))} ≈ 0.878727625... where m ≈ p/ln(p)
- Bound interval [0.801, 0.956] with width=0.155 should capture factor ~50% of time
- θ'(n,k) = φ·((n mod φ)/φ)^k with k=0.3 as Z5D approximation function

**Falsification Criteria**:
1. The proposed bounds systematically miss the actual factor's fractional part
2. Coverage rates < 30% (significantly below claimed 51.5%)
3. The method provides no predictive signal vs random baseline

---

## Experiment Design

### Validation Gates

Per `docs/validation/VALIDATION_GATES.md`, the experiment uses all three validation gates:

| Gate | N | p | q | Bit Length |
|------|---|---|---|------------|
| Gate 1 (30-bit) | 1073217479 | 32749 | 32771 | 30 |
| Gate 2 (60-bit) | 1152921470247108503 | 1073741789 | 1073741827 | 60 |
| Gate 3 (127-bit) | 137524771864208156028430259349934309717 | 10508623501177419659 | 13086849276577416863 | 127 |

### Test Parameters

- **Width factor**: 0.155 (from hypothesis)
- **k value**: 0.3 (geodesic exponent for θ'(n,k))
- **Precision**: Adaptive: max(configured, N.bit_length() × 4 + 200)
- **Reproducibility**: Fixed seed = 42 for deterministic RNG
- **Factors tested**: 6 (2 per gate: p and q)

---

## Mathematical Background

### Z5D Prediction Formula

The hypothesis claims Z5D predicts fractional parts via:

```
m = p / ln(p)
prediction = {√(m · ln(m))}
```

Where {x} denotes the fractional part: x - floor(x).

### θ'(n,k) Function

The geodesic approximation:

```
θ'(n,k) = φ · ((n mod φ) / φ)^k
```

Where:
- φ = golden ratio ≈ 1.618033988749895
- n = floor(√N) for semiprime N
- k = 0.3 (geodesic exponent)

### Hash-Bounds Interval

Given a Z5D prediction `center`, the bounds are:

```
lower = center - width/2
upper = center + width/2
```

With width = 0.155, this creates an interval of length 0.155 centered on the prediction.

### Coverage Calculation

A factor p is "in bounds" if:

```
bounds_lower ≤ {√p} ≤ bounds_upper
```

Coverage rate = (factors in bounds) / (total factors tested).

---

## Implementation

### Precision Management

Following geofac convention, precision is adaptive:

```python
def compute_adaptive_precision(n: int, min_precision: int = 50) -> int:
    bit_length = n.bit_length()
    adaptive = bit_length * 4 + 200
    return max(min_precision, adaptive)
```

This yields:
- Gate 1 (30-bit): 320 decimal places
- Gate 2 (60-bit): 440 decimal places
- Gate 3 (127-bit): 708 decimal places

### Core Analysis Function

For each validation gate, the experiment:
1. Computes actual {√p} and {√q} at high precision
2. Computes Z5D predictions using the claimed formula
3. Constructs hash-bounds intervals centered on predictions
4. Checks whether actual fractional parts fall within bounds
5. Calculates prediction errors

### Bounds Handling

The implementation handles wraparound cases where bounds cross 0 or 1:
- If lower < 0: interval is [lower+1, 1) ∪ [0, upper]
- If upper > 1: interval is [lower, 1) ∪ [0, upper-1]
- Normal case: [lower, upper]

---

## Data Collection

### Per-Gate Metrics

For each (gate, factor) pair:
- `actual_frac_p`: True fractional part {√p}
- `actual_frac_q`: True fractional part {√q}
- `z5d_pred_p`: Z5D prediction for p
- `z5d_pred_q`: Z5D prediction for q
- `bounds_p_lower/upper`: Hash-bounds interval for p
- `bounds_q_lower/upper`: Hash-bounds interval for q
- `p_in_bounds`: Boolean (was p captured?)
- `q_in_bounds`: Boolean (was q captured?)
- `error_p`: |{√p} - prediction|
- `error_q`: |{√q} - prediction|
- `rel_error_p_ppm`: Relative error in parts per million
- `rel_error_q_ppm`: Relative error in parts per million

### Aggregate Metrics

- Total factors tested
- Factors in bounds
- Coverage rate
- Average absolute error
- Average relative error (ppm)
- Comparison to claimed metrics

---

## Precision and Reproducibility

### Precision Management
- Uses `mpmath` with adaptive decimal places
- Precision formula: `max(configured, N.bit_length() × 4 + 200)`
- Gate 3 uses 708 decimal places for exponential error control

### Reproducibility Checklist
- ✅ Fixed seed: 42
- ✅ Explicit precision: adaptive per gate
- ✅ Timestamped: ISO 8601 format
- ✅ Parameters logged: width_factor, k_value
- ✅ Code published: hash_bounds_test.py
- ✅ Data exported: results.json
- ✅ No fabrication: All data from actual computation
- ✅ All validation gates from official policy

---

## Validation Gate Compliance

Per `docs/validation/VALIDATION_GATES.md`:
- ✅ Gate 1 (30-bit): 1073217479 with factors 32749, 32771
- ✅ Gate 2 (60-bit): 1152921470247108503 with factors 1073741789, 1073741827
- ✅ Gate 3 (127-bit): CHALLENGE_127 with known factors
- ✅ No fallbacks: Pure mathematical analysis
- ✅ Deterministic: Fixed seed, reproducible results

---

## Expected Outcomes

### If Hypothesis is Supported
- Coverage rate ≥ 51.5% (claimed)
- Bounds capture at least 3/6 factors
- Average error ≤ 0.237 (claimed)
- Z5D predictions correlate with actual {√p}

### If Hypothesis is Falsified
- Coverage rate < 30% (threshold)
- Bounds miss most or all factors
- Prediction errors significantly exceed claimed values
- No meaningful correlation between predictions and actuals

---

## Running the Experiment

```bash
# Navigate to experiment directory
cd experiments/hash-bounds-falsification

# Run experiment
python hash_bounds_test.py

# Run test suite (26 tests)
python -m pytest test_hash_bounds.py -v

# View results
cat results.json

# Analyze with jq
jq '.summary' results.json
```

### Dependencies
- Python 3.8+
- mpmath (`pip install mpmath`)
- pytest (`pip install pytest`) for test suite

---

## Safety and Ethics

- **No fabricated data**: All results from actual computation
- **No synthetic numbers**: Uses official validation gate numbers only
- **No cherry-picking**: All 6 factors reported regardless of outcome
- **Reproducible**: Fixed seed enables independent verification
- **Official sources**: All N, p, q from VALIDATION_GATES.md

---

**Design Date**: 2025-11-28  
**Framework**: geofac experiments  
**Compliance**: CODING_STYLE.md, VALIDATION_GATES.md
