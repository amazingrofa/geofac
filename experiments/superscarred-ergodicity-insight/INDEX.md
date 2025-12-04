# Superscarred Ergodicity Insight Experiment

## Quick Navigation

**Start here:** [README.md](README.md) - Design, methodology, and setup

Code artifacts:
- [superscarred_ergodicity.py](superscarred_ergodicity.py) - Complete experiment implementation

Test artifacts:
- [../../tests/test_superscarred_ergodicity.py](../../tests/test_superscarred_ergodicity.py) - Unit tests

## TL;DR

**Objective:** Apply Ruelle-like spectral resonance analysis to improve geometry-ranking before arithmetic certification.

**Method:** Analyze κ(n) (curvature/Dirichlet amplitude) over search intervals to find "Ruelle-like" resonances via spectral analysis (FFT), then identify "scarred" regions with concentrated energy.

**Key Components:**
1. **Window & Detrend**: High-pass or median-remove detrending of κ(n) series
2. **Spectral Scan (FFT)**: Magnitude spectrum |K(f)|, spectral entropy, peak prominence
3. **Scar Score on Rectangles**: Tiled energy concentration (energy in top 10% tiles)/(total energy)
4. **Stability Test**: Sinusoidal perturbations n' = n + ε·sin(2πn/L), retain candidates with ≥60% peak overlap
5. **Candidate Shortlist**: Rank by (peak_height × stability × scar_score)

**Pass/Fail Gates:**
- **Gate A**: At least one robust peak (prominence z-score ≥ 2.0)
- **Gate B**: Stability overlap ≥ 60% under all ε perturbations
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

---

## Theoretical Foundation

The experiment is inspired by:

1. **Ruelle Resonances**: In dynamical systems, Ruelle resonances characterize decay of correlations in chaotic systems. The spectral peaks in our κ(n) series may reveal similar structure.

2. **Quantum Scarring**: In quantum chaos, "scars" are enhanced probability density along unstable periodic orbits. Our scar score captures analogous energy concentration in (n, feature)-space.

3. **Ergodic Theory**: The stability test probes whether the spectral structure is robust under small perturbations, consistent with ergodic properties.

---

## See Also

- [../../gva_factorization.py](../../gva_factorization.py) - GVA factorization with geodesic guidance
- [../geometric_resonance_factorization.py](../geometric_resonance_factorization.py) - Geometric resonance pipeline
- [../cornerstone_invariant.py](../cornerstone_invariant.py) - Curvature κ(n) computation
