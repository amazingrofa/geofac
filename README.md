⚠️ **Strict scope:** This repo exists solely to run a Geometric Resonance factorization
on N = 137524771864208156028430259349934309717. No alternative algorithms. No fallback.

## Geofac

Geofac is an experimental Spring Boot + Spring Shell application that reimplements the "geometric resonance" factorization algorithm in pure Java for a specific 127-bit semiprime defined in Policy.TARGET.

### Why it exists
- Prototype a deterministic-style factorization approach inspired by the author’s z-sandbox notebooks.
- Provide a reproducible test harness built with Spring Boot, JUnit 5, and Gradle.
- Offer a shell-first user experience for iterating on search parameters without bespoke tooling.

### Key features
- **High-precision core** – `FactorizerService` uses `ch.obermuhlner:big-math` for arbitrary precision math, Dirichlet kernel gating, and phase-corrected “snap” rounding.
- **Adaptive search** – sampling range, kernel order (`J`), and thresholds are all configurable through `application.yml`.
- **Strict enforcement** – only the designated target N is accepted; geometric resonance is the sole algorithm.
- **Spring Shell CLI** – run `factor <semiprime>` directly in the embedded shell, complete with formatted output and helpful error messages.
- **Integration tests** – `FactorizerServiceTest` exercises validation rules and a 127-bit reference semiprime (expect a ~5 minute runtime).

### Getting started
Prerequisites:
- JDK 17 (repo sets `org.gradle.java.home` for convenience, but any local JDK 17 installation works)
- Git & Gradle wrapper (bundled)

Clone and run the interactive shell:
```bash
git clone https://github.com/zfifteen/geofac.git
cd geofac
./gradlew bootRun
```

Once the Spring Shell prompt appears, factor a known semiprime:
```shell
shell:>factor 137524771864208156028430259349934309717
```

You can also review the built-in demo text:
```shell
shell:>example
```

### Configuration
All tuning knobs live in `src/main/resources/application.yml` under the `geofac.*` namespace:

| Property | Default | Description |
| --- | --- | --- |
| `precision` | `240` | Minimum decimal digits used by the BigDecimal math context (automatically raised with input size). |
| `samples` | `3000` | Number of k-samples explored per factorization attempt. |
| `m-span` | `180` | Half-width for the Dirichlet kernel sweep over `m`. |
| `j` | `6` | Dirichlet kernel order. |
| `threshold` | `0.92` | Minimum normalized amplitude required before evaluating a candidate. |
| `k-lo`, `k-hi` | `0.25`, `0.45` | Range for k sampling (fractional offsets). |
| `search-timeout-ms` | `15000` (defaulted in code) | Maximum time allowed for the geometric search. |

Modify these settings, or override them with Spring’s standard configuration mechanisms (env vars, profiles, etc.).

### Testing
Run the full suite (warning: the 127-bit integration test takes ~5–6 minutes):
```bash
./gradlew test
```

For a faster feedback loop, target only the lightweight tests:
```bash
./gradlew test --tests "com.geofac.FactorizerServiceTest.testServiceIsInjected"
```

To exercise the heavy semiprime test by itself:
```bash
./gradlew test --tests "com.geofac.FactorizerServiceTest.testFactor127BitSemiprime"
```

Test reports land in `build/reports/tests/test/index.html`.

### Project layout
```
src/main/java/com/geofac
├── GeofacApplication      # Spring Boot entry point
├── FactorizerService      # Geometric resonance factorization
├── FactorizerShell        # Spring Shell command surface
├── util
│   ├── DirichletKernel    # Kernel amplitude / angular math
│   └── SnapKernel         # Phase-corrected snapping heuristic
└── TestFactorization      # Standalone main for manual experiments
```

### Roadmap ideas
1. Add profiling hooks to capture amplitude distributions per run.
2. Move long-running tests behind a Gradle profile to unblock CI.
3. Experiment with GPU-backed kernels or Kotlin Multiplatform ports.

Pull requests and issue discussions are welcome—this project is a playground for factorization research, so curiosity > polish.
