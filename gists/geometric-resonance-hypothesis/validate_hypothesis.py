#!/usr/bin/env python3
"""
Validate geometric resonance hypothesis for the 127-bit challenge semiprime.

Hypothesis from .github/conversations.md:
- For semiprime n=pq, resonance amplitude peaks at k where θ'(p,0.3) ≈ θ'(q,0.3) mod φ
- Curvature function: κ(n) = d(n) · ln(n+1) / e²
- Geometric resolution: θ'(n, k) = φ · ((n mod φ) / φ)^k

Gate 1 target (from docs/VALIDATION_GATES.md):
- N = 137524771864208156028430259349934309717
- p = 10508623501177419659
- q = 13086849276577416863
"""

from mpmath import mp, log, e, mpf
import json
from datetime import datetime

# Set precision to exceed requirement: N.bitLength() * 4 + 200
# 127 bits * 4 + 200 = 708 decimal digits
mp.dps = 720

# Official Gate 1 factors from docs/VALIDATION_GATES.md
N = mpf('137524771864208156028430259349934309717')
p = mpf('10508623501177419659')
q = mpf('13086849276577416863')

# Validate product
assert p * q == N, f"Factor validation failed: {p} * {q} != {N}"

# Golden ratio φ ≈ 1.618...
phi = (1 + mp.sqrt(5)) / 2

print("=" * 80)
print("GEOMETRIC RESONANCE HYPOTHESIS VALIDATION")
print("=" * 80)
print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
print(f"Precision: {mp.dps} decimal places")
print(f"Target: Gate 1 (127-bit challenge)")
print()

print(f"N = {N}")
print(f"p = {p}")
print(f"q = {q}")
print(f"Product check: p * q == N: {p * q == N}")
print()

# Part 1: Compute curvature κ(n) = d(n) · ln(n+1) / e²
print("-" * 80)
print("PART 1: Curvature Analysis")
print("-" * 80)
print("Computing κ(n) = σ₀(n) · ln(n+1) / e²")
print("where σ₀(n) = divisor_sigma(n, 0) = count of divisors")
print()

# For prime n, σ₀(n) = 2 (divisors: 1, n)
sigma_p = mpf(2)  # p is prime, so d(p) = 2
sigma_q = mpf(2)  # q is prime, so d(q) = 2
# For semiprime N = p*q, σ₀(N) = 4 (divisors: 1, p, q, N)
sigma_N = mpf(4)

kappa_p = sigma_p * log(p + 1) / (e ** 2)
kappa_q = sigma_q * log(q + 1) / (e ** 2)
kappa_N = sigma_N * log(N + 1) / (e ** 2)

print(f"σ₀(p) = {sigma_p}")
print(f"σ₀(q) = {sigma_q}")
print(f"κ(p) = {kappa_p}")
print(f"κ(q) = {kappa_q}")
print(f"κ(N) = {kappa_N}")
print()

kappa_diff = abs(kappa_p - kappa_q)
print(f"|κ(p) - κ(q)| = {kappa_diff}")
print(f"Threshold check (< 1e-16): {kappa_diff < mpf('1e-16')}")
print()

# Part 2: Compute geometric resolution θ'(n, k) = φ · ((n mod φ) / φ)^k
print("-" * 80)
print("PART 2: Geometric Resolution Analysis")
print("-" * 80)
print("Computing θ'(n, k) = φ · ((n mod φ) / φ)^k with k = 0.3")
print()

k = mpf('0.3')

# Note: For integer n and irrational φ, (n mod φ) doesn't have a standard definition
# Interpret as: n - floor(n/φ) * φ
def mod_phi(n):
    """Compute n mod φ for the geometric resolution formula."""
    quotient = mp.floor(n / phi)
    return n - quotient * phi

theta_prime_p = phi * ((mod_phi(p) / phi) ** k)
theta_prime_q = phi * ((mod_phi(q) / phi) ** k)
theta_prime_N = phi * ((mod_phi(N) / phi) ** k)

