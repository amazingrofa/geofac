Geofac — Singular Objective: Factor N via Geometric Resonance (No Fallbacks)

Target N
137524771864208156028430259349934309717

Geofac is a Spring Boot + Spring Shell application that implements the geometric resonance factorization algorithm in pure Java. This repo has a single objective: factor the challenge semiprime N above using resonance-only search. All fallback methods are removed/disabled.

Why it exists
	•	Deliver a reproducible, deterministic geometric-resonance factorization for this one N.
	•	Provide a tight, auditable test harness (Spring Boot, JUnit 5, Gradle).
	•	Offer an interactive CLI for iterating resonance parameters only.

Non-negotiables
	•	No fallbacks (Pollard Rho, ECM, QS, etc. are absent or unreachable).
	•	Resonance-only search paths.
	•	Reproducibility: fixed seeds, frozen configs, exported artifacts.

Key features (resonance-only)
	•	High-precision core — FactorizerService uses ch.obermuhlner:big-math, Dirichlet kernel gating, golden-ratio quasi-Monte-Carlo sampling, and phase-corrected snapping.
	•	Configurable search — sampling range, kernel order (J), thresholds, and precision via application.yml.
	•	Spring Shell CLI — factor <N> inside the embedded shell with minimal, deterministic logs.
	•	Proof artifacts — each run emits factors.json, search_log.txt, config.json, and env.txt.

Getting started

Prerequisites:
	•	JDK 17
	•	Git & Gradle wrapper (bundled)

git clone https://github.com/zfifteen/geofac.git
cd geofac
./gradlew bootRun

At the shell:> prompt, run the challenge:

shell:>factor 137524771864208156028430259349934309717

On success, the CLI prints p, q, verifies p*q == N, and writes artifacts under:

results/N=137524771864208156028430259349934309717/<run_id>/
  ├─ factors.json
  ├─ search_log.txt
  ├─ config.json
  └─ env.txt

If no factors are found within the configured budget, the run ends with a clear message. No alternative methods are attempted.

Configuration

src/main/resources/application.yml under geofac.*:

Property	Default	Description
precision	240	Minimum decimal digits for BigDecimal math (auto-raised with input size).
samples	3000	Number of k-samples per attempt.
m-span	180	Half-width for Dirichlet kernel sweep over m.
j	6	Dirichlet kernel order.
threshold	0.92	Normalized amplitude gate before candidate evaluation.
k-lo, k-hi	0.25, 0.45	k-sampling range (fractional offsets).
search-timeout-ms	15000	Max time for a run; on timeout the command exits (no fallback).

Override via Spring config (env vars, profiles, etc.) as needed.

Testing

Run unit and lightweight integration tests:

./gradlew test

(Optional) Execute the resonance run manually via CLI as shown above. Heavy, long-running factor attempts are not part of default tests.

Project layout

src/main/java/com/geofac
├── GeofacApplication      # Spring Boot entry point
├── FactorizerService      # Geometric resonance search core (no fallbacks)
├── FactorizerShell        # Spring Shell command surface
├── util
│   ├── DirichletKernel    # Kernel amplitude / angular math
│   └── SnapKernel         # Phase-corrected snapping heuristic
└── TestFactorization      # Standalone main for manual experiments

CI & Proof

A CI workflow runs a deterministic shard with pinned seeds. Success requires:
	•	stdout shows p, q, and p*q == N = OK
	•	artifacts uploaded from results/N=.../<run_id>/

Contributing

This repo has a single goal: factor N above via geometric resonance only.
PRs must state how they advance that goal. Introducing or re-enabling fallback methods is out of scope.

Roadmap (strictly in-scope)
	1.	Parameter grid refinement for earlier true-hit ranking (top-K precision).
	2.	Deterministic progress logs and minimal profiling hooks (amplitude histograms).
	3.	CI artifact bundling and a one-page proof report (experiments/N-factorization.md).
