# FFT-Based Candidate Selection Experiment

## Objective

Test whether frequency-domain analysis (FFT) of the κ(n) curvature series can identify promising candidate regions for factorization, reducing the number of arithmetic divisibility checks needed.

**What this is:** Empirical signal processing to find patterns in κ(n) sequences.

**What this is NOT:** This experiment does NOT establish theoretical connections to quantum scarring, Ruelle zeta functions, or geodesic flows. Those terms appear in the original prompt but are not mathematically justified here.

## Hypothesis Under Test

**Empirical Claim:**

> Spectral analysis (FFT) of κ(n) over the search interval may reveal frequency-domain patterns. If these patterns correlate with factor locations, they could guide candidate selection.

**Testable predictions:**

1. **Spectral Structure**: κ(n) series exhibits identifiable FFT peaks (vs. white noise baseline)
2. **Energy Localization**: Spectral energy clusters in specific n-regions more than uniform random
3. **Perturbation Robustness**: Peak structure persists under small sinusoidal perturbations
4. **Efficiency Gain**: FFT-guided selection reduces arithmetic checks ≥10% compared to uniform sampling

## Experimental Design

### Validation Thresholds

**NOTE:** These thresholds are empirically chosen, not theoretically derived. They represent exploratory data analysis criteria:

1. **Gate A - Signal Detection**: At least one FFT peak with prominence z-score ≥ 2.0 (indicates non-random structure)
2. **Gate B - Robustness**: Peak overlap ≥ 60% under sinusoidal perturbations (ε ∈ {10⁻⁶, 10⁻⁵, 10⁻⁴}, L ∈ {100, 500, 1000})
3. **Gate C - Efficiency**: Candidate windows reduce arithmetic checks by ≥ 10% vs. geometry-rank alone

**Statistical Note:** These are not p-values or confidence intervals. They are heuristic cutoffs for exploratory analysis. Parameter tuning to meet these thresholds would constitute p-hacking.

### Test Target

**Primary Target:** 127-bit challenge semiprime (Gate 3)
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863
- √N ≈ 1.17 × 10¹⁹

**Operational Range:** [10¹⁴, 10¹⁸]

## Algorithm Components

### 1. Window & Detrend

Take κ(n) series over the search interval and isolate oscillations:

```python
# Median detrending (default)
trend = median_filter(kappa, window_size=51)
detrended = kappa - trend

# Or highpass filtering
detrended = highpass_filter(kappa, cutoff=0.01)
```

### 2. Spectral Scan (FFT)

Compute magnitude spectrum with analysis:

```python
# Apply Hann window to reduce spectral leakage
windowed = detrended * hann_window

# Compute FFT
spectrum = fft(windowed)
magnitudes = |spectrum|

# Compute metrics
spectral_entropy = -Σ p_i log(p_i)  # where p_i = |K(f_i)|²/Σ|K|²
peak_prominences = find_peaks(magnitudes)
```

### 3. Energy Localization Score

Subdivide n into equal blocks (tiles) and compute energy distribution:

```python
# Partition into tiles
tiles = partition(n_values, num_tiles=20)

# Compute energy per tile (squared amplitudes)
tile_energy[i] = Σ (detrended[j])² for j in tile[i]

# Localization score (analogous to Gini coefficient)
# Higher score = more concentrated in fewer tiles
localization_score = (energy in top 10% tiles) / (total energy)
```

**Note:** The 10% threshold is arbitrary. The term "scar score" in earlier versions referred to quantum scarring, which is not applicable here. This is simply measuring energy concentration.

### 4. Stability Test

Apply sinusoidal perturbations:

```python
for ε in [1e-6, 1e-5, 1e-4]:
    for L in [100, 500, 1000]:
        n' = n + ε·sin(2πn/L)
        peaks' = find_peaks(fft(kappa(n')))
        overlap = |peaks ∩ peaks'| / |peaks|
```

Retain candidates whose peak sets overlap ≥ 60% across all deformations.

### 5. Candidate Shortlist

Rank tiles by composite score:

```python
score = peak_height × stability_overlap × localization_score
candidates = top_M(tiles, by=score)
```

Emit top M n-windows for arithmetic certification.

## Theoretical Disclaimer

**IMPORTANT:** The original issue prompt referenced "Ruelle zeta resonances," "superscarred ergodicity," and "geodesic flows on rectangular tori." These terms come from:
- Dynamical systems theory (Ruelle zeta functions)
- Quantum chaos (quantum scarring)
- Differential geometry (geodesic flows)

**This experiment does NOT establish mathematical connections between these concepts and integer factorization.** The terminology was inherited from an AI-generated prompt and is not rigorously justified.

**What this experiment actually does:**
- Standard FFT-based signal processing
- Peak detection in frequency domain
- Energy localization metrics
- Perturbation stability testing

**If FFT analysis proves useful for factorization, that would be an empirical finding, not theoretical validation of quantum chaos or dynamical systems connections.**

## Null Hypothesis & Falsification

**Null hypothesis:** κ(n) series has no exploitable frequency-domain structure beyond random noise.

**How to falsify the approach:**
1. Compare FFT peak prominence to white noise baseline → if indistinguishable, FFT adds no signal
2. Measure computational overhead of FFT analysis → if overhead > 10% savings, net-negative efficiency
3. Test on known factors → if FFT-selected regions don't contain factors more than random sampling, no predictive power
4. Cross-validation on multiple semiprimes → if approach fails on >50%, not generalizable

