# AGENTS

Mission control document for `geofac-137524771864208156028430259349934309717`.

This repo has **one goal**: use geometric ranking + minimal arithmetic certification to factor

> `N = 137524771864208156028430259349934309717`  (127-bit semiprime, “CHALLENGE_127”).

All agents, tools, and experiments exist only to improve the probability that **the true factor(s)** of this N appear low in the geometric ranking, and are confirmed by `N mod d == 0` (or `gcd(N, d)`).

Baseline: the current Python prototype (`geofac_local_global.py`) generates 50 000 candidates in a narrow band `isqrt(N) ± 10_000_000`, ranks by a Dirichlet-kernel resonance score, and certifies only the top‑500. For this N, that run produces **no factors**; all 500 top‑ranked candidates are near `sqrt(N)` and `is_factor = false`.

---

## 0. Global rules & constraints

These apply to **every agent**.

### 0.1 Non‑negotiables (carried over from main Geofac)

* **Geometry ranks, arithmetic certifies**

    * Geometric / analytic phase proposes and **orders** candidates.
    * Arithmetic phase uses only:

        * `IsFactor_N(d) := (N mod d == 0)` and/or
        * `gcd(N, d)` as a shortcut.
    * Every reported factor must appear in logs with a clear `N mod d` / `gcd(N, d)` certificate.

* **No wide classical fallbacks**

    * Out of scope **for the factoring pipeline**:

        * Pollard Rho, Pollard p−1, ECM, quadratic sieve, NFS.
        * Bulk trial division beyond the geometrically ranked set.
    * You may use classical methods **only** as a *ground‑truth oracle* in offline analysis (e.g., to evaluate ranking quality or confirm factors), never as part of the production factoring path.

* **Determinism & reproducibility**

    * Seeds derive deterministically from N (e.g., `seed = SHA256(N)[0..63 bits]`).
    * All precision, sampling, and thresholds must be logged and reproducible.
    * Every “successful” run must be replayable from its artifact bundle alone.

* **Geometric certification boundary**

    * Geometry suggests *where* to look and in *what order*.
    * Certification only runs on the top `m` ranked candidates `d₁…dₘ`.
    * Artifacts must log:

        * All certified candidates.
        * Their geometric scores.
        * Rank of any factor.
        * Predicate outcomes (`is_factor`, `gcd`, etc.).

### 0.2 Single‑target focus

* There is **exactly one N** in scope:

    * All configuration, theory, and tuning is allowed to specialize to this N.
    * But **no injection of its known factors** into any geometric heuristic or candidate generator (e.g., no “seed with p and q”, no “bias window around p”).

* You may:

    * Specialize **scaling laws** to the bit‑length and structure of this N.
    * Use logs and artifacts from the main `zfifteen/geofac` repo to inform priors.

* You may not:

    * Hard‑code `p` or `q` inside geometric or sampling logic.
    * Use any function that returns factors of N as part of the production pipeline.

---

## 1. Agent roster (high‑level)

1. **Orchestrator & Governance Agent (`ORCH`)** – owns mission, backlog, guardrails.
2. **Challenge Steward Agent (`N-STEW`)** – maintains canonical representation of N and all dependent config.
3. **Geometry & Kernel Design Agent (`GEOM`)** – designs / refines resonance and kernel‑based scoring.
4. **Sampling & Topology Agent (`SAMPLE`)** – designs candidate generators, windows, and p‑adic topology.
5. **Scale‑Adaptive Tuning Agent (`SCALE`)** – encodes and tests empirical scaling laws specifically for this N.
6. **Implementation & Refactor Agent (`IMPL`)** – keeps Python/Java implementations coherent, fast, and faithful to theory.
7. **Experiment & Metrics Agent (`XP`)** – runs experiments, collects metrics, and compares configurations.
8. **Verification & Proof Agent (`CERT`)** – ensures every “success” has a replayable, logged certificate and proof pack.
9. **Falsification & Red‑Team Agent (`RED`)** – actively tries to break assumptions and detect cheating (e.g., latent use of p, q, hidden classical sweeps).

Each agent is virtual; the same person or LLM can play multiple roles, but the **interfaces and responsibilities must stay separate**.

---

## 2. ORCH – Orchestrator & Governance

