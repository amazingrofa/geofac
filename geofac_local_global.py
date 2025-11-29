#!/usr/bin/env python3
"""
Geofac Local-Global Resonance
==============================

Factorization prototype using local-global resonance with Dirichlet kernels.
Generates candidates near sqrt(N), applies p-adic filtering, ranks by resonance score,
and validates via arithmetic predicate (N mod d == 0).

Validation range: [10^14, 10^18] per docs/validation/VALIDATION_GATES.md
Whitelist: 127-bit CHALLENGE_127 = 137524771864208156028430259349934309717
"""
import argparse
import math
import random
import hashlib
import json
from typing import List, Tuple, Dict, Any

# Validation gates
CHALLENGE_127 = 137524771864208156028430259349934309717  # Gate 3: 127-bit challenge
RANGE_MIN = 10**14  # Gate 4: Operational range minimum
RANGE_MAX = 10**18  # Gate 4: Operational range maximum

# Retry multiplier for candidate generation (p-adic filter may reject candidates)
FILTER_RETRY_MULTIPLIER = 50


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bit_length() * 4 + 200)
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def validate_n(N: int) -> bool:
    """Validate N is in operational range or whitelisted 127-bit challenge."""
    if N == CHALLENGE_127:
        return True
    if RANGE_MIN <= N <= RANGE_MAX:
        return True
    return False


def dirichlet_kernel(x: float, j: int) -> float:
    """Compute Dirichlet kernel D_j(x) = 1 + 2*sum(cos(k*x) for k in 1..j)."""
    s = 1.0
    for k in range(1, j + 1):
        s += 2.0 * math.cos(k * x)
    return s


def real_resonance_score(N: int, d: int, j: int) -> float:
    """Compute resonance score using Dirichlet kernel at fractional position."""
    frac = (N % d) / float(d)
    x = 2.0 * math.pi * frac
    return abs(dirichlet_kernel(x, j))


def small_primes(limit: int = 97) -> List[int]:
    """Generate primes up to limit for p-adic filtering (25 primes for limit=97)."""
    primes: List[int] = []
    for n in range(2, limit + 1):
        ok = True
        for p in primes:
            if p * p > n:
                break
            if n % p == 0:
                ok = False
                break
        if ok:
            primes.append(n)
    return primes


def build_p_adic_filter(N: int, primes: List[int]) -> Dict[int, int]:
    """Build p-adic filter: maps prime p to N mod p."""
    return {p: N % p for p in primes}


def passes_p_adic_filter(d: int, N_mod: Dict[int, int]) -> bool:
    """Check if candidate d passes p-adic filter."""
    for p, nmod in N_mod.items():
        if nmod != 0 and d % p == 0:
            return False
    return True


def generate_candidates(
    N: int,
    window: int,
    samples: int,
    seed: int,
    N_mod: Dict[int, int],
) -> List[int]:
    """Generate candidate divisors near sqrt(N) using deterministic sampling."""
    rnd = random.Random(seed)
    root = int(math.isqrt(N))
    seen = set()
    candidates: List[int] = []
    max_attempts = samples * FILTER_RETRY_MULTIPLIER
    attempts = 0
    while len(candidates) < samples and attempts < max_attempts:
        attempts += 1
        offset = rnd.randint(-window, window)
        d = root + offset
        if d <= 1 or d >= N:
            continue
        if d in seen:
            continue
        seen.add(d)
        if not passes_p_adic_filter(d, N_mod):
            continue
        candidates.append(d)
    return candidates


def resonance_rank(
    N: int,
    candidates: List[int],
    j: int,
) -> List[Tuple[int, float]]:
    """Rank candidates by resonance score (descending)."""
    scored: List[Tuple[int, float]] = []
    for d in candidates:
        s = real_resonance_score(N, d, j)
        scored.append((d, s))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


def is_factor(N: int, d: int) -> bool:
    """Arithmetic certification: check if d divides N."""
    return N % d == 0


def geofac_local_global(
    N: int,
    window: int = 10_000_000,
    samples: int = 50_000,
    j: int = 25,
    top_k: int = 500,
) -> Dict[str, Any]:
    """
    Run local-global resonance factorization.

    Args:
        N: Semiprime to factor (must be in [10^14, 10^18] or CHALLENGE_127)
        window: Half-width of search window around sqrt(N)
        samples: Number of candidates to generate
        j: Dirichlet kernel order
        top_k: Number of top-ranked candidates to certify

    Returns:
        Dictionary with N, parameters, candidates, and any factors found.
    """
    # Validate composite requirement first
    if N < 4:
        raise ValueError(f"N must be >= 4 (composite). Got N = {N}")
    # Validate operational range
    if not validate_n(N):
        raise ValueError(
            f"N must be in [{RANGE_MIN}, {RANGE_MAX}] or be the 127-bit challenge "
            f"({CHALLENGE_127}). Got N = {N}"
        )
    if window <= 0 or samples <= 0 or j <= 0 or top_k <= 0:
        raise ValueError("window, samples, j, and top_k must be positive.")

    # Compute adaptive precision for reproducibility per docs/validation/VALIDATION_GATES.md.
    # This prototype uses standard floats for Dirichlet scoring; precision is logged
    # for consistency with repo standards. Future high-precision extensions may use mpmath.
    precision = adaptive_precision(N)

    seed_bytes = hashlib.sha256(str(N).encode("utf-8")).digest()
    seed = int.from_bytes(seed_bytes[:8], "big")
    primes = small_primes()
    N_mod = build_p_adic_filter(N, primes)
    candidates = generate_candidates(N, window, samples, seed, N_mod)
    ranked = resonance_rank(N, candidates, j)
    tail = ranked[: min(top_k, len(ranked))]
    candidate_logs = []
    factors = []
    for rank, (d, score) in enumerate(tail, start=1):
        flag = is_factor(N, d)
        entry = {"d": int(d), "score": float(score), "rank": rank, "is_factor": flag}
        candidate_logs.append(entry)
        if flag:
            factors.append(entry)
    log: Dict[str, Any] = {
        "N": str(N),
        "bit_length": int(N.bit_length()),
        "precision": int(precision),
        "params": {
            "window": int(window),
            "samples": int(samples),
            "dirichlet_order_j": int(j),
            "top_k": int(top_k),
            "seed": int(seed),
        },
        "p_adic_primes": primes,
        "candidates": candidate_logs,
        "factors": factors,
    }
    return log


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(
        description="Geofac-style local-global resonance prototype."
    )
    ap.add_argument("N", type=int, help="Integer to factor (target semiprime range).")
    ap.add_argument("--window", type=int, default=10_000_000)
    ap.add_argument("--samples", type=int, default=50_000)
    ap.add_argument("--j", type=int, default=25, help="Dirichlet kernel order.")
    ap.add_argument("--top-k", type=int, default=500)
    args = ap.parse_args()
    log = geofac_local_global(
        N=args.N,
        window=args.window,
        samples=args.samples,
        j=args.j,
        top_k=args.top_k,
    )
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
