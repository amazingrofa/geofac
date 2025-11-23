"""
GVA 5D Falsification Experiment
================================

Tests the GVA hypothesis: Can 5D toroidal embedding with geodesic distance
and Jacobian-weighted QMC sampling efficiently factor RSA moduli?

Falsification targets: RSA-100, RSA-129
Validation baseline: 127-bit CHALLENGE_127

Key Claims to Test:
- 15-20% density enhancement from Jacobian weighting
- 100x speedup from geodesic guidance
- Correlation between geodesic distance minima and actual factors

Methodology:
- 5D torus embedding with golden ratio quasi-periodicity
- Riemannian geodesic distance with curvature κ(n) = d(n)·ln(n+1)/e²
- QMC sampling with Sobol sequences
- Jacobian scale factors: sin⁴θ₁ · sin²θ₂ · sinθ₃

Validation range: [10^14, 10^18] per VALIDATION_GATES.md
Whitelist: 127-bit CHALLENGE_127 = 137524771864208156028430259349934309717

No classical fallbacks. Deterministic/quasi-deterministic only.
"""

import mpmath as mp
from typing import Tuple, Optional, List, Dict, Any
import time
import json
from datetime import datetime
from math import log, sqrt, e, sin, pi
import sys

# Try scipy for Sobol, fallback to simple QMC
try:
    from scipy.stats import qmc
    HAS_SCIPY_QMC = True
except ImportError:
    HAS_SCIPY_QMC = False
    print("Warning: scipy.stats.qmc not available, using simple golden ratio QMC")

# Try numpy for bootstrap, fallback to basic resampling
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: numpy not available, bootstrap CIs disabled")

# Validation gates
CHALLENGE_127 = 137524771864208156028430259349934309717
RANGE_MIN = 10**14
RANGE_MAX = 10**18

# RSA challenge numbers
RSA_100 = 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
RSA_129 = 114381625757888867669235779976146612010218296721242362562561842935706935245733897830597123563958705058989075147599290026879543541


def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bitLength() × 4 + 200)
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def embed_5d_torus(n: int, k: float) -> List[mp.mpf]:
    """
    Embed integer n into 5D torus using golden ratio quasi-periodicity.
    
    Args:
        n: Integer to embed
        k: Geodesic exponent in [0.25, 0.45]
        
    Returns:
        5D torus coordinates [0,1)^5
    """
    phi = mp.mpf(1 + mp.sqrt(5)) / 2  # Golden ratio
    
    coords = []
    for d in range(5):
        phi_power = phi ** (d + 1)
        coord = mp.fmod(n * phi_power, 1)
        
        # Apply geodesic exponent
        if k != 1.0:
            coord = mp.power(coord, k)
            coord = mp.fmod(coord, 1)
        
        coords.append(coord)
    
    return coords


def jacobian_weight(theta: List[float]) -> float:
    """
    Compute Jacobian-derived scale factor for 5D spherical coordinates.
    
    Weight: w(θ) = sin⁴θ₁ · sin²θ₂ · sinθ₃
    
    This approximates the volume element weighting for proper density sampling.
    
    Args:
        theta: Angular coordinates [θ₁, θ₂, θ₃, θ₄] (skip θ₀)
        
    Returns:
        Jacobian weight in [0, 1]
    """
    if len(theta) < 3:
        return 1.0
    
    # Map [0,1) torus coords to [0, π) angular range
    theta_1 = theta[0] * pi
    theta_2 = theta[1] * pi
    theta_3 = theta[2] * pi
    
    weight = (sin(theta_1) ** 4) * (sin(theta_2) ** 2) * sin(theta_3)
    return weight


def curvature_term(n: int) -> mp.mpf:
    """
    Compute curvature term κ(n) = d(n) · ln(n+1) / e²
    
    d(n) estimated as 2^(ω(n)) where ω(n) ≈ log(log(n))
    
    Args:
        n: Integer for curvature computation
        
    Returns:
        Curvature term κ(n)
    """
    if n <= 1:
        return mp.mpf(1)
    
    # Estimate ω(n) ≈ log(log(n))
    log_log_n = mp.log(mp.log(n + 2))  # +2 to avoid log(1)
    omega = log_log_n
    
    # d(n) ≈ 2^ω(n)
    divisor_estimate = mp.power(2, omega)
    
    # κ(n) = d(n) · ln(n+1) / e²
    kappa = divisor_estimate * mp.log(n + 1) / (mp.e ** 2)
    
    return kappa


