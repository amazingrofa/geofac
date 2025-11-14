# Geofac Documentation

This directory contains comprehensive documentation for the geometric resonance factorization method, including empirical results, theoretical foundations, and reproducibility notes.

## Documents

### [VALIDATION_GATES.md](VALIDATION_GATES.md)
**Official Project Policy** — Defines the two-gate validation policy for the project.

**Contents:**
- **Gate 1:** The 127-bit challenge number, its factors, and success criteria.
- **Gate 2:** The operational range for the algorithm after Gate 1 is passed.
- This is the canonical source for the project's official targets.

---

### [WHITEPAPER.md](WHITEPAPER.md)
**Main whitepaper** — Complete empirical documentation of the geometric-resonance factorization method as applied to the Gate 1 challenge.

**Contents:**
- Method overview (Dirichlet kernel, golden ratio QMC, phase-corrected snapping)
- Algorithm flow and pseudocode
- Verification and artifacts
- Reproduction instructions
- QMC vs PRN experimental comparison
- Theoretical context and scaling considerations

---

### [VERIFICATION.md](VERIFICATION.md)
**Verification appendix** — Detailed verification details for independent reproduction of the Gate 1 challenge.

**Contents:**
- Reference to the official test case specification in `VALIDATION_GATES.md`.
- Mathematical verification procedures (multiplication, coprimality, primality).
- Artifact locations (z-sandbox, geofac repositories).
- Step-by-step reproduction instructions.
- Configuration parameters and sensitivity.
- External verification methods (Python, Wolfram Alpha, GNU factor).

---

### [QMC_METHODS.md](QMC_METHODS.md)
**Quasi-Monte Carlo reference** — Theory and practice of low-discrepancy sampling.

**Contents:**
- Monte Carlo vs Quasi-Monte Carlo comparison
- Low-discrepancy sequences (definition, examples)
- Golden ratio sampling (current implementation)
- Sobol sequences (future enhancement)
- Variance reduction in geometric resonance

---

### [THEORY.md](THEORY.md)
**Theoretical foundations** — Complexity theory, decidability, and physical computation limits.

**Contents:**
- Complexity Theory (Time Hierarchy, P vs NP)
- Decidability (Rice's Theorem, Halting Problem)
- Physical Limits (Margolus-Levitin, Bremermann's Limit)
- Quantum Computing (Shor's Algorithm)

---

### [ACCEPTANCE_VALIDATION.md](ACCEPTANCE_VALIDATION.md)
**Acceptance criteria summary** — Points to the canonical `VALIDATION_GATES.md` which superseded its original content.

---

## Quick Start

1. **Understand the Goal**: Read [VALIDATION_GATES.md](VALIDATION_GATES.md) to understand the project's official targets.

2. **Read the Whitepaper**: [WHITEPAPER.md](WHITEPAPER.md) provides the method overview, results, and context.

3. **Follow Reproduction Instructions**: [VERIFICATION.md](VERIFICATION.md) provides the steps to clone, run, and verify the result for the Gate 1 challenge.

## Key Results Summary

The key result is the successful factorization of the Gate 1 challenge number.

**For the specific N, p, and q values, see [VALIDATION_GATES.md](VALIDATION_GATES.md).**

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
- `p * q = N` ✓
- `p` and `q` are prime (Miller-Rabin) ✓
- Reproducible with `./gradlew bootRun` ✓

## Related Repositories

- **geofac**: https://github.com/zfifteen/geofac (this repository)
- **z-sandbox**: https://github.com/zfifteen/z-sandbox (historical research)

## License

Documentation is distributed under the same license as the parent repository.
