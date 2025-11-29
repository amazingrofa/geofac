"""
GVA-τ''' Hybrid Falsification Experiment
=========================================

Tests the hypothesis: Integrating Z-Framework GVA (7D torus embedding, geodesic scanning
near b=63.28–63.50 bits) with refined τ''' spike ranking can recover factors of the
127-bit challenge N=137524771864208156028430259349934309717 using only geometric signals.

Background from PR #132:
- Richardson extrapolation + Sobol QMC achieved 0.026-bit spike accuracy
- 993k candidates tested
- Failure: closest spike ranked 10th by confidence metric (|τ'''|/error), not 1st
- Root cause: ranking metric inversely correlates with factor proximity

Proposed Improvements:
1. Spike Ranking Upgrade: Score = error⁻¹ · log(|τ'''|)
2. GVA Integration: 7D torus embedding, scan geodesics in [63.2, 63.6] bits
3. QMC Enhancement: Sobol with Owen scrambling for candidates in ±0.05 bits
4. No prior factors used: Only geometric operations + final mod checks

Validation gate: CHALLENGE_127 = 137524771864208156028430259349934309717
Precision: max(configured, N.bit_length() × 4 + 200) = 708 dps

No classical fallbacks (Pollard's Rho, trial division, ECM, sieves).
Deterministic/quasi-deterministic methods only (Sobol sampling allowed).
"""

import mpmath as mp
from typing import Tuple, Optional, List, Dict, Any
import time
import json
import math
from datetime import datetime
import sys
import os

# Try scipy for Sobol (requires scipy >= 1.7.0)
try:
    from scipy.stats import qmc
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy.stats.qmc not available (requires scipy >= 1.7.0), using fallback QMC")

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717

# Known factors (for post-hoc validation ONLY, not used in algorithm)
P_KNOWN = 10508623501177419659
Q_KNOWN = 13086849276577416863

