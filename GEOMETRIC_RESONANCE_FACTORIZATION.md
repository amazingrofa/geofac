# Geofac Geometric Resonance Factorization Design

Timestamp: 2025-11-21T07:56:22.695Z

## 1. Purpose
Implement factor discovery for large integers N using only geometric resonance (Z5D-style manifold navigation) without Pollard Rho / ECM / QS / NFS. Leverage the scale-invariant prediction principles proven in `z5d-prime-predictor` while restricting operations to deterministic integer arithmetic + resonance scoring.

## 2. Foundational Insight (from Z5D work)
Precision decoupling: Floating MPFR precision (e.g. 2048 bits) is needed only to seed an approximate geodesic center. Integer operations (candidate generation, divisibility tests) use arbitrary-precision GMP (`mpz_t`). Average structural features (prime gaps, local curvature of log/log surfaces) remain small relative to adaptive windows, enabling fixed-precision prediction at extreme scales.

References:
- Prime center scan: `src/c/z5d-mersenne/z5d_mersenne.c`
- Prediction math / Riemann R inversion: `src/c/z5d-predictor-c/src/z5d_predictor.c`, `src/c/z5d-predictor-c/src/z5d_math.c`
- Header API: `src/c/z5d-predictor-c/include/z5d_predictor.h`
- Wave-knob adaptation logic (window, step, ratio R): `z5d_mersenne.c` auto_tune_scan()
- Benchmark scripts & CSV format: `benchmarks/z5d-mersenne/z5d-mersenne_smoke_test.sh`
- Primality verification pattern: `benchmarks/z5d-mersenne/verify_primes.py`
- README precision explanation: `README.md` (added note on precision vs huge k)

## 3. Conceptual Geometry
Treat factoring as searching for a factor f such that f divides N. We model candidate factor space around sqrt(N) as a 1D projection of a 5D manifold (Z5D + density corrections). Resonance valleys correspond to regions where a mapped curvature/density score S(f; N) peaks. Window/step define an aperture exploring these valleys.

## 4. Mathematical Components
- Let L = ln(N), L2 = ln(ln(N)).
- Define baseline center C0 = sqrt(N).
- Apply geodesic shift: C = C0 + g(L, L2) where g mimics predictor correction (use Dusart-like expansion restricted to factor domain).
- Resonance score S(f): combine (i) deviation from center |f - C| scaled by window, (ii) local smoothness proxy: small remainder r = N mod f implies higher pre-resonance, (iii) wheel residue alignment (mod primorial P = 210 or 2310) encouraging coprimality with small primes, (iv) optional density booster analogous to Stadlmann term.
- Adaptive ratio R = window / step maintained near target R* for efficient valley capture.

## 5. Data Structures
```
typedef struct {
    mpfr_prec_t precision;      // floating mantle for logs
    unsigned long window_start; // initial window
    unsigned long step_start;   // initial step
    unsigned long max_iters;    // tuning iterations
    unsigned long wheel_mod;    // 30 / 210 / 2310
    unsigned int target_hits;   // target near-factor hits before narrowing (e.g. 1)
    int verbose;
} gf_config_t;

typedef struct {
    mpz_t N;            // input composite
    mpz_t factor_found; // factor > 1 if found
    unsigned long window_final;
    unsigned long step_final;
    double ratio_final;
    unsigned long iterations;
    unsigned long candidates_tested;
    unsigned long divisibility_tests;
    double elapsed_ms;
    int locked;         // 1 if factor found
    char wheel_label[32];
} gf_result_t;
```
Wheel offsets reuse arrays from `z5d_mersenne.c`.

## 6. Algorithm Phases
1. Initialize config and MPFR precision (e.g. 2048 bits).
2. Compute logs of N (mpfr) and derive center C (MPFR) → convert to mpz (rounded).
3. Align C to nearest wheel residue (mod wheel_mod).
4. Auto-tune loop (similar to auto_tune_scan):
   - Generate candidates: for offset k = 0..window with stride step, forward/backward: f = C ± k * wheel_mod.
   - Quick filter: ensure 2 < f < N.
   - Divisibility test: mpz_divisible_p(N, f). If true: record factor, set locked.
   - Resonance heuristic: if remainder r = N mod f is small (e.g. < f / window), treat as near-hit; accumulate near_hits.
   - Adjust window/step:
     * If no near_hits: increase window (grow by 1.5x) or decrease step.
     * If too many near_hits: shrink window or increase step.
     * If near_hits == target_hits and still no exact factor: narrow window (×2/3) to intensify local search.
5. Terminate when factor found or max_iters reached.
6. If factor found and N/f still composite: Optionally recurse with updated N ← N/f.

## 7. Adaptation Rules (Initial Heuristics)
- No hits: `window = min(window * 3 / 2, WINDOW_CAP)`.
- Many hits (> target_hits): `window = max(window * 2 / 3, WINDOW_MIN)` or `step++`.
- Near convergence (near_hits == target_hits with rising density): decrease step if step > 1.
Maintain `ratio = window / step` within a band [R_min, R_max]; log adjustments.

## 8. Divisibility & Validation
Strictly use `mpz_divisible_p`. Upon factor detection, verify by division and multiplication back: (N / f) * f == N. Optionally perform a GCD fallback: g = gcd(f, N) to confirm primal factor; if g != f, treat g as factor and re-run.

