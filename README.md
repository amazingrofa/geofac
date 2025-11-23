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

### P-adic topology (normalized terminology)
Geofac's per-prime structures align with standard p-adic language: spines are truncated `Z_p` expansions, "residue tunnels" are Hensel lifts, and cluster strata are p-adic balls. The global real + per-prime snapshot is a truncated adele; behavior is unchanged, only the vocabulary is standardized.

See `docs/padic_topology_geofac.md` for the mapping and definitions. A deterministic demo lives at `python docs/experiments/padic_spine_demo.py` and logs the adaptive precision it uses (formula: `max(configured, bitlength * 4 + 200)`).

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
| `enable-scale-adaptive` | `true` | **NEW**: Automatically tune parameters based on N's bit-length using empirical scaling laws (Z5D insights). |
| `scale-adaptive-attenuation` | `0.05` | Threshold attenuation factor for scale-adaptive mode. |
| `precision` | `240` | Minimum decimal digits for the BigDecimal math context (auto-raised with input size). |
| `samples` | `3000` | Number of k-samples explored per attempt (base value, scaled adaptively if enabled). |
| `m-span` | `180` | Half-width for the Dirichlet kernel sweep over `m` (base value, scaled adaptively if enabled). |
| `j` | `6` | Dirichlet kernel order. |
| `threshold` | `0.92` | Normalized amplitude gate before evaluating a candidate (base value, scaled adaptively if enabled). |
| `k-lo`, `k-hi` | `0.25`, `0.45` | Fractional k-sampling range (base values, adjusted adaptively if enabled). |
| `search-timeout-ms` | `600000` | Max time per attempt; on timeout the command exits (base value, scaled adaptively if enabled). |

**Scale-Adaptive Mode** (enabled by default): Implements empirical scaling laws based on Z5D Prime Predictor research. Parameters automatically adapt to N's bit-length, recognizing that number-theoretic patterns exhibit scale-dependent (not scale-invariant) behavior. See `docs/SCALE_ADAPTIVE_TUNING.md` for details.

Override via Spring config (profiles, env vars, command-line args) as needed.

---

### Testing

The test suite implements a four-gate progressive validation framework. Run the full suite:

```bash
./gradlew test
```

#### Validation Gates

The project uses four sequential validation gates of increasing difficulty:

1. **Gate 1 (30-bit)**: Quick sanity check (~5 seconds)
   ```bash
   ./gradlew test --tests "com.geofac.FactorizerServiceTest.testGate1_30BitValidation"
   ```

2. **Gate 2 (60-bit)**: Scaling validation (~30 seconds)
   ```bash
   ./gradlew test --tests "com.geofac.FactorizerServiceTest.testGate2_60BitValidation"
   ```

3. **Gate 3 (127-bit)**: Challenge verification (~5 minutes)
   ```bash
   ./gradlew test --tests "com.geofac.FactorizerServiceTest.testGate3_127BitChallenge"
   ```

4. **Gate 4**: Operational range testing [10^14, 10^18]
   ```bash
   ./gradlew test --tests "com.geofac.FactorizerServiceTest.testGate4_OperationalRange"
   ```

For development, start with Gates 1-2 for fast feedback:
```bash
./gradlew test --tests "*Gate1*" --tests "*Gate2*"
```

See `docs/VALIDATION_GATES.md` for complete gate specifications and success criteria.

---

### Project layout
```
geofac/
├── src/main/java/com/geofac    # Java source (Spring Boot application)
│   ├── GeofacApplication       # Spring Boot entry point
│   ├── FactorizerService       # Geometric resonance search core (no fallbacks)
│   ├── FactorizerShell         # Spring Shell command surface
│   └── util/                   # Kernel implementations
├── docs/                       # All documentation
│   ├── CODING_STYLE.md         # Canonical style and invariants
│   ├── VALIDATION_GATES.md     # Gate specifications
│   ├── WHITEPAPER.md           # Method overview and verification
│   └── ...                     # Additional technical docs
├── tests/                      # Python test suite (scale-based + method tests)
├── scripts/                    # Shell scripts (factor_one.sh, proof_pack.sh)
├── experiments/                # Experimental implementations and falsification attempts
├── geofac.py                   # Main Python implementation (GVA)
├── gva_factorization.py        # Core GVA algorithm
└── build.gradle                # Gradle build configuration
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
- **[SCALE_ADAPTIVE_TUNING.md](docs/SCALE_ADAPTIVE_TUNING.md)** — Scale-adaptive parameter tuning: empirical scaling laws, Z5D insights, and implementation for the 127-bit challenge
- **[Z5D_INSIGHTS_CONCLUSION.md](docs/Z5D_INSIGHTS_CONCLUSION.md)** — Executive summary: how Z5D Prime Predictor research applies to breaking the 127-bit barrier

These documents provide verifiable artifacts, reproducibility notes, and links to canonical theoretical sources.

### Additional Research Directions (Performance-focused)
- **Hardware Acceleration**: Explore and implement hardware-accelerated optimizations, such as using the Apple Matrix Coprocessor (AMX) or other specialized hardware for computational tasks.
- **Advanced QMC Methods**: Investigate and benchmark alternative Quasi-Monte Carlo sequences or methods for further variance reduction and faster convergence.