def riemannian_distance_5d(p1: List[mp.mpf], p2: List[mp.mpf], 
                           kappa_weights: Optional[List[mp.mpf]] = None) -> mp.mpf:
    """
    Compute Riemannian geodesic distance on 5D torus.
    
    Uses curvature-weighted metric with periodic boundaries.
    
    Args:
        p1, p2: 5D torus coordinates
        kappa_weights: Optional per-dimension curvature weights
        
    Returns:
        Riemannian distance
    """
    if len(p1) != 5 or len(p2) != 5:
        raise ValueError("Points must be 5D")
    
    if kappa_weights is None:
        kappa_weights = [mp.mpf(1)] * 5
    
    dist_sq = mp.mpf(0)
    for i, (c1, c2, kappa) in enumerate(zip(p1, p2, kappa_weights)):
        # Torus distance: min distance considering wrapping
        diff = abs(c1 - c2)
        wrap_diff = mp.mpf(1) - diff
        min_diff = min(diff, wrap_diff)
        
        dist_sq += kappa * min_diff * min_diff
    
    return mp.sqrt(dist_sq)


def generate_sobol_samples(n_samples: int, dimension: int, seed: int = 42) -> List[List[float]]:
    """
    Generate Sobol QMC sequence.
    
    Falls back to golden ratio sequence if scipy unavailable.
    
    Args:
        n_samples: Number of samples
        dimension: Dimension of samples
        seed: Random seed for reproducibility
        
    Returns:
        List of n_samples points in [0,1)^dimension
    """
    if HAS_SCIPY_QMC:
        sampler = qmc.Sobol(d=dimension, scramble=True, seed=seed)
        samples = sampler.random(n_samples)
        return [list(s) for s in samples]
    else:
        # Fallback: golden ratio sequence
        phi = (1 + sqrt(5)) / 2
        samples = []
        for i in range(n_samples):
            point = []
            for d in range(dimension):
                coord = ((i + 0.5) * (phi ** (d + 1))) % 1.0
                point.append(coord)
            samples.append(point)
        return samples


def apply_jacobian_weighting(samples: List[List[float]], 
                            accept_rate: float = 0.5) -> List[List[float]]:
    """
    Apply Jacobian weighting to samples via rejection sampling.
    
    Keep samples with probability proportional to jacobian_weight().
    
    Args:
        samples: Input QMC samples
        accept_rate: Target acceptance rate (controls w_max normalization)
        
    Returns:
        Filtered samples with Jacobian weighting
    """
    if not samples:
        return []
    
    # Find max weight for normalization
    weights = [jacobian_weight(s) for s in samples]
    w_max = max(weights) if weights else 1.0
    
    # Scale to achieve target acceptance rate
    w_max = w_max / accept_rate if w_max > 0 else 1.0
    
    # Rejection sampling
    filtered = []
    for sample, weight in zip(samples, weights):
        # Accept with probability weight/w_max
        # Deterministic: use sample hash as pseudo-random value
        pseudo_rand = (hash(tuple(sample)) % 10000) / 10000.0
        if pseudo_rand < weight / w_max:
            filtered.append(sample)
    
    return filtered


