# GVA Root-Cause Analysis Suite

Experimental diagnostic toolkit to analyze why GVA (Geodesic Validation Assault) fails on 45-50 bit semiprimes in the operational range [10^14, 10^18] despite succeeding on Gate 1 (30-bit).

## Purpose

Identify the **root cause** of GVA scaling failures through:
1. **Signal decay quantification** - Measure geodesic signal-to-noise ratio across bit lengths
2. **Parameter sensitivity analysis** - Grid search to identify optimal configurations
3. **Theoretical simulation** - Mathematical modeling of phase cancellation behavior

## Modules

### 1. signal_decay_analyzer.py
Quantifies geodesic signal decay by computing Signal-to-Noise Ratio (SNR).

**Key metric**: SNR = min_distance_at_factors / avg_distance_over_candidates

Tests on bit lengths: 30, 40, 47, 50
Fits exponential decay: `SNR = a × exp(-b × bit_length)`

**Usage:**
```bash
python signal_decay_analyzer.py
```

**Outputs:**
- `results/snr_analysis.json` - Full SNR data
- `results/snr_plot.png` - Exponential decay visualization

### 2. parameter_sweep.py
Grid search over GVA parameters (k_values, candidate_budgets).

**Parameters tested:**
- k values: [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
- Candidate budgets: [10000, 50000, 100000]

**Usage:**
```bash
python parameter_sweep.py
```

**Outputs:**
- `results/param_sweep.csv` - All parameter combinations and results
- `results/param_heatmap_*.png` - Success rate and runtime heatmaps

### 3. theoretical_sim.py
Mathematical simulation of phase cancellation and geodesic distance.

Compares theoretical predictions vs empirical measurements.
Tests imbalance gradients: r = ln(q/p) from 0 to 1.4

**Usage:**
```bash
python theoretical_sim.py
```

**Outputs:**
- `results/theory_sim.md` - Theoretical analysis with identified flaws

### 4. gva_root_cause.py
Integration CLI script that runs all analyses and generates unified report.

**Usage:**
```bash
# Run all analyses
python gva_root_cause.py --mode all

# Run individual analysis
python gva_root_cause.py --mode signal_decay
python gva_root_cause.py --mode param_sweep
python gva_root_cause.py --mode theory_sim

# Test specific semiprime
python gva_root_cause.py --mode signal_decay --N 1073217479 --p 32749 --q 32771
```

**Output:**
- `results/report.md` - Unified executive summary with all findings

### 5. test_root_cause.py
Test suite validating each module.

**Usage:**
```bash
python test_root_cause.py
```

Tests on:
- Gate 1 (30-bit): 1073217479 = 32749 × 32771
- 47-bit balanced: 100000001506523 = 9999991 × 10000061

## Quick Start

Run full analysis suite:
```bash
cd experiments/gva-root-cause-analysis/
python gva_root_cause.py --mode all
```

View results:
```bash
ls results/
# snr_analysis.json  snr_plot.png  param_sweep.csv  param_heatmap_*.png  theory_sim.md  report.md
```

Read executive summary:
```bash
cat results/report.md
```

## Key Findings

**Root Cause:** Exponential signal decay due to ergodic behavior of 7D torus embedding.

**SNR Decay:** Signal-to-noise ratio decreases by ~5-10% per bit, making 50+ bit factorization infeasible.

**Parameter Insensitivity:** No combination of k or budget succeeds consistently on operational range semiprimes.

**Theoretical Flaws:**
1. Uniform minima distribution (ergodic behavior)
2. Phase cancellation does not scale
3. Higher dimensions do not help (validated by 8D experiment)

**Conclusion:** GVA has fundamental mathematical limitations that prevent scaling beyond ~35-40 bits. Incremental improvements cannot overcome exponential signal decay.

## Reproducibility

**Precision:** Adaptive based on N.bit_length()
- Formula: `max(50, N.bit_length() × 4 + 200)` decimal places

**Seeds:** All stochastic analyses use fixed seed = 42

**Test cases:** Known RSA-style semiprimes from validation gates

**Environment:**
- Python 3.12+
- mpmath 1.3.0
- numpy 2.0+
- matplotlib 3.8+

## Design Principles

Following CODING_STYLE.md:
- **Minimal code** - Smallest possible implementation
- **Plain language names** - Functions read like natural language
- **Explicit precision** - Adaptive precision logged for every computation
- **Reproducible** - Fixed seeds, logged parameters, timestamped outputs
- **No classical fallbacks** - Pure geometric analysis only
- **Linear code flow** - Guard clauses, early returns, no deep nesting

## Validation Gates

Test cases respect validation gate requirements:
- **Gate 1 (30-bit):** 1073217479 = 32749 × 32771
- **Operational range [10^14, 10^18]:** Used for 47-50 bit test cases
- **127-bit whitelist:** CHALLENGE_127 = 137524771864208156028430259349934309717

No synthetic "RSA-like" numbers used. All test semiprimes are from official gates or 8d-imbalance-tuned-gva experiment failures.

## References

- `gva_factorization.py` - Core GVA implementation
- `experiments/8d-imbalance-tuned-gva/` - Failure cases used as test inputs
- `docs/VALIDATION_GATES.md` - Official validation requirements
- `docs/CODING_STYLE.md` - Coding standards

## License

Same as parent repository.
