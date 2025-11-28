## Geofac — Ranked Geometric Search + Arithmetic Certification

This repo pursues one objective: factor the challenge semiprime `N` defined in the official validation policy by **using
geometry to rank candidates and arithmetic to certify them**. See [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md)
for target and success criteria,
and [docs/theory/GEOMETRIC_CERTIFICATION_BOUNDARY.md](docs/theory/GEOMETRIC_CERTIFICATION_BOUNDARY.md) for the formal
boundary between geometry and certification.

Geofac is a Spring Boot + Spring Shell application whose geometric phase produces a small, ordered candidate set near
\(\sqrt{N}\). Certification is the minimal arithmetic predicate `IsFactor_N(d) := (N mod d == 0)` applied only to the
top-ranked candidates. Classical wide-sweep fallbacks (Pollard Rho, ECM, QS, etc.) remain out of scope, but arithmetic
certification is **required** and explicitly logged.

### Why it exists

- Demonstrate that geometric ranking can shrink the expected rank of the true factor so only a handful of modular checks
  are needed.
- Provide a reproducible, deterministic harness (Spring Boot, JUnit 5, Gradle) for measuring that ranking quality.
- Offer an interactive CLI to tune geometric parameters while keeping the arithmetic certificate explicit.

### Non-negotiables

- **Geometry ranks, arithmetic certifies** – every reported factor is confirmed via `N mod d`; geometry only orders
  candidates.
- **No wide classical sweeps** – we do not broaden into Pollard Rho, ECM, QS, or bulk trial division beyond the ranked
  set.
- **Reproducibility and logging** – deterministic seeds/precision; logs include parameters, candidate list, rank of any
  factor, and predicate outputs so runs can be replayed without rerunning geometry.

### Core Philosophy: Geometry as a Map
**Geometry is a map, not a key.**

1. **Certification Boundary:** Purely geometric factorization is impossible; arithmetic verification is mandatory.
   Geofac measures success by how small the certified set \(d_1,\dots,d_m\) can be made.
2. **Value Proposition:** Use geometric scoring to push the true factor’s expected rank well below any naive window
   width \(W\), shrinking the number of `N mod d` evaluations.
3. **Final Step:** The pipeline always ends with `N mod d` (or GCD) on the top-ranked candidates. The log of those
   predicates is part of the proof artifact.

### Geometric certification boundary
- Geometry proposes **where to look and in what order**; arithmetic certifies truth with `IsFactor_N(d) := (N mod d == 0)`.
- Only the top-ranked geometric candidates `d1..dm` are certified; no wide trial-division sweeps, Pollard Rho, ECM, or other classical fallbacks.
- Progress is measured when the expected rank of the true factor is far smaller than any naive scan window (
  \(\mathbb{E}[\text{rank}(p)] \ll W\)).
- Artifacts must log parameters, the exact candidates submitted to `IsFactor_N`, their scores, the observed rank of any
  discovered factor, and predicate outputs so a replayed log fully certifies the result.
- See `docs/theory/GEOMETRIC_CERTIFICATION_BOUNDARY.md` for the formal statement and evidence expectations.

### Key features

- **Banded geometric search near \(\sqrt{N}\)** – candidate divisors are generated in a symmetric window, deduped by
  distance, and ranked by a high-precision resonance score.
- **High-precision math** – scoring uses `BigDecimal`/`BigInteger` with precision tied to `N.bitLength()` to avoid
  drift; zero-remainder shortcut when a candidate divides cleanly.
- **Deterministic seeding** – `SplittableRandom` seeds derive from \(N\) so runs are reproducible and replayable.
- **Spring Shell CLI** – run `factor <N>` with deterministic logs; job artifacts include parameters, ranked candidates,
  and certification outcomes.

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
- **[GEOMETRIC_CERTIFICATION_BOUNDARY.md](docs/theory/GEOMETRIC_CERTIFICATION_BOUNDARY.md)** — Clarifies the boundary between geometric ranking and the arithmetic predicate, plus logging expectations for certification
- **[Z5D_INSIGHTS_CONCLUSION.md](docs/Z5D_INSIGHTS_CONCLUSION.md)** — Executive summary: how Z5D Prime Predictor research applies to breaking the 127-bit barrier

These documents provide verifiable artifacts, reproducibility notes, and links to canonical theoretical sources.

### Additional Research Directions (Performance-focused)
- **Hardware Acceleration**: Explore and implement hardware-accelerated optimizations, such as using the Apple Matrix Coprocessor (AMX) or other specialized hardware for computational tasks.
- **Advanced QMC Methods**: Investigate and benchmark alternative Quasi-Monte Carlo sequences or methods for further variance reduction and faster convergence.
