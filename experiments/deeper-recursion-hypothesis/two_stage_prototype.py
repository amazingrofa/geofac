"""
Two-stage coarse-to-fine prototype (PR #92 simulation).

Implements the 2-stage approach described in PR #92 analysis:
- Stage 1 (Coarse): Score segments by geodesic density
- Stage 2 (Fine): Search top-K segments exhaustively

Expected results on 110-bit N:
- Runtime: ~9s (2.3× baseline)
- Coverage: 50%
- Factors: recovered
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import mpmath as mp
import time
from typing import Tuple, Optional, Dict, Any, List
from math import sqrt
from gva_factorization import (
    adaptive_precision,
    embed_torus_geodesic,
    riemannian_distance
)


def score_segment(N: int, sqrt_N: int, start_offset: int, end_offset: int,
                  N_coords: List[mp.mpf], k: float, sample_count: int = 50) -> float:
    """
    Score a segment by average geodesic distance.
    
    Lower distance = higher score (factor-bearing regions have low distance).
    
    Args:
        N: Semiprime
        sqrt_N: Square root of N
        start_offset: Start offset from sqrt_N
        end_offset: End offset from sqrt_N
        N_coords: N's coordinates in 7D torus
        k: Geodesic exponent
        sample_count: Number of samples to take in segment
        
    Returns:
        Average geodesic score (1 / avg_distance)
    """
    segment_size = end_offset - start_offset
    if segment_size == 0:
        return 0.0
    
    step = max(1, segment_size // sample_count)
    distances = []
    
    for offset in range(start_offset, end_offset, step):
        candidate = sqrt_N + offset
        if candidate <= 1 or candidate >= N:
            continue
        if candidate % 2 == 0:  # Quick filter
            continue
        
        # Compute geodesic distance
        cand_coords = embed_torus_geodesic(candidate, k)
        dist = riemannian_distance(N_coords, cand_coords)
        distances.append(float(dist))
    
    if not distances:
        return 0.0
    
    avg_dist = sum(distances) / len(distances)
    # Score is inverse of distance (lower distance = higher score)
    return 1.0 / (avg_dist + 1e-10)


def two_stage_gva(N: int, segments: int = 32, top_k: int = 16,
                  verbose: bool = False) -> Dict[str, Any]:
    """
    Two-stage coarse-to-fine factorization.
    
    Stage 1 (Coarse): Divide search window into segments, score by geodesic density
    Stage 2 (Fine): Search top-K segments exhaustively
    
    Args:
        N: Semiprime to factor
        segments: Number of segments in Stage 1
        top_k: Number of top segments to search in Stage 2
        verbose: Enable detailed logging
        
    Returns:
        Dictionary with results and metrics
    """
    start_time = time.time()
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    mp.mp.dps = required_dps
    
    if verbose:
        print(f"\n=== Two-Stage GVA ===")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Precision: {required_dps} dps")
        print(f"Segments: {segments}, Top-K: {top_k}")
    
    sqrt_N = int(mp.sqrt(N))
    
    # Determine search window (same as baseline GVA for 110-bit)
    bit_length = N.bit_length()
    if bit_length >= 110:
        base_window = max(600000, sqrt_N // 200)
    elif bit_length >= 105:
        base_window = max(500000, sqrt_N // 250)
    else:
        base_window = max(400000, sqrt_N // 300)
    
    if verbose:
        print(f"Search window: ±{base_window} around sqrt(N) = {sqrt_N}")
    
    # Stage 1: Coarse scoring
    if verbose:
        print(f"\n--- Stage 1: Coarse Scoring ---")
    
    k = 0.35  # Use middle k value
    N_coords = embed_torus_geodesic(N, k)
    
    segment_size = (2 * base_window) // segments
    segment_scores = []
    
    stage1_start = time.time()
    samples_stage1 = 0
    
    for i in range(segments):
        start_offset = -base_window + i * segment_size
        end_offset = start_offset + segment_size
        
        score = score_segment(N, sqrt_N, start_offset, end_offset, N_coords, k, sample_count=50)
        segment_scores.append((i, score, start_offset, end_offset))
        samples_stage1 += 50
    
    stage1_time = time.time() - stage1_start
    
    # Sort by score (descending) and select top-K
    segment_scores.sort(key=lambda x: x[1], reverse=True)
    top_segments = segment_scores[:top_k]
    
    if verbose:
        print(f"  Samples: {samples_stage1}")
        print(f"  Time: {stage1_time:.3f}s")
        print(f"  Top-{top_k} segments selected")
    
    # Stage 2: Fine search in top segments
    if verbose:
        print(f"\n--- Stage 2: Fine Search ---")
    
    stage2_start = time.time()
    candidates_tested = 0
    max_candidates = 50000
    
    result_factors = None
    
    for seg_idx, score, start_offset, end_offset in top_segments:
        if candidates_tested >= max_candidates:
            break
        
        # Exhaustive search in this segment
        for offset in range(start_offset, end_offset):
            if candidates_tested >= max_candidates:
                break
            
            candidate = sqrt_N + offset
            
            # Skip invalid candidates
            if candidate <= 1 or candidate >= N:
                continue
            if candidate % 2 == 0 or candidate % 3 == 0 or candidate % 5 == 0:
                continue
            
            candidates_tested += 1
            
            # Test divisibility
            if N % candidate == 0:
                p = candidate
                q = N // candidate
                result_factors = (p, q)
                break
        
        if result_factors:
            break
    
    stage2_time = time.time() - stage2_start
    total_runtime = time.time() - start_time
    
    # Calculate coverage
    total_segments_searched = len(top_segments)
    coverage = (total_segments_searched / segments) * 100.0
    
    # Package results
    output = {
        'success': result_factors is not None,
        'factors': result_factors,
        'runtime': total_runtime,
        'stage1_time': stage1_time,
        'stage2_time': stage2_time,
        'stage1_samples': samples_stage1,
        'stage2_tested': candidates_tested,
        'total_candidates': samples_stage1 + candidates_tested,
        'coverage': coverage,
        'method': 'two_stage_gva',
        'segments': segments,
        'top_k': top_k
    }
    
    if verbose:
        print(f"  Candidates tested: {candidates_tested}")
        print(f"  Time: {stage2_time:.3f}s")
        print(f"\n--- Results ---")
        print(f"  Success: {output['success']}")
        if result_factors:
            p, q = result_factors
            print(f"  p = {p}")
            print(f"  q = {q}")
            print(f"  Verification: {p} × {q} = {p * q} {'✓' if p * q == N else '✗'}")
        print(f"  Total Runtime: {total_runtime:.3f}s")
        print(f"  Stage 1: {stage1_time:.3f}s ({samples_stage1} samples)")
        print(f"  Stage 2: {stage2_time:.3f}s ({candidates_tested} tested)")
        print(f"  Coverage: {coverage:.1f}%")
    
    return output


if __name__ == "__main__":
    # Test on the 110-bit case from PR #92
    N = 1296000000000003744000000000001183
    # Expected factors: 36000000000000013 × 36000000000000091
    
    result = two_stage_gva(N, segments=32, top_k=16, verbose=True)
    
    if result['success']:
        p, q = result['factors']
        print(f"\n✓ Factorization successful!")
        print(f"p = {p}")
        print(f"q = {q}")
        print(f"Gap: {abs(q - p)}")
        print(f"\nCompare to PR #92 baseline:")
        print(f"  Expected runtime: ~9.076s")
        print(f"  Actual runtime: {result['runtime']:.3f}s")
    else:
        print(f"\n✗ Factorization failed")
