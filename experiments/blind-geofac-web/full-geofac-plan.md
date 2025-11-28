# Plan to Implement Full GeoFac in the Blind Geofac Web App

This document outlines a step-by-step plan to evolve the current \"blind\" prototype into a Full GeoFac implementation. The focus is on the **simplest correct version**: Using z-normalization to map N to a 2D torus (phase space), generating candidates via resonance probes (geodesic-like orbits), and scoring with modular resonance. This replaces heuristic bands with true geometric exploration, ensuring the true factor p ranks high (e.g., top 10-20 candidates for verification). 

The plan is incremental, testable, and leverages existing code (e.g., FactorService, BigIntMath). Estimated time: 1 day for MVP. Changes: ~200-300 LOC, primarily in FactorService + utils. Test on 127-bit demo N, scaling to 256-bit. Tools: Edit/Write for code, Bash for build/test.

## Key Concepts (From GeoFac Issue #141)
- **Geometric Space (X)**: 2D torus S¹×S¹ for phases (θ_p, θ_q ≈ 0.5 for balanced semiprimes).
- **Mapping Φ**: Phase θ → d = √N + offset(θ) (candidate divisor near √N).
- **Scoring S_N**: Resonance = 1 - (N mod d / d) * geometric bonus (phase alignment |sin(Δθ)|).
- **Flow**: Explore orbits → Generate/rank k=1000 candidates → Verify top m=20 with N mod d == 0.
- **Success Metric**: E[rank(p)] < 50; total time << blind trial division.

## Phase 1: Define & Stub Core Components (Prep – 1-2 hours)
**Goal**: Implement z-normalization, resonance scoring, and probe stubs. No full integration yet.

1. **Add Utils to BigIntMath.java** (Edit existing file):
   - `double[] zNormalize(BigInteger n, BigInteger sqrtN)`: Deterministic phases via `θ = frac(ln(n)/ln(sqrtN))`, `θ_q = frac(θ + 0.5)`, using double logs (upgrade to BigDecimal later).
   - `double resonanceScore(BigInteger n, BigInteger d)`: `1.0 - (n.mod(d).doubleValue() / d.doubleValue())` + 0.1 if d probable prime (use `d.isProbablePrime(10)`).
   - `List<Candidate> generateResonanceProbes(BigInteger n, int numProbes, int orbitSteps)`: Stub – random θ, simple orbit, map to d, score.

2. **New Model: Candidate.java** (Write new file: src/main/java/com/geofac/blind/model/Candidate.java):
   ```java
   package com.geofac.blind.model;
   import java.math.BigInteger;
   public record Candidate(BigInteger d, double score, String source) {}
   ```

3. **Test Stub** (Bash: Add to FactorService.main or new test class):
   - Generate 100 probes for DEFAULT_N, log top-10. Run `gradle build` to verify.

**Why Simple/Full?**: Covers Φ, S_N, basic exploration—core GeoFac without complexity.

## Phase 2: Integrate into FactorService – Geometric Exploration & Ranking (Core – 4-6 hours)
**Goal**: Replace `scoreBands` (heuristic bands) with GeoFac probes; update verification to point-wise checks on top candidates.

