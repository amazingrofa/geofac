Goal

- Keep the blind-geofac web app functionally aligned with the main repo’s geometric resonance engine (Dirichlet kernel +
  Sobol QMC + adaptive precision), proving factors without shortcuts.

Done so far

- Replaced heuristic scorer with the real geometric engine (FactorizerService) and shared math utilities (
  DirichletKernel, SnapKernel, PrecisionUtil, ScaleAdaptiveParams, ShellExclusionFilter).
- Added big-math and commons-math3 deps; wired Spring config defaults to mirror main repo settings.
- Updated FactorService to delegate to the engine and stream logs; kept async job handling.
- Added smoke test on a Gate-4 composite and a full-budget 127-bit benchmark integration test that fails on no factor.
- Ensured builds use JDK 21 toolchain (set JAVA_HOME=/opt/homebrew/opt/openjdk@21 for Gradle runs).

Remaining tasks

- Run the long benchmark test (`FactorServiceChallengeIT`) end-to-end and capture logs/artifacts; tune parameters only
  if it fails (threshold, samples, m-span, k-range).
- Decide on gating the long challenge IT behind a flag to keep default test runs fast (e.g., system property) while
  preserving its assertions when enabled.
- Surface engine configuration/status in the REST API/README so operators know which parameters are in effect and how to
  override safely.
- Review SSE/log streaming under long runs to ensure no backpressure or memory issues; cap history or stream window if
  needed.
- Optional: add lightweight unit tests around PrecisionUtil.principalAngle and DirichletKernel edge cases (singularity
  guard) to catch regressions without extending runtime.
- Optional: consider exposing diagnostics toggle in request payload, defaulting off, to match main repo’s diagnostic
  behavior.
