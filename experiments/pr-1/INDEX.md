# PR-1: Isospectral Non-Isometric Flat Tori Falsification Experiment

## Quick Navigation

- **[README.md](README.md)** - Complete technical design specification
- **[config.yaml](config.yaml)** - Experiment configuration and parameters
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[validate_framework.py](validate_framework.py)** - Framework validation script

## Source Code

- **[src/torus_construction.py](src/torus_construction.py)** - Isospectral lattice generators
- **[src/gva_embedding.py](src/gva_embedding.py)** - GVA embedding and curvature
- **[src/qmc_probe.py](src/qmc_probe.py)** - Sobol/Owen QMC sampling
- **[src/falsification_test.py](src/falsification_test.py)** - Main experiment runner
- **[src/__init__.py](src/__init__.py)** - Package initialization

## Data

- **[data/test_cases.json](data/test_cases.json)** - Test case configurations (TC-001, TC-002, TC-003)
- **data/results/** - Output directory (auto-generated, gitignored)

## TL;DR

**Status**: Framework complete, Phase 1 ready

**Objective**: Attempt falsification of the hypothesis that non-isometric isospectral flat tori in dimensions ≥4 preserve curvature-divisor metrics under GVA embeddings and yield accelerated factor detection.

**Falsification Criteria**:
- Metric deviation >5% (preservation ratio <0.95)
- Runtime increase >10% (ratio >1.1)
- Success threshold: ≥2/3 test cases show deviation

**Hypothesis**: GVA's high-dimensional toroidal embeddings with geodesic analysis can utilize non-isometric isospectral flat tori to enable multi-embedding strategies that map arithmetic factors to isospectral classes while preserving curvature-divisor metrics.

## Quick Start

### 1. Validate Framework
```bash
python3 validate_framework.py
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Experiment
```bash
cd src
python3 falsification_test.py --log-level INFO
```

### 4. Check Results
```bash
ls -l data/results/
cat data/results/falsification_report_*.json
```

## Test Cases

| ID | Dimension | Lattice Type | Target Semiprime | Choir Number | Est. Runtime |
|----|-----------|--------------|------------------|--------------|--------------|
| TC-001 | 4 | Even quadratic forms | 2^64 product | ≥2 | 10s |
| TC-002 | 6 | Product of lower-dim pairs | 2^96 product | ≥3 | 30s |
| TC-003 | 8 | Continuous family deformation | 2^128 product | ≥4 | 120s |

## Implementation Status

**Phase 1 (Complete)**: Framework setup
- ✅ Directory structure created
- ✅ Isospectral lattice generators implemented
- ✅ GVA embedding with adaptive precision
- ✅ QMC Sobol/Owen probing
- ✅ Full experiment orchestration
- ✅ Statistical validation (KS test)
- ✅ Configuration and test cases

**Phase 2 (Pending)**: GVA integration and unit tests
**Phase 3 (Pending)**: QMC parallelization and TC-001 execution
**Phase 4 (Pending)**: Higher dimensions and falsification report

## Key Features

1. **Isospectral Tori Construction**
   - Even quadratic forms for 4D
   - Non-isometric deformations preserving spectrum
   - Laplace eigenvalue verification (tolerance 1e-10)
   - Choir generation with configurable size

2. **GVA Embedding**
   - Discrete curvature: κ(n) = d(n) * ln(n+1) / e²
   - Adaptive precision: max(200, bitLength * 4 + 200)
   - Toroidal coordinate embedding via lattice basis
   - Geodesic distance computation

3. **QMC Probing**
   - Sobol sequences with Owen scrambling
   - Parallel choir probing (ready for multiprocessing)
   - Resonance cross-validation with spectral overlap
   - Convergence error estimation

4. **Falsification Testing**
   - Baseline vs. isospectral comparison
   - Metric preservation ratio computation
   - Runtime performance tracking
   - Kolmogorov-Smirnov statistical validation
   - Comprehensive JSON reporting

## References

- **Schiemann's Theorem**: Non-isometric isospectral tori exist in dim ≥4
  - https://research.chalmers.se/publication/537996/file/537996_Fulltext.pdf

- **GVA Implementation**: https://github.com/zfifteen/z-sandbox

- **Spectral Statistics**: 
  - https://people.maths.bris.ac.uk/~majm/bib/spectral.pdf
  - https://arxiv.org/pdf/2511.10398.pdf

## Reproducibility

All components enforce reproducibility:
- Fixed seeds for RNG and QMC scrambling
- Explicit precision declarations logged
- Configuration parameters exported
- Test case definitions versioned
- Complete artifact generation

## Notes

This experiment follows the established pattern in the experiments/ directory:
- Minimal, focused implementation
- Clear falsification criteria
- Reproducible methodology
- Comprehensive documentation
- Phase-based development plan

The hypothesis is intentionally constructed to be falsifiable through specific, measurable criteria rather than vague claims of "improvement."
