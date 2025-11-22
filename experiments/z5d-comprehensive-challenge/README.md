# Z5D Comprehensive Challenge Experiment

A systematic, calibration-driven approach to factoring the 127-bit challenge semiprime using Z5D as a band/step oracle.

## Quick Start

```bash
# Navigate to experiment directory
cd experiments/z5d-comprehensive-challenge

# Run full experiment pipeline
python3 calibrate_bands.py      # Step 1: Calibration
python3 rehearsal_60_96bit.py   # Step 3: Rehearsal  
python3 parameterize_127bit.py  # Step 4: Parameterize
python3 production_run.py       # Step 5: Production run
python3 analyze_results.py      # Step 6: Analysis

# Run tests
pytest test_z5d_comprehensive.py -v
```

## Overview

This experiment implements a **comprehensive Z5D-informed GVA pipeline** that uses Z5D as a **stepping oracle** rather than just a score term. The approach is calibration-driven, systematic, and fully instrumented.

### Challenge
- **N** = 137524771864208156028430259349934309717
- **Factors**: p = 10508623501177419659, q = 13086849276577416863
- **Bit-length**: 127 bits

### Key Innovation
Previous experiments added Z5D density as a score term. This experiment separates concerns:
- **Z5D**: Guides which δ-bands to search (strategy layer)
- **210-Wheel**: Hard filter for admissibility (pruning layer)
- **FR-GVA**: Ranks candidates within filtered stream (ranking layer)

## Architecture

### Step 0: Z5D API (`z5d_api.py`)
Adapter providing Z5D oracle functionality:
- Prime index band prediction [k₋, k₊]
- Local density estimation using PNT
- Adaptive step size calculation
- δ-band prioritization

### Step 1: Calibration (`calibrate_bands.py`)
Measures Z5D accuracy across bit-lengths:
- Generates balanced semiprimes at 60, 70, 80, 90, 96 bits
- Computes prediction error ε(bit-length)
- Fits curve for 95% capture rate
- **Output**: `calibration_results.json`

### Step 2: Pipeline (`z5d_pipeline.py`)
Core candidate generation pipeline:
- 210-wheel filter (77% pruning)
- Z5D-guided δ-band traversal
- Adaptive stepping (dense → small, sparse → large)
- FR-GVA amplitude ranking

### Step 3: Rehearsal (`rehearsal_60_96bit.py`)
Tests 4 variants across scales:
- **Baseline**: uniform sampling, no filters
- **Wheel-only**: 210-wheel filter
- **Z5D-only**: Z5D stepping (no wheel)
- **Full-Z5D**: wheel + Z5D + GVA

Measures success rates at budgets: 10⁴, 10⁵, 10⁶
- **Output**: `rehearsal_results.json`

### Step 4: Parameterization (`parameterize_127bit.py`)
Computes optimal 127-bit parameters:
- Uses calibration ε(127)
- Uses rehearsal success curves
- Computes target coverage C* for 95% success
- Translates to candidate budget
- **Output**: `challenge_params.json`

### Step 5: Production (`production_run.py`)
Executes factorization attempt:
- Full Z5D mode
- 1-hour timeout
- Heavy instrumentation (log every 1000 candidates)
- **Output**: `run_log.jsonl`, `production_summary.json`

### Step 6: Analysis (`analyze_results.py`)
Post-run diagnostics:
- Diagnoses failure mode (band miss, budget miss, ranking miss)
- Suggests parameter adjustments
- **Output**: `retune_params.json`, `ANALYSIS_SUMMARY.md`

## Components

### Z5D Oracle (PNT-based)
Since enumerating primes near √N ≈ 10^19 is computationally prohibitive, we simulate Z5D using Prime Number Theorem:
- Density: ρ(x) ≈ 1/log(x)
- Gap: ḡ(x) ≈ log(x)
- Index: π(x) ≈ x/log(x)

This provides realistic density behavior for validating the pipeline concept.

### 210-Wheel Filter
Hard filter eliminating multiples of 2, 3, 5, 7:
- Modulus: 210
- Admissible residues: 48
- Pruning factor: 77.14%
- Zero false negatives

### FR-GVA Amplitude
Geodesic distance in 7D torus:
- Embedding: n ↦ (n·φᵈ mod 1)^k for d=1..7
- Distance: Riemannian metric with wraparound
- Used for ranking within Z5D-filtered stream

### Coverage Metric
Scale-invariant measure of search thoroughness:
```
C = (δ_span × wheel_factor) / log(√N)
```

Enables prediction of success probability across bit-lengths.

## Validation Gates

Per project requirements:
- **Gate 1** (30-bit): 1,073,217,479 = 32,749 × 32,771 ✓
- **Gate 3** (127-bit): Whitelisted challenge number
- **Gate 4**: Work in [10^14, 10^18] validation window

No classical fallbacks: no Pollard's Rho, ECM, trial division, or generic sieves.

## Precision

Explicit precision management:
- Uses mpmath with declared `mp.dps`
- Adaptive: max(100, N.bitLength() × 4 + 200)
- For 127-bit: ≥708 decimal places
- All precision choices logged

## Reproducibility

