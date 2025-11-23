# GVA 5D Falsification Experiment

## Overview

This experiment rigorously tests the GVA (Geodesic Validation Assault) hypothesis: Can 5D toroidal embedding with Riemannian geodesic distance and Jacobian-weighted QMC sampling efficiently factor RSA moduli?

**Primary Goal:** Falsify the claim that GVA achieves 100x speedup and 15-20% density enhancement.

**Falsification Method:** Test on RSA-100 (330 bits) with 10^6 QMC samples. If the claimed 100x speedup were real, this budget should suffice. Failure to factor constitutes falsification.

## Hypothesis Under Test

The GVA method claims:
1. High-dimensional torus embeddings (5D or 7D) reveal factorization structure
2. Geodesic distances on Riemannian manifolds guide factor search
3. Jacobian-weighted QMC sampling provides 15-20% density enhancement
4. The method achieves 100x speedup over classical approaches

## Experimental Design

### Targets

1. **RSA-100** (330 bits) - Primary falsification target
   - N = 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
   - Known factors: p = 37975227936943673922808872755445627854565536638199, q = 40094690950920881030683735292761468389214899724061
   - Budget: 10^6 QMC samples
   - Expected: **FAILURE (falsification)**

2. **CHALLENGE_127** (127 bits) - Positive control
   - N = 137524771864208156028430259349934309717
   - Used to verify implementation correctness
   - Only allowed non-RSA exception per VALIDATION_GATES.md

3. **RSA-129** (427 bits) - Stretch goal
   - N = 114381625757888867669235779976146612010218296721242362562561842935706935245733897830597123563958705058989075147599290026879543541
   - Budget: 10^7 QMC samples
   - Expected: **FAILURE (falsification)**

### Methodology

**5D Torus Embedding:**
- Map integer n → T^5 = [0,1)^5 using golden ratio quasi-periodicity
- Geodesic exponent k ∈ [0.30, 0.35, 0.40]
- Formula: θᵢ = (n · φⁱ⁺¹)^k mod 1

**Jacobian Weighting:**
- Scale factor from 5D spherical volume element: w(θ) = sin⁴θ₁ · sin²θ₂ · sinθ₃
- Applied via rejection sampling to QMC points
- Target: 15-20% density enhancement

**Riemannian Distance:**
- Curvature-weighted metric: κ(n) = d(n)·ln(n+1)/e²
- Torus geodesic with periodic boundaries
- Hypothesis: Factors minimize distance to N's embedding

**QMC Sampling:**
- Sobol sequences (scrambled, seeded for reproducibility)
- Fallback to golden ratio sequence if scipy unavailable
- Deterministic/quasi-deterministic only (no stochastic search)

### Metrics

1. **Success Rate**: Did we find factors within budget?
2. **Density Enhancement**: (weighted_density / uniform_density) - 1
3. **Variance Reduction**: 1 - (σ²_weighted / σ²_uniform)
4. **Distance Correlation**: Pearson r between geodesic distance and factor proximity
5. **Sample Efficiency**: Samples needed to reach minimum distance
6. **Bootstrap CI**: 95% confidence interval for density enhancement (1000 resamples)

## Setup and Execution

### Prerequisites

```bash
# Required
python3 (3.7+)
mpmath

# Optional (for full functionality)
scipy (for Sobol QMC)
numpy (for bootstrap CIs)
```

### Installation

```bash
cd /home/runner/work/geofac/geofac/experiments/pr-1-gva-falsification-experiment

# Install dependencies (if needed)
pip3 install mpmath scipy numpy
```

### Running the Experiment

**Quick test on CHALLENGE_127** (~5 minutes):
```bash
python3 gva_5d_falsification.py --target CHALLENGE_127 --samples 100000
```

**Full RSA-100 falsification** (~8 hours):
```bash
python3 gva_5d_falsification.py --target RSA-100 --samples 1000000
```

**RSA-129 stretch goal** (~80 hours):
```bash
python3 gva_5d_falsification.py --target RSA-129 --samples 10000000
```

**Without saving results:**
```bash
python3 gva_5d_falsification.py --target RSA-100 --samples 1000000 --no-save
```

### Command-Line Options

```
--target {RSA-100, RSA-129, CHALLENGE_127}
    Factorization target (default: CHALLENGE_127)

--samples N
    Maximum QMC samples per k value (default: 100000)

--no-save
    Do not save results to JSON file
```

## Output

The experiment produces:
1. **Console output**: Real-time progress, metrics, and final verdict
2. **JSON results**: Complete data saved to `results_{target}_{timestamp}.json`

### Sample Output

