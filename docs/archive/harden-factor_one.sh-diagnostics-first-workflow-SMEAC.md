# Harden factor_one.sh & Diagnostics-First Workflow (SMEAC Brief)

Issue Reference: #29  
Branch: factor-one-shell-script  
Timestamp: 2025-11-14T02:56:15.285Z  
Target N (Gate 1 whitelist, 127-bit): 137524771864208156028430259349934309717  
Fast-path: DISABLED  
Classical fallbacks (Pollard Rho, trial division, ECM, sieves): FORBIDDEN

---
## S (Situation → Context & Problem)
The geometric resonance factorizer (Dirichlet-kernel search) fails one-shot factorization of the 127‑bit Gate 1 challenge. Hardened script now produces per‑run artifacts but still times out: high amplitude peaks, snap heuristic projects invalid p0 (0 or >> N), no divisibility lock. Need deterministic, diagnostic expansion—no stochastic retries, no classical fallbacks.

Signals observed:
- Precision chosen: 708 (rule: max(configured, bitlen*4 + 200)).
- Runtime ≈ 90s (timeout 90s) with only 141 samples processed of 7500 planned.
- Amplitude distribution healthy (mean ≈ 0.127; max = 1.0) yet candidate rejection dominated by snap projection failures.

## M (Mission → Objective)
Produce a SUCCESS run where p and q are discovered (p*q = N) by geometric resonance only. Deliver machine‑parseable factorization.json + candidate telemetry enabling exact reruns and snap heuristic refinement. Reduce invalid p0 events (0 / overflow) to a negligible fraction.

Success Criteria:
1. factor_one.sh yields status SUCCESS (no fast-path) and writes p.txt, q.txt matching N.
2. Java diagnostics logging provides amplitude distribution stats and candidate evaluation logs when enable-diagnostics=true.
3. Snap misfires (invalid p0 values) are logged and can be analyzed from stdout diagnostics.
4. All parameters are logged by Java service and captured in run.log.

## E (Execution → Plan & Tasks)
Ordered, surgical tasks—stop once SUCCESS artifacts produced.

1. Harden factor_one.sh to improve diagnostics and artifact generation:
   - Ensure per-run artifacts (run.log, factorization.json) are written reliably.
   - Echo all relevant parameters (precision, samples, m-span, J, threshold, k-lo, k-hi, timeout, bitLength, adaptiveFormula) to logs and artifacts.
   - Enforce deterministic sampling and parameter selection; log seeds and configuration.
   - Add guard clauses to prevent classical fallback methods and probabilistic retries.
   - Optionally stage two runs (high specificity then recall) into same OUT_DIR when first fails.
2. Parameter sweep (deterministic shells; do NOT randomize):
   - Plan 1 (specificity): precision=640; samples=2000; m-span=128; J=6; threshold=0.92; k-lo/hi=0.28/0.42; timeout=30s.
   - Plan 2 (recall): precision=640–708; samples=5000; m-span=160; J=7; threshold=0.88; k-lo/hi=0.25/0.45; timeout=60s.
   - Plan 3 (verification): precision=708; samples=7500; m-span=200; J=8; threshold=0.86; k-lo/hi=0.20/0.50; timeout=90s.
   Abort early if SUCCESS; archive each run's JSON for comparison.

Guard Clauses / Constraints:
- Do not introduce probabilistic loops; all sampling sequences should be deterministic (Sobol/Halton acceptable if seed fixed and logged).
- Do not widen scope beyond Gate 1 until SUCCESS achieved.
- No fallback factoring methods; if you find yourself writing modular exponentiation for primality test, STOP.

Rollback / Abort: If changes increase timeout frequency before sample loop starts (<10 samples processed), revert snap modifications and reassess m-span/J pair.

## A&L (Administration & Logistics → Artifacts & Repro)
Artifacts per run (under results/single_run_<RUN_ID>):
- run.log (stdout/stderr with Java diagnostics logging)
- p.txt, q.txt on SUCCESS

Logging Requirements:
- Timestamps (UTC ISO-8601) for: start, precision decision, each diagnostics flush, completion.
- Precision formula logged: configured X vs required (bitlen*4+200) Y -> chosen Z.
- Counts: samplesPlanned vs samplesProcessed; candidateAccept vs candidateReject by failClass.

Repro Command:
```
./gradlew clean build -x test && ./scripts/factor_one.sh
```

Validation Gate Reminder:
- Allowed range: [1e14, 1e18] or Gate 1 whitelist (current N). Do not test tiny semiprimes.

## C&S (Command & Signal → Coordination & Interfaces)
Coordination Channels:
- Primary tracking: Issue #29.
- This PR discussion thread: implementation diffs, progress notes.

For LLM Contributors (No prior project knowledge assumed):
- Read CODING_STYLE.md for invariants (minimal diff, deterministic methods, adaptive precision rule).
- Edit only necessary classes: FactorizerService (snap), diagnostics emitter, precision echo.
- After each diff: run factor_one.sh once; attach factorization.json excerpt (first 5 candidates, summary stats) to comment.
- If SUCCESS achieved: post p, q, confirm p*q=N, attach params.json & amplitude stats.

Interface Expectations:
- New classes must have clear, linear methods (no hidden state). Prefer static helpers or small immutable records.
- Public method names should be plain language (e.g., emitDiagnostics(), projectSnapQuorum()).

Failure Classification (add enum if absent): ZERO, OVERFLOW, INCOHERENT, NOT_DIVISIBLE, TIMEOUT.

Escalation:
- If snap still yields >20% OVERFLOW after quorum, propose parameter tweak referencing amplitudeStats.
- If samplesProcessed << samplesPlanned (e.g., <5%), investigate early termination guard or blocking call around diagnostics emission.

---
### Definition of Done (Reaffirmed)
A deterministic one-shot run (no classical fallbacks) returns SUCCESS with valid p,q and complete diagnostic artifacts enabling independent reproduction and snap analysis. Shell script hardened with improved diagnostics, artifact generation, and parameter logging. All changes confined to shell script improvements and documentation; Java implementation changes deferred to future PR.

### Post-SUCCESS Next Step (Out of Scope Here)
Only after SUCCESS: evaluate scaling approach for Gate 2 (within [1e14,1e18]) using same deterministic harness. Not part of this PR.

---
### Quick Checklist for Reviewers
- [ ] factor_one.sh hardened with improved diagnostics and artifact generation
- [ ] Java diagnostics logging enabled and captured in run.log
- [ ] precision log matches rule
- [ ] No classical factoring code introduced
- [ ] Snap quorum logic deterministic & documented *(N/A for this PR: shell script & docs only)*
- [ ] JSON diagnostics schema *(N/A: not implemented in this PR)*
- [ ] Issue #29 referenced in commit messages

---
Prepared: 2025-11-14T02:56:15.285Z