### Seeds Pinned
- Calibration: deterministic semiprime generation
- Rehearsal: fixed test cases
- Pipeline: quasi-deterministic traversal

### Parameters Logged
Every run exports:
- N, √N, bit-length
- ε, δ_max, budget, num_bands, k-value
- Timestamps, candidate counts
- Success/failure status

### Artifacts Exported
All intermediate results saved:
- JSON for structured data
- JSONL for streaming logs
- Markdown for reports

## Expected Performance

### Baseline Metrics
- Wheel pruning: 77%
- Expected gap at √N: ~44 units
- Base density: ~0.023 primes/unit

### Budget Estimates
Depends on calibration/rehearsal results. Typical:
- Coverage target C*: 50-100
- δ_max: 50,000-200,000
- Total budget: 10⁵-10⁶ candidates

### Failure Modes
1. **Band Miss**: Factor outside δ-range → increase δ_max/ε
2. **Budget Miss**: Exhausted candidates → increase budget
3. **Ranking Miss**: Factor in range but not tested → adjust k-value

## Usage

### Run Full Pipeline
```bash
# Step 1: Calibrate (generates calibration_results.json)
python3 calibrate_bands.py

# Step 3: Rehearse (generates rehearsal_results.json)
python3 rehearsal_60_96bit.py

# Step 4: Parameterize (generates challenge_params.json)
python3 parameterize_127bit.py

# Step 5: Execute (generates run_log.jsonl)
python3 production_run.py

# Step 6: Analyze (generates ANALYSIS_SUMMARY.md, retune_params.json)
python3 analyze_results.py
```

### Run Individual Components
```bash
# Test Z5D API
python3 z5d_api.py

# Test pipeline on small case
python3 z5d_pipeline.py

# Run test suite
pytest test_z5d_comprehensive.py -v
```

### Quick Validation
```bash
# Run tests only (fastest check)
pytest test_z5d_comprehensive.py -v
```

## Dependencies

- Python 3.12.3
- mpmath (arbitrary precision arithmetic)
- pytest (for tests)

Already installed in geofac environment.

## File Manifest

### Core Implementation
- `z5d_api.py` - Z5D oracle adapter (Step 0)
- `calibrate_bands.py` - Calibration script (Step 1)
- `z5d_pipeline.py` - Candidate pipeline (Step 2)
- `rehearsal_60_96bit.py` - Rehearsal experiments (Step 3)
- `parameterize_127bit.py` - Parameter computation (Step 4)
- `production_run.py` - Production execution (Step 5)
- `analyze_results.py` - Post-run analysis (Step 6)

### Tests & Documentation
- `test_z5d_comprehensive.py` - Pytest test suite
- `EXECUTIVE_SUMMARY.md` - High-level overview
- `README.md` - This file

### Generated Artifacts
- `calibration_results.json` - Calibration output
- `rehearsal_results.json` - Rehearsal output
- `challenge_params.json` - Computed parameters
- `run_log.jsonl` - Production run log
- `production_summary.json` - Run summary
- `retune_params.json` - Adjusted parameters
- `ANALYSIS_SUMMARY.md` - Post-run report

## Theory

### Prime Number Theorem
Foundation for Z5D simulation:
```
π(x) ~ x / log(x)          (prime counting)
p_n ~ n × log(n)           (n-th prime)
ḡ(x) ~ log(x)             (average gap)
ρ(x) ~ 1/log(x)           (local density)
```

### Wheel Sieve
Eliminates multiples of small primes deterministically.
For modulus M = 2×3×5×7 = 210:
- Admissible residues: φ(210) = 48
- Coverage: 48/210 ≈ 22.86%

### Geodesic Distance
7D torus embedding with golden ratio:
```
φ = (1 + √5)/2
coord_d = (n × φ^d mod 1)^k
```

Riemannian distance with wraparound for compositeness detection.

## Success Criteria

- **Primary**: Factor 127-bit challenge within 1-hour timeout
- **Secondary**: Success rate ≥50% on 60-96 bit rehearsal
- **Tertiary**: Pass all validation gate tests

## Limitations

### PNT Approximation
Z5D oracle uses PNT estimates rather than actual prime enumeration. This is necessary due to computational constraints at scale ~10^19.

### Scale Challenge
127-bit represents ~10^38 search space. Even with all optimizations, success is not guaranteed.

### No Fallbacks
Per project rules, no classical methods allowed. Pure geometric/density approach only.

## Next Steps

### If Successful
1. Document exact parameter set
2. Measure component timing breakdown
3. Scale to larger validation window cases

### If Failed
1. Review ANALYSIS_SUMMARY.md
2. Apply retune_params.json adjustments
3. Re-run production_run.py
4. Iterate until success or theoretical limit

## References

- Project CODING_STYLE.md - Coding standards
- Project VALIDATION_GATES.md - Scale requirements
- experiments/z5d-informed-gva/ - Previous Z5D work

## Contact

This experiment follows the geofac repository coding style and validation gates.
See AGENTS.md and CODING_STYLE.md in repository root for details.

---

**Status**: Implementation complete, ready for execution.
**Last Updated**: 2025-11-22
**Experiment**: z5d-comprehensive-challenge
