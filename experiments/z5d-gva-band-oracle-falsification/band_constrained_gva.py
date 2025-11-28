"""
Band-Constrained GVA
=====================

Implements the core GVA algorithm constrained to Z5D bands.

Components:
1. Band-constrained search: Only search within bands from band oracle
2. Bin quantization: k/m grid quantized to bins.json
3. Wheel mask filtering: mod 2310 residue filtering
4. A/B density weighting toggle: use_density_weight=false by default
5. Short-circuit distant shells: variance/curvature thresholds
6. Geometric acceptance: SNR threshold + wheel mask (no divisibility in scoring)

Output: peaks.jsonl with candidate peaks found during search

Validation: 127-bit challenge N = 137524771864208156028430259349934309717
"""

import mpmath as mp
from typing import List, Tuple, Optional, Dict, Set
import time
import json
from math import log, sqrt, isqrt, floor
from datetime import datetime, timezone
import os

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717
P_EXPECTED = 10508623501177419659
Q_EXPECTED = 13086849276577416863

# Short-circuit thresholds
TAU_1_VARIANCE = 0.001      # Variance threshold for short-circuit
TAU_2_CURVATURE = 0.0001    # Curvature threshold for short-circuit
T_STEPS = 5                  # Consecutive steps below threshold to trigger short-circuit

# Acceptance criteria (geometric only)
SNR_THRESHOLD = 2.0          # Signal-to-noise ratio threshold


def adaptive_precision(N: int) -> int:
    """Compute adaptive precision: max(100, N.bitLength() × 4 + 200)"""
    return max(100, N.bit_length() * 4 + 200)


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


def quantize_km_grid(k_values: List[float], 
                     m_range: Tuple[int, int],
                     k_bins: int = 20,
                     m_bins: int = 50) -> Dict:
    """
    Quantize k/m parameter grid into bins.
    
    Args:
        k_values: List of geodesic exponent values
        m_range: (m_min, m_max) for Dirichlet kernel
        k_bins: Number of bins for k dimension
        m_bins: Number of bins for m dimension
        
    Returns:
        Bin data dictionary
    """
    k_min, k_max = min(k_values), max(k_values)
    m_min, m_max = m_range
    
    k_bin_width = (k_max - k_min) / k_bins
    m_bin_width = (m_max - m_min) / m_bins
    
    bins = []
    bin_id = 0
    
    for i in range(k_bins):
        k_lo = k_min + i * k_bin_width
        k_hi = k_lo + k_bin_width
        k_center = (k_lo + k_hi) / 2
        
        for j in range(m_bins):
            m_lo = m_min + j * m_bin_width
            m_hi = m_lo + m_bin_width
            m_center = (m_lo + m_hi) / 2
            
            bins.append({
                "id": bin_id,
                "k_range": [k_lo, k_hi],
                "k_center": k_center,
                "m_range": [int(m_lo), int(m_hi)],
                "m_center": int(m_center),
                "explored": False,
                "best_score": None
            })
            bin_id += 1
    
    return {
        "metadata": {
            "k_values": k_values,
            "m_range": list(m_range),
            "k_bins": k_bins,
            "m_bins": m_bins,
            "total_bins": len(bins),
            "generated_at": datetime.now(timezone.utc).isoformat()
        },
        "bins": bins
    }


def export_bins_json(bins_data: Dict, output_path: str):
    """Export bins to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(bins_data, f, indent=2)


def load_bins_json(path: str) -> Dict:
    """Load bins from JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def compute_signal_metrics(distances: List[float]) -> Tuple[float, float, float]:
    """
    Compute signal metrics for short-circuit decision.
    
    Args:
        distances: List of recent distances
        
    Returns:
        (variance, curvature, snr)
    """
    if len(distances) < 3:
        return float('inf'), float('inf'), 0.0
    
    # Variance
    mean = sum(distances) / len(distances)
    variance = sum((d - mean) ** 2 for d in distances) / len(distances)
    
    # Curvature: second derivative approximation
    curvatures = []
    for i in range(1, len(distances) - 1):
        curv = abs(distances[i-1] - 2*distances[i] + distances[i+1])
        curvatures.append(curv)
    curvature = sum(curvatures) / len(curvatures) if curvatures else 0.0
    
    # SNR: ratio of mean to standard deviation
    # Use epsilon guard to avoid division by zero
    EPSILON_DIVISION_GUARD = 1e-10
    std = sqrt(variance) if variance > 0 else EPSILON_DIVISION_GUARD
    snr = abs(mean) / std
    
    return variance, curvature, snr


