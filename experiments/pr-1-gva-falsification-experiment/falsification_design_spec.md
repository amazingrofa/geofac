# GVA 5D Falsification Experiment - Technical Design Specification

## Executive Summary

This experiment tests the core GVA (Geodesic Validation Assault) hypothesis: that embedding numbers into high-dimensional tori (5D or 7D) and measuring geodesic distances can efficiently factor RSA moduli. We specifically target the claim that 5D toroidal embeddings with QMC sampling and Jacobian-derived scale factors provide 15-20% density enhancement and 100x speedup over baseline methods.

**Falsification Targets:**
- RSA-100 (330 bits): 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
- RSA-129 (427 bits): 114381625757888867669235779976146612010218296721242362562561842935706935245733897830597123563958705058989075147599290026879543541

**Falsification Criteria:**
1. Cannot factor RSA-100 within 10^6 QMC samples (claimed 100x speedup implies this should succeed)
2. Density enhancement < 15% (below claimed 15-20% range)
3. Variance reduction < 50% compared to uniform sampling
4. No correlation between geodesic distance minima and actual factors

## Background

The GVA hypothesis posits that:
1. Embedding integers into high-dimensional tori reveals factorization structure
2. Geodesic distances on Riemannian manifolds guide factor search
3. QMC sampling with Jacobian-weighted scale factors provides density enhancement
4. The method achieves 100x speedup over classical approaches

This experiment extends existing `gva_factorization.py` (7D implementation) to test 5D embeddings with specific claimed optimizations.

## Methodology

### 5D Torus Embedding

Map integer n to 5D torus T^5 = [0,1)^5 using angles (θ₀, θ₁, θ₂, θ₃, θ₄):

```
θᵢ = (n · φⁱ⁺¹)^k mod 1,  i = 0..4
```

where φ = (1 + √5)/2 (golden ratio) and k ∈ [0.25, 0.45] is geodesic exponent.

### Jacobian-Derived Scale Factors

For 5D spherical coordinates embedded in torus, volume element includes Jacobian:

```
dV = r⁴ sin⁴θ₁ sin³θ₂ sin²θ₃ sinθ₄ dr dθ₁ dθ₂ dθ₃ dθ₄
```

We use simplified scale factor for weighted sampling:

```
w(θ) = sin⁴θ₁ · sin²θ₂ · sinθ₃
```

This weights QMC samples toward regions with higher geometric density.

### Riemannian Metric

Geodesic distance uses curvature-weighted metric:

```
κ(n) = d(n) · ln(n+1) / e²
```

where d(n) is divisor count estimate. Distance on torus with periodic boundaries:

```
dist²(p, q) = Σᵢ κᵢ · min(|pᵢ - qᵢ|, 1 - |pᵢ - qᵢ|)²
```

### QMC Sampling Strategy

1. Generate Sobol sequence in [0,1)^5
2. Apply Jacobian weighting: reject samples with probability 1 - w(θ)/w_max
3. Map accepted samples to candidate factors near √N
4. Compute geodesic distance from N's embedding
5. Test factors with smallest distances

### Test Configuration

**RSA-100 Test:**
- Target: 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
- Factors: p = 37975227936943673922808872755445627854565536638199, q = 40094690950920881030683735292761468389214899724061
- Budget: 10^6 QMC samples (claimed 100x speedup implies success)
- k values: [0.30, 0.35, 0.40]
- Precision: max(50, 330 × 4 + 200) = 1520 decimal digits
- Expected: FAILURE (falsification)

**RSA-129 Test:**
- Target: 114381625757888867669235779976146612010218296721242362562561842935706935245733897830597123563958705058989075147599290026879543541
- Budget: 10^7 QMC samples (stretch goal)
- k values: [0.30, 0.35, 0.40]
- Precision: max(50, 427 × 4 + 200) = 1908 decimal digits
- Expected: FAILURE (falsification)

**Validation Baseline (127-bit CHALLENGE_127):**
- N = 137524771864208156028430259349934309717
- This is the only allowed exception outside [10^14, 10^18] range
- Use as positive control to verify implementation correctness

## Metrics

### Primary Metrics

