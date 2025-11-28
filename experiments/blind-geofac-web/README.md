# Blind Geofac Web (Spring Boot, Java 21)

## Summary

This web app tries to break a very large number into two secret factors. It does this by looking near the square root of
the number and scoring which nearby divisors are most likely to be real. Only the best few candidates are checked
exactly, which keeps the work small. You can start a job in the browser, watch the logs live, and see if the number
splits. Everything is repeatable because the random choices are fixed by the number itself.

How to run locally:
```bash
# from repo root
./gradlew -p experiments/blind-geofac-web bootRun
```

Then open http://localhost:8080/ to launch or monitor factoring jobs.

### Config/status endpoint

`GET /api/config` returns the current engine settings (pre-adaptive) so operators can confirm which parameters are
active and decide what to override.

### Long 127-bit challenge test

- Gated to stay out of default CI: run with
  `./gradlew -p experiments/blind-geofac-web test -Dgeofac.runLongChallengeIT=true --tests \"*FactorServiceChallengeIT\"`
- Success criterion: find a factor within 30 minutes. Feel free to tweak `geofac.*` parameters if it runs long; watch
  the console/SSE logs for progress.

## Technical and Scientific Detail

### Goal and Scope

Blind Geofac implements a geometric ranking model that narrows the search for a factor of an odd semiprime \(N\). It
does **not** replace the arithmetic certificate `N mod d == 0`; instead it orders a thin candidate set so that only a
handful of modular checks are needed. This aligns with the Geometric Certification Boundary: geometry suggests where to
look, arithmetic certifies the result.

### Algorithm Outline

1. Input: a target integer \(N\) (default `137524771864208156028430259349934309717`). The service assumes no prior
   knowledge of its factors.
2. Deterministic parameters: derive a `SplittableRandom` seed from \(N\) so runs are reproducible; set numeric precision
   to exceed `N.bitLength()` to avoid score drift.
3. Band construction: compute \(a = \lfloor\sqrt{N}\rfloor\). Probe integer offsets \(k\) in a symmetric
   window \([-W, W]\) (the band). Skip even \(d = a + k\) to remain on odd candidates.
4. Geometric scoring: map each offset to a candidate divisor \(d\) and evaluate a resonance score \(S_N(d)\) using
   high-precision `BigDecimal` arithmetic. A zero remainder shortcut handles the exact hit case; otherwise scores are
   normalized to compare uneven magnitudes.
5. Ranking and pruning: normalize scores (\(z\)-normalize) and keep the best unique candidates keyed by their deviation
   \(|d - a|\) to avoid redundant checks.
6. Certification: submit only the top-ranked divisors to the predicate `N mod d` until a factor is found or limits are
   reached. Execution is bounded by configured `maxIterations` and `timeLimitMillis` to preserve determinism.

### Interfaces

- `POST /api/factor` with `{ n?, maxIterations?, timeLimitMillis?, logEvery? }` starts a run and returns
  `{ jobId, status }`.
- `GET /api/status/{jobId}` reports progress and any discovered factors.
- `GET /api/logs/{jobId}` streams the structured log (Server-Sent Events), replaying past lines on reconnect.

### Logging and Reproducibility

- Every job logs \(N\), precision, band width, step size, random seed, and the count of geometric probes vs arithmetic
  checks.
- SSE logging ensures the full certificate is viewable without rerunning geometry: each checked candidate emits its
  score and `N mod d` outcome.
- Deterministic seeding guarantees identical candidate order for the same input, enabling peer review of geometric
  ranking quality.

### Constraints and Non-goals

- The system purposely avoids wide classical sweeps (Pollard Rho, ECM, etc.). Any factor discovery is attributable to
  the geometric ranking’s ability to reduce the candidate set, not to fallback algorithms.
- The band around \(\sqrt{N}\) is narrow by design; extending it or replacing the scorer is the primary avenue for
  experimentation.

### Operations Checklist

- Build/run: `./gradlew -p experiments/blind-geofac-web bootRun`
- Default challenge: 127-bit semiprime noted above; factors are **not** embedded in the code or config.
- Resource use: CPU-bound scoring with bounded thread pools; graceful shutdown closes executors after each job.
