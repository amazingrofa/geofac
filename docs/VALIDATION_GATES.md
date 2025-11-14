# Project Validation Gates

This document defines the official validation gates for the `geofac` project. The project follows a sequential, two-gate validation process. All experiments, claims, and code must adhere to this policy.

## Gate 1: 127-Bit Challenge Verification

The first gate is a single, specific validation target: the deterministic factorization of a 127-bit semiprime.

- **Target Number (N):** `137524771864208156028430259349934309717`
- **Factors (p, q):**
  - `p = 10508623501177419659`
  - `q = 13086849276577416863`

### Success Criteria

The primary goal of this project is to prove that the geometric resonance algorithm, as implemented, can deterministically and reproducibly factor this specific number.

**Gate 1 is considered passed if and only if:**
1. The factorization is successful using the canonical algorithm (`./gradlew bootRun` -> `factor <N>`).
2. The result is independently verified by at least three (3) designated reviewers.
3. The "fast path" or any other short-circuit mechanism is disabled, ensuring the algorithm runs in its entirety.

No other numbers will be considered for validation until Gate 1 is passed.

## Gate 2: Operational Range

Once Gate 1 is successfully passed and verified, the project's operational scope expands to a defined range of semiprimes.

- **Operational Range:** `[1e14, 1e18]` (i.e., numbers between 10^14 and 10^18).
- **Exclusions:** The 127-bit challenge number from Gate 1 is excluded from this range.

### Success Criteria

Gate 2 validates the general applicability of the algorithm to a wider set of problems. The focus shifts from a single target to performance and success rates across the specified range.

This two-step process ensures that the core claim is verified under strict, reproducible conditions (Gate 1) before the method is generalized (Gate 2).
