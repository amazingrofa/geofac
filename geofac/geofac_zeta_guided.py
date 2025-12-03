#!/usr/bin/env python3
"""
Geofac Zeta-Guided Resonance (The Insight)
==========================================

Implements the "Equidistributed Periodic Tori with Twisted Ruelle Zetas" insight.
Replaces random sampling with Quasi-Monte Carlo (QMC) sequences tuned to
arithmetic spectral symmetries.

Key Features:
1. Equidistribution: Uses Scipy's Sobol sequence (QMC) for low-discrepancy sampling.
2. Torsion: Modulates the Dirichlet kernel with a "Twisted Zeta" factor.
3. Fractal: Applies power-law scaling to the search window.
"""
import argparse
import math
import hashlib
import json
import numpy as np
from scipy.stats import qmc
from typing import List, Tuple, Dict, Any

# Constants
CHALLENGE_127 = 137524771864208156028430259349934309717
RANGE_MIN = 10**14
RANGE_MAX = 10**18

def adaptive_precision(N: int) -> int:
    return max(50, N.bit_length() * 4 + 200)

def validate_n(N: int) -> bool:
    if N == CHALLENGE_127: return True
    if RANGE_MIN <= N <= RANGE_MAX: return True
    return False

def dirichlet_kernel(x: float, j: int) -> float:
    """Standard Dirichlet kernel."""
    # D_j(x) = sin((j + 0.5) * x) / sin(0.5 * x)
    # Using the summation form for stability/clarity in this prototype
    s = 1.0
    for k in range(1, j + 1):
        s += 2.0 * math.cos(k * x)
    return s

def zeta_modulation(x: float, N: int) -> float:
    """
    The 'Twisted Ruelle Zeta' modulation.
    Simulates the 'signed counts of special paths' on the orbisurface.
    """
    # We derive "torsion phases" from N to simulate the arithmetic structure
    # This acts as the "representation rho" in the insight.
    phases = [
        (N >> i) & 1 for i in range(0, 8) # Take bottom 8 bits as phase keys
    ]
    
    # Construct a weighted sum of cosines (trace of the representation)
    modulation = 1.0
    for k, bit in enumerate(phases, start=1):
        # If bit is 1, we add a "twisted" harmonic
        if bit:
            # The frequency and phase are arbitrary but deterministic (simulating the topology)
            modulation += 0.5 * math.cos(k * x * 1.618 + float(k)/13.0) 
            
    return abs(modulation)

def real_resonance_score(N: int, d: int, j: int) -> float:
    """
    Compute resonance score:
    Score = |Dirichlet(d)| * ZetaModulation(d)
    """
    frac = (N % d) / float(d)
    x = 2.0 * math.pi * frac
    
    base_score = abs(dirichlet_kernel(x, j))
    mod_factor = zeta_modulation(x, N)
    
    return base_score * mod_factor

def small_primes(limit: int = 97) -> List[int]:
    primes = []
    for n in range(2, limit + 1):
        ok = True
        for p in primes:
            if p * p > n: break
            if n % p == 0:
                ok = False
                break
        if ok: primes.append(n)
    return primes

def build_p_adic_filter(N: int, primes: List[int]) -> Dict[int, int]:
    return {p: N % p for p in primes}

def passes_p_adic_filter(d: int, N_mod: Dict[int, int]) -> bool:
    for p, nmod in N_mod.items():
        if nmod != 0 and d % p == 0:
            return False
    return True

def generate_candidates_zeta(
    N: int,
    window: int,
    samples: int,
    seed: int,
    N_mod: Dict[int, int],
) -> List[int]:
    """
    Generate candidates using Fractal QMC (The Insight).
    """
    root = int(math.isqrt(N))
    candidates = []
    seen = set()
    
    # 1. Equidistribution: Use Sobol Sequence
    # Dimension 1 for the offset
    sampler = qmc.Sobol(d=1, scramble=True, seed=seed)
    
    # We generate in batches to handle p-adic rejection
    batch_size = samples * 2 
    
    while len(candidates) < samples:
        # Get QMC points in [0, 1)
        qmc_points = sampler.random(batch_size).flatten()
        
        # 2. Fractal Scaling: Apply power-law mapping
        # Insight mentions "fractal exponents in strong coupling regime"
        # We simulate this by transforming the uniform QMC points to a power law.
        # Map [0, 1] -> [-1, 1] with heavier weight near 0 (the "resonance valley")
        
        # Transform to [-1, 1]
        u = 2 * qmc_points - 1 
        
        # Apply signed power law: sgn(u) * |u|^gamma
        # gamma = 1.5 simulates "strong coupling" clustering near the center
        gamma = 1.5 
        fractal_offsets = np.sign(u) * (np.abs(u) ** gamma)
        
        # Scale to window
        integer_offsets = (fractal_offsets * window).astype(int)
        
        for offset in integer_offsets:
            d = root + int(offset)
            
            if d <= 1 or d >= N: continue
            if d in seen: continue
            seen.add(d)
            
            if not passes_p_adic_filter(d, N_mod):
                continue
                
            candidates.append(d)
            if len(candidates) >= samples:
                break
                
    return candidates

def resonance_rank(
    N: int,
    candidates: List[int],
    j: int,
) -> List[Tuple[int, float]]:
    scored = []
    for d in candidates:
        s = real_resonance_score(N, d, j)
        scored.append((d, s))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored

def is_factor(N: int, d: int) -> bool:
    return N % d == 0

def geofac_zeta(
    N: int,
    window: int = 10_000_000,
    samples: int = 50_000,
    j: int = 25,
    top_k: int = 500,
) -> Dict[str, Any]:
    
    if N < 4: raise ValueError(f"N must be >= 4. Got {N}")
    if not validate_n(N):
        raise ValueError(f"N out of range or not challenge. Got {N}")

    precision = adaptive_precision(N)
    
    # Deterministic seed from N
    seed_bytes = hashlib.sha256(str(N).encode("utf-8")).digest()
    seed = int.from_bytes(seed_bytes[:8], "big")
    
    primes = small_primes()
    N_mod = build_p_adic_filter(N, primes)
    
    # Use the Zeta-Guided Generator
    candidates = generate_candidates_zeta(N, window, samples, seed, N_mod)
    
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
            
    log = {
        "N": str(N),
        "method": "Zeta-Guided QMC",
        "params": {
            "window": int(window),
            "samples": int(samples),
            "j": int(j),
            "top_k": int(top_k),
            "seed": int(seed)
        },
        "candidates": candidate_logs,
        "factors": factors,
    }
    return log

def main():
    ap = argparse.ArgumentParser(description="Geofac Zeta-Guided Resonance.")
    ap.add_argument("N", type=int, help="Integer to factor.")
    ap.add_argument("--window", type=int, default=10_000_000)
    ap.add_argument("--samples", type=int, default=50_000)
    ap.add_argument("--j", type=int, default=25)
    ap.add_argument("--top-k", type=int, default=500)
    args = ap.parse_args()
    
    log = geofac_zeta(
        N=args.N,
        window=args.window,
        samples=args.samples,
        j=args.j,
        top_k=args.top_k,
    )
    print(json.dumps(log, indent=2))

if __name__ == "__main__":
    main()