def gva_5d_factor_search(N: int, 
                        k_values: List[float] = [0.30, 0.35, 0.40],
                        max_samples: int = 1000000,
                        use_jacobian: bool = True,
                        use_geodesic: bool = True,
                        seed: int = 42,
                        verbose: bool = True) -> Dict[str, Any]:
    """
    GVA 5D factorization with geodesic guidance and Jacobian weighting.
    
    Tests the core GVA hypothesis on RSA challenge numbers.
    
    Args:
        N: Semiprime to factor (RSA-100, RSA-129, or CHALLENGE_127)
        k_values: Geodesic exponents to test
        max_samples: Maximum QMC samples per k value
        use_jacobian: Apply Jacobian weighting to QMC samples
        use_geodesic: Use geodesic distance for guidance
        seed: Random seed for reproducibility
        verbose: Enable detailed logging
        
    Returns:
        Dictionary with results and metrics
    """
    # Validate input
    if N not in [RSA_100, RSA_129, CHALLENGE_127]:
        if not (RANGE_MIN <= N <= RANGE_MAX):
            raise ValueError(f"N must be RSA-100, RSA-129, CHALLENGE_127, or in [{RANGE_MIN}, {RANGE_MAX}]")
    
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    mp.mp.dps = required_dps
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"GVA 5D Falsification Experiment")
        print(f"{'='*70}")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Adaptive precision: {required_dps} dps")
        print(f"Max samples per k: {max_samples:,}")
        print(f"Jacobian weighting: {use_jacobian}")
        print(f"Geodesic guidance: {use_geodesic}")
        print(f"Random seed: {seed}")
        print(f"Timestamp: {timestamp}")
        print(f"{'='*70}\n")
    
    # Quick check for even numbers
    if N % 2 == 0:
        elapsed = time.time() - start_time
        return {
            'N': N,
            'success': True,
            'p': 2,
            'q': N // 2,
            'method': 'trivial',
            'elapsed_seconds': elapsed,
            'timestamp': timestamp
        }
    
    sqrt_N = int(mp.sqrt(N))
    
    # Determine search window
    bit_length = N.bit_length()
    if bit_length <= 60:
        base_window = max(10000, sqrt_N // 5000)
    elif bit_length <= 130:
        base_window = max(100000, sqrt_N // 1000)
    else:
        base_window = max(1000000, sqrt_N // 500)
    
    if verbose:
        print(f"sqrt(N) ≈ {sqrt_N}")
        print(f"Search window: ±{base_window:,}\n")
    
    results = {
        'N': N,
        'N_bitlength': bit_length,
        'precision_dps': required_dps,
        'sqrt_N': sqrt_N,
        'search_window': base_window,
        'max_samples': max_samples,
        'k_values': k_values,
        'use_jacobian': use_jacobian,
        'use_geodesic': use_geodesic,
        'seed': seed,
        'timestamp': timestamp,
        'success': False,
        'factors': None,
        'method': 'gva_5d',
        'experiments': []
    }
    
    # Test each k value
    for k_idx, k in enumerate(k_values):
        if verbose:
            print(f"\n--- Testing k = {k} ({k_idx + 1}/{len(k_values)}) ---")
        
        exp_start = time.time()
        
        # Embed N in 5D torus
        N_coords = embed_5d_torus(N, k)
        
        # Compute curvature weights
        kappa = curvature_term(N)
        kappa_weights = [kappa] * 5
        
        if verbose:
            print(f"N embedded at: [{', '.join(f'{float(c):.6f}' for c in N_coords[:3])}, ...]")
            print(f"Curvature κ(N) = {float(kappa):.6e}")
        
        # Generate QMC samples
        if verbose:
            print(f"\nGenerating {max_samples:,} Sobol samples...")
        
        samples_5d = generate_sobol_samples(max_samples, 5, seed + k_idx)
        
        # Apply Jacobian weighting if enabled
        if use_jacobian:
            if verbose:
                print(f"Applying Jacobian weighting...")
            samples_weighted = apply_jacobian_weighting(samples_5d, accept_rate=0.5)
            if verbose:
                density_enhancement = len(samples_weighted) / (len(samples_5d) * 0.5) - 1
                print(f"Samples after weighting: {len(samples_weighted):,}")
                print(f"Density enhancement: {density_enhancement:.1%}")
        else:
            samples_weighted = samples_5d
        
        # Map samples to candidate factors
        if verbose:
            print(f"\nTesting candidates...")
        
        candidates_tested = 0
        min_distance = float('inf')
        min_distance_candidate = None
        distances = []
        
        for sample_idx, sample in enumerate(samples_weighted):
            if candidates_tested >= max_samples:
                break
            
            # Map sample to candidate near sqrt(N)
            # Use first dimension to determine offset
            offset = int((sample[0] - 0.5) * 2 * base_window)
            candidate = sqrt_N + offset
            
            # Skip invalid candidates
            if candidate <= 1 or candidate >= N:
                continue
            if candidate % 2 == 0:  # Skip even
                continue
            
            candidates_tested += 1
            
            # Compute geodesic distance if enabled
            if use_geodesic:
                cand_coords = embed_5d_torus(candidate, k)
                dist = float(riemannian_distance_5d(N_coords, cand_coords, kappa_weights))
                distances.append((candidate, dist))
                
                if dist < min_distance:
                    min_distance = dist
                    min_distance_candidate = candidate
            
            # Test for factorization
            if N % candidate == 0:
                p = candidate
                q = N // candidate
                exp_elapsed = time.time() - exp_start
                total_elapsed = time.time() - start_time
                
                if verbose:
                    print(f"\n{'*'*70}")
                    print(f"SUCCESS! Factors found:")
                    print(f"p = {p}")
                    print(f"q = {q}")
                    print(f"Verification: p × q = {p * q}")
                    print(f"Match: {p * q == N}")
                    print(f"Candidates tested: {candidates_tested:,}")
                    print(f"Time for this k: {exp_elapsed:.2f}s")
                    print(f"Total time: {total_elapsed:.2f}s")
                    print(f"{'*'*70}\n")
                
                results['success'] = True
                results['factors'] = {'p': p, 'q': q}
                results['k_success'] = k
                results['candidates_tested'] = candidates_tested
                results['min_distance'] = min_distance
                results['elapsed_seconds'] = total_elapsed
                
                return results
            
            # Progress reporting
            if verbose and candidates_tested % 10000 == 0:
                print(f"  Tested {candidates_tested:,} candidates, min distance: {min_distance:.6e}")
        
        exp_elapsed = time.time() - exp_start
        
        # Record experiment metrics
        exp_results = {
            'k': k,
            'candidates_tested': candidates_tested,
            'samples_generated': len(samples_5d),
            'samples_weighted': len(samples_weighted),
            'min_distance': min_distance,
            'min_distance_candidate': min_distance_candidate,
            'elapsed_seconds': exp_elapsed,
            'density_enhancement': (len(samples_weighted) / (len(samples_5d) * 0.5) - 1) if use_jacobian else 0.0
        }
        
        # Compute variance if enough samples
        if len(distances) > 100 and HAS_NUMPY:
            dist_values = [d for _, d in distances[:1000]]  # First 1000
            variance = float(np.var(dist_values))
            exp_results['distance_variance'] = variance
        
        results['experiments'].append(exp_results)
        
        if verbose:
            print(f"Completed k={k}: {candidates_tested:,} candidates in {exp_elapsed:.2f}s")
            print(f"Min distance: {min_distance:.6e}")
    
    # Final summary
    total_elapsed = time.time() - start_time
    results['elapsed_seconds'] = total_elapsed
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"Experiment completed: No factors found")
        print(f"Total candidates tested: {sum(e['candidates_tested'] for e in results['experiments']):,}")
        print(f"Total time: {total_elapsed:.2f}s")
        print(f"{'='*70}\n")
    
    return results


def bootstrap_confidence_interval(data: List[float], n_bootstrap: int = 1000, 
                                  alpha: float = 0.05) -> Tuple[float, float, float]:
    """
    Compute bootstrap confidence interval for mean.
    
    Args:
        data: Sample data
        n_bootstrap: Number of bootstrap resamples
        alpha: Significance level (0.05 for 95% CI)
        
    Returns:
        (mean, lower_bound, upper_bound)
    """
    if not HAS_NUMPY:
        mean = sum(data) / len(data) if data else 0.0
        return (mean, mean, mean)
    
    data_array = np.array(data)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        resample = np.random.choice(data_array, size=len(data_array), replace=True)
        bootstrap_means.append(np.mean(resample))
    
    bootstrap_means = np.array(bootstrap_means)
    mean = np.mean(data_array)
    lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    return (float(mean), float(lower), float(upper))


def run_falsification_experiment(target: str = 'RSA-100', 
                                 max_samples: int = 1000000,
                                 save_results: bool = True) -> Dict[str, Any]:
    """
    Run complete falsification experiment on specified target.
    
    Args:
        target: 'RSA-100', 'RSA-129', or 'CHALLENGE_127'
        max_samples: Maximum QMC samples per k value
        save_results: Save results to JSON file
        
    Returns:
        Complete results dictionary
    """
    target_map = {
        'RSA-100': RSA_100,
        'RSA-129': RSA_129,
        'CHALLENGE_127': CHALLENGE_127
    }
    
    if target not in target_map:
        raise ValueError(f"Target must be one of {list(target_map.keys())}")
    
    N = target_map[target]
    
    print(f"\n{'#'*70}")
    print(f"# GVA 5D Falsification Experiment: {target}")
    print(f"{'#'*70}\n")
    
    # Run main experiment with all features
    results = gva_5d_factor_search(
        N=N,
        k_values=[0.30, 0.35, 0.40],
        max_samples=max_samples,
        use_jacobian=True,
        use_geodesic=True,
        seed=42,
        verbose=True
    )
    
    # Add summary
    results['target_name'] = target
    results['falsification_verdict'] = 'FALSIFIED' if not results['success'] else 'NOT_YET_FALSIFIED'
    
    # Save results
    if save_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"results_{target}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {filename}")
    
    return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='GVA 5D Falsification Experiment')
    parser.add_argument('--target', type=str, default='CHALLENGE_127',
                       choices=['RSA-100', 'RSA-129', 'CHALLENGE_127'],
                       help='Factorization target')
    parser.add_argument('--samples', type=int, default=100000,
                       help='Maximum QMC samples per k value')
    parser.add_argument('--no-save', action='store_true',
                       help='Do not save results to file')
    
    args = parser.parse_args()
    
    results = run_falsification_experiment(
        target=args.target,
        max_samples=args.samples,
        save_results=not args.no_save
    )
    
    # Print final verdict
    print(f"\n{'='*70}")
    print(f"VERDICT: {results['falsification_verdict']}")
    print(f"{'='*70}")