def check_acceptance_criterion(candidate: int, N: int, 
                               snr: float, mask_set: Set[int], 
                               modulus: int) -> Tuple[bool, Dict]:
    """
    Geometric acceptance criterion check.
    
    Criteria:
    1. SNR > τ (signal-to-noise above threshold)
    2. Mask holds (candidate in allowed residue class)
    
    Args:
        candidate: Factor candidate
        N: Target semiprime
        snr: Signal-to-noise ratio
        mask_set: Set of allowed residues
        modulus: Wheel modulus
        
    Returns:
        (accepted, details_dict)
    """
    details = {
        "candidate": candidate,
        "snr": snr,
        "snr_ok": snr > SNR_THRESHOLD,
        "mask_ok": (candidate % modulus) in mask_set,
        "accepted": False
    }
    
    # Check mask
    if not details["mask_ok"]:
        return False, details
    
    # Check SNR
    if not details["snr_ok"]:
        return False, details

    details["accepted"] = True
    return True, details


def band_constrained_gva(N: int,
                         bands: List[Dict],
                         mask_set: Set[int],
                         modulus: int,
                         k_values: List[float] = None,
                         max_candidates_per_band: int = 1000,
                         use_density_weight: bool = False,
                         use_short_circuit: bool = True,
                         verbose: bool = False) -> Tuple[Optional[Tuple[int, int]], List[Dict]]:
    """
    Band-constrained GVA with all Z5D enhancements.
    
    Args:
        N: Semiprime to factor
        bands: List of bands from band oracle
        mask_set: Set of allowed residues from mask
        modulus: Wheel modulus
        k_values: Geodesic exponents to test
        max_candidates_per_band: Max candidates per band
        use_density_weight: A/B toggle for density weighting (default False)
        use_short_circuit: Enable short-circuit for distant shells
        verbose: Enable detailed logging
        
    Returns:
        Tuple of (factors, peaks_list) where factors is (p,q) or None
    """
    if k_values is None:
        k_values = [0.30, 0.35, 0.40]
    
    required_dps = adaptive_precision(N)
    sqrt_N = isqrt(N)
    
    peaks = []
    total_tested = 0
    total_filtered = 0
    bands_explored = 0
    short_circuited = 0
    
    start_time = time.time()
    
    if verbose:
        print("=" * 70)
        print("Band-Constrained GVA")
        print("=" * 70)
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Precision: {required_dps} dps")
        print(f"√N = {sqrt_N}")
        print(f"Bands: {len(bands)}")
        print(f"k values: {k_values}")
        print(f"Max candidates/band: {max_candidates_per_band}")
        print(f"Density weighting: {use_density_weight}")
        print(f"Short-circuit: {use_short_circuit}")
        print()
    
    with mp.workdps(required_dps):
        # Sort bands by priority
        sorted_bands = sorted(bands, key=lambda b: b["priority"], reverse=True)
        
        for band in sorted_bands:
            bands_explored += 1
            band_start = band["start"]
            band_end = band["end"]
            band_width = band["width"]
            
            if verbose and bands_explored <= 5:
                print(f"Band {band['id']}: δ ∈ [{band_start:+,}, {band_end:+,}] "
                      f"(priority={band['priority']}, type={band['type']})")
            
            # Track distances for short-circuit
            recent_distances = []
            consecutive_low = 0
            
            for k in k_values:
                # Embed N
                N_coords = embed_torus_geodesic(N, k)
                
                # Generate candidates in this band
                # Use golden ratio stepping within band
                phi = float((1 + mp.sqrt(5)) / 2)
                phi_inv = 1 / phi
                
                for i in range(max_candidates_per_band):
                    # Map [0,1) to band range
                    alpha = (i * phi_inv) % 1.0
                    delta = int(band_start + alpha * band_width)
                    
                    candidate = sqrt_N + delta
                    
                    # Skip trivial cases
                    if candidate <= 1 or candidate >= N:
                        continue
                    if candidate % 2 == 0:
                        continue
                    
                    # Wheel mask filter
                    if (candidate % modulus) not in mask_set:
                        total_filtered += 1
                        continue
                    
                    total_tested += 1
                    
                    # Compute geodesic distance
                    cand_coords = embed_torus_geodesic(candidate, k)
                    distance = float(riemannian_distance(N_coords, cand_coords))
                    
                    # Apply density weight if enabled
                    if use_density_weight and "density_weight" in band:
                        score = 1.0 / (1.0 + distance) + 0.1 * band["density_weight"]
                    else:
                        score = 1.0 / (1.0 + distance)
                    
                    # Track for short-circuit
                    recent_distances.append(distance)
                    if len(recent_distances) > 20:
                        recent_distances.pop(0)
                    
                    # Short-circuit check
                    if use_short_circuit and len(recent_distances) >= 10:
                        variance, curvature, snr = compute_signal_metrics(recent_distances)
                        
                        if variance < TAU_1_VARIANCE and curvature < TAU_2_CURVATURE:
                            consecutive_low += 1
                            if consecutive_low >= T_STEPS:
                                short_circuited += 1
                                if verbose and short_circuited <= 3:
                                    print(f"  Short-circuit: band {band['id']} (var={variance:.6f}, curv={curvature:.6f})")
                                break
                        else:
                            consecutive_low = 0
                    
                    # Check acceptance criterion
                    variance, curvature, snr = compute_signal_metrics(recent_distances)
                    accepted, details = check_acceptance_criterion(
                        candidate, N, snr, mask_set, modulus
                    )
                    
                    # Record peak
                    peak = {
                        "candidate": candidate,
                        "delta": delta,
                        "k": k,
                        "distance": distance,
                        "score": score,
                        "band_id": band["id"],
                        "band_type": band["type"],
                        "accepted": accepted,
                        "snr": snr
                    }
                    
                    if accepted:
                        p = candidate
                        q = N // candidate
                        
                        if N % p == 0:
                            elapsed = time.time() - start_time
                            
                            if verbose:
                                print()
                                print("✓ FACTOR FOUND!")
                                print(f"  p = {p}")
                                print(f"  q = {q}")
                                print(f"  δ = {delta:+,}")
                                print(f"  k = {k}")
                                print(f"  Distance = {distance:.6e}")
                                print(f"  SNR = {snr:.4f}")
                                print(f"  Band: {band['id']} ({band['type']})")
                                print(f"  Candidates tested: {total_tested}")
                                print(f"  Filtered by mask: {total_filtered}")
                                print(f"  Bands explored: {bands_explored}")
                                print(f"  Short-circuited: {short_circuited}")
                                print(f"  Elapsed: {elapsed:.3f}s")
                            
                            peak["verified"] = True
                            peaks.append(peak)
                            
                            return (p, q), peaks
                    
                    # Only keep high-score peaks
                    if score > 0.5:
                        peaks.append(peak)
                
                # Break k-loop if short-circuited
                if consecutive_low >= T_STEPS:
                    break
        
        elapsed = time.time() - start_time
        
        if verbose:
            print()
            print("✗ No factors found")
            print(f"  Candidates tested: {total_tested}")
            print(f"  Filtered by mask: {total_filtered}")
            print(f"  Bands explored: {bands_explored}")
            print(f"  Short-circuited: {short_circuited}")
            print(f"  Peaks recorded: {len(peaks)}")
            print(f"  Elapsed: {elapsed:.3f}s")
    
    return None, peaks


