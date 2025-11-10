# Geofac Constitution

<!--
SYNC IMPACT REPORT - 2025-11-09

VERSION CHANGE: N/A → 1.0.0
RATIONALE: Initial constitution establishment (MAJOR version for first release)

MODIFIED PRINCIPLES: N/A (initial version)
ADDED SECTIONS:
  - Core Principles (5 principles)
  - Quality Standards
  - Development Workflow
  - Governance

TEMPLATES STATUS:
  ✅ .specify/templates/plan-template.md - Reviewed, constitution check placeholder is generic and compatible
  ✅ .specify/templates/spec-template.md - Reviewed, no principle-specific dependencies
  ✅ .specify/templates/tasks-template.md - Reviewed, task categorization aligns with principles
  ✅ .specify/templates/checklist-template.md - Reviewed, no principle-specific dependencies

FOLLOW-UP TODOS: None
-->

## Core Principles

### I. Resonance-Only Factorization (NON-NEGOTIABLE)

The system MUST factor semiprimes exclusively through geometric resonance search. Fallback methods (Pollard Rho, ECM, QS, GNFS, trial division) are strictly prohibited and must not exist in reachable code paths. Every factorization attempt uses Dirichlet kernel gating, golden-ratio QMC sampling, and phase-corrected snapping.

**Rationale**: Geofac exists to prove geometric resonance factorization works for the target semiprime N=137524771864208156028430259349934309717. Allowing fallbacks would invalidate the experimental objective and make results non-attributable to resonance alone.

**Test criteria**:
- Code review must verify no imports or calls to fallback algorithms
- Integration tests must fail gracefully when no factors found (no fallback execution)
- All factorization paths must trace through FactorizerService.findFactors() only

### II. Reproducibility (NON-NEGOTIABLE)

Every factorization run MUST be fully reproducible via fixed seeds, frozen configuration, and exported artifacts. Results must include: factors.json, search_log.txt, config.json, and env.txt capturing all parameters, timings, kernel amplitudes, and system state.

**Rationale**: Scientific credibility requires that successful factorization can be verified independently. Reproducibility enables peer review, debugging, and parameter sensitivity analysis.

**Test criteria**:
- Same input + same config + same seed → identical output
- Artifact exports contain complete parameter state
- CI runs must capture and archive all four artifact files

### III. Test-First Development

New features and bug fixes MUST follow TDD discipline: tests written → user approved → tests fail → then implement. Focus on integration tests for factorization workflows and contract tests for CLI/API boundaries. Unit tests are optional for internal math utilities.

**Rationale**: Factorization algorithms are complex and error-prone. TDD ensures we document expected behavior before implementation and catch regressions early. Integration tests validate end-to-end correctness critical for mathematical correctness.

**Test criteria**:
- PRs must include test code written before implementation
- Test commit must predate implementation commit (via git log)
- CI must run tests on every push

### IV. High-Precision Arithmetic

All mathematical operations MUST use arbitrary-precision arithmetic via ch.obermuhlner:big-math with MathContext precision determined by input size (minimum 240 decimal digits, auto-raised for larger N). Kernel amplitude calculations, QMC sampling, and candidate snapping all require precise rational arithmetic—never floating-point approximations.

**Rationale**: Factorization depends on detecting resonance peaks within narrow amplitude windows. Floating-point error accumulation can cause false negatives (missed factors) or false positives (invalid candidates). High-precision arithmetic ensures numerical stability.

**Test criteria**:
- Code review verifies all math uses BigDecimal or BigRational types
- No usage of Java double/float types in factorization paths
- Precision validation tests check MathContext settings match requirements

### V. Deterministic Configuration

All tunable parameters (samples, m-span, kernel order J, threshold, k-range, timeout) MUST live in application.yml and be overridable via Spring profiles, environment variables, or CLI args. No hardcoded "magic numbers" in factorization logic. Default values must be documented with empirical justification.