1. **Success Rate**: Proportion of test cases where factors found within budget
2. **Speedup**: Time/samples ratio vs. baseline linear search
3. **Density Enhancement**: (geodesic_guided_density / uniform_density) - 1
4. **Variance Reduction**: 1 - (σ²_guided / σ²_uniform)

### Secondary Metrics

5. **Distance Correlation**: Pearson r between geodesic distance and factor proximity
6. **Sample Efficiency**: Samples needed to reach distance minimum
7. **Bootstrap CI Width**: 95% CI for density enhancement (1000 resamples)

## Experimental Design

### Experiment 1: Baseline Uniform Sampling
- No geodesic guidance
- Uniform QMC sampling
- Linear search around √N
- Establishes performance floor

### Experiment 2: Geodesic-Guided (No Weighting)
- Geodesic distance computed
- Uniform QMC sampling (no Jacobian weights)
- Distance-guided search
- Tests pure geometric hypothesis

### Experiment 3: Jacobian-Weighted QMC
- Full Jacobian scale factors
- Geodesic distance computed
- Combined guidance + weighting
- Tests complete GVA claim

### Ablation Study
Compare all three to isolate:
- Contribution of geodesic guidance alone
- Contribution of Jacobian weighting alone
- Interaction effects

## Implementation Requirements

### Precision Management
```python
def adaptive_precision(N: int) -> int:
    """Adaptive precision: max(50, N.bitLength() × 4 + 200)"""
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)
```

### Reproducibility
- Pin random seeds (use seed=42 for Sobol generator)
- Log all parameters: N, k, samples, precision, timeout
- Record timestamps
- Export results to JSON artifacts

### Validation Gates
- Only test on RSA challenge numbers (RSA-100, RSA-129)
- Use CHALLENGE_127 as positive control
- No synthetic "RSA-like" numbers
- Respect [10^14, 10^18] operational range for other tests

### No Classical Fallbacks
- No trial division beyond small primes (2, 3, 5)
- No Pollard's Rho, ECM, or sieve methods
- Purely geometric/geodesic approach
- Deterministic or quasi-deterministic only

## Expected Results (Falsification)

We expect this experiment to **falsify** the GVA hypothesis by demonstrating:

1. **RSA-100 Failure**: Cannot factor within 10^6 samples despite 100x speedup claim
2. **Low Density Enhancement**: < 15% improvement (below claimed 15-20%)
3. **Weak Distance Correlation**: r < 0.3 between distance and factor proximity
4. **High Variance**: Bootstrap CI for density enhancement includes zero
5. **No Speedup**: Time/sample ratio similar to or worse than uniform search

## Success Criteria for Falsification

The GVA hypothesis is considered **falsified** if:
- RSA-100 not factored within 10^6 QMC samples
- OR density enhancement < 10% with tight bootstrap CI
- OR distance correlation < 0.2
- OR no measurable speedup vs baseline

The hypothesis is considered **not yet falsified** if:
- RSA-100 factored within budget
- AND density enhancement > 15%
- AND distance correlation > 0.5
- AND speedup > 10x

## Artifacts

All runs will generate:
- `results_{timestamp}.json`: Complete results with all metrics
- `bootstrap_samples_{timestamp}.csv`: Bootstrap resamples for CI
- `distance_profile_{timestamp}.csv`: Geodesic distances for all candidates
- `execution_log_{timestamp}.txt`: Detailed execution log

## Timeline

- Implementation: 1 day
- RSA-100 test: ~8 hours (10^6 samples @ high precision)
- RSA-129 test: ~80 hours (10^7 samples @ high precision) - optional
- Analysis: 1 day

Total: 2-3 days for complete falsification experiment.

## References

- docs/VALIDATION_GATES.md - Project validation gates
- gva_factorization.py - Existing 7D GVA implementation
- docs/CODING_STYLE.md - Code style and invariants
- RSA Factoring Challenge: https://en.wikipedia.org/wiki/RSA_Factoring_Challenge

## Conclusion

This experiment provides a rigorous falsification test of the GVA hypothesis using industry-standard RSA challenge numbers, precise metrics, and controlled experimental design. The focus on RSA-100 with 10^6 samples directly tests the claimed 100x speedup, while the density enhancement and distance correlation metrics provide quantitative falsification criteria.
