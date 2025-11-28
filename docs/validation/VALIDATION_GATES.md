# Project Validation Gates

This document defines the official four-gate validation process for the `geofac` project. Gates are sequential: evidence at a higher gate is considered only after the lower gate is demonstrated.

All gates adhere to the certification boundary in `../theory/GEOMETRIC_CERTIFICATION_BOUNDARY.md`: geometry ranks; arithmetic certification uses `IsFactor_N(d) := (N mod d == 0)` on only the top-ranked list, with no fallback algorithms or broad trial-division sweeps.

## Gate 1: 30-Bit Quick Check (Plumbing Sanity)
- **Purpose:** Fast, deterministic smoke test of pipeline and diagnostics.
- **Target Number (N):** `1073217479`
- **Factors (p, q):** `p = 32749`, `q = 32771`
- **Success Criteria:** Canonical run (`factor <N>` or `factor_one.sh`) completes; logs precision/parameters; verifies `p*q == N`.

## Gate 2: 60-Bit Scaling Validation
- **Purpose:** Confirm scaling behavior and precision handling beyond trivial widths.
- **Target Number (N):** `1152921470247108503`
- **Factors (p, q):** `p = 1073741789`, `q = 1073741827`
- **Success Criteria:** Deterministic factorization with canonical configuration; artifacts recorded (run.log, factorization.json), precision logged.

## Gate 3: 127-Bit Challenge Verification
- **Purpose:** Primary deterministic claim target for the geometric resonance method.
- **Target Number (N):** `137524771864208156028430259349934309717`
- **Factors (p, q):**
  - `p = 10508623501177419659`
  - `q = 13086849276577416863`
- **Success Criteria:**
  1. Successful factorization with the canonical algorithm (`./gradlew bootRun` then `factor <N>` or `factor_one.sh`).
  2. Result independently verified by at least three reviewers.
  3. No fast-path or short-circuit; full algorithm run; precision and parameters logged.
 4. **Verification:** The pipeline must conclude with arithmetic checks (`IsFactor_N`) on the ranked candidates produced by geometry—no fallback algorithms and no wide trial-division sweeps. The candidate list, predicate outputs, and observed rank of the discovered factor must be logged.

## Gate 4: Operational Range
- **Purpose:** Demonstrate generality across the project’s declared operating window.
- **Operational Range:** `[1e14, 1e18]` (10^14–10^18), excluding the Gate 3 number.
- **Success Criteria:** Reproducible factorization results and diagnostics on representative semiprimes in this range using deterministic settings; artifacts exported per run.

---

### Reproducibility & Logging (applies to all gates)
- Precision must be explicit: `precision = max(configured, N.bitLength() × 4 + 200)`.
- Log seeds, parameters, thresholds, sample counts, timeouts, and timestamps.
- Log the ranked candidates forwarded to `IsFactor_N`, their predicate outputs (`N mod d`), and the observed rank of any discovered factor.
- Export artifacts (run.log, factorization.json where applicable).