**Rationale**: Parameter tuning is essential for resonance algorithm optimization. Centralized configuration enables reproducibility, A/B testing, and transparent documentation of what values produced successful factorizations.

**Test criteria**:
- Grep src/ for numeric literals in factorization code (must have config references)
- Config changes must not require code recompilation
- Documentation must explain default parameter rationale

## Quality Standards

### Code Quality

- **Language**: Java 17+ with Spring Boot 3.2.0
- **Build**: Gradle with dependency locking
- **Testing**: JUnit 5 with Spring Boot Test
- **Formatting**: Standard Java conventions (4-space indent, 120-char line limit)
- **Linting**: SpotBugs or CheckStyle for static analysis (recommended but not enforced initially)

### Mathematical Precision Requirements

- **BigDecimal MathContext**: Minimum 240 decimal digits precision, auto-scaled with input size
- **Numerical stability**: Monitor for precision loss in iterative kernel calculations
- **Guard conditions**: Validate division by zero, domain constraints (k in [0,1], m positive integer)
- **Performance regression**: Benchmark kernel amplitude calculation time (baseline: <1ms per sample on M1 Mac)

### Scientific Rigor Requirements

- **Empirical validation**: Document all successful factorizations with full artifact sets
- **Parameter transparency**: Config files must capture exact values used in each run
- **Failure documentation**: Log unsuccessful runs to inform parameter tuning
- **Statistical analysis**: Track amplitude distribution histograms for resonance peak analysis

## Development Workflow

### Branching Strategy

- **main**: Production-ready code only (successful factorizations)
- **Feature branches**: `###-feature-name` format
- **Hotfixes**: `hotfix/description` for critical bug fixes

### Pull Request Requirements

1. **Tests pass**: All JUnit tests green
2. **No fallbacks**: Code review confirms resonance-only paths
3. **Artifact export**: If factorization changes, verify artifact generation works
4. **Config documented**: New parameters added to application.yml with comments
5. **Reproducibility**: Include seed values and expected outputs in PR description

### Commit Message Format

Standard conventional commits:
- `feat:` new factorization capabilities or CLI commands
- `fix:` bug fixes in resonance algorithm
- `test:` test additions or fixes
- `docs:` documentation updates
- `config:` application.yml or build configuration changes
- `refactor:` code improvements without behavior change

### CI/CD Requirements

- **CI runs**: Execute tests on every push
- **Artifact archival**: Capture results/ directory contents for successful factorization runs
- **Seed pinning**: CI must use fixed seeds for reproducibility verification
- **Timeout enforcement**: Respect search-timeout-ms to prevent hung CI jobs

## Governance

### Amendment Procedure

1. **Proposal**: Open GitHub issue describing constitutional change and rationale
2. **Discussion**: Maintainers discuss impact on project objectives
3. **Approval**: Requires maintainer consensus (unanimous for NON-NEGOTIABLE principles)
4. **Migration**: Update all affected code, tests, and documentation before merge
5. **Version bump**: Increment constitution version according to semantic versioning

### Versioning Policy

- **MAJOR**: Backward-incompatible changes (e.g., removing a principle, changing NON-NEGOTIABLE status)
- **MINOR**: New principles added or significant guidance expansion
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Review

- **PR reviews**: Reviewers must verify constitutional compliance (checklist in PR template recommended)
- **Quarterly audits**: Review codebase for principle drift (e.g., accidental fallback code introduction)
- **Violation handling**: Constitutional violations block PR merge until resolved

### Complexity Justification

Any PR that violates simplicity expectations (e.g., introduces new dependency, adds architectural pattern) must include:
- **What**: Specific complexity being added
- **Why needed**: Problem it solves that simpler approach cannot
- **Simpler alternative rejected because**: Explicit reasoning

**Version**: 1.0.0 | **Ratified**: 2025-11-09 | **Last Amended**: 2025-11-09