1. **Edit FactorService.java**:
   - Update `scoreBands(BigInteger n, int maxIter)` → `List<Candidate> scoreBands(...)`:
     ```java
     private List<Candidate> scoreBands(BigInteger n, int maxIter) {
         BigInteger sqrtN = BigIntMath.sqrtFloor(n);
         double[] basePhases = BigIntMath.zNormalize(n, sqrtN);  // Approx {θ_p, θ_q}
         List<Candidate> candidates = new ArrayList<>();
         long seed = 42L;  // Fixed, reproducible
         SplittableRandom rnd = new SplittableRandom(seed);
         int numProbes = Math.min(1000, maxIter / 10);
         for (int i = 0; i < numProbes; i++) {
             double θx = rnd.nextDouble(0, 2 * Math.PI);
             double θy = rnd.nextDouble(0, 2 * Math.PI);
             for (int t = 0; t < 50; t++) {  // Orbit: Ergodic flow
                 θx = (θx + Math.sqrt(2) * (t + 1)) % (2 * Math.PI);  // Irrational rotation
                 θy = (θy + Math.PI * (t + 1)) % (2 * Math.PI);
                 // Φ: Phase to offset
                long offset = Math.round((θx - Math.PI) * 1e6 / Math.PI);  // Scale width=2e6
                BigInteger d = sqrtN.add(BigInteger.valueOf(offset)).max(BigInteger.TWO).min(n.subtract(BigInteger.ONE));
                if (d.compareTo(BigInteger.valueOf(2)) > 0 && d.testBit(0)) {  // Skip evens
                     double resScore = BigIntMath.resonanceScore(n, d);
                     double geoBonus = 1 - Math.abs(Math.sin(θx - basePhases[0]));  // Align to θ_p
                     double score = resScore * (0.7 + 0.3 * geoBonus);
                     candidates.add(new Candidate(d, score, "orbit-" + i + "-t" + t));
                 }
             }
         }
         return candidates.stream()
                 .sorted(Comparator.comparingDouble(Candidate::score).reversed())
                 .limit(20)
                 .toList();  // Top m=20
     }
     ```
   - Update `runBlindGeofac`: After scoring, loop over topCandidates (not bands):
     ```java
     List<Candidate> top = scoreBands(n, maxIter);
     log(job, "Generated " + top.size() + " top candidates via GeoFac resonance.");
     int checked = 0;
     for (Candidate cand : top) {
         if (Duration.between(start, Instant.now()).toMillis() > timeLimit) {
             job.markFailed("Time limit in verification");
             return;
         }
         if (checked >= maxIter) return;  // Budget
         if (n.mod(cand.d()).equals(BigInteger.ZERO)) {
             BigInteger q = n.divide(cand.d());
             job.markCompleted(cand.d(), q);
             log(job, "Factor found at rank " + (checked + 1) + ": p=" + cand.d() + " q=" + q + " (score=" + cand.score() + ")");
             return;
         }
         checked++;
         if (checked % logEvery == 0) log(job, "Checked rank " + checked + ": d=" + cand.d() + " score=" + cand.score());
     }
     job.markFailed("No factor in top candidates");
     ```
   - Remove `scanBand` and `Band` references; fallback to old heuristics if <5 candidates.

2. **Add to FactorRequest**: Fields like `int numProbes` (default 1000), `int orbitSteps` (50) with orDefault().

3. **Logging Enhancements**: Add "Phase alignment: Δθ=" + Δθ, "Resonance score: " + resScore.

**Why Simple/Full?**: Torus orbits simulate geodesics; z-norm + resonance = S_N. Generates k=1000 cheaply, verifies m=20—proves space reduction.

## Phase 3: UI/API Updates & Verification (Integration – 2-3 hours)
**Goal**: Expose GeoFac details in API/UI; test correctness.

1. **Edit FactorController.java**: Status JSON include \"topCandidates\": List of {d, score} for top 5 (truncate strings).
2. **Edit index.html (JS)**: In pollStatus, if completed, log \"Found at rank X (score Y)\". Add section to display top probes table (e.g., via innerHTML).
3. **Testing**:
   - **Unit (Add src/test/java/.../FactorServiceTest.java)**: JUnit for zNormalize/resonanceScore (e.g., N=15, assert high score for d=3/5).
   - **Integration**: `gradle bootRun`; UI test default N (expect rank<10, <1s). Bash script: Generate 10 random 100-bit semiprimes (p=BigInteger.probablePrime(50,rnd), q=p.nextProbablePrime(), N=p*q), avg rank(p).
   - **Metrics**: Log E[rank(p)] over runs; aim <50. Edge: Prime N (fail gracefully), bitLength>512 (cap).
   - **Build/Run**: `gradle clean build && java -jar build/libs/blind-geofac-web-0.0.1-SNAPSHOT.jar`; curl /api/factor.

## Phase 4: Optimization & Extensions (Polish – 3-5 hours, Post-MVP)
- **Perf**: Parallelize probes (use executor). Cache phases. For larger N, increase probes to 10k, m=50.
- **Enhance GeoFac**: 3D torus (add θ_z), integrate LLL (via lib) for lattice candidates. ML: Train simple regressor on phase-score correlations.
- **Config**: application.yml for params (numProbes=1000).
- **Docs**: Update README.md with math refs (link #141), add /api/debug/{jobId} for full candidates.
- **Scale Test**: 256-bit N; measure speedup vs. blind (expect 10-100x faster due to m<<√N).

## Risks & Rollback
- **Precision Loss**: BigDecimal for logs; test on small N first.
- **Fallback**: If GeoFac rank poor, hybrid: Mix with Rho bands.
- **Deps**: No new libs (use java.math); if needed, add to build.gradle (e.g., for advanced logs).

This MVP delivers full GeoFac core: Geometric prior reduces search to tiny m, with trial division as oracle. Proceed phase-by-phase; confirm after Phase 1.
