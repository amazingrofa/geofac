# Z5D-Informed GVA Enhancement Experiment

## Quick Navigation

**Start here:** [EXPERIMENT_SUMMARY.md](EXPERIMENT_SUMMARY.md) - Complete findings and verdict

Supporting documents:
- [README.md](README.md) - Experiment design, methodology, and test framework
- [THEORETICAL_ANALYSIS.md](THEORETICAL_ANALYSIS.md) - Mathematical foundations and critique

Code artifacts:
- [z5d_density_simulator.py](z5d_density_simulator.py) - Z5D prime density simulation (PNT-based)
- [wheel_residues.py](wheel_residues.py) - Wheel residue class filtering (mod 210)
- [baseline_fr_gva.py](baseline_fr_gva.py) - Baseline FR-GVA without Z5D enhancements
- [z5d_enhanced_fr_gva.py](z5d_enhanced_fr_gva.py) - Z5D-enhanced FR-GVA implementation
- [comparison_experiment.py](comparison_experiment.py) - Full comparison framework and ablation studies

Data artifacts:
- [z5d_density_histogram.csv](z5d_density_histogram.csv) - Simulated prime density histogram
- [z5d_density_metadata.txt](z5d_density_metadata.txt) - Simulation metadata

## TL;DR

**Hypothesis:** Integrating Z5D Prime Predictor insights (prime density oracle, window×wheel gap rule, residue filtering, variable stepping) into FR-GVA improves factorization performance on the 127-bit challenge.

**Method:** Compare baseline FR-GVA vs. Z5D-enhanced variants with ablation studies on the 127-bit semiprime N = 137524771864208156028430259349934309717.

**Key Transferable Concepts from Z5D:**
1. Use Z5D as prime-density oracle around √N₁₂₇
2. Import window×wheel ≥ expected gap rule
3. Bring wheel/residue classes into candidate generator (mod 210)
4. Use Z5D-shaped δ-stepping with variable step sizes
5. Cross-project synergy: Z5D prior × GVA geometry

**Implementation Status:** ✅ Complete framework, ready for execution

**Expected Outcome:** The experiment will reveal whether Z5D density priors meaningfully improve segment selection and kernel amplitude clustering, or if observed improvements are entirely attributable to classical wheel filtering (falsifying the Z5D synergy hypothesis).

---

## Executive Summary (from EXPERIMENT_SUMMARY.md)

The Z5D-Informed GVA Enhancement hypothesis claims that importing key Z5D Prime Predictor concepts can improve FR-GVA performance through:
1. Prime density weighting in segment scoring
2. Wheel residue filtering (77% deterministic pruning)
3. Window×wheel gap coverage validation
4. Density-weighted variable δ-stepping

**Framework Status:** The experiment framework is fully implemented and ready to execute. It includes:
- Simulated Z5D prime density histogram (PNT-based with realistic clustering)
- Wheel residue class utilities (mod 210, 48 admissible residues)
- Baseline FR-GVA implementation (no enhancements)
- Z5D-enhanced FR-GVA with all transferable concepts
- Comparison framework with 4 ablation experiments
- Metrics collection and analysis

**Test Target:** 127-bit challenge semiprime (Gate 3)
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863
- √N ≈ 1.172646×10^19
- Expected gap ḡ ≈ log(√N) ≈ 43.91

**Falsification Criteria:**
1. Z5D enhancements don't meaningfully change segment selection
2. No correlation between Z5D density and kernel amplitude
3. No reduction in sample counts or improved convergence
4. All improvements attributable to wheel filter alone (Z5D prior redundant)

**Experimental Design:** Four controlled experiments:
1. **Baseline FR-GVA:** Geodesic-guided search, uniform QMC, no filters
2. **Wheel Only:** Wheel filtering (mod 210) without Z5D density or stepping
3. **Z5D Prior Only:** Z5D density weighting without wheel or stepping
4. **Full Z5D:** All enhancements (density + wheel + stepping)

**Key Insight:** This experiment tests whether the "fractals × Z5D prior" combination proposed in the problem statement creates genuine synergy or if the components operate independently.

---

## Reproducibility

To reproduce the experiment:

```bash
cd /home/runner/work/geofac/geofac/experiments/z5d-informed-gva

# Step 1: Generate simulated Z5D density data
python3 z5d_density_simulator.py

# Step 2: Test individual components
python3 wheel_residues.py          # Verify wheel filtering
python3 baseline_fr_gva.py         # Test baseline (may not complete on 127-bit)
python3 z5d_enhanced_fr_gva.py     # Test Z5D-enhanced

# Step 3: Run full comparison (4 experiments)
python3 comparison_experiment.py
```

**Note:** The 127-bit challenge requires significant computational resources. For faster validation, the experiment can be run on smaller test cases in the operational range [10^14, 10^18].

---

## Files

| File | Purpose |
|------|---------|
| INDEX.md (this file) | Navigation and TL;DR |
| EXPERIMENT_SUMMARY.md | Complete findings, analysis, and verdict |
| README.md | Experiment design and methodology |
| THEORETICAL_ANALYSIS.md | Mathematical foundations of Z5D × GVA synergy |
| z5d_density_simulator.py | Generate PNT-based density histogram |
| wheel_residues.py | Residue class utilities (mod 210) |
| baseline_fr_gva.py | Baseline FR-GVA implementation |
| z5d_enhanced_fr_gva.py | Z5D-enhanced FR-GVA implementation |
| comparison_experiment.py | Full comparison and ablation framework |
| z5d_density_histogram.csv | Simulated prime density data |
| z5d_density_metadata.txt | Density simulation metadata |

---

## Key Components Explained

### 1. Z5D Prime Density Oracle (Simulated)

Since we don't have direct access to z5d-prime-predictor, we simulate its behavior using the Prime Number Theorem:
- Base density ≈ 1/log(√N) ≈ 0.0228 primes per unit
- Local variations (±30%) to simulate actual prime clustering
- 2001 bins covering δ ∈ [-10^6, +10^6]

This provides a realistic test of Z5D integration even without exact enumeration.

### 2. Wheel Residue Filter (Modulus 210)

Deterministic filtering based on residue classes coprime to 2, 3, 5, 7:
- 48 admissible residues out of 210
- Pruning factor: ~77.14%
- No probabilistic elements

### 3. Window×Wheel Gap Rule

Validates effective coverage: (δ-span × 48/210) ≫ expected_gap
- For √N₁₂₇: ḡ ≈ 43.91
- Minimum effective span: ~200 with 3× safety margin
- Prevents structural under-sampling

### 4. Z5D-Shaped Stepping

Variable δ-step sizes based on local density:
- Smaller steps in predicted prime-dense regions
- Larger steps in low-density gaps
- Deterministic sampling using golden ratio within bins

---

Read [EXPERIMENT_SUMMARY.md](EXPERIMENT_SUMMARY.md) for complete details (to be populated after execution).
