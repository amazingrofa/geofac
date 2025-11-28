# Geometric Factorization and Arithmetic Certification

Timestamp: 2025-11-22T00:00:00Z

## Purpose
Clarify the hard boundary between geometric scoring and the arithmetic predicate that certifies a factor. Geofac’s claim is not to bypass divisibility tests, but to rank a tiny candidate set so that only a handful of exact `N mod d` checks are needed.

## Minimum Arithmetic Step
- Every factoring procedure must evaluate `IsFactor_N(d) := (N mod d == 0)` for some candidate `d`.
- Geometry proposes **where to look and in what order**; arithmetic provides the truth value.
- Certification stays narrow: only the top-ranked geometric candidates are checked—no wide trial-division sweeps, Pollard Rho, ECM, or other classical fallbacks.

## Geometric Model
- Let a configuration space \(X\) map to candidate integers via \(\Phi : X \to \mathbb{Z}_{>0}\).
- A scoring functional \(S_N : X \to \mathbb{R}\) induces candidate scores \(S_N^{\*}(d) = \sup{ S_N(x) : \Phi(x)=d }\).
- The geofac goal is to make the true factor \(p\) appear near the top of the ranked list \(d_1, d_2, \dots\) ordered by \(S_N^{\*}\), so only \(d_1, \dots, d_m\) need arithmetic checks.

## Complexity Framing
- Blind trial division over a width \(W\) near \(\sqrt{N}\) performs \(O(W)\) modular checks.
- Geofac splits the cost: a geometric phase \(T_{geo}(N)\) that produces a ranked candidate list, plus \(m\) arithmetic checks on the top entries.
- Progress is shown when \(\mathbb{E}[\text{rank}(p)] \ll W\) for balanced semiprimes, i.e., the expected rank of the true factor is far smaller than any naive scan window.

## Evidence and Logging Expectations
- Log all parameters (\(N\), precision, seeds if any, window/step/band choices), timestamps, and the exact number of candidates tested.
- Report \(m\) (the number of arithmetic checks) alongside geometric work so validation can separate ranking quality from certification cost.
- Keep methods deterministic or quasi-deterministic; pin seeds and precision (adaptive: `precision = max(configured, N.bitLength() * 4 + 200)`).
- Tie reports to the validation gates: spell out the geometric phase cost \(T_{geo}(N)\), the exact candidates submitted to `IsFactor_N`, and the observed rank of any discovered factor.
- Include the arithmetic predicate output (`N mod d`) for each certified candidate so replay logs provide a complete certificate without re-running geometry.

## Non-Goals
- Eliminating the arithmetic predicate is impossible; `N mod d` remains the certificate.
- Expanding the certified candidate set into a broad search, or adding probabilistic classical algorithms, violates the geofac scope.
