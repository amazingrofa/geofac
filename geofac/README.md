# geofac-137524771864208156028430259349934309717

**Target:** `137524771864208156028430259349934309717` ($N_{127}$)  
**Methodology:** Geometric Resonance & Geodesic Validation Assault (GVA)  
**Constraint:** **Zero-Knowledge Discovery** (Strictly no factor injection allowed)

## 🎯 Mission Statement

This repository exists for one purpose: to factor the 127-bit challenge semiprime $N_{127}$ using the **Geofac** geometric resonance principles.

Unlike previous general-purpose implementations, this codebase is hyper-tuned to address the specific physical properties of $N_{127}$—specifically its unbalanced nature—without violating the "blind" constraint of the challenge.

## 📉 The Challenge Target

```python
N = 137524771864208156028430259349934309717
# Bit Length: 127
# Sqrt(N) ≈ 1.1727 × 10^19
# Status: UNBALANCED (Requires extended geodesic search)
```

## 🔍 The Strategy Shift

Previous attempts with the standard Geofac toolchain failed because the default search window ($\approx 5.8 \times 10^{16}$) was insufficient for unbalanced semiprimes. Analysis indicates the factors for $N_{127}$ likely lie beyond this horizon.

**This repository implements "Workflow A" (The Wide Net):**

1.  **Extended Window:** Enforces a search radius of **$2.0 \times 10^{18}$** around $\sqrt{N}$ to capture the resonance valley.
2.  **QMC Sampling:** Replaces standard random walks with **Sobol** and **Halton** sequences to ensure uniform coverage of this massive search space.
3.  **Resonance Ranking:** Uses high-order Dirichlet kernels to rank candidates based on manifold resonance rather than trial division.
4.  **Arithmetic Certification:** Only the final ranked candidates are subjected to `N % d == 0`.

## 📂 Repository Structure

```text
.
├── AGENTS.md                 # The operational playbook for AI agents
├── gva_core.py               # Patched GVA engine with user-definable windows
├── qmc_sampler.py            # High-performance Sobol/Halton sequence generator
├── resonance_scoring.py      # Vectorized Dirichlet kernel scoring
├── verify_blind.sh           # Audit script to ensure no hardcoded factors
└── README.md                 # This file
```

## 🚀 Usage

### 1\. The "Wide Net" Scan

Generate candidate lists using the extended window parameters defined by `@agent-architect`:

```bash
# Generate 10M candidates using Sobol sequences in the 2e18 window
python3 qmc_sampler.py --n 137524771864208156028430259349934309717 \
                       --window 2000000000000000000 \
                       --count 10000000 \
                       --out candidates.bin
```

### 2\. Resonance Ranking

Score the candidates to find the "resonance valley":

```bash
# Rank candidates by Dirichlet kernel amplitude
python3 resonance_scoring.py --input candidates.bin --top-k 1000
```

### 3\. Certification

Verify the top candidates (performed by `@agent-red-team`):

```bash
python3 gva_core.py --verify-list ranked_candidates.txt
```

## 🧪 Experimental Arctan-Curvature Factorization

This script implements **Arctan Geodesic Mappings** for $\kappa(n)$ Curvature in prime diagnostics.

**Key Result:** Achieved **10,000x ranking improvement** on 40-bit semiprimes versus random scanning. Factors are consistently found in the top 100 candidates of a 1,000,000 sample set.

### 📄 Full Results & Analysis
See **[RESULTS_ARCTAN.md](RESULTS_ARCTAN.md)** for the detailed reproducibility report and analysis of the "Scaling Wall" at 42 bits.

### 🔁 Run the Experiment
To reproduce the 40-bit success case:

```bash
python3 geofac/geofac_arctan_curvature.py --N 169435573207 --samples 1000000 --method golden
```

**Note:** Do not attempt $N > 50$ bits without increasing `samples` to $\approx \sqrt{N}$, which may require significant compute time.

## 🛡️ The "Blind" Protocol

To maintain integrity, **no script in this repository acts on prior knowledge of the factors.**

* **Audit:** Run `./verify_blind.sh` before every commit. It greps for the factor literals to ensure they haven't been sneaked into the logic.
* **Drift Check:** Ranking quality is assessed solely by the `resonance_score` (amplitude $> 1.0$), not by checking distance to the known solution.

-----

*Based on the Geofac research by [zfifteen](https://github.com/zfifteen/geofac).*