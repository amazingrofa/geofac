"""
Newton-Raphson Microkernel GVA Implementation
==============================================

Implements GVA with embedded Newton-Raphson refinement inside the QMC scoring loop.

Hypothesis: Embedding NR directly inside each QMC iteration improves peak detection
by locally refining promising peaks on-the-fly, rather than in a separate post-phase.

Key features:
- NR microkernel triggers on top candidates (z-score > 1.5 or top 5%)
- 1-2 NR steps per triggered candidate
- Safety stops: |f'| < epsilon or update escapes scan band
- Same precision as main scoring path
- Full telemetry: logs (raw_k, raw_S) -> (nr_k, nr_S, delta_k, delta_S)

Validation range: [10^14, 10^18] per VALIDATION_GATES.md
Whitelist: 127-bit CHALLENGE_127
"""

import mpmath as mp
from typing import Tuple, Optional, List, Dict
import time
from math import log, sqrt, e
from dataclasses import dataclass, field

# Configure high precision
mp.mp.dps = 50

# Validation gates (from gva_factorization.py)
GATE_1_30BIT = 1073217479  # 32749 × 32771
GATE_2_60BIT = 1152921470247108503  # 1073741789 × 1073741827
CHALLENGE_127 = 137524771864208156028430259349934309717

# Operational range
RANGE_MIN = 10**14
RANGE_MAX = 10**18


@dataclass
class NRConfig:
    """Newton-Raphson microkernel configuration."""
    enabled: bool = True
    max_steps: int = 1  # Default 1, allow 2 for best candidates
    trigger_zscore: float = 1.5  # Trigger if score >= mu + 1.5*sigma
    trigger_percentile: float = 0.05  # Or if in top 5%
    tolerance: float = 1e-6  # Stop if relative improvement < this
    epsilon: float = 1e-12  # Derivative safety threshold
    max_refines_per_batch: int = 64  # Cap refines per batch
    
    
@dataclass
class NRTelemetry:
    """Telemetry for NR refinement."""
    raw_candidate: int = 0
    raw_score: float = 0.0
    refined_candidate: int = 0
    refined_score: float = 0.0
    delta_candidate: int = 0
    delta_score: float = 0.0
    nr_steps_taken: int = 0
    improvement: bool = False
    

@dataclass
class ExperimentMetrics:
    """Metrics for comparing QMC-only vs QMC+NR."""
    total_candidates: int = 0
    candidates_triggered: int = 0
    candidates_improved: int = 0
    total_nr_steps: int = 0
    total_time: float = 0.0
    nr_overhead_time: float = 0.0
    top_scores: List[float] = field(default_factory=list)
    telemetry: List[NRTelemetry] = field(default_factory=list)
    factor_found: bool = False
    factor_candidate: int = 0
    factor_score: float = 0.0
    

def adaptive_precision(N: int) -> int:
    """
    Compute adaptive precision based on N's bit length.
    Formula: max(50, N.bitLength() × 4 + 200)
    
    Rationale: The formula ensures adequate precision for high-precision arithmetic:
    - Base 200 digits provides buffer for intermediate calculations
    - 4x bit length accounts for the fact that operations like sqrt, trig
      functions, and iterative algorithms can lose precision
    - Minimum of 50 ensures reasonable precision for small numbers
    
    This formula is consistent with gva_factorization.py and CODING_STYLE.md.
    """
    bit_length = N.bit_length()
    return max(50, bit_length * 4 + 200)


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """
    Embed integer n into a 7D torus using geodesic mapping.
    
    Uses golden ratio (φ) and its powers to create quasi-periodic embedding
    that reveals factorization structure through Riemannian distance minimization.
    """
    phi = mp.mpf(1 + mp.sqrt(5)) / 2  # Golden ratio
    
    coords = []
    for d in range(dimensions):
        phi_power = phi ** (d + 1)
        coord = mp.fmod(n * phi_power, 1)
        
        if k != 1.0:
            coord = mp.power(coord, k)
            coord = mp.fmod(coord, 1)
        
        coords.append(coord)
    
    return coords


