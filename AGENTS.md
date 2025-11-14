# AGENTS.md

Operating rules for all coding agents (Copilot Chat/Code Agent/CLI, Claude, etc.) in this repository.

Authoritative references
- CODING_STYLE.md (style, invariants, discipline)
- README.md (project scope and boundaries)
- CLAUDE.md (geofac-specific constraints and rationale)

Non‑negotiable invariants
- Validation gate: The project follows a strict, two-gate validation policy. All code must adhere to the rules defined in [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md).
- No classical fallbacks: Do not propose or insert Pollard’s Rho, trial division, ECM, or sieves.
- Deterministic/quasi‑deterministic methods only (Sobol/Halton, Gaussian kernel resonance, phase‑corrected snap). No stochastic “try until it works.”
- Precision is explicit and adaptive: precision = max(configured, N.bitLength() × 4 + 200). In Java use BigDecimal with explicit MathContext; in Python use mpmath/mpfr with explicit mp.dps/bits. Log the chosen precision.

Reproducibility requirements
- Pin seeds; log exact parameters, thresholds, sample counts, and timeouts; include precise timestamps; export artifacts when applicable.
- Tests/benchmarks must state scale, parameters, and success criteria in output.

Code change rules
- Smallest possible change that proves the claim; delete scaffolding that outlives its usefulness; no speculative “just in case” branches.
- Flatten control flow with guard clauses; prefer pure functions; collapse unearned branches.
- Names are plain language and precise; small, literal interfaces; code reads linearly.
- Use only RSA challenge numbers for semiprimes; no synthetic look‑alikes.

Tooling and execution
- Run only existing linters/builds/tests; prefer ecosystem tools; chain commands; keep output quiet.
- Search/edit only within this repo (cwd and children). Do not introduce external services or secrets.
- Log parameters and precision when running experiments or tests.

Default refusals
- Requests that violate the gate/whitelist, add classical fallbacks, broaden scope without proof, or remove precision/reproducibility logging.

Commit/PR discipline
- Single, surgical diffs tied to a demonstrated failure mode.
- Commit message format:
  fix: <what> for <scale/domain>
  Root cause: <exact failure mode>
  Fix: <minimal change>
  Impact: <measurable improvement>
  Tested: <exact parameters, scale, result>
  Artifact: <where proof lives>

Behavioral defaults for agents
- When ambiguous, ask for exact N, scale, and timeout; refuse to proceed without them for factorization tasks.
- Enforce adaptive precision and log it; pin seeds by default for any stochastic component in the environment.
- Prefer deletions and guard‑clause refactors over adding branches.

Pointers
- See ./CODING_STYLE.md, ./README.md, and ./CLAUDE.md for details and examples.

Timestamp
- 2025-11-13T02:31:21.417Z
