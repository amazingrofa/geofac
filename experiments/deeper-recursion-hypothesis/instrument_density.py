"""
Density profiling instrumentation for deeper recursion experiment.

Profiles geodesic density distribution across segments to guide
dynamic threshold tuning.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import mpmath as mp
import json
import time
from typing import Dict, List, Any
from gva_factorization import (
    adaptive_precision,
    embed_torus_geodesic,
    riemannian_distance
)


def profile_density(N: int, segments: int = 32, samples_per_segment: int = 100,
                   verbose: bool = False) -> Dict[str, Any]:
    """
    Profile geodesic density distribution across search window.
    
    Args:
        N: Semiprime to analyze
        segments: Number of segments to divide window into
        samples_per_segment: Samples to take per segment
        verbose: Enable detailed logging
        
    Returns:
        Dictionary with density profile data
    """
    if verbose:
        print(f"\n=== Density Profiling ===")
        print(f"N = {N}")
        print(f"Segments: {segments}")
        print(f"Samples per segment: {samples_per_segment}")
    
    start_time = time.time()
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    mp.mp.dps = required_dps
    
    sqrt_N = int(mp.sqrt(N))
    bit_length = N.bit_length()
    
    # Determine search window
    if bit_length >= 110:
        base_window = max(600000, sqrt_N // 200)
    elif bit_length >= 105:
        base_window = max(500000, sqrt_N // 250)
    else:
        base_window = max(400000, sqrt_N // 300)
    
    if verbose:
        print(f"Search window: ±{base_window} around sqrt(N) = {sqrt_N}")
    
    # Profile density for different k values
    k_values = [0.30, 0.35, 0.40]
    profiles = {}
    
    for k in k_values:
        if verbose:
            print(f"\nProfiling k = {k}...")
        
        N_coords = embed_torus_geodesic(N, k)
        segment_size = (2 * base_window) // segments
        
        segment_data = []
        
        for i in range(segments):
            start_offset = -base_window + i * segment_size
            end_offset = start_offset + segment_size
            
            step = max(1, segment_size // samples_per_segment)
            distances = []
            
            for offset in range(start_offset, end_offset, step):
                candidate = sqrt_N + offset
                if candidate <= 1 or candidate >= N:
                    continue
                if candidate % 2 == 0:
                    continue
                
                cand_coords = embed_torus_geodesic(candidate, k)
                dist = riemannian_distance(N_coords, cand_coords)
                distances.append(float(dist))
            
            if distances:
                avg_dist = sum(distances) / len(distances)
                min_dist = min(distances)
                max_dist = max(distances)
                score = 1.0 / (avg_dist + 1e-10)
            else:
                avg_dist = 0.0
                min_dist = 0.0
                max_dist = 0.0
                score = 0.0
            
            segment_data.append({
                'segment_idx': i,
                'start_offset': start_offset,
                'end_offset': end_offset,
                'avg_distance': avg_dist,
                'min_distance': min_dist,
                'max_distance': max_dist,
                'score': score,
                'samples': len(distances)
            })
        
        profiles[f'k_{k}'] = segment_data
    
    runtime = time.time() - start_time
    
    # Compute statistics
    stats = {}
    for k_key, seg_data in profiles.items():
        scores = [seg['score'] for seg in seg_data]
        avg_distances = [seg['avg_distance'] for seg in seg_data]
        
        stats[k_key] = {
            'mean_score': sum(scores) / len(scores) if scores else 0.0,
            'max_score': max(scores) if scores else 0.0,
            'min_score': min(scores) if scores else 0.0,
            'mean_distance': sum(avg_distances) / len(avg_distances) if avg_distances else 0.0,
            'top_10_percent_threshold': sorted(scores, reverse=True)[len(scores) // 10] if scores else 0.0,
            'top_25_percent_threshold': sorted(scores, reverse=True)[len(scores) // 4] if scores else 0.0,
            'top_50_percent_threshold': sorted(scores, reverse=True)[len(scores) // 2] if scores else 0.0
        }
    
    output = {
        'N': str(N),
        'sqrt_N': sqrt_N,
        'bit_length': bit_length,
        'search_window': base_window,
        'segments': segments,
        'samples_per_segment': samples_per_segment,
        'profiles': profiles,
        'statistics': stats,
        'runtime': runtime,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if verbose:
        print(f"\n--- Density Statistics ---")
        for k_key, k_stats in stats.items():
            print(f"\n{k_key}:")
            print(f"  Mean score: {k_stats['mean_score']:.6f}")
            print(f"  Max score: {k_stats['max_score']:.6f}")
            print(f"  Top 10% threshold: {k_stats['top_10_percent_threshold']:.6f}")
            print(f"  Top 25% threshold: {k_stats['top_25_percent_threshold']:.6f}")
            print(f"  Top 50% threshold: {k_stats['top_50_percent_threshold']:.6f}")
        
        print(f"\nTotal runtime: {runtime:.3f}s")
    
    return output


def save_density_profile(profile_data: Dict[str, Any], filename: str = "density_profile.json"):
    """Save density profile to JSON file."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'w') as f:
        json.dump(profile_data, f, indent=2)
    print(f"Density profile saved to {filepath}")


def load_density_profile(filename: str = "density_profile.json") -> Dict[str, Any]:
    """Load density profile from JSON file."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    # Profile the 110-bit test case
    N = 1296000000000003744000000000001183
    # Expected factors: 36000000000000013 × 36000000000000091
    
    print("Profiling geodesic density distribution...")
    profile = profile_density(N, segments=32, samples_per_segment=50, verbose=True)
    
    # Save to JSON
    save_density_profile(profile)
    
    print("\n✓ Density profiling complete")
    print(f"Use statistics to tune dynamic thresholds for 3-stage approach")
