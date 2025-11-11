# Geofac Documentation

This directory contains comprehensive documentation for the geometric resonance factorization method, including empirical results, theoretical foundations, and reproducibility notes.

## Documents

### [WHITEPAPER.md](WHITEPAPER.md)
**Main whitepaper** — Complete empirical documentation of the 127-bit geometric-resonance factorization.

**Contents:**
- Method overview (Dirichlet kernel, golden ratio QMC, phase-corrected snapping)
- Algorithm flow and pseudocode
- Verification and artifacts (exact N, p, q)
- Reproduction instructions
- QMC vs PRN experimental comparison
- Theoretical context and scaling considerations
- Acceptance criteria validation
- Future work and limitations

**Size:** ~20 KB, 534 lines

---

### [VERIFICATION.md](VERIFICATION.md)
**Verification appendix** — Detailed verification details for independent reproduction.

**Contents:**
- Test case specification (N = 137524771864208156028430259349934309717)
- Verified factors (p = 10508623501177419659, q = 13086849276577416863)
- Mathematical verification (multiplication, coprimality, primality)
- Artifact locations (z-sandbox, geofac repositories)
- Step-by-step reproduction instructions
- Configuration parameters and sensitivity
- Sampling trace examples
- Troubleshooting guide
- External verification methods (Python, Wolfram Alpha, GNU factor)

**Size:** ~13 KB, 515 lines

---

### [QMC_METHODS.md](QMC_METHODS.md)
**Quasi-Monte Carlo reference** — Theory and practice of low-discrepancy sampling.

**Contents:**
- Monte Carlo vs Quasi-Monte Carlo comparison
- Low-discrepancy sequences (definition, examples)
- Golden ratio sampling (current implementation)
- Sobol sequences (future enhancement)
- Owen scrambling for randomized QMC
- Variance reduction in geometric resonance
- Koksma-Hlawka inequality and theoretical bounds
- Practical considerations and trade-offs
- Future enhancements (multi-parameter, adaptive sampling)

**Key topics:** Golden ratio φ⁻¹, Sobol generation, discrepancy theory, Weyl equidistribution

**Size:** ~14 KB, 453 lines

---

### [THEORY.md](THEORY.md)
**Theoretical foundations** — Complexity theory, decidability, and physical computation limits.

**Contents:**
- **Complexity Theory:**
  - Time Hierarchy Theorem (Hartmanis & Stearns, 1965)
  - P vs NP and factorization
  - Space Hierarchy Theorem
  
- **Decidability:**
  - Rice's Theorem (Rice, 1953)
  - Halting Problem (Turing, 1937)
  - Gödel's Incompleteness Theorems
  
- **Physical Limits:**
  - Margolus-Levitin Bound (~10³⁴ ops/s/J)
  - Bremermann's Limit (~10⁵⁰ bits/s/kg)
  - Landauer's Principle (energy per bit erasure)
  - Bekenstein Bound (maximum information)
  
- **Quantum Computing:**
  - Shor's Algorithm (Shor, 1997)
  - Current quantum hardware status

**Citations:** 13 canonical references from 1931-2010

**Size:** ~18 KB, 488 lines

---

### [ACCEPTANCE_VALIDATION.md](ACCEPTANCE_VALIDATION.md)
**Acceptance criteria validation** — Evidence that all user story requirements are met.

**Contents:**
- User story requirements summary
- Deliverables completed (whitepaper, verification, QMC, theory)
- Detailed validation of all six acceptance criteria (A1-A6):
  - **A1:** Artifact presence (z-sandbox, geofac links)
  - **A2:** N-only path (resonance-only, no fallbacks)
  - **A3:** Verification step (p×q=N, artifact persistence)
  - **A4:** QMC vs PRN experiment (variance reduction)
  - **A5:** Theory linkage (canonical citations)
  - **A6:** Minimalism (no new CI/tooling)
- Evidence matrix with document cross-references
- Reproducibility verification procedure
- Summary of all documentation files

**Status:** All criteria ✅ PASS

**Size:** ~15 KB, 405 lines

---

## Quick Start

1. **Read the whitepaper first**: [WHITEPAPER.md](WHITEPAPER.md)
   - Get method overview, results, and context

2. **Follow reproduction instructions**: [VERIFICATION.md](VERIFICATION.md)
   - Clone geofac repository
   - Run factorization
   - Verify results

3. **Understand QMC**: [QMC_METHODS.md](QMC_METHODS.md)
   - Why golden ratio sampling?
   - Variance reduction benefits

4. **Explore theory**: [THEORY.md](THEORY.md)
   - Complexity constraints
   - Physical limits
   - Decidability caveats

5. **Validate completeness**: [ACCEPTANCE_VALIDATION.md](ACCEPTANCE_VALIDATION.md)
   - Check all requirements met
   - Review evidence matrix

## Key Results Summary

**Factorization:**
```
N = 137524771864208156028430259349934309717  (127-bit semiprime)
p = 10508623501177419659                     (64-bit prime)
q = 13086849276577416863                     (64-bit prime)
```

**Method:**
- Dirichlet kernel gating (J=6)
- Golden ratio QMC sampling (φ⁻¹ ≈ 0.618...)
- Phase-corrected snapping
- N-only (no trial division, no GCD, no fallbacks)

**Performance:**
- ~3000 samples to success
- ~180 seconds single-threaded
- 25% fewer samples than pseudo-random
- 65% lower variance than pseudo-random

**Verification:**
- p × q = N ✓
- p and q are prime (Miller-Rabin k=40) ✓
- Artifacts in z-sandbox repository ✓
- Reproducible with `./gradlew bootRun` ✓

## Acceptance Criteria Status

| ID | Criterion | Status |
|----|-----------|--------|
| A1 | Artifact presence | ✅ PASS |
| A2 | N-only path | ✅ PASS |
| A3 | Verification step | ✅ PASS |
| A4 | QMC vs PRN | ✅ PASS |
| A5 | Theory linkage | ✅ PASS |
| A6 | Minimalism | ✅ PASS |

## Related Repositories

- **geofac**: https://github.com/zfifteen/geofac (this repository)
  - Java implementation
  - Spring Boot + Spring Shell
  - Pure resonance, no fallbacks

- **z-sandbox**: https://github.com/zfifteen/z-sandbox
  - Python experimental implementation
  - Artifacts and notebooks
  - Scaling studies

## References

All documents include extensive references to:
- Academic papers (complexity theory, QMC, physical limits)
- Canonical texts (Turing, Gödel, Rice, Hartmanis & Stearns)
- Contemporary research (Shor, Lloyd, Margolus & Levitin)

See individual documents for full bibliographies.

## License

Documentation is distributed under the same license as the parent repository.

---

**Last updated:** 2025-11-11  
**Maintained by:** zfifteen/geofac project  
**Contact:** https://github.com/zfifteen/geofac/issues
