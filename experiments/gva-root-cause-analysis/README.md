# GVA Root-Cause Analysis

## Overview

Diagnostic experiment to understand WHY GVA (Geodesic Validation Assault) fails in the operational range [10^14, 10^18] despite succeeding on Gate 1 (30-bit).

Following the falsification of the 8D Imbalance-Tuned GVA hypothesis, this experiment investigates the fundamental limitations of the GVA approach through two diagnostic phases.

## Motivation

The 8D experiment revealed:
- Both 7D and 8D GVA fail on operational range semiprimes (even balanced cases)
- Success on Gate 1 (30-bit) but failure at 47-50 bits
- Root cause is NOT imbalance sensitivity

**Key Question**: Why does GVA work on small semiprimes but fail as bit-length increases?

## Phase 1: Signal Decay and Parameter Sensitivity

### Phase 1.1: Geodesic Signal Decay Analysis

Tests hypothesis: **SNR decays exponentially with bit-length**

**Methodology**:
- Generate balanced RSA-style semiprimes from 20-bit to 50-bit
- 10 samples per bit-length for statistical robustness
- Measure geodesic distances at true factor locations vs random candidates
- Calculate SNR = (min_distance_at_factors) / (avg_distance_over_candidates)
- Visualize decay curve

**Expected Result**: If SNR decays exponentially, this explains why GVA loses signal in operational range.

### Phase 1.2: Parameter Sensitivity Sweep

Tests hypothesis: **Failure is NOT due to suboptimal parameters**

**Methodology**:
- Grid search over k ∈ [0.1, 0.5] in 0.05 increments (9 values)
- Grid search over candidate budgets: [10k, 25k, 50k, 100k, 250k, 500k, 1M] (7 values)
- Test on 47-bit balanced semiprime (N=100000001506523, operational range)
- 63 total parameter combinations
- Measure success rate, runtime, false positive rate

**Expected Result**: If no parameter combination succeeds, confirms that parameters are not the limiting factor.

## Reproduction

### Prerequisites

```bash
pip install mpmath matplotlib numpy
```

### Run Phase 1.1

```bash
cd experiments/gva-root-cause-analysis
python3 geodesic_signal_decay.py
```

Generates:
- `signal_decay_data.json` - Raw measurements
- Terminal output with statistics

### Run Phase 1.2

```bash
python3 parameter_sensitivity_sweep.py
```

Generates:
- `parameter_sweep_results.json` - Grid search results
- Terminal output with success rates

### Generate Visualizations

```bash
python3 generate_visualizations.py
```

Generates:
- `snr_vs_bitlength.png` - Signal decay curve
- `parameter_sensitivity_heatmap.png` - Success/runtime heatmaps

### Expected Runtime

- Phase 1.1: ~5-15 minutes (310 measurements)
- Phase 1.2: ~10-30 minutes (63 parameter combinations)
- Visualizations: <10 seconds

## File Descriptions

| File | Purpose |
|------|---------|
| `geodesic_signal_decay.py` | Phase 1.1 implementation |
| `parameter_sensitivity_sweep.py` | Phase 1.2 implementation |
| `generate_visualizations.py` | Plot generation |
| `signal_decay_data.json` | Phase 1.1 output data |
| `parameter_sweep_results.json` | Phase 1.2 output data |
| `snr_vs_bitlength.png` | Signal decay visualization |
| `parameter_sensitivity_heatmap.png` | Parameter sweep visualization |
| `EXECUTIVE_SUMMARY.md` | Findings and conclusions |
| `INDEX.md` | Experiment metadata |

## Key Invariants

All code follows repository guidelines:

- **Validation Gates**: All test semiprimes are balanced RSA-style numbers in [10^14, 10^18] operational range
- **No Classical Fallbacks**: Pure GVA geodesic distance metric only
- **Precision**: Adaptive precision = max(50, N.bitLength() × 4 + 200), logged per test
- **Reproducibility**: Deterministic seeds, logged parameters, timestamped outputs
- **Minimal Implementation**: Surgical code focused on diagnostic measurements

## Next Steps

After Phase 1 completes:
- Analyze findings in `EXECUTIVE_SUMMARY.md`
- Determine if Phase 2 (alternative geometric approaches) is warranted
- Or conclude that GVA fundamentally cannot scale to operational range
