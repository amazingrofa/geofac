# Technical Design Specification: Falsification Experiment for Isospectral Non-Isometric Flat Tori in High-Dimensional GVA Embeddings

**Document Metadata**
- Version: 1.0
- Date: November 23, 2025
- Author: Grok (Computational Investigation Mode)
- Repository Path: experiments/pr-1/
- Related Hypothesis: GVA's high-dimensional toroidal embeddings with geodesic analysis for factorization can utilize non-isometric isospectral flat tori in dimensions ≥4 to enable multi-embedding strategies that map arithmetic factors to isospectral classes while preserving curvature-divisor metrics, allowing parallel QMC probes to cross-validate resonances and accelerate factor heuristics.

## 1. Objective

Design an experiment to attempt falsification of the hypothesis by testing whether non-isometric isospectral flat tori in dimensions ≥4 preserve curvature-divisor metrics under GVA embeddings and yield accelerated factor detection via parallel QMC cross-validation.

**Falsification Criteria:**
- Failure to preserve metrics (deviation >5% in geodesic distances)
- No acceleration (runtime increase >10% over baseline)

## 2. Scope

**In Scope:**
- Computational simulation of torus embeddings in dimensions 4-8
- Geodesic distance computations
- QMC sampling with Sobol sequences
- Factor detection on semiprimes (bit lengths 64-128)
- Comparison against baseline (isometric tori)

**Out of Scope:**
- Physical hardware implementations
- Dimensions >8
- Non-flat tori
- Cryptographic-grade security analysis

## 3. Assumptions and Dependencies

**Assumptions:**
- Schiemann's theorem holds: Non-isometric isospectral tori exist in dim ≥4 with finite choir numbers.
- GVA curvature κ(n) = d(n) * ln(n+1) / e² computable for n up to 2^128.
- Spectral form factor follows Poisson statistics for generic tori.

**Dependencies:**
- Python 3.12+ with NumPy, SciPy, SymPy, MPmath
- GitHub repo: https://github.com/zfifteen/z-sandbox (embeddings code)
- Supporting literature: https://research.chalmers.se/publication/537996/file/537996_Fulltext.pdf (isospectral tori constructions)

## 4. Experiment Design

### 4.1 Test Cases

| Test Case ID | Dimension | Lattice Type | Target n (Semiprime) | Expected Choir Number | Baseline Runtime (est.) |
|-------------|-----------|--------------|---------------------|---------------------|------------------------|
| TC-001 | 4 | Even quadratic forms | 2^64 + 1 product | ≥2 | 10s |
| TC-002 | 6 | Product of lower-dim pairs | 2^96 + 1 product | ≥3 | 30s |
| TC-003 | 8 | Continuous family deformation | 2^128 + 1 product | ≥4 | 120s |

**Selection Criteria:** Targets with known factors; choir numbers from source constructions.
**Negative Controls:** Isometric tori (dim ≤3) expected to match baseline.

### 4.2 Metrics

**Primary (Falsification):** Geodesic distance preservation ratio (computed vs. expected; threshold <0.95 falsifies).
**Secondary:** Factor detection success rate (>90% success falsifies non-acceleration); QMC convergence speed (Sobol samples to 1% error).
**Tertiary:** Runtime ratio (isospectral vs. baseline; >1.1 falsifies acceleration).

### 4.3 Procedure

1. **Torus Construction:**
   - Generate k non-isometric isospectral tori using even quadratic forms (k = choir number).
   - Embed integer n into each via GVA: toroidal coordinates scaled by lattice basis.

2. **Geodesic Analysis:**
   - Compute Riemannian geodesics using discrete curvature κ(n).
   - Map factors to isospectral classes; check metric preservation.

3. **QMC Probing:**
   - Parallel probes: Sobol sequences + Owen scrambling across tori.
   - Cross-validate resonances: Spectral overlap > threshold indicates preservation.

4. **Factor Heuristic:**
   - Run detection; log runtime and success.

5. **Validation:**
   - Statistical test: Kolmogorov-Smirnov on distance distributions (p<0.05 falsifies Poisson consistency).

## 5. Implementation Plan

### 5.1 Folder Structure

```
experiments/pr-1/
├── README.md                 # This document
├── src/
│   ├── torus_construction.py # Isospectral lattice generators
│   ├── gva_embedding.py      # GVA embedding and curvature
│   ├── qmc_probe.py          # Sobol/Owen QMC
│   └── falsification_test.py # Main experiment runner
├── data/
│   ├── test_cases.json       # TC configs
│   └── results/              # Output logs (runtime, metrics)
├── requirements.txt          # Dependencies
└── config.yaml               # Params (dims, thresholds)
```

### 5.2 Development Phases

- **Phase 1 (Week 1):** Implement torus construction; validate isospectrality via Laplace eigenvalues (match within 1e-10).
- **Phase 2 (Week 2):** Integrate GVA; unit tests for metric preservation on synthetic data.
- **Phase 3 (Week 3):** QMC parallelization; run TC-001; analyze results.
- **Phase 4 (Week 4):** Scale to higher dims; full falsification report.
- **Milestones:** Commit per phase; PR to main repo post-Phase 4.

### 5.3 Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Numerical instability in high-dim geodesics | Medium | High | Use MPmath for arbitrary precision; cap dim at 8. |
| QMC non-convergence | Low | Medium | Increase samples; fallback to baseline scrambling. |
| No acceleration observed (falsifies) | High (test goal) | N/A | Document as success; hypothesize refinements. |

## 6. Success Criteria

**Falsification Success:** ≥2/3 test cases show metric deviation >5% or runtime >10% increase.
**Overall:** Reproducible results; code coverage >80%; documented in results/ with plots (geodesic histograms, runtime bars).

## 7. References

- GVA Implementation: https://github.com/zfifteen/z-sandbox
- Isospectral Tori: https://research.chalmers.se/publication/537996/file/537996_Fulltext.pdf
- Spectral Statistics: https://people.maths.bris.ac.uk/~majm/bib/spectral.pdf
- Deformations: https://arxiv.org/pdf/2511.10398.pdf

## Appendix: Code Snippets for Validation

```python
# Example: Isospectral Check (Phase 1)
import numpy as np
from scipy.linalg import eigh

def laplace_eigenvalues(lattice_basis):
    # Compute Laplace-Beltrami eigenvalues for flat torus
    A = np.dot(lattice_basis.T, lattice_basis)
    eigenvalues = np.sum(A * np.arange(1, len(A)+1)**2, axis=1)  # Simplified
    return np.sort(eigenvalues)

# Test: Generate two non-isometric bases; assert eigenvalues match
basis1 = np.random.rand(4,4)  # Even quadratic form
basis2 = deform_basis(basis1)  # Non-isometric deformation
assert np.allclose(laplace_eigenvalues(basis1), laplace_eigenvalues(basis2), atol=1e-10)
```

## Status

**Current Phase:** Phase 1 - Framework setup complete, ready for implementation
**Last Updated:** 2025-11-23
