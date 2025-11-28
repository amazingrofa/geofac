Goal

- Keep the blind-geofac web app functionally aligned with the main repo’s geometric resonance engine (Dirichlet kernel +
  Sobol QMC + adaptive precision), proving factors without shortcuts.
- Use local JDK 21 at /opt/homebrew/opt/openjdk@21 for builds/tests.

Done so far

- Replaced heuristic scorer with the real geometric engine (FactorizerService) and shared math utilities (
  DirichletKernel, SnapKernel, PrecisionUtil, ScaleAdaptiveParams, ShellExclusionFilter).
- Added big-math and commons-math3 deps; wired Spring config defaults to mirror main repo settings.
- Updated FactorService to delegate to the engine and stream logs; kept async job handling.
- Added smoke test on a Gate-4 composite and a full-budget 127-bit benchmark integration test that fails on no factor.
- Ensured builds use JDK 21 toolchain (set JAVA_HOME=/opt/homebrew/opt/openjdk@21 for Gradle runs).

Remaining tasks

- Run the 127-bit benchmark (`FactorServiceChallengeIT`) end-to-end; success = factor found within 30 minutes. Capture
  streaming console/SSE logs; adjust threshold/samples/m-span/k-range/timeouts as needed to hit the target.
- Add a flag to gate the long challenge IT so default test runs stay fast, while preserving assertions when enabled.
- Surface current engine config/status via REST and README notes so operators know active parameters and safe overrides
  (no new CI tasks yet).
- Review SSE/log streaming for long runs; ensure periodic, meaningful output and guard against backpressure/memory
  buildup
  (your call on the approach).
- Optional: add micro-tests for PrecisionUtil.principalAngle and DirichletKernel singularity guard; add diagnostics
  toggle
  handling tests if runtime fits within the 30-minute budget.
