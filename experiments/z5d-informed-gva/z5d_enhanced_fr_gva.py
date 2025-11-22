"""
Z5D-Enhanced FR-GVA Implementation
===================================

FR-GVA enhanced with Z5D Prime Predictor insights:

1. Z5D Prime Density Oracle: Weight segments by empirical prime density
2. Window×Wheel Gap Rule: Ensure (δ-span × 48/210) ≫ log(√N)
3. Wheel Residue Filter: Only test candidates in admissible residue classes (mod 210)
4. Z5D-Shaped Stepping: Variable δ-steps based on local density

This represents the core hypothesis: Z5D prior × GVA geometry improves
factorization performance on the 127-bit challenge.
"""

import mpmath as mp
from typing import List, Tuple, Optional, Dict
import time
from math import log, sqrt, isqrt, floor
import csv
import os

import sys
sys.path.append(os.path.dirname(__file__))
from wheel_residues import (
    is_admissible, next_admissible, 
    meets_gap_rule, effective_coverage,
    WHEEL_SIZE, WHEEL_MODULUS
)

# Configure precision
mp.mp.dps = 100

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717


def adaptive_precision(N: int) -> int:
    """Compute adaptive precision: max(100, N.bitLength() × 4 + 200)"""
    return max(100, N.bit_length() * 4 + 200)


def load_z5d_density_histogram(filename: str) -> Dict[int, float]:
    """
    Load Z5D prime density histogram from CSV.
    
    Args:
        filename: Path to histogram CSV (bin_center, count, density)
        
    Returns:
        Dict mapping bin_center -> density
    """
    density_map = {}
    
    if not os.path.exists(filename):
        print(f"Warning: Z5D density file not found: {filename}")
        print("Using uniform density (no Z5D prior)")
        return {}
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bin_center = int(row['bin_center'])
            density = float(row['density'])
            density_map[bin_center] = density
    
    return density_map


def get_z5d_density_weight(delta: int, density_map: Dict[int, float], 
                           bin_width: int = 1000) -> float:
    """
    Get Z5D density weight for a given δ value.
    
    Args:
        delta: δ = p - √N
        density_map: Histogram from load_z5d_density_histogram
        bin_width: Histogram bin width
        
    Returns:
        Density weight (normalized to [0, 1])
    """
    if not density_map:
        return 1.0  # Uniform if no Z5D data
    
    # Find corresponding bin using floor division
    # For bin_width=1000: delta=-1500 -> bin_idx=-2 -> bin_center=-2000
    #                     delta=-500  -> bin_idx=-1 -> bin_center=-1000
    #                     delta=500   -> bin_idx=0  -> bin_center=0
    #                     delta=1500  -> bin_idx=1  -> bin_center=1000
    bin_idx = floor(delta / bin_width)
    bin_center = bin_idx * bin_width
    
    # Get density (default to mean if bin not in map)
    if bin_center in density_map:
        density = density_map[bin_center]
    else:
        # Interpolate or use mean
        mean_density = sum(density_map.values()) / len(density_map)
        density = mean_density
    
    # Normalize (assuming densities are already per-unit values)
    # Add small epsilon to avoid zero weights
    return max(0.01, density)


def embed_torus_geodesic(n: int, k: float, dimensions: int = 7) -> List[mp.mpf]:
    """Embed integer n into 7D torus using geodesic mapping."""
    phi = mp.mpf(1 + mp.sqrt(5)) / 2
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
    """Compute Riemannian geodesic distance on 7D torus."""
    dist_sq = mp.mpf(0)
    for c1, c2 in zip(p1, p2):
        diff = abs(c1 - c2)
        wrap_diff = mp.mpf(1) - diff
        min_diff = min(diff, wrap_diff)
        dist_sq += min_diff * min_diff
    return mp.sqrt(dist_sq)