## 9. Files to Add in geofac Project
```
geofac/
  include/geofac.h              # public API (gf_config_t, gf_result_t, gf_factor_resonance)
  src/geofac_core.c             # main factoring loop
  src/geofac_resonance.c        # resonance scoring S(f)
  src/geofac_resonance.h        # internal resonance prototypes
  src/geofac_math.c             # log-based center & adjustment g(L, L2)
  src/geofac_math.h             # math helpers
  src/geofac_cli.c              # CLI similar to z5d_mersenne
  benchmarks/geofac_smoke_test.sh  # CSV+MD output like z5d-mersenne
  benchmarks/verify_factors.py  # analogous to verify_primes.py
  Makefile                      # link against MPFR/GMP
```
Reuse wheel offset arrays by copying from `src/c/z5d-mersenne/z5d_mersenne.c` or placing in a shared header.

## 10. Function Prototypes (Draft)
```
void gf_init(void);
void gf_cleanup(void);
void gf_config_init(gf_config_t*);
void gf_result_init(gf_result_t*, mpfr_prec_t);
int  gf_factor_resonance(gf_result_t*, const mpz_t N, const gf_config_t*);
static int gf_auto_tune(const mpz_t N, mpz_t center, gf_config_t*, gf_result_t*); // internal
static void gf_align_center(mpz_t center, unsigned long wheel_mod);
static int gf_scan_candidates(const mpz_t N, const mpz_t center,
                              unsigned long window, unsigned long step,
                              unsigned long wheel_mod, mpz_t* found);
```

## 11. CLI Behavior (geofac_cli)
```
Usage: geofac <N> [--prec=2048] [--window=64] [--step=2] [--wheel=210] [--max-iters=500] [--json] [--verbose]
Output: factor_found (if any), window/step evolution, candidates_tested, iterations, elapsed_ms.
```
JSON schema parallels `output_json_result` in `z5d_mersenne.c` but replaces `prime_found` with `factor_found` and adds `remaining_cofactor` if factor found.

## 12. Benchmark & Verification
- Smoke script pattern: model after `benchmarks/z5d-mersenne/z5d-mersenne_smoke_test.sh` capturing CSV with columns: tool, precision_bits, window_final, step_final, ratio_final, iterations, candidates_tested, factor_found, elapsed_ms.
- Verification script: For each factor_found, assert mpz_divisible and produce PASS/FAIL rows.

## 13. Implementation Plan (Ordered Steps)
1. Create headers (`geofac.h`, `geofac_resonance.h`, `geofac_math.h`).
2. Port wheel offsets & basic alignment code.
3. Implement math center (logs + correction) in `geofac_math.c`.
4. Implement resonance scoring stub returning remainder magnitude class.
5. Implement candidate scan (`gf_scan_candidates`).
6. Implement auto-tune (`gf_auto_tune`) using adaptation rules.
7. Implement public factoring function wrapping setup, loop, result assignment.
8. Add CLI (`geofac_cli.c`) with JSON/human output.
9. Add Makefile (link MPFR/GMP like `src/c/z5d-mersenne/Makefile`).
10. Add smoke benchmark & verify scripts.
11. Test on 127-bit challenge number; iterate scoring function for better window stability.
12. Document tuning knobs in README extension.

## 14. Resonance Scoring Extensions (Future)
- Incorporate second-order curvature of log surfaces: use MPFR to compute f-dependent adjustment term.
- Multi-center approach: generate a small lattice of centers C_i around sqrt(N) and interleave scans.
- Adaptive primorial expansion: escalate wheel_mod from 210 → 2310 if no near_hits in early iterations.

## 15. Non-Goals
- No classical probabilistic factor methods (Pollard, ECM, QS, NFS).
- No use of advanced algebraic number theory beyond log-based density correction.

## 16. Risk & Mitigations
| Risk | Mitigation |
|------|------------|
| Center drift too large for tough N | Increase window growth multiplier early; log drift stats; refine g(L,L2). |
| Excess candidate explosion | Cap window; increase step to preserve R within bounds. |
| False near_hits (small remainders random) | Refine resonance score combining remainder ratio & local derivative of S(f). |
| Long runtimes on semi-primes with large close factors | Introduce multi-center lattice or dynamic wheel modulus. |

## 17. Validation Metrics
- Factor found? Y/N within max_iters.
- Candidates tested vs theoretical average gap * multiplier.
- Elapsed_ms scaling vs bit-length of N.
- Stability of ratio_final across different composites.

## 18. Deliverables for Implementation LLM
Provide this file plus referenced source paths so it can copy structural patterns:
- `/Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-mersenne/z5d_mersenne.c`
- `/Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-predictor-c/include/z5d_predictor.h`
- `/Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-predictor-c/src/z5d_predictor.c`
- `/Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-predictor-c/src/z5d_math.c`
- `/Users/velocityworks/IdeaProjects/z5d-prime-predictor/benchmarks/z5d-mersenne/z5d-mersenne_smoke_test.sh`
- `/Users/velocityworks/IdeaProjects/z5d-prime-predictor/benchmarks/z5d-mersenne/verify_primes.py`
- `/Users/velocityworks/IdeaProjects/z5d-prime-predictor/README.md`

LLM should generate geofac code mirroring predictor + scanner patterns but replacing primality with resonance-based divisibility checks.

## 19. Summary
Geofac will adapt the scale-invariant geodesic prediction + wave-knob auto-tuning paradigm to factor discovery by scanning resonant factor neighborhoods around sqrt(N). Fixed MPFR precision suffices; resonance scoring and adaptive windows drive efficient integer-only exploration.

---
End of design.