print(f"p mod φ = {mod_phi(p)}")
print(f"q mod φ = {mod_phi(q)}")
print(f"N mod φ = {mod_phi(N)}")
print()

print(f"θ'(p, 0.3) = {theta_prime_p}")
print(f"θ'(q, 0.3) = {theta_prime_q}")
print(f"θ'(N, 0.3) = {theta_prime_N}")
print()

theta_diff = abs(theta_prime_p - theta_prime_q)
theta_mod_phi = theta_diff  # Already computed difference

print(f"|θ'(p, 0.3) - θ'(q, 0.3)| = {theta_diff}")
print(f"Relative difference: {theta_diff / max(theta_prime_p, theta_prime_q)}")
print()

# Part 3: Hypothesis evaluation
print("-" * 80)
print("PART 3: Hypothesis Evaluation")
print("-" * 80)
print()

hypothesis_1 = kappa_diff < mpf('1e-16')
print(f"Hypothesis 1: |κ(p) - κ(q)| < 1e-16")
print(f"Result: {hypothesis_1}")
print(f"Analysis: {'PASS - Curvatures are nearly identical' if hypothesis_1 else 'FAIL - Curvatures differ significantly'}")
print()

# For hypothesis 2, we need a more relaxed threshold since θ' values may not be exact
theta_threshold = mpf('0.01')  # 1% relative difference
relative_theta_diff = theta_diff / max(theta_prime_p, theta_prime_q)
hypothesis_2 = relative_theta_diff < theta_threshold

print(f"Hypothesis 2: θ'(p, 0.3) ≈ θ'(q, 0.3) (relative diff < {theta_threshold})")
print(f"Result: {hypothesis_2}")
print(f"Analysis: {'PASS - Geometric resolutions are similar' if hypothesis_2 else 'FAIL - Geometric resolutions differ significantly'}")
print()

# Part 4: Export artifacts
print("-" * 80)
print("PART 4: Artifact Export")
print("-" * 80)

results = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "precision_decimal_places": mp.dps,
    "gate": "Gate 1 (127-bit challenge)",
    "target": {
        "N": str(N),
        "p": str(p),
        "q": str(q),
        "product_verified": bool(p * q == N)
    },
    "curvature_analysis": {
        "kappa_p": str(kappa_p),
        "kappa_q": str(kappa_q),
        "kappa_N": str(kappa_N),
        "kappa_diff": str(kappa_diff),
        "hypothesis_threshold": "1e-16",
        "hypothesis_pass": hypothesis_1
    },
    "geometric_resolution_analysis": {
        "k": str(k),
        "phi": str(phi),
        "theta_prime_p": str(theta_prime_p),
        "theta_prime_q": str(theta_prime_q),
        "theta_prime_N": str(theta_prime_N),
        "theta_diff": str(theta_diff),
        "relative_diff": str(relative_theta_diff),
        "hypothesis_threshold": str(theta_threshold),
        "hypothesis_pass": hypothesis_2
    },
    "overall_conclusion": {
        "hypothesis_1_pass": hypothesis_1,
        "hypothesis_2_pass": hypothesis_2,
        "overall_status": "VALIDATED" if (hypothesis_1 and hypothesis_2) else "FALSIFIED"
    }
}

with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Results exported to: results.json")
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
if hypothesis_1 and hypothesis_2:
    print("✓ HYPOTHESIS VALIDATED")
    print()
    print("Both curvature analysis and geometric resolution analysis support")
    print("the hypothesis that resonance amplitude peaks align with low κ(n)")
    print("for the Gate 1 semiprime factors.")
else:
    print("✗ HYPOTHESIS FALSIFIED")
    print()
    if not hypothesis_1:
        print("- Curvature analysis does not support the hypothesis")
    if not hypothesis_2:
        print("- Geometric resolution analysis does not support the hypothesis")

print()
print("=" * 80)
