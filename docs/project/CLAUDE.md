# CLAUDE.md

Instructions for Claude Code when working with this repository.

## Philosophy: Every Line is a Liability

The perfect program has no lines. Nature takes the path of least resistance; this software does the same.

- **Delete as readily as you write.** Remove scaffolding that outlives its usefulness.
- **Smallest change wins.** The minimal fix that satisfies the goal. No future-proofing.
- **When simpler is possible, simpler is required.**

## Complexity is a Failure Mode

Treat cyclomatic complexity like gravity—escape it.

- **Flatten control flow:** Guard clauses over nesting
- **Pure functions over tangled state**
- **Collapse branches that don't earn their keep**
- **No "just in case" paths.** Each branch is paid for forever in testing, comprehension, error surface.
- **No fallbacks that blur inference.** A method proves or fails a hypothesis without hedging.

## Code Reads Like a Story

- **Names are plain language, not puzzles:** Verbs for behaviors, nouns for data
- **Interfaces are small and literal:** Function says what it does, arguments mirror domain
- **Composition feels like putting sentences together**
- **Linear readability:** When read top-to-bottom, code explains itself
- **Spend time on naming precision, not comments apologizing for ambiguity**

## Invariants Anchor Everything

Work from first principles. Guard them in code.

### Validation Gate (Non-Negotiable)
- The project follows a strict, four-gate validation policy. All code and analysis must adhere to the rules defined in **[docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md)**.
- Small-prime "wins" are noise. They don't generalize. They don't count.
- Only official challenge numbers are to be used for semiprimes.

### Geometric Purity
- **No classical fallbacks:** No Pollard's Rho, trial division, ECM, or sieve methods
- **Prove the hypothesis or fail it.** No hedging with fallback paths.
- **Deterministic/quasi-deterministic methods only:** Sobol/Halton sequences, Dirichlet kernel gating, phase snapping

## Reproducibility is Part of Design

Every run leaves a trail:

- **Seeds pinned**
- **Precision declared** (explicit `mp.dps` in Python, `MathContext` in Java)
- **Configs logged** (parameters, thresholds, sample counts)
- **Artifacts exported** (results, plots, data)
- **Statistics:** Sample definition + bootstrap intervals (1000+ resamples)
- **Timestamps:** Exact dates, exact magnitudes, exact parameters
- **Rerunnable by anyone, including you six months from now**

## Precision is First-Class

Numerical drift hides in "good enough." Surface precision explicitly.

- **Python:** `mpmath` with declared `mp.dps` or `MPFR` with bit precision
- **Java:** `BigDecimal` with explicit `MathContext`, arbitrary-precision where warranted
- **Measure overhead, don't guess**
- **Raise precision until errors vanish, record the choice, move on**

### Adaptive Precision Formula
For phase-corrected logarithmic factorization:
```
precision = max(configured, N.bitLength() × 4 + 200)
```
Justified by exponential error propagation in `exp((ln(N) + Δφ) / 2)`.

## Iterative Development Discipline

**Never batch fixes.** Prove each change in isolation.

### The Geodesic Path (Shortest Distance to Proof)
1. **Implement smallest change** (e.g., precision scaling alone)
2. **Run test, capture exact failure mode**
3. **Document why it failed** (epsilon too loose? phase bias?)
4. **Add one more fix**
5. **Repeat until success**
6. **Delete unnecessary additions**

### Anti-Pattern: Frontloading Complexity
Do NOT:
- Add 5 fixes simultaneously
- Commit before test passes
- Create comprehensive documentation before proving success
- Introduce "just in case" checks without proving necessity

### Correct Pattern: Incremental Proof
Example for 127-bit factorization failure:
1. Test with precision 708 alone → still times out
2. Add epsilon regularization (10⁻³⁵⁴) → still times out
3. Add Newton refinement → partial success (finds factors 30% of runs)
4. Add expanded sampling → consistent success
5. Remove stability verification → still succeeds → DELETE IT
6. Commit minimal working set

## Testing Discipline

"Works" means:
- **Worked at declared scale** (e.g., the Gate 1 challenge number)
- **Under declared constraints** (gate range, precision, timeout)
- **With declared parameters** (samples, m-span, threshold)
- **Artifact exists to prove it** (test output, logs, timing)

### Before Committing
- [ ] Test passes at target scale
- [ ] Exact parameters logged in test output
- [ ] Failure modes documented if applicable
- [ ] No "just in case" code remains
- [ ] No scaffolding outliving its usefulness

## Scope is a Promise

Label precisely:
- **Prototypes as prototypes**
- **Narrow by design as intentionally narrow**
- **Success criteria in measurable terms**

Example:
```java
// BENCHMARK: Gate 1 Challenge Number (see docs/VALIDATION_GATES.md)
// Success: factors found within 600s timeout at 708-digit precision
// Parameters: samples=10000, m-span=1000, threshold=0.80
```

When something fails:
- Record exact conditions (N, precision, parameters, timeout)
- Move forward without ritual
- Prefer precision about small, relevant domain over vagueness about broad, irrelevant one

## Tooling Philosophy

- **Fast local loops over heavy CI**
- **Lean CI that enforces rules that matter:** Validation gate, canonical terminology, minimal scope
- **One targeted guard > forest of brittle jobs**
- **Documentation mirrors code:** Slim, canonical, just enough to reproduce and verify

## Code Structure Preferences

### Java
```java
// GOOD: Guard clause, early exit, flat control flow
if (N == null) {
    throw new IllegalArgumentException("N cannot be null");
}
if (N.signum() <= 0) {
    throw new IllegalArgumentException("N must be positive");
}

// BAD: Nested if/else, tangled state
if (N != null) {
    if (N.signum() > 0) {
        // deep nesting
    } else {
        throw new IllegalArgumentException("N must be positive");
    }
}
```