def z5d_enhanced_fr_gva(N: int,
                        z5d_density_file: Optional[str] = None,
                        k_value: float = 0.35,
                        max_candidates: int = 10000,
                        delta_window: int = 100000,
                        z5d_weight_beta: float = 0.1,
                        use_wheel_filter: bool = True,
                        use_z5d_stepping: bool = True,
                        verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Z5D-Enhanced FR-GVA with all transferable concepts from Z5D Prime Predictor.
    
    Enhancements:
    1. Z5D density prior: weight segments by empirical prime density
    2. Wheel filter: only test admissible residues (mod 210)
    3. Window×wheel gap rule: validate effective coverage
    4. Z5D-shaped stepping: variable δ-steps based on density
    
    Args:
        N: Semiprime to factor
        z5d_density_file: Path to Z5D density histogram CSV
        k_value: Geodesic exponent
        max_candidates: Maximum candidates to test
        delta_window: Half-width of δ-search window around √N
        z5d_weight_beta: Weight for Z5D density in scoring (β)
        use_wheel_filter: Enable wheel residue filtering
        use_z5d_stepping: Enable variable δ-steps based on density
        verbose: Enable detailed logging
        
    Returns:
        Tuple (p, q) if factors found, None otherwise
    """
    required_dps = adaptive_precision(N)
    with mp.workdps(required_dps):
        if verbose:
            print("=" * 70)
            print("Z5D-Enhanced FR-GVA")
            print("=" * 70)
            print(f"N = {N}")
            print(f"Bit length: {N.bit_length()}")
            print(f"Precision: {required_dps} dps")
            print(f"k = {k_value}")
            print(f"Max candidates: {max_candidates}")
            print(f"Delta window: ±{delta_window}")
            print(f"Z5D weight β = {z5d_weight_beta}")
            print(f"Wheel filter: {use_wheel_filter}")
            print(f"Z5D stepping: {use_z5d_stepping}")
            print()
        
        sqrt_N = isqrt(N)
        expected_gap = log(float(sqrt_N))
        
        if verbose:
            print(f"√N = {sqrt_N}")
            print(f"Expected prime gap: ḡ ≈ {expected_gap:.2f}")
            print()
        
        # Load Z5D density histogram
        density_map = {}
        if z5d_density_file:
            density_map = load_z5d_density_histogram(z5d_density_file)
            if verbose and density_map:
                print(f"Z5D density map loaded: {len(density_map)} bins")
        
        # Validate window×wheel gap rule
        if use_wheel_filter:
            eff_coverage = effective_coverage(2 * delta_window)
            meets_rule = meets_gap_rule(2 * delta_window, expected_gap)
            
            if verbose:
                print(f"Window×wheel gap rule:")
                print(f"  Window span: {2 * delta_window}")
                print(f"  Effective coverage: {eff_coverage:.2f}")
                print(f"  Expected gap: {expected_gap:.2f}")
                print(f"  Safety threshold (3×gap): {3 * expected_gap:.2f}")
                print(f"  Rule satisfied: {meets_rule}")
                
                if not meets_rule:
                    print(f"  ⚠ WARNING: Window may be under-sampled!")
                print()
        
        # Embed N in 7D torus
        N_coords = embed_torus_geodesic(N, k_value)
        
        start_time = time.time()
        
        # Sample candidates with Z5D enhancements
        candidates_with_scores = []
        
        if verbose:
            print("Phase 1: Sampling candidates with Z5D enhancements...")
        
        # Generate candidate deltas
        if use_z5d_stepping and density_map:
            # Z5D-shaped stepping: smaller steps in high-density regions
            deltas = _generate_z5d_shaped_deltas(density_map, delta_window, max_candidates)
        else:
            # Uniform golden ratio stepping (baseline)
            phi = (1 + sqrt(5)) / 2
            phi_inv = 1 / phi
            deltas = []
            for i in range(max_candidates):
                alpha = (i * phi_inv) % 1.0
                delta = int(alpha * 2 * delta_window - delta_window)
                deltas.append(delta)
        
        if verbose:
            print(f"  Generated {len(deltas)} delta values")
        
        # Convert deltas to candidates and score them
        wheel_filtered = 0
        for delta in deltas:
            candidate = sqrt_N + delta
            
            # Skip trivial cases
            if candidate <= 1 or candidate >= N:
                continue
            if candidate % 2 == 0:
                continue
            
            # Wheel filter: only admissible residues
            if use_wheel_filter and not is_admissible(candidate):
                wheel_filtered += 1
                continue
            
            # Compute geodesic distance (fractal amplitude)
            cand_coords = embed_torus_geodesic(candidate, k_value)
            distance = riemannian_distance(N_coords, cand_coords)
            
            # Compute Z5D density weight
            z5d_weight = get_z5d_density_weight(delta, density_map)
            
            # Combined score: α × fractal_score + β × z5d_weight
            # Fractal score: inverse distance (smaller distance = higher score)
            # Add 1 to avoid division by zero for distance=0
            fractal_score = 1.0 / (1.0 + float(distance))
            combined_score = fractal_score + z5d_weight_beta * z5d_weight
            
            candidates_with_scores.append((candidate, combined_score, distance, delta, z5d_weight))
        
        if verbose:
            print(f"  Wheel filtered: {wheel_filtered} ({wheel_filtered / max(1, len(deltas)) * 100:.1f}%)")
            print(f"  Valid candidates: {len(candidates_with_scores)}")
            print()
        
        # Sort by combined score (descending)
        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        if verbose:
            print("Phase 2: Testing top candidates...")
            print(f"  Top 10 scores: {[s for _, s, _, _, _ in candidates_with_scores[:10]]}")
            if density_map:
                print(f"  Top 10 deltas: {[d for _, _, _, d, _ in candidates_with_scores[:10]]}")
                print(f"  Top 10 Z5D weights: {[w for _, _, _, _, w in candidates_with_scores[:10]]}")
            print()
        
        # Test candidates in order of descending combined score
        tested = 0
        for candidate, combined_score, distance, delta, z5d_weight in candidates_with_scores:
            tested += 1
            
            if N % candidate == 0:
                p = candidate
                q = N // candidate
                
                elapsed = time.time() - start_time
                
                if verbose:
                    print("✓ FACTOR FOUND!")
                    print(f"  p = {p}")
                    print(f"  q = {q}")
                    print(f"  δ = {delta}")
                    print(f"  Combined score = {combined_score:.6f}")
                    print(f"  Distance = {float(distance):.6e}")
                    print(f"  Z5D weight = {z5d_weight:.6f}")
                    print(f"  Candidates tested: {tested}")
                    print(f"  Wheel filtered: {wheel_filtered}")
                    print(f"  Elapsed: {elapsed:.3f}s")
                    print()
                
                return (p, q)
        
        elapsed = time.time() - start_time
        
        if verbose:
            print("✗ No factors found")
            print(f"  Candidates tested: {tested}")
            print(f"  Wheel filtered: {wheel_filtered}")
            print(f"  Elapsed: {elapsed:.3f}s")
            print()
        
        return None


def _generate_z5d_shaped_deltas(density_map: Dict[int, float], 
                                delta_window: int, 
                                target_count: int,
                                bin_width: int = 1000) -> List[int]:
    """
    Generate δ values with Z5D-shaped stepping: denser in high-density regions.
    
    Args:
        density_map: Z5D density histogram
        delta_window: Half-width of δ-range
        target_count: Target number of deltas to generate
        bin_width: Histogram bin width
        
    Returns:
        List of delta values with density-weighted distribution
    """
    # Build cumulative density function for inverse sampling
    bins = sorted(density_map.keys())
    
    if not bins:
        # Fallback to uniform if no density data
        phi = (1 + sqrt(5)) / 2
        phi_inv = 1 / phi
        return [int((i * phi_inv % 1.0) * 2 * delta_window - delta_window) 
                for i in range(target_count)]
    
    # Normalize densities to probability distribution
    total_density = sum(density_map.values())
    prob_map = {b: density_map[b] / total_density for b in bins}
    
    # Generate samples proportional to density
    deltas = []
    phi = (1 + sqrt(5)) / 2
    phi_inv = 1 / phi
    
    for i in range(target_count):
        # Use golden ratio for deterministic sampling within bins
        alpha = (i * phi_inv) % 1.0
        
        # Select bin based on cumulative probability
        cumsum = 0.0
        selected_bin = bins[0]
        for bin_center in bins:
            cumsum += prob_map[bin_center]
            if alpha <= cumsum:
                selected_bin = bin_center
                break
        
        # Sample within selected bin
        offset_in_bin = int((alpha * len(bins) % 1.0) * bin_width - bin_width // 2)
        delta = selected_bin + offset_in_bin
        
        # Clamp to window
        delta = max(-delta_window, min(delta_window, delta))
        deltas.append(delta)
    
    return deltas


def main():
    """Test Z5D-enhanced FR-GVA on 127-bit challenge."""
    print("Testing Z5D-Enhanced FR-GVA on 127-bit Challenge")
    print("=" * 70)
    print()
    
    # Known factors for verification
    p_expected = 10508623501177419659
    q_expected = 13086849276577416863
    
    print(f"N = {CHALLENGE_127}")
    print(f"Expected factors:")
    print(f"  p = {p_expected}")
    print(f"  q = {q_expected}")
    print(f"  p × q = {p_expected * q_expected}")
    print(f"  Verify: {p_expected * q_expected == CHALLENGE_127}")
    print()
    
    # Path to Z5D density histogram (may not exist yet)
    density_file = os.path.join(os.path.dirname(__file__), "z5d_density_histogram.csv")
    
    # Run Z5D-enhanced version
    result = z5d_enhanced_fr_gva(
        CHALLENGE_127,
        z5d_density_file=density_file,
        k_value=0.35,
        max_candidates=50000,
        delta_window=500000,
        z5d_weight_beta=0.1,
        use_wheel_filter=True,
        use_z5d_stepping=True,
        verbose=True
    )
    
    if result:
        p, q = result
        print("=" * 70)
        print("SUCCESS: Factors found!")
        print(f"  p = {p}")
        print(f"  q = {q}")
        print(f"  p × q = {p * q}")
        print(f"  Verify: {p * q == CHALLENGE_127}")
    else:
        print("=" * 70)
        print("FAILURE: No factors found within budget")


if __name__ == "__main__":
    main()
