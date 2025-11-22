# Z5D-Informed GVA: Quick Start Guide

## What is This Experiment?

This experiment tests whether integrating insights from the Z5D Prime Predictor project into Fractal-Recursive GVA (FR-GVA) can improve factorization performance on the 127-bit challenge semiprime.

**Hypothesis:** Combining Z5D's prime density oracle with GVA's geometric resonance creates synergy that outperforms either approach alone.

**Target:** N = 137524771864208156028430259349934309717 (127-bit challenge, Gate 3)

## Key Transferable Concepts from Z5D

1. **Prime Density Oracle:** Use Z5D to map prime density around √N, then weight GVA segments by this density
2. **Window×Wheel Gap Rule:** Ensure (δ-span × wheel_fraction) ≫ expected_gap prevents under-sampling
3. **Wheel Residue Filter:** Only test candidates in admissible residue classes mod 210 (~77% pruning)
4. **Z5D-Shaped Stepping:** Variable δ-steps based on local prime density (denser sampling in high-density regions)
5. **Cross-Project Integration:** Arithmetic (Z5D) + Geometric (GVA) orthogonal approaches

## Quick Validation

### Test Wheel Filter (< 1 second)

```bash
cd /home/runner/work/geofac/geofac/experiments/z5d-informed-gva
python3 wheel_residues.py
```

Expected output: 77.14% pruning factor, gap rule tests, residue validation

### Test Z5D Density Simulation (< 5 seconds)

```bash
python3 z5d_density_simulator.py
```

Expected output: 2001 bins, density range [1.68e-02, 2.64e-02], CSV files created

### Test Individual Components (60-bit, ~30 seconds)

```bash
# Baseline FR-GVA
python3 -c "
from baseline_fr_gva import baseline_fr_gva
N = 1152921470247108503  # 60-bit test case
result = baseline_fr_gva(N, max_candidates=10000, delta_window=100000, verbose=True)
print('Result:', result)
"

# Z5D-Enhanced FR-GVA
python3 -c "
from z5d_enhanced_fr_gva import z5d_enhanced_fr_gva
N = 1152921470247108503
result = z5d_enhanced_fr_gva(N, max_candidates=10000, delta_window=100000, verbose=True)
print('Result:', result)
"
```

## Full Experiment Execution

**Warning:** The 127-bit challenge requires significant computational resources (hours to days depending on hardware).

### Run All 4 Experiments (Interactive)

```bash
python3 comparison_experiment.py
```

This runs:
1. Baseline FR-GVA (control)
2. Wheel filter only (isolate arithmetic benefit)
3. Z5D prior only (isolate density benefit)
4. Full Z5D (test synergy hypothesis)

Results exported to `comparison_results.json`

### Run Individual Experiments

```bash
# Baseline only
python3 baseline_fr_gva.py

# Z5D-enhanced only
python3 z5d_enhanced_fr_gva.py
```

## Understanding Results

### Success Metrics

**Hypothesis is SUPPORTED if:**
- Z5D density prior changes segment selection toward actual factors
- Kernel amplitudes correlate with Z5D prime-dense regions
- Sample counts reduced ≥20% vs. baseline
- Full Z5D outperforms wheel-only and Z5D-only variants

**Hypothesis is FALSIFIED if:**
- Z5D prior doesn't change segment ordering
- No correlation between amplitude and density
- No performance improvement
- Wheel filter alone accounts for all benefits (Z5D redundant)

### Key Output Files

- `comparison_results.json` - Metrics for all 4 experiments
- `z5d_density_histogram.csv` - Prime density data (2001 bins)
- `z5d_density_metadata.txt` - Simulation parameters

## Parameters (Configurable)

### Baseline FR-GVA

```python
baseline_fr_gva(
    N,
    k_value=0.35,           # Geodesic exponent
    max_candidates=50000,   # Candidate budget
    delta_window=500000,    # Half-width of search around √N
    verbose=True
)
```

### Z5D-Enhanced FR-GVA

```python
z5d_enhanced_fr_gva(
    N,
    z5d_density_file="z5d_density_histogram.csv",
    k_value=0.35,
    max_candidates=50000,
    delta_window=500000,
    z5d_weight_beta=0.1,     # Z5D density weight in scoring
    use_wheel_filter=True,   # Enable/disable wheel
    use_z5d_stepping=True,   # Enable/disable variable stepping
    verbose=True
)
```

## File Structure

```
z5d-informed-gva/
├── INDEX.md                      # Navigation (start here)
├── README.md                     # Full experiment design
├── EXPERIMENT_SUMMARY.md         # Methodology and status
├── THEORETICAL_ANALYSIS.md       # Mathematical foundations
├── QUICKSTART.md                 # This file
│
├── wheel_residues.py             # Wheel mod 210 utilities
├── z5d_density_simulator.py      # PNT-based density generator
├── baseline_fr_gva.py            # Baseline implementation
├── z5d_enhanced_fr_gva.py        # Z5D-enhanced implementation
├── comparison_experiment.py      # Full comparison framework
│
├── z5d_density_histogram.csv     # Simulated density data
└── z5d_density_metadata.txt      # Simulation metadata
```

## Theoretical Foundation

### Why This Might Work

1. **Z5D Precedent:** z5d-prime-predictor works at scales up to k ≈ 10^1233
2. **Gap Coverage:** Window×wheel rule prevents structural under-sampling
3. **Orthogonal Approaches:** Arithmetic (density) + Geometric (resonance)
4. **Deterministic:** No stochastic fallbacks; all components reproducible

### Why This Might Not Work

1. **Task Mismatch:** Prime finding ≠ factorization
2. **Scale Limitation:** Density variations at 10^19 may be too fine
3. **Simulation Approximation:** PNT-based, not exact enumeration
4. **Geometric Dominance:** GVA signal may override density prior

## Expected Runtime

- **60-bit test cases:** 5-30 seconds per experiment
- **127-bit challenge:** Hours to days per experiment (scale-dependent)
- **Full comparison (4 experiments):** ~4× single experiment time

## Troubleshooting

**ModuleNotFoundError: No module named 'mpmath'**
```bash
pip install mpmath
```

**"Z5D density file not found"**
```bash
python3 z5d_density_simulator.py
```

**"No factors found within budget"**
- Increase `max_candidates` (e.g., 100000, 200000)
- Increase `delta_window` (e.g., 1000000)
- Try different `k_value` (0.30, 0.35, 0.40)
- Adjust `z5d_weight_beta` (0.01, 0.1, 0.5)

## References

- **Problem Statement:** See task description in repository issue
- **Z5D Prime Predictor:** github.com/zfifteen/z5d-prime-predictor
- **Validation Gates:** ../../docs/VALIDATION_GATES.md
- **Coding Style:** ../../CODING_STYLE.md

## Status

✅ **Framework Complete** - All components implemented and tested

⏳ **Execution Pending** - Awaiting computational resources for 127-bit challenge

📊 **Results TBD** - Hypothesis will be supported or falsified based on empirical data

---

**Next Step:** Run `python3 comparison_experiment.py` to execute the full experiment.