# Target bit range for q: [63.2, 63.6] bits
# q ≈ 2^63.50 bits, so we scan around this region
TARGET_BIT_CENTER = 63.5
TARGET_BIT_WIDTH = 0.4  # ±0.2 bits around center


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision: max(50, N.bit_length() × 4 + 200)
    
    For N = CHALLENGE_127 (127 bits): max(50, 127×4+200) = 708 dps
    """
    return max(50, N.bit_length() * 4 + 200)


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """
    Embed integer n into 7D torus using geodesic mapping.
    
    The 7D torus embedding uses golden ratio (φ) and its powers to create
    a quasi-periodic embedding that reveals factorization structure through
    Riemannian distance minimization.
    """
    phi = mp.mpf(1 + mp.sqrt(5)) / 2  # Golden ratio
    
    coords = []
    for d in range(dimensions):
        phi_power = phi ** (d + 1)
        coord = mp.fmod(n * phi_power, 1)
        
        if k != 1.0:
            coord = mp.power(abs(coord), k)
            coord = mp.fmod(coord, 1)
        
        coords.append(coord)
    
    return coords


def riemannian_distance(p1: List[mp.mpf], p2: List[mp.mpf]) -> mp.mpf:
    """
    Compute Riemannian geodesic distance on 7D torus with periodic boundaries.
    """
    dist_sq = mp.mpf(0)
    for c1, c2 in zip(p1, p2):
        diff = abs(c1 - c2)
        wrap_diff = mp.mpf(1) - diff
        min_diff = min(diff, wrap_diff)
        dist_sq += min_diff * min_diff
    return mp.sqrt(dist_sq)


def compute_tau_triple_prime(N: int, b: mp.mpf, h: mp.mpf) -> Tuple[mp.mpf, mp.mpf]:
    """
    Compute τ'''(b) = third derivative of tau function at bit position b
    using Richardson extrapolation for improved accuracy.
    
    τ(b) = N - 2^b * floor(N / 2^b) - remainder structure
    τ'''(b) approximated via finite differences with Richardson extrapolation.
    
    Args:
        N: Semiprime to analyze
        b: Bit position (e.g., 63.5)
        h: Step size for finite difference
    
    Returns:
        Tuple of (τ'''(b) approximation, error estimate)
    """
    def tau(b_val):
        """Compute τ(b) = N - 2^b * floor(N / 2^b)"""
        two_b = mp.power(2, b_val)
        quotient = mp.floor(N / two_b)
        return N - two_b * quotient
    
    # Third derivative using central differences: f'''(x) ≈ (f(x+2h) - 2f(x+h) + 2f(x-h) - f(x-2h)) / (2h³)
    # Richardson extrapolation: combine coarse (h) and fine (h/2) estimates
    
    # Coarse estimate with step h
    tau_p2h = tau(b + 2*h)
    tau_ph = tau(b + h)
    tau_mh = tau(b - h)
    tau_m2h = tau(b - 2*h)
    
    coarse = (tau_p2h - 2*tau_ph + 2*tau_mh - tau_m2h) / (2 * h**3)
    
    # Fine estimate with step h/2
    h2 = h / 2
    tau_p2h2 = tau(b + 2*h2)
    tau_ph2 = tau(b + h2)
    tau_mh2 = tau(b - h2)
    tau_m2h2 = tau(b - 2*h2)
    
    fine = (tau_p2h2 - 2*tau_ph2 + 2*tau_mh2 - tau_m2h2) / (2 * h2**3)
    
    # Richardson extrapolation: (4*fine - coarse) / 3 for second-order improvement
    richardson = (4 * fine - coarse) / 3
    
    # Error estimate
    error = abs(richardson - fine) + mp.mpf('1e-50')
    
    return richardson, error


def generate_sobol_samples(n_samples: int, dimension: int, seed: int = 42) -> List[List[float]]:
    """
    Generate Sobol QMC sequence with Owen scrambling.
    Falls back to golden ratio sequence if scipy unavailable.
    """
    if HAS_SCIPY:
        sampler = qmc.Sobol(d=dimension, scramble=True, seed=seed)
        samples = sampler.random(n_samples)
        return samples.tolist()
    else:
        # Fallback: golden ratio sequence
        phi = (1 + math.sqrt(5)) / 2
        samples = []
        for i in range(n_samples):
            point = []
            for d in range(dimension):
                coord = ((i + 0.5) * (phi ** (d + 1))) % 1.0
                point.append(coord)
            samples.append(point)
        return samples


def compute_spike_score(tau_triple_prime: mp.mpf, error_estimate: mp.mpf) -> mp.mpf:
    """
    Compute new spike ranking score: Score = error⁻¹ · log(|τ'''|)
    
    This addresses the PR #132 failure where |τ'''|/error inversely correlated
    with factor proximity. The log scaling reduces dominance of large τ''' values.
    """
    abs_tau = abs(tau_triple_prime)
    
    if abs_tau < mp.mpf('1e-100'):
        return mp.mpf('-inf')
    
    if error_estimate < mp.mpf('1e-100'):
        error_estimate = mp.mpf('1e-100')
    
    # New ranking: error⁻¹ · log(|τ'''|)
    score = (1 / error_estimate) * mp.log(abs_tau)
    
    return score


def bit_to_candidate(b: mp.mpf) -> int:
    """Convert bit position to integer candidate: candidate = 2^b"""
    return int(mp.power(2, b))


def candidate_to_bit(c: int) -> mp.mpf:
    """Convert integer candidate to bit position: b = log2(c)"""
    if c <= 0:
        return mp.mpf('-inf')
    return mp.log(c) / mp.log(2)


def run_gva_tau_hybrid_experiment(
    N: int = CHALLENGE_127,
    bit_center: float = TARGET_BIT_CENTER,
    bit_width: float = TARGET_BIT_WIDTH,
    n_samples: int = 50000,
    k_values: List[float] = [0.30, 0.35, 0.40],
    h_step: float = 0.001,
    timeout_seconds: int = 60,
    seed: int = 42,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run GVA-τ''' hybrid factorization experiment.
    
    Strategy:
    1. Generate QMC samples in bit range [bit_center - bit_width/2, bit_center + bit_width/2]
    2. For each sample, compute τ'''(b) with Richardson extrapolation
    3. Score spikes using: Score = error⁻¹ · log(|τ'''|)
    4. Use GVA 7D torus embedding to compute geodesic distances
    5. Combine spike score with geodesic score for final ranking
    6. Test top candidates with N % c == 0
    
    Args:
        N: Semiprime to factor (default: 127-bit challenge)
        bit_center: Center of bit range to scan (default: 63.5)
        bit_width: Width of bit range (default: 0.4 = ±0.2)
        n_samples: Number of QMC samples
        k_values: Geodesic exponents to test
        h_step: Step size for τ''' computation
        timeout_seconds: Maximum runtime
        seed: Random seed for reproducibility
        verbose: Enable detailed logging
    
    Returns:
        Dictionary with experiment results
    """
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    mp.mp.dps = required_dps
    
    # Compute actual q bit position for post-hoc analysis
    q_actual_bits = float(mp.log(Q_KNOWN) / mp.log(2))
    
    results = {
        'N': str(N),
        'N_bitlength': N.bit_length(),
        'precision_dps': required_dps,
        'bit_center': bit_center,
        'bit_width': bit_width,
        'bit_range': [bit_center - bit_width/2, bit_center + bit_width/2],
        'n_samples': n_samples,
        'k_values': k_values,
        'h_step': h_step,
        'timeout_seconds': timeout_seconds,
        'seed': seed,
        'timestamp': timestamp,
        'q_actual_bits': q_actual_bits,
        'success': False,
        'factors': None,
        'method': 'gva_tau_hybrid',
        'phases': []
    }
    
    if verbose:
        print("=" * 70)
        print("GVA-τ''' HYBRID FALSIFICATION EXPERIMENT")
        print("=" * 70)
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Precision: {required_dps} dps")
        print(f"Bit scan range: [{bit_center - bit_width/2:.2f}, {bit_center + bit_width/2:.2f}]")
        print(f"Target q bits: {q_actual_bits:.6f} (for post-hoc validation only)")
        print(f"QMC samples: {n_samples:,}")
        print(f"k values: {k_values}")
        print(f"h step: {h_step}")
        print(f"Timeout: {timeout_seconds}s")
        print(f"Seed: {seed}")
        print(f"Timestamp: {timestamp}")
        print("=" * 70)
        print()
    
    # Phase 1: Generate QMC samples in bit range
    if verbose:
        print("Phase 1: Generating Sobol QMC samples...")
    
    phase1_start = time.time()
    
    # Generate 2D Sobol samples: first dim for bit position, second for k selection
    sobol_samples = generate_sobol_samples(n_samples, 2, seed)
    
    # Map samples to bit positions in range
    bit_low = bit_center - bit_width / 2
    bit_high = bit_center + bit_width / 2
    
    bit_samples = []
    for sample in sobol_samples:
        # Map [0,1) to [bit_low, bit_high)
        b = bit_low + sample[0] * (bit_high - bit_low)
        bit_samples.append(b)
    
    phase1_elapsed = time.time() - phase1_start
    results['phases'].append({
        'name': 'QMC_sampling',
        'n_samples': len(bit_samples),
        'elapsed_seconds': phase1_elapsed
    })
    
    if verbose:
        print(f"  Generated {len(bit_samples):,} bit samples in [{bit_low:.2f}, {bit_high:.2f}]")
        print(f"  Phase 1 elapsed: {phase1_elapsed:.3f}s")
        print()
    
    # Phase 2: Compute τ''' spikes with Richardson extrapolation
    if verbose:
        print("Phase 2: Computing τ''' spikes with Richardson extrapolation...")
    
    phase2_start = time.time()
    
    # Use a lower working precision for τ''' computation (100 dps is sufficient)
    # This dramatically speeds up computation while maintaining accuracy
    working_dps = 100
    
    h = mp.mpf(h_step)
    spikes = []
    
    with mp.workdps(working_dps):
        for idx, b_float in enumerate(bit_samples):
            if time.time() - start_time > timeout_seconds:
                if verbose:
                    print(f"  Timeout reached at spike {idx}")
                break
            
            b = mp.mpf(b_float)
            
            # Compute τ'''(b) with Richardson extrapolation
            tau_tpp, error_estimate = compute_tau_triple_prime(N, b, h)
            
            # Compute new spike score
            score = compute_spike_score(tau_tpp, error_estimate)
            
            spikes.append({
                'b': float(b),
                'tau_triple_prime': float(tau_tpp),
                'error_estimate': float(error_estimate),
                'score': float(score) if mp.isfinite(score) else float('-inf'),
                'candidate': bit_to_candidate(b),
                'geodesic_distance': float('inf'),
                'combined_score': float(score) if mp.isfinite(score) else float('-inf')
            })
            
            if verbose and (idx + 1) % 10000 == 0:
                print(f"  Processed {idx + 1:,} / {len(bit_samples):,} samples...")
    
    phase2_elapsed = time.time() - phase2_start
    results['phases'].append({
        'name': 'tau_triple_prime_computation',
        'n_spikes': len(spikes),
        'elapsed_seconds': phase2_elapsed
    })
    
    if verbose:
        print(f"  Computed {len(spikes):,} τ''' spikes")
        print(f"  Phase 2 elapsed: {phase2_elapsed:.3f}s")
        print()
    
    # Phase 3: GVA geodesic scoring
    if verbose:
        print("Phase 3: Computing GVA geodesic scores...")
    
    phase3_start = time.time()
    
    # Embed N in 7D torus
    N_coords = embed_torus_geodesic(N, k_values[0])
    
    for spike in spikes:
        if time.time() - start_time > timeout_seconds:
            break
        
        candidate = spike['candidate']
        
        # Skip invalid candidates
        if candidate <= 1 or candidate >= N:
            spike['geodesic_distance'] = float('inf')
            spike['combined_score'] = float('-inf')
            continue
        
        # Compute geodesic distance
        cand_coords = embed_torus_geodesic(candidate, k_values[0])
        geo_dist = float(riemannian_distance(N_coords, cand_coords))
        
        spike['geodesic_distance'] = geo_dist
        
        # Combined score: spike_score + α * (1 / geodesic_distance)
        # α = 0.1 to weight geodesic contribution
        alpha = 0.1
        if geo_dist > 1e-20:
            spike['combined_score'] = spike['score'] + alpha * (1 / geo_dist)
        else:
            spike['combined_score'] = spike['score']
    
    phase3_elapsed = time.time() - phase3_start
    results['phases'].append({
        'name': 'geodesic_scoring',
        'elapsed_seconds': phase3_elapsed
    })
    
    if verbose:
        print(f"  Computed geodesic distances for {len(spikes):,} candidates")
        print(f"  Phase 3 elapsed: {phase3_elapsed:.3f}s")
        print()
    
    # Phase 4: Rank and test candidates
    if verbose:
        print("Phase 4: Ranking and testing candidates...")
    
    phase4_start = time.time()
    
    # Sort by combined score (descending)
    spikes_sorted = sorted(spikes, key=lambda x: x['combined_score'], reverse=True)
    
    # Find rank of actual q
    q_candidate = Q_KNOWN
    q_rank = None
    q_bit_error = None
    
    for rank, spike in enumerate(spikes_sorted, 1):
        candidate = spike['candidate']
        
        # Check if this is close to actual q
        bit_error = abs(spike['b'] - q_actual_bits)
        if bit_error < 0.05:  # Within 0.05 bits of actual q
            if q_rank is None or bit_error < q_bit_error:
                q_rank = rank
                q_bit_error = bit_error
        
        # Test for factorization
        if N % candidate == 0:
            p = candidate
            q = N // candidate
            
            total_elapsed = time.time() - start_time
            
            if verbose:
                print(f"\n{'*' * 70}")
                print(f"SUCCESS! Factors found at rank {rank}:")
                print(f"  p = {p}")
                print(f"  q = {q}")
                print(f"  Verification: p × q = {p * q}")
                print(f"  Match: {p * q == N}")
                print(f"  Bit position: {spike['b']:.6f}")
                print(f"  Score: {spike['combined_score']:.6f}")
                print(f"  Total elapsed: {total_elapsed:.3f}s")
                print(f"{'*' * 70}\n")
            
            results['success'] = True
            results['factors'] = {'p': str(p), 'q': str(q)}
            results['factor_rank'] = rank
            results['factor_bit_position'] = spike['b']
            results['elapsed_seconds'] = total_elapsed
            
            return results
    
    phase4_elapsed = time.time() - phase4_start
    total_elapsed = time.time() - start_time
    
    results['phases'].append({
        'name': 'candidate_testing',
        'candidates_tested': len(spikes_sorted),
        'elapsed_seconds': phase4_elapsed
    })
    
    # Record top spikes for analysis
    top_spikes = []
    for spike in spikes_sorted[:20]:
        top_spikes.append({
            'b': spike['b'],
            'tau_triple_prime': spike['tau_triple_prime'],
            'score': spike['score'],
            'combined_score': spike['combined_score'],
            'geodesic_distance': spike.get('geodesic_distance', None),
            'candidate': str(spike['candidate']),
            'bit_error_from_q': abs(spike['b'] - q_actual_bits)
        })
    
    results['top_spikes'] = top_spikes
    results['q_actual_rank'] = q_rank
    results['q_bit_error'] = q_bit_error
    results['elapsed_seconds'] = total_elapsed
    
    # Compute metrics for analysis
    if q_rank:
        results['ranking_improved'] = q_rank < 10  # Was 10th in PR #132
    else:
        results['ranking_improved'] = False
    
    # Find best spike by bit proximity to actual q
    best_proximity = float('inf')
    best_proximity_rank = None
    for rank, spike in enumerate(spikes_sorted, 1):
        proximity = abs(spike['b'] - q_actual_bits)
        if proximity < best_proximity:
            best_proximity = proximity
            best_proximity_rank = rank
    
    results['best_proximity_bits'] = best_proximity
    results['best_proximity_rank'] = best_proximity_rank
    
    if verbose:
        print(f"  Tested {len(spikes_sorted):,} candidates")
        print(f"  Phase 4 elapsed: {phase4_elapsed:.3f}s")
        print()
        print("=" * 70)
        print("EXPERIMENT COMPLETE: No factors found")
        print("=" * 70)
        print(f"Total elapsed: {total_elapsed:.3f}s")
        print(f"Best proximity to q: {best_proximity:.6f} bits (rank {best_proximity_rank})")
        if q_rank:
            print(f"Spike closest to q ranked: {q_rank}")
        print()
        print("Top 10 spikes:")
        for i, spike in enumerate(top_spikes[:10], 1):
            print(f"  {i}. b={spike['b']:.6f}, score={spike['combined_score']:.3f}, "
                  f"bit_error={spike['bit_error_from_q']:.6f}")
        print()
    
    return results


def main():
    """Run the full GVA-τ''' hybrid falsification experiment."""
    
    print()
    print("#" * 70)
    print("# GVA-τ''' HYBRID FALSIFICATION EXPERIMENT")
    print("# Target: 127-bit Challenge")
    print("# N = 137524771864208156028430259349934309717")
    print("#" * 70)
    print()
    
    # Known factors for post-hoc validation
    print(f"Known factors (for validation only):")
    print(f"  p = {P_KNOWN}")
    print(f"  q = {Q_KNOWN}")
    print(f"  p × q = {P_KNOWN * Q_KNOWN}")
    print(f"  Verify: {P_KNOWN * Q_KNOWN == CHALLENGE_127}")
    print(f"  q bits: {math.log2(Q_KNOWN):.6f}")
    print()
    
    # Run experiment with default parameters
    results = run_gva_tau_hybrid_experiment(
        N=CHALLENGE_127,
        bit_center=63.5,
        bit_width=0.4,  # Scan [63.3, 63.7] bits
        n_samples=50000,
        k_values=[0.30, 0.35, 0.40],
        h_step=0.001,
        timeout_seconds=60,
        seed=42,
        verbose=True
    )
    
    # Save results
    results_file = os.path.join(os.path.dirname(__file__), 'results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_file}")
    
    # Print verdict
    print()
    print("=" * 70)
    if results['success']:
        print("VERDICT: HYPOTHESIS NOT YET FALSIFIED")
        print(f"Factors recovered: p={results['factors']['p']}, q={results['factors']['q']}")
    else:
        print("VERDICT: HYPOTHESIS FALSIFIED")
        print(f"No factors found within {results['timeout_seconds']}s timeout")
        if results.get('q_actual_rank'):
            print(f"Spike closest to actual q ranked: {results['q_actual_rank']}")
            if results.get('ranking_improved'):
                print("Ranking IMPROVED over PR #132 baseline (was 10th)")
            else:
                print("Ranking NOT improved over PR #132 baseline")
        print(f"Best bit proximity to q: {results.get('best_proximity_bits', 'N/A'):.6f} bits")
    print("=" * 70)
    
    return results


if __name__ == '__main__':
    main()
