# FFT-Based Candidate Selection Experiment

## Quick Navigation

**Start here:** [README.md](README.md) - Design, methodology, and setup

Code artifacts:
- [superscarred_ergodicity.py](superscarced_ergodicity.py) - Complete experiment implementation

Test artifacts:
- [../../tests/test_superscarred_ergodicity.py](../../tests/test_superscarred_ergodicity.py) - Unit tests

## TL;DR

**Objective:** Test whether FFT analysis of κ(n) (curvature) can identify candidate regions for factorization.

**Method:** Frequency-domain analysis (FFT) of κ(n) to find spectral peaks and energy-concentrated regions.

**Honest disclaimer:** The original prompt referenced "Ruelle zeta resonances" and "superscarred ergodicity." These terms are from quantum chaos and dynamical systems theory but are NOT rigorously justified for integer factorization. This is empirical signal processing, not theoretical mathematics.

**Key Components:**
1. **Window & Detrend**: High-pass or median-remove detrending of κ(n) series
2. **Spectral Scan (FFT)**: Magnitude spectrum |K(f)|, spectral entropy, peak prominence
3. **Energy Localization**: Measure concentration (top 10% tiles)/(total energy)
4. **Stability Test**: Sinusoidal perturbations n' = n + ε·sin(2πn/L), retain candidates with ≥60% peak overlap
5. **Candidate Shortlist**: Rank by (peak_height × stability × localization_score)

**Validation Thresholds (empirical, not theoretical):**
- **Gate A**: At least one FFT peak with prominence z-score ≥ 2.0
- **Gate B**: Stability overlap ≥ 60% under perturbations
- **Gate C**: Candidate windows reduce arithmetic checks by ≥ 10%

**Validation Range:**
- Primary gate: CHALLENGE_127 = 137524771864208156028430259349934309717
- Operational range: [10^14, 10^18]

---

## Quick Start

```bash
cd /home/runner/work/geofac/geofac/experiments/superscarred-ergodicity-insight

# Run on 127-bit challenge (default)
python3 superscarred_ergodicity.py

# Run on custom N in operational range
python3 superscarred_ergodicity.py --n 100000000000007 --half-window 5000

# Run tests
cd /home/runner/work/geofac/geofac
python3 -m pytest tests/test_superscarred_ergodicity.py -v
```

---

## Outputs

Each run produces:
1. `experiment_results.json` - Complete configuration and metrics
2. `peak_table.csv` - Frequency, height, bandwidth, z-score for top peaks
3. `candidates.csv` - Ranked candidate windows (start_n, end_n, composite_score)
4. `spectrum_tiles_*.png` - Visualization of spectrum and tile energy distribution

---

## Files

| File | Purpose |
|------|---------|
| INDEX.md (this file) | Navigation and TL;DR |
| README.md | Design, methodology, and setup |
| superscarred_ergodicity.py | Complete experiment implementation |
| results_*/ | Output directories with JSON, CSV, PNG |

---

## Reproducibility

All experiments use:
- Deterministic seeding (default: seed=42)
- Explicit precision: max(50, N.bit_length() × 4 + 200) dps
- Logged parameters with timestamps
- No stochastic methods (Sobol/Halton-style QMC only)

## What This Is (and Isn't)

**This IS:**
- Empirical signal processing on κ(n) sequences
- Exploratory data analysis with FFT
- Heuristic candidate selection

**This is NOT:**
- Theoretical connection to quantum chaos
- Application of Ruelle zeta function theory
- Geodesic flow analysis on tori

The original prompt used these sophisticated terms, but they are not mathematically justified for this problem. The experiment may still be useful as practical feature engineering, but claims of theoretical foundations should be disregarded.

---

## See Also

- [../../gva_factorization.py](../../gva_factorization.py) - GVA factorization with geodesic guidance
- [../geometric_resonance_factorization.py](../geometric_resonance_factorization.py) - Geometric resonance pipeline
- [../cornerstone_invariant.py](../cornerstone_invariant.py) - Curvature κ(n) computation
