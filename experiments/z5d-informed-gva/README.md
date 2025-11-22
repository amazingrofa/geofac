# Z5D-Informed GVA Enhancement Experiment

## Objective

Attempt to falsify the hypothesis that integrating Z5D Prime Predictor insights into Fractal-Recursive GVA (FR-GVA) can enhance factorization performance on the 127-bit challenge semiprime.

## Hypothesis Under Test

**Claimed:**

> "By importing key Z5D Prime Predictor concepts—prime density oracles, window×wheel gap coverage, residue class filtering, and density-weighted δ-stepping—into FR-GVA, we can create a 'fractals × Z5D prior' system that meaningfully improves shell/segment selection and kernel amplitude clustering for the 127-bit challenge."

**Specific claims:**
1. **Z5D prime-density oracle**: Using nth-prime estimates around √N₁₂₇ creates a density profile that can weight FR-GVA segments
2. **Window×wheel gap rule**: Forcing (δ-span × wheel admissible residues) ≫ log(√N) prevents structural under-sampling
3. **Wheel residue filtering**: Constraining p to residue classes (modulus 210) deterministically prunes ~77% of candidates
4. **Z5D-shaped stepping**: Variable δ-steps based on local prime density improve resolution where it matters
5. **Cross-project synergy**: Z5D prior + GVA geometry creates measurably better convergence than either alone

## Experimental Design

### Falsification Criteria

The hypothesis is falsified if any of the following hold:

1. **Failure criterion 1:** Z5D-enhanced FR-GVA does NOT meaningfully change which shells/segments are selected vs. baseline FR-GVA
2. **Failure criterion 2:** Kernel amplitude clustering does NOT align better with Z5D prime-dense δ-bands
3. **Failure criterion 3:** Z5D enhancements do NOT reduce sample counts or improve convergence metrics
4. **Failure criterion 4:** Wheel filtering and gap rules alone account for all observed improvements (Z5D density prior is redundant)

At least one falsification criterion must be violated for the hypothesis to be considered supported.

### Test Target

**Primary Target:** 127-bit challenge semiprime (Gate 3)
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863
- √N ≈ 1.172646 × 10^19

**Analysis Window:** δ ∈ [-10^6, +10^6] around √N

### Key Components

#### 1. Z5D Prime Density Oracle (Simulated)

Since we don't have direct access to z5d-prime-predictor, we simulate its behavior:
- Approximate prime index k₀ of ⌊√N₁₂₇⌋ via inverse PNT: k ≈ x/log(x)
- Generate empirical prime density histogram in δ-space
- Use actual prime counting around √N₁₂₇ to build density profile

#### 2. Wheel Residue Filter (Modulus 210)

Residue classes coprime to 2, 3, 5, 7:
- Total residues: 48 out of 210 (φ(210)/210 ≈ 22.86%)
- Deterministic pruning factor: ~77% of candidates excluded before geometric scoring

#### 3. Window × Wheel Gap Rule

For shell j with δ-span Δⱼ:
- Expected prime gap near √N₁₂₇: ḡ ≈ log(√N) ≈ 43.67
- Require: Δⱼ × 48/210 ≫ ḡ
- Minimum effective span: Δⱼ ≥ 200 (safety margin)

#### 4. Z5D-Shaped Stepping

Instead of uniform QMC δ-steps:
- Step size ∝ 1/local_density(δ)
- Smaller steps in predicted prime-dense regions
- Larger steps in low-density gaps

### Implementation

#### Baseline: Standard FR-GVA
- Fractal candidate generation (Mandelbrot iterations)
- Recursive window subdivision
- Uniform δ-sampling
- No wheel filtering
- No Z5D prior

#### Enhanced: Z5D-Informed FR-GVA
- All baseline components
- **+ Z5D density prior** in segment scoring
- **+ Wheel residue filtering** (mod 210)
- **+ Window×wheel gap validation**
- **+ Variable δ-stepping** based on Z5D density

#### Scoring Function

Baseline segment score:
```
score_baseline = α × fractal_amplitude
```

Enhanced segment score:
```
score_enhanced = α × fractal_amplitude + β × z5d_density_weight
```

Start with β = 0.1 (small Z5D weight), α = 1.0 (preserve geometric signal)

### Metrics

1. **Shell/Segment Selection:**
   - Which δ-ranges are explored first?
   - Do Z5D-dense bands get prioritized?

2. **Kernel Amplitude Clustering:**
   - Correlation between high amplitude and Z5D density
   - Spatial distribution of top candidates

3. **Convergence Performance:**
   - Samples to first factor (if found)
   - Total candidates tested
   - Runtime comparison

4. **Ablation Analysis:**
   - Z5D prior alone
   - Wheel filter alone
   - Gap rule alone
   - All components together

## Reproducibility

### Data Generation

```bash
# Generate Z5D prime density histogram around √N₁₂₇
python3 z5d_density_generator.py
# Output: z5d_density_histogram.csv
```

### Run Experiment

```bash
# Baseline FR-GVA
python3 baseline_fr_gva.py

# Z5D-enhanced FR-GVA
python3 z5d_enhanced_fr_gva.py

# Full comparison
python3 comparison_experiment.py
```

All experiments use deterministic parameters, fixed seeds, and export artifacts.

## Files

| File | Purpose |
|------|---------|
| INDEX.md | Navigation and TL;DR |
| README.md (this file) | Experiment design and methodology |
| EXPERIMENT_SUMMARY.md | Complete findings and verdict |
| z5d_density_generator.py | Generate empirical Z5D density histogram |
| z5d_density_histogram.csv | Prime density data (δ → density) |
| baseline_fr_gva.py | Standard FR-GVA implementation |
| z5d_enhanced_fr_gva.py | Z5D-informed FR-GVA implementation |
| comparison_experiment.py | Test suite and analysis framework |
| wheel_residues.py | Modulus 210 residue class utilities |
| THEORETICAL_ANALYSIS.md | Mathematical foundations and critique |

## Expected Outcomes

### If Hypothesis is Supported
- Z5D density prior shifts segment selection toward known factor locations
- Kernel amplitudes cluster in Z5D prime-dense δ-bands
- Sample counts reduced by ≥20% vs. baseline
- Wheel filtering provides orthogonal ~77% pruning

### If Hypothesis is Falsified
- Z5D prior doesn't change segment selection meaningfully
- No correlation between Z5D density and kernel amplitude
- All improvements attributable to wheel filter alone (classical optimization)
- Z5D density is too coarse/irrelevant at 127-bit scale