def export_peaks_jsonl(peaks: List[Dict], N: int, output_path: str, run_info: Dict = None):
    """Export peaks to JSON Lines format."""
    with open(output_path, 'w') as f:
        # Write metadata
        metadata = {
            "_metadata": True,
            "N": str(N),
            "bit_length": N.bit_length(),
            "peak_count": len(peaks),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "band_constrained_gva.py"
        }
        if run_info:
            metadata.update(run_info)
        f.write(json.dumps(metadata) + "\n")
        
        # Write peaks
        for peak in peaks:
            f.write(json.dumps(peak) + "\n")


if __name__ == "__main__":
    from mask_generator import load_mask, WHEEL_MODULUS
    from z5d_band_oracle import load_bands_jsonl
    
    print("Band-Constrained GVA - Test Run")
    print("=" * 70)
    print()
    
    # Load mask
    output_dir = os.path.dirname(os.path.abspath(__file__))
    mask_path = os.path.join(output_dir, "mask.json")
    bands_path = os.path.join(output_dir, "bands.jsonl")
    
    # Generate mask if not exists
    if not os.path.exists(mask_path):
        from mask_generator import generate_mask
        print("Generating mask...")
        generate_mask(mask_path)
    
    mask_set = load_mask(mask_path)
    print(f"Loaded mask: {len(mask_set)} allowed residues (mod {WHEEL_MODULUS})")
    
    # Generate bands if not exists
    if not os.path.exists(bands_path):
        from z5d_band_oracle import generate_bands, export_bands_jsonl
        print("Generating bands...")
        bands = generate_bands(CHALLENGE_127)
        export_bands_jsonl(bands, CHALLENGE_127, bands_path)
    
    metadata, bands = load_bands_jsonl(bands_path)
    print(f"Loaded bands: {len(bands)} bands")
    print()
    
    # Run band-constrained GVA
    result, peaks = band_constrained_gva(
        CHALLENGE_127,
        bands,
        mask_set,
        WHEEL_MODULUS,
        k_values=[0.30, 0.35, 0.40],
        max_candidates_per_band=500,
        use_density_weight=False,  # A/B toggle: default off
        use_short_circuit=True,
        verbose=True
    )
    
    # Export peaks
    peaks_path = os.path.join(output_dir, "peaks.jsonl")
    export_peaks_jsonl(peaks, CHALLENGE_127, peaks_path)
    print()
    print(f"Peaks exported to: {peaks_path}")
    
    if result:
        p, q = result
        print()
        print("=" * 70)
        print("SUCCESS!")
        print(f"p = {p}")
        print(f"q = {q}")
        print(f"p × q = {p * q}")
        print(f"Verified: {p * q == CHALLENGE_127}")
    else:
        print()
        print("=" * 70)
        print("FAILURE: No factors found within budget")
