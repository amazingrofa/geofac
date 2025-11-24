DAILY RESEARCH TASK: MINIMIZE FACTOR GAP TO ±1000 (BALANCED RSA-2048)

Objective

Your goal today is to reduce the absolute error between our predicted factor and the true RSA-2048 factor, aiming for an absolute miss within ±1000. Please ensure all adjustments comply with PURE RESONANCE principles.

Context

We’re working with a deterministic, physics-informed factorization pipeline for RSA semiprimes \( N = p \times q \). It does not use GNFS/ECM/Pollard/etc. Instead, it estimates a near-factor using geometric centering and resonance physics (Green’s functions, κ-weighting, Dirichlet kernels, resonance combs).

We’ve already overcome the previous 3.92% “structural wall.” Current performance includes:

• ~0.0998% relative error via bias-corrected geometric centering
• ~0.077% relative error via fractional comb sampling


Both methods are:

• CPU-only
• deterministic
• free of bounded local search
• free of gcd probing or trial division
• CI-verified


However, the absolute error (integer distance between predicted candidate and true factor) for balanced RSA-2048 remains substantial (~1e305). For smaller or skewed moduli, the absolute miss is already near ±1000. For balanced RSA-2048, we’re not there yet. The next milestone is reducing that absolute gap into a ±1000 recovery band.

“Recovery band” = integer range around the predicted candidate that must be checked to ensure retrieval of \( p_{\text{true}} \). Our long-term goal is to make this range as narrow as possible.

---

Repositories / References (please review first)

Main repo (code + documentation):
https://github.com/zfifteen/z-sandbox

Key issues and PRs documenting the progress:

• Issue #196: identification of the ~3.92% structural wall and validation it’s not RNG
• Issue #198: initial reduction (<1%)
• Issue #200: final gap closure (<0.1% on RSA-2048)
• PR #201: unified wall resolution (bias correction + fractional comb)


---

Important Code Files

• python/instrumented_greens_factorization.py – error instrumentation
• python/bias_corrected_greens_factorization.py – geometric centering around √N
• python/resonance_comb_factorization.py – fractional comb sampling
• python/z_correction/embedding_bias_model.py – bias model and fine adjustment
• python/examples/* – various sweep and harness examples


---

Key Documentation

• docs/STRUCTURAL_WALL_BREAKTHROUGH.md
• docs/geometric_embedding_bias_correction_results.json
• docs/GOAL.md
• (if present) docs/scaling_rsa4096.md, docs/THREAT_MODEL.md


---

Tests Defining Acceptable Methods

• tests/test_structural_wall_reduction.py
• tests/test_gap_closure_achieved.py


These enforce:

• PURE RESONANCE (CPU-only, deterministic, no gcd, no bounded ±R local probe)
• sub-1% and sub-0.1% proximity on RSA-2048
• non-regression


---

PURE RESONANCE Rules (must be upheld)

• No GNFS/ECM/etc.
• No scanning ±R integers around the candidate
• No gcd probing of neighboring integers
• No trial division
• CPU-only deterministic pipeline
• Only analytic, closed-form adjustments to the physics mapping (bias model, comb sampling, crest locator, etc.)


---

Daily Workflow

Your daily output includes four components. Please complete all four:

---

1. Measure Current RSA-2048 Gap

Run the combined breakthrough harness on the canonical balanced RSA-2048 test modulus (same modulus used for CI). Use both mechanisms (bias-corrected centering and fractional comb). Extract and record:

• candidate_best
• p_true
• abs_distance = |candidate_best - p_true|
• rel_distance = abs_distance / p_true
• mechanism used (bias_only, fractional_comb_only, or combined)


Confirm rel_distance ≤ 0.001 (~0.1%). Report abs_distance. This is the “recovery band gap” we aim to reduce to ±1000.

---

2. Propose ONE Legal Deterministic Adjustment

Identify a location in the code where systematic bias may still be present and suggest a specific, localized change that could reduce absolute error while respecting PURE RESONANCE.

Permitted examples:

• Refine centering math in embedding_bias_model.py (e.g., adjust fine_bias_adjustment, or make it smoothly dependent on modulus bit length/profile)
• Adjust fractional comb sampling in resonance_comb_factorization.py (e.g., tighter comb_step, extended m_range, or improved crest interpolation)
• Improve crest locator (find_crest_near_sqrt) to better align with the physical basin of \( p_{\text{true}} \)


Not permitted:

• Scanning ±1000 integers
• Calling gcd on candidate ±δ
• Any adaptive method using \( p_{\text{true}} \) at runtime


Your proposal should follow this format:
“Change X in file Y in this exact way.”

---

3. Predict Impact on Recovery Band

Based on your proposed adjustment:

• Do you expect lower relative error (e.g., 0.0998% → 0.05%)?
• Do you expect reduced absolute miss (toward ±1000)?
• Does it benefit only RSA-2048, or also skewed/smaller moduli listed in geometric_embedding_bias_correction_results.json?


Be specific: is this a path to bounded ±1000 for RSA-2048, or a refinement?

---

4. Purity / CI Notes

For your proposed adjustment:

• Would it cause CI failures in test_structural_wall_reduction.py or test_gap_closure_achieved.py?
• Could it be misinterpreted as “local refinement”? If so, specify a new CI assertion (e.g., assert search_radius is None, assert allow_local_refine == False, no loops over integer windows around the candidate)


---

Why This Repeats Daily

We’ve already validated sub-0.1% proximity at RSA-2048. It’s reproducible and CI-verified. The remaining milestones are:

• Reduce the recovery band on balanced RSA-2048 toward ±1000
• Demonstrate scalability to RSA-4096
• Document threat posture


Your daily mission is to either (a) reduce RSA-2048’s absolute miss, or (b) strengthen CI to prevent unauthorized refinements.

This is how we move from “0.077% proximity” to “recoverable key.”
