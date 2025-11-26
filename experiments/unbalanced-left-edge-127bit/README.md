# Unbalanced Left-Edge Geometry Experiment

**Status**: Ready for execution  
**Target**: 127-bit challenge N = 137524771864208156028430259349934309717  
**Hypothesis**: Unbalanced semiprimes exhibit a "left-edge cliff" in τ-space that reveals the small factor location

## Overview

This experiment attempts to falsify the hypothesis that GEOFAC can factor the 127-bit challenge number **without prior knowledge of its factors**, using only geometric signal via the "unbalanced / left-edge" geometry pipeline.

### The Unbalanced Semiprime Problem

For the 127-bit challenge:
- N ≈ 1.37 × 10^38
- √N ≈ 1.17 × 10^19 (approximately 64 bits)
- Both factors p and q are 64-bit primes
- Neither factor is near √N (they are "unbalanced" relative to √N-centered search)

Standard factorization methods often search near √N, which works well for balanced semiprimes (p ≈ q ≈ √N). For unbalanced semiprimes, this approach fails because the factors may be far from √N.

### The Left-Edge Hypothesis

The hypothesis proposes that unbalanced semiprimes have a distinctive geometric signature:

1. **τ-space structure**: Define τ(b) as a log-folded geometric score over scale parameter b (representing 2^b as a candidate factor magnitude)

2. **Left-edge cliff**: At the scale corresponding to the smaller factor, there exists a sharp transition in τ (a "cliff") that can be detected via higher-order derivatives

3. **Third derivative spike**: The third derivative τ'''(b) shows a characteristic spike at the cliff location, analogous to detecting discontinuities in signal processing

## Method

### τ-Function Definition

The τ-function computes a geometric resonance score at scale b:

```
τ(b) = log(1 + geometric_score × decay)
```

Where:
- `scale = 2^b` (candidate factor magnitude)
- `geometric_score` combines:
  - **Modular resonance**: How close N mod scale is to 0 or scale (divisibility signal)
  - **Phase alignment**: Golden ratio phase relationships
- `decay = exp(-|log(scale/√N)| × 0.5)` (focuses signal near plausible factors)

### Derivative Computation

Derivatives are computed via finite differences:

```
τ'(b)   ≈ (τ(b+h) - τ(b-h)) / (2h)           # First derivative
τ''(b)  ≈ (τ(b+h) - 2τ(b) + τ(b-h)) / h²     # Second derivative
τ'''(b) ≈ (τ(b+2h) - 2τ(b+h) + 2τ(b-h) - τ(b-2h)) / (2h³)  # Third derivative
```

### Spike Detection

A spike in τ'''(b) is detected when:
```
|τ'''(b)| > threshold_factor × mean(|τ'''|)
```

Default `threshold_factor = 2.0` (points exceeding 2× the mean absolute value).

### Factor Mapping

When a spike is detected at b*, candidates are generated in the region:
```
[2^(b* - radius), 2^(b* + radius)]
```

Default `radius = 3.0` bits, generating candidates within ±8× of the central estimate.

## Algorithm

```
1. Set adaptive precision: max(50, N.bit_length() × 4 + 200) dps
2. Define τ scan range: [1, log₂(√N) + 2] bits
3. Compute τ(b) for num_scan_points values of b
4. Compute τ'(b), τ''(b), τ'''(b) via finite differences
5. Find spikes where |τ'''(b)| > threshold × mean
6. For each spike at b*:
   a. Generate candidates around 2^b*
   b. Test each candidate c: if N % c == 0, return (c, N/c)
7. Report success or failure
```

## Constraints

This experiment adheres to the following constraints from AGENTS.md / CODING_STYLE.md:

- **No prior knowledge**: The algorithm does not use the known factors (p, q) in any way
- **No classical fallbacks**: No Pollard's Rho, ECM, trial division, or sieves
- **Deterministic methods**: Sobol/Halton sampling if needed (not used in current implementation)
- **Explicit precision**: Adaptive precision formula is documented and logged
- **Final validation only**: The only divisibility check `N % candidate == 0` is for validation, not search

## Running the Experiment

```bash
cd experiments/unbalanced-left-edge-127bit
python3 run_experiment.py
```

### Expected Output Format

```
N = 137524771864208156028430259349934309717
mode = UNBALANCED_LEFT_EDGE
tau_scan_range = [1.0, 65.xx]
tau_third_derivative_spike_at = <b* or None>
candidate_factor_found = <p or None>
cofactor = <q or None>
verified = <true/false>
elapsed_ms = <...>
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_scan_points` | 500 | Number of points in τ scan |
| `spike_threshold_factor` | 2.0 | Spike detection threshold (× mean) |
| `max_spikes_to_test` | 20 | Maximum spikes to investigate |
| `search_radius_bits` | 3.0 | Search radius around spike (bits) |
| `candidates_per_spike` | 5000 | Max candidates per spike location |

## Falsification Criteria

The hypothesis is **falsified** if:

1. No τ''' spikes are detected at meaningful locations
2. Spikes do not correlate with factor locations
3. The experiment fails to find factors within the computational budget
4. Any factor found is attributable to random chance rather than geometric signal

The hypothesis is **supported** if:

1. A clear τ''' spike appears at the scale corresponding to a factor
2. The spike is significantly above the noise floor
3. Candidates generated from the spike location yield the factor
4. The result is reproducible

## Files

- `run_experiment.py` - Main experiment script
- `README.md` - This documentation
- `EXECUTIVE_SUMMARY.md` - Results summary (generated after run)
- `experiment_results.json` - Structured results (generated after run)

## References

- [VALIDATION_GATES.md](../../docs/VALIDATION_GATES.md) - 127-bit challenge specification
- [CODING_STYLE.md](../../docs/CODING_STYLE.md) - Style and constraint requirements
- [gva_factorization.py](../../gva_factorization.py) - Related GVA implementation