### Method Naming
```java
// GOOD: Verbs for actions, precise domain language
verifyAmplitudeStability(theta, sigma, threshold, mc)
newtonRefinementTowardExponent(pInitial, lnN, dPhi, mc, iterations)

// BAD: Vague, abbreviated, puzzle-like
checkAmp(t, s, thr, m)
refine(p, ln, d, mc, i)
```

### Comments
```java
// GOOD: Explains WHY, references theory
// CRITICAL: Use 4 × bitLength + 200 for 127-bit precision stability
// Addresses exponential error propagation in phase-corrected logarithmic factorization

// BAD: Apologizes for ambiguity or restates code
// Set precision to a big number
// This is important
```

## What to Delete Immediately

- **Classical fallback paths:** Pollard's Rho, trial division, ECM
- **Unused parameters or config options**
- **"Just in case" validation that never fires**
- **Comments explaining bad names** (rename instead)
- **Scaffolding after the feature is done**
- **Synthetic test data** (use official challenge numbers)
- **Branches that can be collapsed**

## What to Keep

- **Explicit validation gates** (as defined in `docs/VALIDATION_GATES.md`)
- **Precision declarations**
- **Reproducibility metadata** (seeds, timestamps, parameters)
- **Guard clauses that enforce invariants**
- **Names that explain themselves**
- **Academic references with URLs** (theory grounding)

## Geometric, Invariant-Driven Taste

Code treats structure as primary, algorithms as ways to reveal structure.

### Good Abstractions
- Remove branches
- Reduce moving parts
- Clarify the story

### Bad Abstractions
- Add complexity without removing branches
- Complicate boundaries without improving claims
- Future-proof for scenarios that don't exist

If an abstraction doesn't do one of the good things, delete it.

## Commit Discipline

### Before Committing
1. **Test passes** at declared scale with declared parameters
2. **Smallest change** that makes test pass (no extras)
3. **No dead code, no commented-out blocks**
4. **No scaffolding remaining**
5. **Artifacts exist** (test output proves success)

### Commit Message Format
```
fix: <what> for <scale/domain>

Root cause: <exact failure mode>
Fix: <minimal change applied>
Impact: <measurable improvement>

Tested: <exact parameters, scale, result>
Artifact: <where proof lives>
```

Example:
```
fix: Adaptive precision scaling for Gate 1 challenge factorization

Root cause: Exponential error propagation in exp((ln(N) + Δφ)/2) exceeded ±1 neighbor window at 260 digits.
Fix: precision = N.bitLength() × 4 + 200 (708 digits for 127-bit)
Impact: Post-exponential error reduced from 10^-222 to 10^-670

Tested: Gate 1 challenge number, factors found in 4.2 minutes.
Artifact: test/FactorizerServiceTest.java assertion passes.
```

## PR Requirements

### Before Creating PR
- [ ] All tests pass at target scale
- [ ] No untested code paths
- [ ] No "just in case" branches
- [ ] Commit message explains exact failure mode and minimal fix
- [ ] Documentation updates only if boundary changed

### PR Description Structure
```markdown
## Problem
<Exact failure mode with parameters>

## Fix
<Minimal change applied>

## Testing
<Exact scale, parameters, result, artifact location>

## Changes
<File-by-file summary, line count deltas>
```

Keep it short. No speculation about future work. No "nice to have" sections.

## When You Make a Mistake

If you introduce complexity that doesn't remove branches or clarify the story:

1. **Acknowledge it:** "This adds a verification step that may not be necessary"
2. **Test without it:** Remove the code, re-run test
3. **Delete if test still passes**
4. **Keep only if failure is proven**

Do NOT defend complexity. If it's not minimal, it's wrong.

## Project-Specific Context

### Geofac: Geometric Factorization Service
- **Algorithm:** Resonance-guided factorization via Gaussian kernel + phase-corrected logarithmic snap
- **Validation Policy:** See `docs/VALIDATION_GATES.md` for the official project gates.
- **Precision:** Adaptive formula `4 × bitLength + 200` for phase correction stability
- **Purity:** No classical fallbacks, ever
- **Target:** Balanced semiprimes (|p - q| small, narrow resonance peaks)

### Key Classes
- `FactorizerService.java` - Main search loop, QMC sampling, resonance detection
- `GaussianKernel.java` - A(θ) = exp(-θ²/(2σ²)), no singularities
- `DirichletKernel.java` - Legacy, kept for comparison, has singularity guards
- `SnapKernel.java` - Phase-corrected factor snap with Newton refinement
- `FactorizerServiceTest.java` - Validates the Gate 1 challenge number.

### Critical Invariants
The project's validation gates are defined in `docs/VALIDATION_GATES.md`. The constants in `FactorizerService.java` reflect this policy.
```java
// See docs/VALIDATION_GATES.md for the policy behind these constants.
private static final BigInteger GATE_2_MIN = ...;
private static final BigInteger GATE_2_MAX = ...;
private static final BigInteger GATE_1_CHALLENGE = ...;

// Adaptive precision formula
int adaptivePrecision = Math.max(configuredPrecision, N.bitLength() * 4 + 200);
```

Never relax these without explicit user approval.

## Summary: The Geodesic Principle

Every decision flows from one question:

**"Is this the shortest path from problem to proof?"**

If the answer is no:
- Simplify
- Remove branches
- Flatten control flow
- Delete scaffolding
- Test smaller change

If the answer is yes:
- Name it precisely
- Guard invariants explicitly
- Log parameters exactly
- Commit with proof

The result should feel like the shortest geodesic from problem to proof: spare but not austere, strict but not brittle.

---

**Remember:** Every line is a liability. Make each one indispensable—or remove it.