**Purpose:** Keep the entire multi‑agent system aligned on “factor this N by geometric ranking + arithmetic certification only”.

**Responsibilities**

* Maintain the canonical **mission statement** and this AGENTS file.
* Hold a single prioritized **backlog**:

    * Theoretical hypotheses (e.g., new kernels, p‑adic structures).
    * Sampling/tuning directions.
    * Implementation tasks.
    * Logging / proof packaging tasks.
* Approve / reject proposals that violate non‑negotiables (e.g., “let’s just run ECM”).

**Inputs**

* PRs, issues, and design notes from all other agents.
* Logs and metrics produced by `XP` and `CERT`.

**Outputs**

* Updated `AGENTS.md`, ROADMAP, and high‑level design docs.
* Clear labels on issues/PRs: `geometry`, `sampling`, `scale`, `impl`, `xp`, `cert`, `red`.

**Guardrails**

* Reject any change that:

    * Treats factors as known inputs to geometry/sampling.
    * Adds classical fallback as a default path.
* Ensure **one source of truth** for N and seeds across the repo.

---

## 3. N-STEW – Challenge Steward

**Purpose:** Maintain the canonical definition of N, its derived constants, and all N‑dependent config.

**Responsibilities**

* Define and maintain:

    * `N` in a single config file (e.g., `config/challenge.json` or `ChallengeN.java`).
    * Bit‑length, approximate `sqrt(N)`, and any derived constants (for logging only).
* Ensure every experiment, script, and service:

    * Reads N from the canonical source.
    * Logs N explicitly in artifacts.

**Inputs**

* Main geofac docs and Java definitions of `CHALLENGE_127`.
* Existing baseline logs (e.g., `geofac_local_global` JSON run).

**Outputs**

* `config/challenge.json` (or similar) with:

    * `N`,
    * `bit_length`,
    * optional `sqrtN` (approx),
    * deterministic seed spec.

**Guardrails**

* No factor info (`p`, `q`) in `N` config.
* Any changes to N must be treated as a **breaking change** and reviewed by `ORCH` + `CERT`.

---

## 4. GEOM – Geometry & Kernel Design

**Purpose:** Design and refine the **geometric scoring** that ranks candidate divisors.

**Responsibilities**

* Maintain the core resonance score:

    * Currently Dirichlet kernel on `x = 2π * (N mod d)/d`, e.g.
      `score(d) = |D_j(x)|`, with `D_j(x) = 1 + 2 Σ cos(kx)`.
* Explore kernel variants:

    * Normalized Dirichlet (divide by `2j+1`) vs raw amplitude.
    * Different `j` regimes (e.g., low j vs high j) and composite kernels.
    * Multi‑frequency combinations, windowed sums, or smoothed kernels.
* Analyze:

    * Score distribution for random `d` vs structure near divisors.
    * Sensitivity to floating‑point precision vs decimal (BigDecimal) precision.
* Propose **scale‑adapted** kernels tuned for the bit‑length and structure of this N.

**Inputs**

* N from `N-STEW`.
* Candidate lists from `SAMPLE`.
* Logs of `(d, score, is_factor)` from `XP` / `CERT`.

**Outputs**

* Formal definition of the scoring functions in `docs/geometry/` (e.g., `KERNELS.md`).
* Reference implementations (Python and Java) for:

    * `dirichlet_kernel(x, j)`
    * `resonance_score(N, d, params)`
* Suggested default kernel parameters for the challenge:

    * `j`, number of passes, any normalizations.

**Guardrails**

* Scoring must be **computable from N and d alone**, without hidden access to factors.
* No ad‑hoc “cheat features” like “if d ≈ known factor, add large bias”.

---

## 5. SAMPLE – Sampling & Topology

**Purpose:** Design how candidate divisors `d` are generated before scoring, including p‑adic filters and search geometry.

**Responsibilities**

* Maintain and evolve the **candidate generator**:

    * Current baseline: uniform `offset ∈ [-window, window]` around `sqrt(N)`.
    * Ensure generated `d` are unique, in `(1, N)`, and pass the p‑adic filter.
* Implement and document **p‑adic filtering**:

    * Current baseline: reject `d` that share small prime factors with N (for primes where `N mod p != 0`).
    * Maintain consistent set of small primes.