**Current status:** This is exploratory. Gates may be tuned to artificially "pass" (p-hacking). Independent validation required.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `window_length` | 4096 | FFT window size (power of 2) |
| `detrend_method` | "median" | Detrending method: "median" or "highpass" |
| `top_peaks` | 5 | Number of top peaks to record |
| `min_prominence_zscore` | 2.0 | Gate A threshold |
| `num_tiles` | 20 | Number of rectangular tiles |
| `top_tile_fraction` | 0.10 | Top 10% tiles for scar score |
| `epsilon_values` | [1e-6, 1e-5, 1e-4] | Perturbation magnitudes |
| `L_values` | [100, 500, 1000] | Perturbation wavelengths |
| `stability_overlap_threshold` | 0.60 | Gate B threshold (60%) |
| `top_candidates` | 10 | Final candidate count |
| `reduction_threshold` | 0.10 | Gate C threshold (10% reduction) |
| `seed` | 42 | Deterministic seed |

## Outputs

### Per-run artifacts:

1. **experiment_results.json** - Complete configuration and metrics:
   ```json
   {
     "timestamp": "...",
     "N": "...",
     "config": {...},
     "spectral_analysis": {"peaks": [...]},
     "scar_analysis": {"global_scar_score": ...},
     "stability_test": {"average_overlap": ...},
     "candidates": [...],
     "gates": {"all_passed": true/false}
   }
   ```

2. **peak_table.csv** - Frequency, height, bandwidth, z-score for each peak

3. **candidates.csv** - Ranked candidate windows with scores

4. **spectrum_tiles_*.png** - Visualization of:
   - Magnitude spectrum with marked peaks
   - Tile energy distribution with highlighted scar tiles

## Usage

### Basic usage (127-bit challenge):

```bash
cd experiments/superscarred-ergodicity-insight
python3 superscarred_ergodicity.py
```

### Custom parameters:

```bash
python3 superscarred_ergodicity.py \
    --n 100000000000007 \
    --half-window 5000 \
    --step 1 \
    --seed 42 \
    --output-dir ./my_results
```

### Python API:

```python
from superscarred_ergodicity import SuperscarredErgodicityExperiment, ExperimentConfig

config = ExperimentConfig(
    window_length=4096,
    detrend_method="median",
    top_peaks=5,
    seed=42
)

experiment = SuperscarredErgodicityExperiment(config)
results = experiment.run(
    N=137524771864208156028430259349934309717,
    half_window=10000,
    step=1
)

print(f"Gates passed: {results['gates']['all_passed']}")
```

## Running Tests

```bash
cd /home/runner/work/geofac/geofac
python3 -m pytest tests/test_superscarred_ergodicity.py -v
```

## Dependencies

Required:
- numpy
- scipy
- mpmath

Optional (for visualization):
- matplotlib

Install:
```bash
pip install numpy scipy mpmath matplotlib
```

## Theoretical Background

### Ruelle Resonances

In dynamical systems theory, Ruelle resonances characterize the decay of correlations in chaotic systems. For Anosov flows, these resonances appear as poles of the meromorphic continuation of the zeta function.

The κ(n) series in geofac may exhibit similar spectral structure, where peaks correspond to underlying geometric periodicity in the factor search space.

### Quantum Scarring

In quantum chaos, "scars" are enhanced probability density along unstable periodic orbits. Despite the underlying classical chaos, certain quantum states show non-ergodic concentration along periodic trajectories.

The scar score in this experiment captures analogous energy concentration in (n, feature)-space, where certain tiles contain disproportionate spectral energy.

### Connection to Factorization

The hypothesis is that:
1. The κ(n) series encodes geometric structure related to factor locations
2. Spectral analysis reveals this structure as peaks at characteristic frequencies
3. Scarred regions indicate promising n-ranges for arithmetic certification
4. Stability under perturbation distinguishes robust geometric signals from noise

## Constraints

Per VALIDATION_GATES.md:

- **No classical fallbacks**: No Pollard Rho, ECM, trial division, or sieve methods
- **Deterministic only**: Sobol/Halton sampling, no stochastic methods
- **Explicit precision**: max(configured, N.bitLength() × 4 + 200)
- **Pinned seeds**: All randomness controlled by seed parameter
- **Logged parameters**: Full configuration in output JSON

## Expected Outcomes

### If Hypothesis Supported:
- Gate A passes: Robust peaks with z-score ≥ 2.0
- Gate B passes: Stability overlap ≥ 60%
- Gate C passes: Reduction ≥ 10%
- Scarred regions correlate with actual factor locations

### If Hypothesis Falsified:
- Gate A fails: No robust peaks (random-like spectrum)
- Gate B fails: Peaks unstable under perturbation (noise artifacts)
- Gate C fails: No reduction in arithmetic checks
- Scar score uniform across tiles (no concentration)

## References

1. Ruelle, D. (1986). "Resonances of chaotic dynamical systems"
2. Heller, E. J. (1984). "Bound-state eigenfunctions of classically chaotic Hamiltonian systems: Scars of periodic orbits"
3. Weyl, H. (1912). "Das asymptotische Verteilungsgesetz der Eigenwerte linearer partieller Differentialgleichungen"