def riemannian_distance(p1: List[mp.mpf], p2: List[mp.mpf]) -> mp.mpf:
    """
    Compute Riemannian geodesic distance on 7D torus.
    Uses flat torus metric with periodic boundary conditions.
    """
    if len(p1) != len(p2):
        raise ValueError("Points must have same dimension")
    
    dist_sq = mp.mpf(0)
    for c1, c2 in zip(p1, p2):
        diff = abs(c1 - c2)
        wrap_diff = mp.mpf(1) - diff
        min_diff = min(diff, wrap_diff)
        dist_sq += min_diff * min_diff
    
    return mp.sqrt(dist_sq)


def compute_score_objective(candidate: int, N: int, N_coords: List[mp.mpf], 
                             k: float) -> Tuple[float, float]:
    """
    Compute the scoring objective and its numerical derivative.
    
    Objective: Negative Riemannian distance (we want to minimize distance,
    so higher score = smaller distance = better candidate).
    
    Returns: (f, f') where f is the objective at candidate, f' is the derivative.
    """
    # Compute score at candidate
    cand_coords = embed_torus_geodesic(candidate, k)
    dist = riemannian_distance(N_coords, cand_coords)
    score = -float(dist)  # Negative because we maximize score (minimize distance)
    
    # Numerical derivative using central difference
    # f'(x) ≈ (f(x+h) - f(x-h)) / (2h)
    h = 1  # Integer step for candidates
    
    cand_plus = embed_torus_geodesic(candidate + h, k)
    dist_plus = riemannian_distance(N_coords, cand_plus)
    score_plus = -float(dist_plus)
    
    cand_minus = embed_torus_geodesic(candidate - h, k)
    dist_minus = riemannian_distance(N_coords, cand_minus)
    score_minus = -float(dist_minus)
    
    derivative = (score_plus - score_minus) / (2 * h)
    
    return score, derivative


def nr_refine(candidate: int, N: int, N_coords: List[mp.mpf], k: float,
              config: NRConfig, window_min: int, window_max: int) -> Tuple[int, float, NRTelemetry]:
    """
    Apply Newton-Raphson refinement to a candidate.
    
    NR step: x_new = x - f(x)/f'(x)
    
    Here we want to maximize the score (minimize distance), so we use:
    x_new = x + f(x)/|f'(x)| to move toward higher scores when f < 0.
    
    However, since our objective is distance-based and highly nonlinear in integer space,
    we instead use NR to find the zero of the gradient (stationary point).
    
    Returns: (refined_candidate, refined_score, telemetry)
    """
    # Get initial score
    initial_score, _ = compute_score_objective(candidate, N, N_coords, k)
    
    telemetry = NRTelemetry(
        raw_candidate=candidate,
        raw_score=initial_score
    )
    
    x = float(candidate)
    best_x = candidate
    best_score = initial_score
    
    for step in range(config.max_steps):
        # Compute gradient and Hessian approximation at current position
        # We use numerical differences
        int_x = int(round(x))
        if int_x < window_min or int_x > window_max:
            break
            
        score, deriv = compute_score_objective(int_x, N, N_coords, k)
        
        # Safety check: skip if derivative is too small
        if abs(deriv) < config.epsilon:
            break
        
        # NR update to find stationary point (where derivative = 0)
        # We approximate the second derivative (Hessian) numerically
        h = 1
        _, deriv_plus = compute_score_objective(int_x + h, N, N_coords, k)
        _, deriv_minus = compute_score_objective(int_x - h, N, N_coords, k)
        second_deriv = (deriv_plus - deriv_minus) / (2 * h)
        
        # Avoid division by zero or near-zero
        if abs(second_deriv) < config.epsilon:
            # Use gradient ascent as fallback
            step_size = 1.0 if deriv > 0 else -1.0
            new_x = x + step_size
        else:
            # Standard NR step to find gradient zero
            new_x = x - deriv / second_deriv
        
        # Bound check
        new_int_x = int(round(new_x))
        if new_int_x < window_min or new_int_x > window_max:
            break
        
        # Evaluate new position
        new_score, _ = compute_score_objective(new_int_x, N, N_coords, k)
        
        telemetry.nr_steps_taken = step + 1
        
        # Keep best so far
        if new_score > best_score:
            best_x = new_int_x
            best_score = new_score
        
        # Check convergence
        if best_score > initial_score:
            rel_improvement = (best_score - initial_score) / abs(initial_score) if initial_score != 0 else float('inf')
            if rel_improvement < config.tolerance:
                break
        
        x = new_x
    
    # Fill telemetry
    telemetry.refined_candidate = best_x
    telemetry.refined_score = best_score
    telemetry.delta_candidate = best_x - candidate
    telemetry.delta_score = best_score - initial_score
    telemetry.improvement = best_score > initial_score
    
    return best_x, best_score, telemetry


