# 127-bit Challenge Router Attack Experiment

## Overview

This experiment attacks the 127-bit challenge semiprime using the portfolio router from PR #96. The router analyzes structural features to intelligently choose between FR-GVA and standard GVA, with fallback support for maximum coverage.

## Target

```
N₁₂₇ = 137524771864208156028430259349934309717
Expected p = 10508623501177419659
Expected q = 13086849276577416863
```

## Strategy

Based on the tech memo, the attack follows these steps:

1. **Compute Features** - Extract structural features (bit-length, √N, κ-band, segment score distribution)
2. **Router Decision** - Use PR #96 router to choose GVA vs FR-GVA based on feature similarity to training data
3. **Primary Execution** - Run chosen engine with 127-bit optimized config
4. **Fallback** - If primary fails, automatically try alternate engine
5. **Validation** - Confirm p·q = N₁₂₇ and match expected factors

## Configuration

Per tech memo specifications:

```python
precision: 800                          # Minimum decimal precision
max_candidates: 700,000                 # Candidate budget
k_values: [0.30, 0.35, 0.40]           # GVA k-sampling range
fr_gva_max_depth: 5                     # FR-GVA recursion depth
fr_gva_kappa_threshold: 0.525           # FR-GVA geodesic density gate
```

Adaptive precision formula: `max(configured, bitLength × 4 + 200)`

For 127-bit: `max(800, 127 × 4 + 200) = max(800, 708) = 800 dps`

## Files

- **`run_experiment.py`** - Main experiment script
- **`test_router_integration.py`** - Integration test with known test cases
- **`results/EXPERIMENT_REPORT.md`** - Comprehensive experiment report
- **`results/results.json`** - Machine-readable results
- **`README.md`** - This file

## Usage

### Quick Start

```bash
cd /home/runner/work/geofac/geofac
python3 experiments/127bit-challenge-router-attack/run_experiment.py
```

### Using CLI

```bash
python3 geofac.py --n 137524771864208156028430259349934309717 \
                  --use-router true \
                  --precision 800 \
                  --max-candidates 700000 \
                  --k-values 0.30 0.35 0.40
```

### Integration Test

Validate router setup with known test cases:

```bash
python3 experiments/127bit-challenge-router-attack/test_router_integration.py
```

Expected: 3/3 test cases pass (100% success rate with fallback)

## Router Methodology

The portfolio router (PR #96) uses weighted distance-based scoring:

### Features Analyzed
- **Bit length** (weighted 2x) - Primary predictor
- **Kappa (κ)** (weighted 1x) - Secondary signal

### Decision Algorithm

```python
# Score both methods based on feature proximity
gva_score = bit_proximity_gva * 2.0 + kappa_proximity_gva * 1.0
fr_gva_score = bit_proximity_fr_gva * 2.0 + kappa_proximity_fr_gva * 1.0

# Choose method with higher score
chosen_method = "FR-GVA" if fr_gva_score > gva_score else "GVA"
```

Proximity uses inverse distance with exponential decay:
```python
proximity = 1.0 / (1.0 + distance * decay_rate)
```

### Training Data (PR #93)

Router learns from 6 test cases showing complementary success patterns:

| Method | Success Cases | Bit Range | Gap Pattern |
|--------|---------------|-----------|-------------|
| GVA | 3/6 (50%) | 50-60 bits | Very small gaps (10⁻⁹ to 10⁻⁷) |
| FR-GVA | 3/6 (50%) | 47-57 bits | Medium gaps (10⁻⁷ to 10⁻⁶) |
| Router (with fallback) | 6/6 (100%) | All | All |

### Expected Router Decision for N₁₂₇

- Bit length: 127 → Outside training range, extrapolates from patterns
- Kappa: ~29.4 → Higher than training data
- Prediction: Router will choose based on which training cluster is closer

## Reproducibility

All methods are deterministic/quasi-deterministic:

- **Adaptive precision:** Explicit formula logged
- **QMC sampling:** Sobol/Halton sequences (no randomness)
- **Phase snapping:** Deterministic geometric corrections
- **Fixed parameters:** All values logged to JSON
- **Validation gates:** Whitelist for 127-bit challenge

## Expected Behavior

Per tech memo:

> Router should choose FR-GVA if the 127-bit curvature/band looks "distant-factor-like."
> With fallback enabled, combined system should cover the target even if first pick misses.

Portfolio approach achieves 100% coverage by:
1. Making intelligent first choice (67% accuracy)
2. Falling back to alternate method if needed (100% with both)

## References

- **PR #93:** FR-GVA implementation and complementary success analysis
- **PR #96:** Portfolio router implementation and validation
- **Tech Memo:** Router-based 127-bit attack strategy
- **CODING_STYLE.md:** Validation gates and reproducibility requirements
- **VALIDATION_GATES.md:** Gate 3 (127-bit challenge) specifications

## Notes

- Current FR-GVA implementation uses `max_depth` and `kappa_threshold` parameters
- CLI accepts `segments`, `top-k`, `min-random-segments` for documentation/future use
- Both engines respect the 127-bit whitelist (CHALLENGE_127)
- No classical fallbacks (Pollard Rho, ECM, etc.) are used