```
======================================================================
GVA 5D Falsification Experiment
======================================================================
N = 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
Bit length: 330
Adaptive precision: 1520 dps
Max samples per k: 1000000
Jacobian weighting: True
Geodesic guidance: True
Random seed: 42
Timestamp: 2025-11-23T14:55:00
======================================================================

sqrt(N) ≈ 39020174043076899790...
Search window: ±1000000

--- Testing k = 0.30 (1/3) ---
N embedded at: [0.123456, 0.789012, 0.345678, ...]
Curvature κ(N) = 1.234567e+02

Generating 1000000 Sobol samples...
Applying Jacobian weighting...
Samples after weighting: 485231
Density enhancement: -2.9%

Testing candidates...
  Tested 10000 candidates, min distance: 3.456789e-03
  Tested 20000 candidates, min distance: 2.345678e-03
  ...

Completed k=0.30: 485231 candidates in 28765.43s
Min distance: 1.234567e-03

======================================================================
Experiment completed: No factors found
Total candidates tested: 1,455,693
Total time: 86400.00s
======================================================================

VERDICT: FALSIFIED
```

## Results Structure

The JSON results file contains:

```json
{
  "N": 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139,
  "N_bitlength": 330,
  "precision_dps": 1520,
  "sqrt_N": 39020174043076899790,
  "search_window": 1000000,
  "max_samples": 1000000,
  "k_values": [0.30, 0.35, 0.40],
  "use_jacobian": true,
  "use_geodesic": true,
  "seed": 42,
  "timestamp": "2025-11-23T14:55:00",
  "success": false,
  "factors": null,
  "method": "gva_5d",
  "target_name": "RSA-100",
  "falsification_verdict": "FALSIFIED",
  "experiments": [
    {
      "k": 0.30,
      "candidates_tested": 485231,
      "samples_generated": 1000000,
      "samples_weighted": 485231,
      "min_distance": 0.001234567,
      "min_distance_candidate": 39020174043076899790,
      "elapsed_seconds": 28765.43,
      "density_enhancement": -0.029,
      "distance_variance": 1.234e-05
    },
    ...
  ],
  "elapsed_seconds": 86400.00
}
```

## Falsification Criteria

The GVA hypothesis is **falsified** if:
1. RSA-100 not factored within 10^6 QMC samples ✓ (expected)
2. Density enhancement < 10% (below claimed 15-20%) ✓ (expected)
3. Distance correlation < 0.2 ✓ (expected)
4. No measurable speedup vs baseline ✓ (expected)

The hypothesis is **not yet falsified** if:
1. RSA-100 factored within budget
2. AND density enhancement > 15%
3. AND distance correlation > 0.5
4. AND speedup > 10x

## Validation Gates Compliance

Per docs/VALIDATION_GATES.md:

- ✓ **Operational range**: RSA-100, RSA-129 are industry-standard challenge numbers
- ✓ **Whitelist**: CHALLENGE_127 used as positive control only
- ✓ **No classical fallbacks**: Pure geometric/geodesic method (no Pollard's Rho, ECM, trial division beyond 2,3,5)
- ✓ **Deterministic**: QMC with seeded Sobol sequences, deterministic Jacobian weighting
- ✓ **Adaptive precision**: max(50, N.bitLength() × 4 + 200)
- ✓ **Reproducibility**: Pinned seeds, logged parameters, timestamped artifacts

## Expected Falsification Outcome

**We expect this experiment to falsify the GVA hypothesis** by demonstrating:

1. **No factors found** for RSA-100 within 10^6 samples (contradicts 100x speedup claim)
2. **Minimal density enhancement** < 10%, possibly negative (far below claimed 15-20%)
3. **Random distance correlation** r ≈ 0, indicating geodesic distance does not predict factors
4. **No speedup** vs uniform random search around √N

This would demonstrate that:
- The geometric structure claimed by GVA does not exist at cryptographic scales
- Geodesic distance minima are uncorrelated with factor locations
- Jacobian weighting provides no meaningful advantage
- Classical factorization difficulty (exponential) remains in place

## Next Steps After Execution

1. Populate EXPERIMENT_SUMMARY.md with complete results
2. Compute correlation between distance minima and known factors
3. Generate bootstrap confidence intervals for density enhancement
4. Compare variance across k values
5. Produce falsification verdict with statistical evidence

## References

- [falsification_design_spec.md](falsification_design_spec.md) - Complete technical specification
- [INDEX.md](INDEX.md) - Quick navigation
- docs/VALIDATION_GATES.md - Project validation gates
- docs/CODING_STYLE.md - Code style and invariants
- gva_factorization.py - Existing 7D GVA implementation

## Notes

- RSA-100 and RSA-129 tests require significant time and memory (high-precision arithmetic)
- The experiment is compute-bound, not I/O-bound
- Progress is reported every 10,000 candidates
- Early termination on success (though falsification is expected)
- All artifacts include timestamps for reproducibility auditing