def gva_factor_search_with_nr(N: int, k_values: Optional[List[float]] = None,
                               max_candidates: int = 10000,
                               nr_config: Optional[NRConfig] = None,
                               verbose: bool = False,
                               allow_any_range: bool = False) -> Tuple[Optional[Tuple[int, int]], ExperimentMetrics]:
    """
    Factor semiprime N using GVA with embedded Newton-Raphson microkernel.
    
    This is the core experiment: NR refinement is embedded directly in the
    QMC scoring loop, triggered on promising candidates.
    
    Args:
        N: Semiprime to factor
        k_values: Geodesic exponents to test
        max_candidates: Maximum candidates to test per k value
        nr_config: Newton-Raphson configuration (None = NR disabled for baseline)
        verbose: Enable detailed logging
        allow_any_range: Allow N outside operational range
        
    Returns:
        Tuple of (factors or None, metrics)
    """
    metrics = ExperimentMetrics()
    
    # Validate input range
    if not allow_any_range and N != CHALLENGE_127 and not (RANGE_MIN <= N <= RANGE_MAX):
        raise ValueError(f"N must be in [{RANGE_MIN}, {RANGE_MAX}] or CHALLENGE_127")
    
    # Quick check for even numbers
    if N % 2 == 0:
        metrics.factor_found = True
        metrics.factor_candidate = 2
        return ((2, N // 2), metrics)
    
    # Default NR config (disabled for baseline)
    if nr_config is None:
        nr_config = NRConfig(enabled=False)
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    with mp.workdps(required_dps):
        if verbose:
            nr_status = "ENABLED" if nr_config.enabled else "DISABLED"
            print(f"GVA+NR Factorization (NR: {nr_status})")
            print(f"N = {N}")
            print(f"Bit length: {N.bit_length()}")
            print(f"Adaptive precision: {required_dps} dps")
            if nr_config.enabled:
                print(f"NR max steps: {nr_config.max_steps}")
                print(f"NR trigger: z-score >= {nr_config.trigger_zscore} or top {nr_config.trigger_percentile*100}%")
        
        # Default k values
        if k_values is None:
            k_values = [0.30, 0.35, 0.40]
        
        sqrt_N = int(mp.sqrt(N))
        
        # Search window scaling
        bit_length = N.bit_length()
        if bit_length <= 40:
            base_window = max(1000, sqrt_N // 1000)
        elif bit_length <= 60:
            base_window = max(10000, sqrt_N // 5000)
        elif bit_length <= 85:
            base_window = max(100000, sqrt_N // 1000)
        elif bit_length <= 92:
            base_window = max(200000, sqrt_N // 500)
        elif bit_length <= 99:
            base_window = max(300000, sqrt_N // 400)
        else:
            base_window = max(400000, sqrt_N // 300)
        
        window_min = max(2, sqrt_N - base_window)
        window_max = min(N - 1, sqrt_N + base_window)
        
        if verbose:
            print(f"Search window: [{window_min}, {window_max}]")
        
        start_time = time.time()
        all_scores = []  # For z-score computation
        
        for k in k_values:
            if verbose:
                print(f"\nTesting k = {k}")
            
            # Embed N in 7D torus
            N_coords = embed_torus_geodesic(N, k)
            
            # Collect candidate scores for this k value
            k_scores = []
            k_candidates = []
            
            # Phase 1: Sample candidates and compute initial scores
            # Use adaptive sampling strategy
            offsets = _generate_sample_offsets(bit_length, base_window)
            
            for offset in offsets:
                candidate = sqrt_N + offset
                
                # Skip invalid candidates
                if candidate <= 1 or candidate >= N:
                    continue
                if candidate % 2 == 0 or candidate % 3 == 0 or candidate % 5 == 0:
                    continue
                
                metrics.total_candidates += 1
                
                # Compute geodesic distance (score = -distance for maximization)
                cand_coords = embed_torus_geodesic(candidate, k)
                dist = riemannian_distance(N_coords, cand_coords)
                score = -float(dist)  # Higher score = smaller distance
                
                k_scores.append(score)
                k_candidates.append(candidate)
                all_scores.append(score)
            
            if not k_scores:
                continue
                
            # Compute statistics for triggering
            mean_score = sum(k_scores) / len(k_scores)
            variance = sum((s - mean_score)**2 for s in k_scores) / len(k_scores)
            std_score = sqrt(variance) if variance > 0 else 1e-10
            
            # Sort candidates by score (descending)
            scored_candidates = list(zip(k_scores, k_candidates))
            scored_candidates.sort(reverse=True)
            
            # Determine trigger thresholds
            zscore_threshold = mean_score + nr_config.trigger_zscore * std_score
            percentile_idx = max(1, int(len(scored_candidates) * nr_config.trigger_percentile))
            percentile_threshold = scored_candidates[percentile_idx - 1][0] if scored_candidates else zscore_threshold
            
            nr_trigger = max(zscore_threshold, percentile_threshold)
            
            if verbose:
                print(f"  Sampled {len(k_candidates)} candidates")
                print(f"  Score stats: mean={mean_score:.6f}, std={std_score:.6f}")
                print(f"  NR trigger threshold: {nr_trigger:.6f}")
            
            # Phase 2: Search top candidates with optional NR refinement
            nr_refines_this_batch = 0
            
            for score, candidate in scored_candidates[:max(50, max_candidates // 10)]:
                # Apply NR refinement if enabled and triggered
                nr_start_time = time.time()
                
                if nr_config.enabled and score >= nr_trigger and nr_refines_this_batch < nr_config.max_refines_per_batch:
                    metrics.candidates_triggered += 1
                    nr_refines_this_batch += 1
                    
                    # Apply NR refinement
                    refined_candidate, refined_score, telemetry = nr_refine(
                        candidate, N, N_coords, k, nr_config, window_min, window_max
                    )
                    
                    metrics.total_nr_steps += telemetry.nr_steps_taken
                    metrics.telemetry.append(telemetry)
                    
                    if telemetry.improvement:
                        metrics.candidates_improved += 1
                        if verbose and telemetry.delta_score > 0.001:
                            print(f"    NR improved: {candidate} -> {refined_candidate} "
                                  f"(Δscore={telemetry.delta_score:.6f})")
                    
                    # Use refined candidate if better
                    if refined_score > score:
                        candidate = refined_candidate
                        score = refined_score
                
                metrics.nr_overhead_time += time.time() - nr_start_time
                metrics.top_scores.append(score)
                
                # Test candidate for factorization
                if N % candidate == 0:
                    p = candidate
                    q = N // candidate
                    
                    metrics.factor_found = True
                    metrics.factor_candidate = candidate
                    metrics.factor_score = score
                    metrics.total_time = time.time() - start_time
                    
                    if verbose:
                        print(f"\nFactor found:")
                        print(f"  p = {p}")
                        print(f"  q = {q}")
                        print(f"  Candidates tested: {metrics.total_candidates}")
                        print(f"  NR triggers: {metrics.candidates_triggered}")
                        print(f"  NR improvements: {metrics.candidates_improved}")
                        print(f"  Total time: {metrics.total_time:.3f}s")
                        print(f"  NR overhead: {metrics.nr_overhead_time:.3f}s")
                    
                    return ((p, q), metrics)
            
            # Phase 3: Local search around top candidates (as in original GVA)
            for score, center_candidate in scored_candidates[:50]:
                local_window = 1500 if bit_length <= 60 else 3000
                
                for local_offset in range(-local_window, local_window + 1):
                    candidate = center_candidate + local_offset
                    
                    if candidate <= 1 or candidate >= N:
                        continue
                    if candidate % 2 == 0 or candidate % 3 == 0 or candidate % 5 == 0:
                        continue
                    
                    metrics.total_candidates += 1
                    
                    if N % candidate == 0:
                        p = candidate
                        q = N // candidate
                        
                        metrics.factor_found = True
                        metrics.factor_candidate = candidate
                        metrics.total_time = time.time() - start_time
                        
                        if verbose:
                            print(f"\nFactor found (local search):")
                            print(f"  p = {p}")
                            print(f"  q = {q}")
                        
                        return ((p, q), metrics)
        
        metrics.total_time = time.time() - start_time
        
        if verbose:
            print(f"\nNo factors found")
            print(f"  Candidates tested: {metrics.total_candidates}")
            print(f"  NR triggers: {metrics.candidates_triggered}")
            print(f"  NR improvements: {metrics.candidates_improved}")
            print(f"  Total time: {metrics.total_time:.3f}s")
            print(f"  NR overhead: {metrics.nr_overhead_time:.3f}s")
    
    return (None, metrics)


def _generate_sample_offsets(bit_length: int, window: int) -> List[int]:
    """Generate sample offsets based on bit length (matching GVA strategy)."""
    offsets = []
    
    if bit_length <= 40:
        sample_size = min(500, window * 2)
        sample_step = max(1, (2 * window) // sample_size)
        offsets = [sample_step * i - window for i in range(sample_size)]
    elif bit_length <= 60:
        # Inner region
        inner_bound = min(10000, window // 2)
        inner_step = 50
        for offset in range(-inner_bound, inner_bound + 1, inner_step):
            offsets.append(offset)
        # Outer regions
        outer_sample = 200
        if window > inner_bound and outer_sample > 0:
            outer_step = max(100, (window - inner_bound) // outer_sample)
            for offset in range(-window, -inner_bound, outer_step):
                offsets.append(offset)
            for offset in range(inner_bound, window + 1, outer_step):
                offsets.append(offset)
    else:
        # Large numbers: dense sampling near sqrt(N)
        inner_bound = 5000
        inner_step = 10
        for offset in range(-inner_bound, inner_bound + 1, inner_step):
            offsets.append(offset)
        # Middle region
        middle_bound = 50000
        middle_step = 200
        for offset in range(-middle_bound, -inner_bound, middle_step):
            offsets.append(offset)
        for offset in range(inner_bound, middle_bound + 1, middle_step):
            offsets.append(offset)
        # Outer region
        outer_sample = 200
        if window > middle_bound and outer_sample > 0:
            outer_step = max(1000, (window - middle_bound) // outer_sample)
            for offset in range(-window, -middle_bound, outer_step):
                offsets.append(offset)
            for offset in range(middle_bound, window + 1, outer_step):
                offsets.append(offset)
    
    return offsets


if __name__ == "__main__":
    print("=" * 70)
    print("NR Microkernel GVA - Quick Validation")
    print("=" * 70)
    
    # Test Gate 1 with NR disabled (baseline)
    print("\n1. Gate 1 (30-bit) - Baseline (NR disabled):")
    result, metrics = gva_factor_search_with_nr(
        GATE_1_30BIT,
        nr_config=NRConfig(enabled=False),
        verbose=True,
        allow_any_range=True
    )
    if result:
        print(f"✓ Success: {GATE_1_30BIT} = {result[0]} × {result[1]}")
    else:
        print("✗ Failed")
    
    # Test Gate 1 with NR enabled
    print("\n2. Gate 1 (30-bit) - NR enabled (1 step):")
    result, metrics = gva_factor_search_with_nr(
        GATE_1_30BIT,
        nr_config=NRConfig(enabled=True, max_steps=1),
        verbose=True,
        allow_any_range=True
    )
    if result:
        print(f"✓ Success: {GATE_1_30BIT} = {result[0]} × {result[1]}")
        print(f"  NR triggers: {metrics.candidates_triggered}")
        print(f"  NR improvements: {metrics.candidates_improved}")
    else:
        print("✗ Failed")
