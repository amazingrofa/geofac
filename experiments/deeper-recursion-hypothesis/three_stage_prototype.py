"""
Three-stage recursive prototype with dynamic thresholds.

Implements deeper recursion hypothesis:
- Stage 1 (Very Coarse): Rough segment scoring, small number of segments
- Stage 2 (Medium): Refine top quadrants, adaptive threshold
- Stage 3 (Fine): Focused geodesic search in highest-density regions

Goal: Reduce runtime below baseline (< 4.027s) while maintaining factor recovery.
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
        
        cand_coords = embed_torus_geodesic(candidate, k)
        dist = riemannian_distance(N_coords, cand_coords)
        distances.append(float(dist))
    
    if not distances:
        return 0.0
    
    avg_dist = sum(distances) / len(distances)
    return 1.0 / (avg_dist + 1e-10)


def three_stage_gva(N: int,
                    stage1_segments: int = 8,
                    stage1_top_k: int = 4,
                    stage2_subsegments: int = 4,
                    stage2_top_k: int = 2,
                    stage2_threshold: float = 0.7,
                    early_exit: bool = True,
                    verbose: bool = False) -> Dict[str, Any]:
    """
    Three-stage recursive factorization with dynamic thresholds.
    
    Stage 1: Very coarse scoring (8 segments, select top 4 = 50%)
    Stage 2: Medium refinement (subdivide each into 4, select top 2 = 50%)
    Stage 3: Fine search in selected regions
    
    Args:
        N: Semiprime to factor
        stage1_segments: Number of coarse segments
        stage1_top_k: Top segments to advance from Stage 1
        stage2_subsegments: Subdivisions per Stage 1 segment
        stage2_top_k: Top subsegments per parent to advance
        stage2_threshold: Minimum score to proceed to Stage 3 (early exit)
        early_exit: Enable early exit based on threshold
        verbose: Enable detailed logging
        
    Returns:
        Dictionary with results and metrics
    """
    start_time = time.time()
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    mp.mp.dps = required_dps
    
    if verbose:
        print(f"\n=== Three-Stage GVA ===")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Precision: {required_dps} dps")
        print(f"Stage 1: {stage1_segments} segments → top {stage1_top_k}")
        print(f"Stage 2: {stage2_subsegments} subsegments each → top {stage2_top_k}")
        print(f"Threshold: {stage2_threshold}, Early exit: {early_exit}")
    
    sqrt_N = int(mp.sqrt(N))
    
    # Determine search window
    bit_length = N.bit_length()
    if bit_length >= 110:
        base_window = max(600000, sqrt_N // 200)
    elif bit_length >= 105:
        base_window = max(500000, sqrt_N // 250)
    else:
        base_window = max(400000, sqrt_N // 300)
    
    if verbose:
        print(f"Search window: ±{base_window} around sqrt(N) = {sqrt_N}")
    
    k = 0.35  # Use middle k value
    N_coords = embed_torus_geodesic(N, k)
    
    # ========== Stage 1: Very Coarse Scoring ==========
    if verbose:
        print(f"\n--- Stage 1: Very Coarse Scoring ---")
    
    stage1_start = time.time()
    stage1_segment_size = (2 * base_window) // stage1_segments
    stage1_scores = []
    samples_stage1 = 0
    
    for i in range(stage1_segments):
        start_offset = -base_window + i * stage1_segment_size
        end_offset = start_offset + stage1_segment_size
        
        score = score_segment(N, sqrt_N, start_offset, end_offset, N_coords, k, sample_count=50)
        stage1_scores.append((i, score, start_offset, end_offset))
        samples_stage1 += 50
    
    stage1_time = time.time() - stage1_start
    
    # Select top-K segments
    stage1_scores.sort(key=lambda x: x[1], reverse=True)
    stage1_top = stage1_scores[:stage1_top_k]
    
    if verbose:
        print(f"  Samples: {samples_stage1}")
        print(f"  Time: {stage1_time:.3f}s")
        print(f"  Top-{stage1_top_k} segments selected")
    
    # ========== Stage 2: Medium Refinement ==========
    if verbose:
        print(f"\n--- Stage 2: Medium Refinement ---")
    
    stage2_start = time.time()
    stage2_regions = []
    samples_stage2 = 0
    max_score_stage2 = 0.0
    
    for parent_idx, parent_score, parent_start, parent_end in stage1_top:
        parent_size = parent_end - parent_start
        subseg_size = parent_size // stage2_subsegments
        
        subseg_scores = []
        for j in range(stage2_subsegments):
            sub_start = parent_start + j * subseg_size
            sub_end = sub_start + subseg_size
            
            score = score_segment(N, sqrt_N, sub_start, sub_end, N_coords, k, sample_count=50)
            subseg_scores.append((parent_idx, j, score, sub_start, sub_end))
            samples_stage2 += 50
            max_score_stage2 = max(max_score_stage2, score)
        
        # Select top-K subsegments from this parent
        subseg_scores.sort(key=lambda x: x[2], reverse=True)
        stage2_regions.extend(subseg_scores[:stage2_top_k])
    
    stage2_time = time.time() - stage2_start
    
    # Early exit check
    early_exited = False
    if early_exit and max_score_stage2 < stage2_threshold:
        early_exited = True
        if verbose:
            print(f"  Samples: {samples_stage2}")
            print(f"  Time: {stage2_time:.3f}s")
            print(f"  Max score: {max_score_stage2:.4f} < threshold {stage2_threshold}")
            print(f"  ⚠ Early exit - no promising regions found")
        
        output = {
            'success': False,
            'factors': None,
            'runtime': time.time() - start_time,
            'stage1_time': stage1_time,
            'stage2_time': stage2_time,
            'stage3_time': 0.0,
            'stage1_samples': samples_stage1,
            'stage2_samples': samples_stage2,
            'stage3_tested': 0,
            'total_candidates': samples_stage1 + samples_stage2,
            'coverage': 0.0,  # Early exit
            'method': 'three_stage_gva',
            'early_exited': True
        }
        return output
    
    if verbose:
        print(f"  Samples: {samples_stage2}")
        print(f"  Time: {stage2_time:.3f}s")
        print(f"  Max score: {max_score_stage2:.4f}")
        print(f"  {len(stage2_regions)} regions selected for Stage 3")
    
    # ========== Stage 3: Fine Search ==========
    if verbose:
        print(f"\n--- Stage 3: Fine Search ---")
    
    stage3_start = time.time()
    candidates_tested = 0
    max_candidates = 50000
    result_factors = None
    
    # Sort Stage 2 regions by score (best first)
    stage2_regions.sort(key=lambda x: x[2], reverse=True)
    
    for parent_idx, sub_idx, score, sub_start, sub_end in stage2_regions:
        if candidates_tested >= max_candidates:
            break
        
        # Exhaustive search in this region
        for offset in range(sub_start, sub_end):
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
    
    stage3_time = time.time() - stage3_start
    total_runtime = time.time() - start_time
    
    # Calculate coverage
    # Coverage = (stage1_top_k / stage1_segments) * (stage2_top_k / stage2_subsegments)
    coverage = (stage1_top_k / stage1_segments) * (stage2_top_k / stage2_subsegments) * 100.0
    
    # Package results
    output = {
        'success': result_factors is not None,
        'factors': result_factors,
        'runtime': total_runtime,
        'stage1_time': stage1_time,
        'stage2_time': stage2_time,
        'stage3_time': stage3_time,
        'stage1_samples': samples_stage1,
        'stage2_samples': samples_stage2,
        'stage3_tested': candidates_tested,
        'total_candidates': samples_stage1 + samples_stage2 + candidates_tested,
        'coverage': coverage,
        'method': 'three_stage_gva',
        'early_exited': early_exited,
        'max_score_stage2': max_score_stage2
    }
    
    if verbose:
        print(f"  Candidates tested: {candidates_tested}")
        print(f"  Time: {stage3_time:.3f}s")
        print(f"\n--- Results ---")
        print(f"  Success: {output['success']}")
        if result_factors:
            p, q = result_factors
            print(f"  p = {p}")
            print(f"  q = {q}")
            print(f"  Verification: {p} × {q} = {p * q} {'✓' if p * q == N else '✗'}")
        print(f"  Total Runtime: {total_runtime:.3f}s")
        print(f"  Stage 1: {stage1_time:.3f}s ({samples_stage1} samples)")
        print(f"  Stage 2: {stage2_time:.3f}s ({samples_stage2} samples)")
        print(f"  Stage 3: {stage3_time:.3f}s ({candidates_tested} tested)")
        print(f"  Coverage: {coverage:.1f}%")
        print(f"  Total candidates: {output['total_candidates']}")
    
    return output


if __name__ == "__main__":
    # Test on the 110-bit case from PR #92
    N = 1296000000000003744000000000001183
    # Expected factors: 36000000000000013 × 36000000000000091
    
    result = three_stage_gva(N, verbose=True)
    
    if result['success']:
        p, q = result['factors']
        print(f"\n✓ Factorization successful!")
        print(f"p = {p}")
        print(f"q = {q}")
        print(f"Gap: {abs(q - p)}")
        print(f"\nCompare to baseline:")
        print(f"  Baseline runtime: ~4.027s")
        print(f"  3-stage runtime: {result['runtime']:.3f}s")
        if result['runtime'] < 4.027:
            print(f"  ✓ HYPOTHESIS SUPPORTED (faster than baseline)")
        else:
            print(f"  ✗ HYPOTHESIS FALSIFIED (slower than baseline)")
    else:
        print(f"\n✗ Factorization failed")
        print(f"  Early exit: {result.get('early_exited', False)}")