* Explore new geometric sampling schemes:

    * Non‑uniform windows (e.g., heavier tails).
    * Multi‑band windows (e.g., several disjoint bands around different centers).
    * Quasi‑Monte Carlo (QMC) sequences (Sobol, Halton) vs pure RNG.
* Consider **multiplicative or log‑scale sampling**:

    * E.g., sampling `d` such that `log d` is around `log sqrt(N)` but with meaningful spread.

**Inputs**

* N and seed config from `N-STEW`.
* Kernel specs from `GEOM`.
* Scale hints from `SCALE`.

**Outputs**

* `generate_candidates(N, params)` API and its implementation(s).
* A clear description of all available sampling modes in `docs/geometry/SAMPLING.md`.
* Default sampling profile(s) for this N (e.g., which bands, how many samples per band).

**Guardrails**

* No explicit usage of `p` or `q` to place bands or choose centers.
* No “scan all d values up to some bound” fallbacks – the candidate set must stay **small and ranked**.

---

## 6. SCALE – Scale‑Adaptive Tuning

**Purpose:** Capture and implement empirical scaling laws (Z5D insights) **specialized** to this 127‑bit challenge.

**Responsibilities**

* Translate high‑level Z5D / scale‑adaptive ideas into concrete rules like:

    * How `samples`, `window`, `j`, `m-span`, and thresholds should depend on `bit_length(N)`.
    * How to adapt these further once we observe performance on this N.
* Maintain a **scale‑adaptive config** layer:

    * e.g., `scale_adaptive.yaml` that maps bit‑length → parameter ranges.
* For this repo:

    * You are allowed to **overfit** the scaling law to this N, as long as it does not use factor values directly.
    * Example: “For 127‑bit semiprimes, use wider windows and higher j than for 60‑bit gates”.

**Inputs**

* Observed performance metrics from `XP`.
* Theoretical proposals from `GEOM` and `SAMPLE`.

**Outputs**

* Concrete parameter presets:

    * e.g., `profile: challenge-127` with `(samples, window, j, m-span, thresholds, timeout)`.
* Documentation in `docs/SCALE_ADAPTIVE_TUNING_127.md`.

**Guardrails**

* All scaling decisions must be explainable in terms of:

    * Bit‑length.
    * Observed performance metrics.
    * Not “because that’s where p is”.

---

## 7. IMPL – Implementation & Refactor

**Purpose:** Keep the factorization code clean, consistent, and fast across languages (Python prototype, Java core).

**Responsibilities**

* Maintain **parity** between:

    * Python prototype(s) in this repo.
    * Java/Spring Boot code in the main geofac repo (where relevant).
* Implement:

    * Geometric scoring (`GEOM`).
    * Sampling / p‑adic filters (`SAMPLE`).
    * Scale‑adaptive parameter loading (`SCALE`).
    * CLI and config surface.
* Ensure determinism:

    * Use consistent RNG and seeding.
    * No hidden global randomness.

**Inputs**

* Specs and APIs defined by `GEOM`, `SAMPLE`, `SCALE`.
* Constraints & logging requirements from `CERT`.

**Outputs**

* Working CLIs, e.g.:

    * `python geofac_local_global.py N --window ... --samples ...`
    * Java/Spring Shell commands (if reused here).
* Unit tests and integration tests for:

    * Kernel computations.
    * Candidate generation.
    * p‑adic filtering.
    * Logging correctness.

**Guardrails**

* No hidden code paths that:

    * Call external factorization services.
    * Use precomputed factors or small factor tables for this N.
* Make it easy for `RED` to inspect and audit for “cheats”.

---

## 8. XP – Experiment & Metrics

**Purpose:** Run experiments on this N, track how often geometric ranking surfaces a factor in the certified set, and compare parameter configurations.

**Responsibilities**

* Define experiment protocols:

    * For a given config `C`, run `K` *independent* factorization attempts (different seeds if allowed, or fixed seed if not).
    * Log:

        * Whether a factor was found.
        * Its rank.
        * Total number of candidates generated.
        * Time and memory usage (if available).
* Maintain a **metrics schema**, e.g.:

    * `success_rate` (over K runs).
    * `E[rank(p)]`, `E[rank(q)]` when we simulate with known factors in candidate sets (for **offline analysis only**).
    * Score distributions for factors vs non‑factors.
