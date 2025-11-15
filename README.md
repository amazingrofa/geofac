## Geofac — Singular Objective: Factor N via Geometric Resonance (No Fallbacks)

This repo has a single objective: factor the challenge semiprime `N` defined in the project's official validation policy. See [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md) for a full description of the target and success criteria.

Geofac is a Spring Boot + Spring Shell application that implements the geometric resonance factorization algorithm in pure Java. All fallback methods (Pollard Rho, ECM, QS, etc.) are removed or unreachable—the code path is 100 % geometric.

### Why it exists
- Deliver a reproducible, deterministic geometric-resonance factorization for the official challenge `N`.
- Provide a tight, auditable test harness (Spring Boot, JUnit 5, Gradle).
- Offer an interactive CLI for iterating resonance parameters only.

### Non-negotiables
- **No fallbacks** – the system never drops into Pollard Rho, ECM, QS, or any probabilistic helper.
- **Resonance-only search paths** – Dirichlet kernel gating + golden-ratio QMC drive every candidate.
- **Reproducibility** – fixed seeds, frozen configs, and exported artifacts per run.

### Key features (resonance-only)
- **High-precision core** – `FactorizerService` uses `ch.obermuhlner:big-math`, Dirichlet kernel gating, golden-ratio quasi Monte Carlo sampling, and phase-corrected snapping.
- **Configurable search** – sampling range, kernel order (`J`), thresholds, and precision live in `application.yml`.
- **Spring Shell CLI** – run `factor <N>` inside the embedded shell with deterministic logs.
- **Proof artifacts** – each run writes `factors.json`, `search_log.txt`, `config.json`, and `env.txt`.

---

### Getting started
Prerequisites
- JDK 17 or later (tested with JDK 24)
- Gradle 8.14 (wrapper bundled)
- Git

```bash
git clone https://github.com/zfifteen/geofac.git
cd geofac
./gradlew bootRun
```

At the `shell:>` prompt, run the `example` command to see how to factor the official challenge number as defined in [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md).

```shell
shell:>example
```

On success the CLI prints `p`, `q`, verifies `p * q == N`, and writes artifacts to a run-specific directory.

If no factors are found within the configured budget, the run exits cleanly. No alternative methods are attempted.

---

### Configuration
`src/main/resources/application.yml` → `geofac.*`

| Property | Default | Description |
| --- | --- | --- |
| `precision` | `240` | Minimum decimal digits for the BigDecimal math context (auto-raised with input size). |
| `samples` | `3000` | Number of k-samples explored per attempt. |
| `m-span` | `180` | Half-width for the Dirichlet kernel sweep over `m`. |
| `j` | `6` | Dirichlet kernel order. |
| `threshold` | `0.92` | Normalized amplitude gate before evaluating a candidate. |
| `k-lo`, `k-hi` | `0.25`, `0.45` | Fractional k-sampling range. |
| `search-timeout-ms` | `600000` | Max time per attempt; on timeout the command exits (no fallback). |

Override via Spring config (profiles, env vars, command-line args) as needed.

---

### Testing
```bash
./gradlew test
```

This runs validation tests plus the long 127-bit reference scenario. For manual resonance runs, use the CLI example above. Heavy, multi-minute factor attempts intentionally stay out of default CI.

---

### Project layout
```
src/main/java/com/geofac
├── GeofacApplication      # Spring Boot entry point
├── FactorizerService      # Geometric resonance search core (no fallbacks)
├── FactorizerShell        # Spring Shell command surface
├── util
│   ├── DirichletKernel    # Kernel amplitude / angular math
│   └── SnapKernel         # Phase-corrected snapping heuristic
└── TestFactorization      # Standalone main for manual experiments
```

---

### CI & proof requirements
- CI shard runs with pinned seeds and expects stdout proof: `p`, `q`, `p*q == N`.
- Artifacts from `results/N=.../<run_id>/` must be captured for verification.

### Contributing
This repo has a single goal: factor `N` above via geometric resonance only. PRs must explain how they advance that goal. Introducing or re-enabling fallback methods is out of scope.

### Roadmap (strictly in-scope)
1. **Performance Optimization (Primary Goal)**: Implement and benchmark optimizations to reduce sample counts, decrease runtime, and/or improve convergence. This includes parameter grid refinement, algorithmic improvements, and hardware acceleration.
2. **Deterministic Progress Logging**: Enhance logging with lightweight amplitude histograms and deterministic progress markers to better analyze performance of runs.
3. **CI Artifact and Proof Bundling**: Automate the bundling of artifacts with a one-page proof report for easier verification.

### Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[WHITEPAPER.md](docs/WHITEPAPER.md)** — Empirical whitepaper on geometric resonance factorization: method overview, verification, QMC analysis, theoretical context, and acceptance criteria validation
- **[VERIFICATION.md](docs/VERIFICATION.md)** — Detailed verification appendix: exact N, p, q, artifact locations, reproduction instructions, and configuration parameters
- **[QMC_METHODS.md](docs/QMC_METHODS.md)** — Quasi-Monte Carlo methods: golden ratio sampling, Sobol sequences, variance reduction theory, and practical comparison
- **[THEORY.md](docs/THEORY.md)** — Theoretical foundations: complexity theory (Time Hierarchy, Rice's theorem), physical limits (Margolus-Levitin, Bremermann), and decidability constraints

These documents provide verifiable artifacts, reproducibility notes, and links to canonical theoretical sources.

### Additional Research Directions (Performance-focused)
- **Hardware Acceleration**: Explore and implement hardware-accelerated optimizations, such as using the Apple Matrix Coprocessor (AMX) or other specialized hardware for computational tasks.
- **Advanced QMC Methods**: Investigate and benchmark alternative Quasi-Monte Carlo sequences or methods for further variance reduction and faster convergence.