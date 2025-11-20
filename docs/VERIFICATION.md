# Verification Appendix: Geometric Resonance Factorization

## Overview

This document provides exact verification details for the deterministic factorization of the project's official challenge number using geometric resonance methods. All information here is reproducible and verifiable by following the steps outlined.

## Test Case Specification

The test case is the successful factorization of the Gate 3 (127-bit) challenge number.

**For the exact target number (N), its factors (p, q), and their properties, please refer to the canonical validation policy document:**

**[./VALIDATION_GATES.md](./VALIDATION_GATES.md)**

All verification and reproduction steps in this document pertain to that specific target.

## Mathematical Verification

### Multiplication Check

The fundamental check is to ensure that the product of the factors equals the original number.
```python
# p, q, and N are defined in docs/VALIDATION_GATES.md
assert p * q == N, "Product verification failed"
print("✓ Verification passed: p × q = N")
```

### Coprimality and Primality

Further verification involves ensuring the factors are prime using a standard algorithm like Miller-Rabin.
```python
from sympy import isprime

# p and q are defined in docs/VALIDATION_GATES.md
assert isprime(p), "p is not prime"
assert isprime(q), "q is not prime"
print("✓ Both p and q are prime")
```

## Artifact Locations and Verification

### Repository: geofac

**URL:** https://github.com/zfifteen/geofac

**Relevant files:**
```
docs/VALIDATION_GATES.md                      # Official validation policy
src/main/java/com/geofac/FactorizerService.java  # Core algorithm
src/main/resources/application.yml               # Configuration
README.md                                         # Usage instructions
```

### Historical Repository: z-sandbox

**URL:** https://github.com/zfifteen/z-sandbox
Contains original research and historical artifacts that predate this project.

### Issue Tracker

**Issue #221:** Single-target resonance factorization  
**URL:** https://github.com/zfifteen/geofac/issues/221
Contains historical context on the development of the factorization method.

## Reproduction Instructions

### Prerequisites

- **JDK:** 17 or later
- **Git:** Any recent version
- **Memory:** 2GB RAM minimum (4GB recommended)

### Step-by-Step Reproduction

#### 1. Clone the repository

```bash
git clone https://github.com/zfifteen/geofac.git
cd geofac
```

#### 2. Verify configuration

The default configuration is set up for the Gate 3 (127-bit) challenge.
```bash
cat src/main/resources/application.yml
```

#### 3. Build the application

```bash
./gradlew build
```

#### 4. Run the application

```bash
./gradlew bootRun
```
Wait for the Spring Shell prompt: `shell:>`

#### 5. Execute factorization

At the shell prompt, use the `example` command to see the command for the Gate 3 (127-bit) challenge number.
```
shell:> example
```
Then, run the `factor` command with the number provided in the example output.

#### 6. Verify artifacts

Check the results directory, which is named after the number being factored.
```bash
ls -la results/N=<challenge_number>/
```
Inside, you will find run-specific artifacts.

#### 7. Verify factor correctness

The `factors.json` file within the run directory contains the results.
```json
{
  "N": "<challenge_number>",
  "p": "<factor_p>",
  "q": "<factor_q>",
  "verified": true,
  ...
}
```
You can manually verify that `p * q == N`.

## Configuration Parameters

The core parameters for the Gate 3 (127-bit) challenge are set in `application.yml`.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `precision` | 240 | BigDecimal math context precision |
| `samples` | 3000 | Maximum quasi-Monte Carlo samples |
| `m-span` | 180 | Half-width for Dirichlet kernel sweep |
| `j` | 6 | Dirichlet kernel order |
| `threshold` | 0.92 | Normalized amplitude gate |
| `k-lo` | 0.25 | Lower bound for k-parameter sampling |
| `k-hi` | 0.45 | Upper bound for k-parameter sampling |

## Verification Checklist

Use this checklist to verify reproduction:

- [ ] Repository cloned successfully.
- [ ] JDK 17+ confirmed (`java -version`).
- [ ] Build completes without errors (`./gradlew build`).
- [ ] Application starts and shows `shell:>` prompt.
- [ ] `factor` command with the Gate 3 (127-bit) challenge number runs successfully.
- [ ] Output shows the correct factors `p` and `q` as defined in `docs/VALIDATION_GATES.md`.
- [ ] Manual verification: `p * q = N`.
- [ ] Artifacts are written to the `results/` directory.
- [ ] `factors.json` contains the correct `p`, `q`, and `verified: true`.

## Troubleshooting

### Factor command times out

**Possible causes:**
1. Insufficient samples: Increase `geofac.samples` in `application.yml`.
2. Resource constraints: Ensure 2GB+ RAM is available.

### Results directory not created

**Cause:** Application may not have write permissions.
**Solution:** `mkdir -p results && chmod 755 results`

### Factors found but verification fails

**This should never happen.** If `p × q ≠ N`, file an issue immediately and include the contents of the run artifact directory.

## External Verification

To verify the factors using external tools, use the `N`, `p`, and `q` values from `docs/VALIDATION_GATES.md`.

### Python (SymPy)

```python
from sympy import isprime

# Get N, p, q from docs/VALIDATION_GATES.md
assert p * q == N, "Product check failed"
assert isprime(p), "p is not prime"
assert isprime(q), "q is not prime"
print("✓ All verifications passed")
```

### Wolfram Alpha

Query: `factor <N>` (where `<N>` is the Gate 3 (127-bit) challenge number).

### GNU Factor (coreutils)

Command: `factor <N>` (where `<N>` is the Gate 3 (127-bit) challenge number). Note that this may be very slow.

## Summary

This verification appendix provides the procedures to reproduce and verify the factorization of the project's official challenge number. For the specific numerical values, refer to the canonical policy document, `docs/VALIDATION_GATES.md`.

---

**Document version:** 1.1
**Last updated:** 2025-11-13
**Maintained by:** zfifteen/geofac project