* Automate:

    * Grid searches over parameters recommended by `SCALE`.
    * Comparisons of different kernels / samplers.

**Inputs**

* Implementations from `IMPL`.
* Configs and profiles from `SCALE`.
* Factor ground truth (p, q) only in **analysis notebooks**, not in production code.

**Outputs**

* Experiment logs in a structured format (JSON/CSV).
* Plots and dashboards (e.g., Jupyter notebooks) summarizing:

    * How often a factor appears in `top_k`.
    * How rank and score behave across runs.

**Guardrails**

* Do not alter code or configs during a batch run; experiments must be reproducible.
* When using ground‑truth factors:

    * Only for *evaluation* (e.g., add them to the candidate list to see ranking behavior).
    * Never baked back into the geometric or sampling logic.

---

## 9. CERT – Verification & Proof

**Purpose:** Turn any “we found a factor” event into a fully replayable **proof artifact**.

**Responsibilities**

* Define the **proof bundle** structure, e.g.:

    * `proofs/`

        * `N.json` – canonical N metadata (from `N-STEW`).
        * `run_<timestamp>/`

            * `config.yaml` – all parameters.
            * `candidates.json` – ranked candidates with scores and `is_factor`.
            * `cert.json` – factors found, `N mod d`, or `gcd(N, d)`.
            * `replay.sh` or `replay.md` – how to rerun.

* Validate that:

    * `p * q == N`.
    * `N mod p == 0`, `N mod q == 0`.
    * No extra hidden steps were used that violate non‑negotiables.

* Ensure all successful proofs can be **checked offline** by a skeptical third party.

**Inputs**

* Experiment logs from `XP`.
* Code and configuration from `IMPL` and `SCALE`.

**Outputs**

* Signed‑off proof bundles.
* A `VERIFICATION_127.md` doc describing:

    * Exact N, p, q.
    * Command(s) used.
    * Run IDs and locations of artifacts.

**Guardrails**

* If a proof cannot be replayed with the published code + configs, it is **invalid**.
* Ensure that any usage of classical methods in offline analysis is **clearly separated** from the geometric factorization path.

---

## 10. RED – Falsification & Red‑Team

**Purpose:** Try to break the story: find hidden classical fallbacks, factor injection, or misleading metrics.

**Responsibilities**

* Code audits:

    * Search for any use of:

        * `p`, `q` constants.
        * Calls to known factoring libraries or APIs.
    * Verify that geometric and sampling logic don’t secretly use factor‑dependent information.
* Experimental audits:

    * Check that “success” runs are not cherry‑picked.
    * Reproduce results on clean machines / clean environments.
* Theoretical audits:

    * Ask: “If this worked, what complexity would it imply? Is that plausible?”

**Inputs**

* Entire codebase.
* Proof bundles from `CERT`.
* Metrics from `XP`.

**Outputs**

* `RED_REPORT.md` with:

    * Findings, concerns, and resolved issues.
    * Checklists for future changes (e.g., “add unit test to ensure no factor constants in geometry modules”).

**Guardrails**

* RED is **allowed** to use any external tools they like to falsify claims, including classical factoring – but only for auditing, not for production factoring.

---

## 11. Recommended initial workplan

1. **N-STEW**

    * Introduce canonical `N` config and ensure all scripts read from it.
2. **IMPL + SAMPLE**

    * Port `geofac_local_global.py` cleanly into this repo, with gates removed and logging consistent with main geofac.
    * Expose window, samples, and j as config (not hard‑coded).
3. **GEOM + SCALE**

    * Define 2–3 kernel variants and 2–3 sampling profiles tailored to 127‑bit scale (but not to p, q).
4. **XP**

    * Build a minimal experiment harness for sweeping over these profiles and collecting metrics.
5. **CERT**

    * Define the proof bundle format *before* any “success” is claimed.
6. **RED**

    * Run an initial audit to confirm:

        * No factor injection.
        * No hidden classical sweep.
        * Logs are sufficient for replay.

All future work and agents should be judged by a single question:

> “Does this increase the probability that the true factors of
> `137524771864208156028430259349934309717` land early in a geometrically ranked, arithmetically certified candidate set – without cheating?”
