# GVA 5D Falsification Experiment

## Quick Navigation

**Start here:** [falsification_design_spec.md](falsification_design_spec.md) - Complete technical design specification

Supporting documents:
- [README.md](README.md) - Experiment overview, setup, and execution instructions
- [EXPERIMENT_SUMMARY.md](EXPERIMENT_SUMMARY.md) - Results and findings (populated after execution)

Code artifacts:
- [gva_5d_falsification.py](gva_5d_falsification.py) - Main experiment implementation

## TL;DR

**Hypothesis:** GVA (Geodesic Validation Assault) claims that 5D toroidal embedding with Riemannian geodesic distance and Jacobian-weighted QMC sampling can efficiently factor RSA moduli, achieving 15-20% density enhancement and 100x speedup.

**Falsification Targets:**
- RSA-100 (330 bits): Primary falsification test
- RSA-129 (427 bits): Stretch goal
- CHALLENGE_127 (127 bits): Positive control

**Method:** Test whether GVA can factor RSA-100 within 10^6 QMC samples (implied by 100x speedup claim). Measure density enhancement, variance reduction, and distance correlation.

**Implementation Status:** ✅ Complete, ready to execute

**Expected Outcome:** Falsification - GVA will not factor RSA-100 within budget, demonstrating that geodesic distance minima do not reliably indicate factor locations.

---

## Executive Summary

The GVA hypothesis posits that:
1. Embedding integers into high-dimensional tori (5D or 7D) reveals factorization structure
2. Geodesic distances on Riemannian manifolds guide factor search
3. QMC sampling with Jacobian-weighted scale factors provides 15-20% density enhancement
4. The method achieves 100x speedup over classical approaches

This experiment rigorously tests these claims using industry-standard RSA challenge numbers.

### Falsification Criteria

The GVA hypothesis is **falsified** if:
- RSA-100 not factored within 10^6 QMC samples
- OR density enhancement < 10% (below claimed 15-20%)
- OR distance correlation < 0.2
- OR no measurable speedup vs baseline

### Test Configuration

**RSA-100 Test:**
- N = 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
- p = 37975227936943673922808872755445627854565536638199
- q = 40094690950920881030683735292761468389214899724061
- Budget: 10^6 QMC samples
- Precision: 1520 decimal digits (adaptive)
- Expected: **FAILURE** (falsification)

**CHALLENGE_127 Baseline:**
- N = 137524771864208156028430259349934309717
- Used as positive control to verify implementation
- Only allowed non-RSA exception per VALIDATION_GATES.md

### Key Features

1. **5D Torus Embedding**: Golden ratio quasi-periodicity, geodesic exponent k ∈ [0.30, 0.35, 0.40]
2. **Jacobian Weighting**: Scale factor w(θ) = sin⁴θ₁ · sin²θ₂ · sinθ₃
3. **Riemannian Distance**: Curvature-weighted metric κ(n) = d(n)·ln(n+1)/e²
4. **QMC Sampling**: Sobol sequences with deterministic seeding
5. **Bootstrap CIs**: 1000 resamples for density enhancement confidence intervals

### Metrics Collected

- Success rate (factors found within budget)
- Density enhancement from Jacobian weighting
- Variance reduction vs uniform sampling
- Geodesic distance correlation with factors
- Time/sample efficiency
- Bootstrap 95% confidence intervals

---

## Reproducibility

To execute the experiment:

```bash
cd /home/runner/work/geofac/geofac/experiments/pr-1-gva-falsification-experiment

# Quick test on CHALLENGE_127 (positive control, ~5 minutes)
python3 gva_5d_falsification.py --target CHALLENGE_127 --samples 100000

# Full RSA-100 falsification test (~8 hours)
python3 gva_5d_falsification.py --target RSA-100 --samples 1000000

# RSA-129 stretch goal (~80 hours)
python3 gva_5d_falsification.py --target RSA-129 --samples 10000000
```

**Note:** RSA-100 and RSA-129 tests require significant computational resources and high precision arithmetic. The expected outcome is falsification (no factors found within budget).

Results are automatically saved to `results_{target}_{timestamp}.json`.

---

## Files

| File | Purpose |
|------|---------|
| INDEX.md (this file) | Navigation and TL;DR |
| falsification_design_spec.md | Complete technical specification |
| README.md | Experiment overview and instructions |
| EXPERIMENT_SUMMARY.md | Results and findings (populated after execution) |
| gva_5d_falsification.py | Main implementation with 5D embedding, geodesic distance, QMC sampling |

---

## Technical Details

### 5D Torus Embedding

Map integer n to T^5 = [0,1)^5:
```
θᵢ = (n · φⁱ⁺¹)^k mod 1,  i = 0..4
```
where φ = (1+√5)/2 is golden ratio, k is geodesic exponent.

### Jacobian-Derived Scale Factors

Volume element for 5D spherical coordinates:
```
dV = r⁴ sin⁴θ₁ sin³θ₂ sin²θ₃ sinθ₄ dr dθ₁ dθ₂ dθ₃ dθ₄
```

Simplified weight for rejection sampling:
```
w(θ) = sin⁴θ₁ · sin²θ₂ · sinθ₃
```

### Riemannian Metric

Curvature-weighted distance on torus:
```
κ(n) = d(n) · ln(n+1) / e²
dist²(p,q) = Σᵢ κᵢ · min(|pᵢ-qᵢ|, 1-|pᵢ-qᵢ|)²
```

### Validation Gates

Per docs/VALIDATION_GATES.md:
- Operational range: [10^14, 10^18]
- Whitelist: 127-bit CHALLENGE_127 = 137524771864208156028430259349934309717
- Test only on RSA challenge numbers (no synthetic semiprimes)
- No classical fallbacks (no Pollard's Rho, ECM, trial division beyond 2,3,5)

### Precision Management

Adaptive precision formula:
```python
precision = max(50, N.bitLength() × 4 + 200)
```

Examples:
- 127-bit: 708 dps
- 330-bit (RSA-100): 1520 dps
- 427-bit (RSA-129): 1908 dps

---

## Expected Falsification Outcome

We expect this experiment to **falsify** the GVA hypothesis by demonstrating:

1. **No factors found for RSA-100** within 10^6 QMC samples (contradicts claimed 100x speedup)
2. **Low density enhancement** < 15% (below claimed 15-20% range)
3. **Weak distance correlation** r < 0.3 between geodesic distance and factor proximity
4. **No speedup** vs uniform baseline search

This outcome would indicate that:
- Geodesic distance minima do not reliably indicate factor locations
- Jacobian weighting provides minimal or no advantage
- The geometric structure claimed by GVA does not generalize to cryptographically-relevant scales
- Classical factorization difficulty (exponential) remains in place

---

Read [falsification_design_spec.md](falsification_design_spec.md) for complete technical details and [EXPERIMENT_SUMMARY.md](EXPERIMENT_SUMMARY.md) for results (to be populated after execution).
