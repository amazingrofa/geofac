"""
Z5D Band Oracle
================

Implements the "Freeze Z5D → Band Oracle" component:
Outputs bands.jsonl with inner bands around √N.

The band oracle divides the search space around √N into bands
based on expected prime density and geometric properties.
Each band has:
- Center offset from √N
- Width (span)
- Expected density based on PNT
- Priority weight for search ordering

This creates a hierarchical search structure that prioritizes
regions most likely to contain factors.

Output: bands.jsonl (JSON Lines format for streaming)

Validation: 127-bit challenge N = 137524771864208156028430259349934309717
"""

import json
from math import log, sqrt, isqrt, floor, ceil
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import os

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717
P_EXPECTED = 10508623501177419659
Q_EXPECTED = 13086849276577416863

# Band oracle configuration constants
# Minimum base width for innermost band (absolute floor)
MIN_BAND_BASE_WIDTH = 100
# Multiplier for expected gap to set initial band width
# Higher values give wider initial bands, better coverage
BAND_GAP_MULTIPLIER = 10


def compute_sqrt_n(N: int) -> int:
    """Compute exact floor(√N)."""
    return isqrt(N)


def expected_prime_gap(x: int) -> float:
    """
    Compute expected prime gap near x using PNT.
    
    By Prime Number Theorem, primes near x have average gap ≈ log(x).
    
    Args:
        x: Location to compute expected gap
        
    Returns:
        Expected gap ≈ log(x)
    """
    if x <= 1:
        return 1.0
    return log(float(x))


def compute_density_weight(delta: int, sqrt_N: int) -> float:
    """
    Compute Z5D-inspired density weight for a position.
    
    Based on prime density near √N + δ.
    Higher density = higher weight = more samples allocated.
    
    Args:
        delta: Offset from √N
        sqrt_N: Floor of √N
        
    Returns:
        Density weight (normalized)
    """
    position = sqrt_N + delta
    if position <= 1:
        return 0.0
    
    # Inverse of expected gap gives relative density
    gap = expected_prime_gap(position)
    density = 1.0 / gap
    
    return density


def generate_bands(N: int, 
                   max_delta: int = 10**7,
                   inner_band_count: int = 20,
                   outer_band_count: int = 10) -> List[Dict]:
    """
    Generate search bands around √N.
    
    Structure:
    1. Inner bands: Dense coverage near √N (where balanced semiprimes have factors)
    2. Outer bands: Sparser coverage for unbalanced cases
    
    Args:
        N: Semiprime to factor
        max_delta: Maximum offset from √N
        inner_band_count: Number of inner (high priority) bands
        outer_band_count: Number of outer (lower priority) bands
        
    Returns:
        List of band dictionaries
    """
    sqrt_N = compute_sqrt_n(N)
    exp_gap = expected_prime_gap(sqrt_N)
    
    bands = []
    band_id = 0
    
    # Inner bands: exponentially increasing width centered on √N
    # Start with band width = BAND_GAP_MULTIPLIER × expected gap, double each time
    inner_base_width = int(max(MIN_BAND_BASE_WIDTH, BAND_GAP_MULTIPLIER * exp_gap))
    cumulative_offset = 0
    
    for i in range(inner_band_count):
        width = inner_base_width * (2 ** i)
        
        # Positive side band
        band = {
            "id": band_id,
            "type": "inner",
            "center": cumulative_offset + width // 2,
            "width": width,
            "start": cumulative_offset,
            "end": cumulative_offset + width,
            "priority": inner_band_count - i,  # Higher priority for closer bands
            "density_weight": compute_density_weight(cumulative_offset + width // 2, sqrt_N),
            "expected_gap": exp_gap
        }
        bands.append(band)
        band_id += 1
        
        # Negative side band (mirror)
        # Skip when i=0 to avoid creating duplicate band at δ=0
        if i > 0:
            band_neg = {
                "id": band_id,
                "type": "inner",
                "center": -(cumulative_offset + width // 2),
                "width": width,
                "start": -(cumulative_offset + width),
                "end": -cumulative_offset if cumulative_offset > 0 else 0,
                "priority": inner_band_count - i,
                "density_weight": compute_density_weight(-(cumulative_offset + width // 2), sqrt_N),
                "expected_gap": exp_gap
            }
            bands.append(band_neg)
            band_id += 1
        
        cumulative_offset += width
        
        if cumulative_offset > max_delta:
            break
    
    # Outer bands: fixed larger width for remainder
    outer_width = min(max_delta - cumulative_offset, 10**6)
    if outer_width > 0:
        outer_start = cumulative_offset
        
        for i in range(outer_band_count):
            if outer_start >= max_delta:
                break
                
            actual_width = min(outer_width, max_delta - outer_start)
            
            # Positive side
            band = {
                "id": band_id,
                "type": "outer",
                "center": outer_start + actual_width // 2,
                "width": actual_width,
                "start": outer_start,
                "end": outer_start + actual_width,
                "priority": -i,  # Lower priority for outer bands
                "density_weight": compute_density_weight(outer_start + actual_width // 2, sqrt_N),
                "expected_gap": expected_prime_gap(sqrt_N + outer_start)
            }
            bands.append(band)
            band_id += 1
            
            # Negative side
            band_neg = {
                "id": band_id,
                "type": "outer",
                "center": -(outer_start + actual_width // 2),
                "width": actual_width,
                "start": -(outer_start + actual_width),
                "end": -outer_start,
                "priority": -i,
                "density_weight": compute_density_weight(-(outer_start + actual_width // 2), sqrt_N),
                "expected_gap": expected_prime_gap(sqrt_N + outer_start)
            }
            bands.append(band_neg)
            band_id += 1
            
            outer_start += actual_width
    
    # Sort by priority (descending)
    bands.sort(key=lambda b: b["priority"], reverse=True)
    
    return bands


def export_bands_jsonl(bands: List[Dict], N: int, output_path: str):
    """
    Export bands to JSON Lines format with metadata header.
    
    Args:
        bands: List of band dictionaries
        N: Target semiprime
        output_path: Output file path
    """
    sqrt_N = compute_sqrt_n(N)
    
    with open(output_path, 'w') as f:
        # Write metadata as first line
        metadata = {
            "_metadata": True,
            "N": str(N),
            "sqrt_N": str(sqrt_N),
            "bit_length": N.bit_length(),
            "expected_gap": expected_prime_gap(sqrt_N),
            "band_count": len(bands),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "z5d_band_oracle.py"
        }
        f.write(json.dumps(metadata) + "\n")
        
        # Write each band
        for band in bands:
            f.write(json.dumps(band) + "\n")


def load_bands_jsonl(path: str) -> Tuple[Dict, List[Dict]]:
    """
    Load bands from JSON Lines file.
    
    Args:
        path: Path to bands.jsonl
        
    Returns:
        Tuple of (metadata, bands_list)
    """
    metadata = None
    bands = []
    
    with open(path, 'r') as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("_metadata"):
                metadata = obj
            else:
                bands.append(obj)
    
    return metadata, bands


def get_band_for_delta(delta: int, bands: List[Dict]) -> Optional[Dict]:
    """
    Find which band contains a given delta.
    
    Args:
        delta: Offset from √N
        bands: List of bands
        
    Returns:
        Band containing delta, or None
    """
    for band in bands:
        if band["start"] <= delta <= band["end"]:
            return band
    return None


def print_bands_summary(bands: List[Dict], N: int):
    """Print summary of bands."""
    sqrt_N = compute_sqrt_n(N)
    
    print("=" * 70)
    print("Z5D Band Oracle Summary")
    print("=" * 70)
    print(f"Target N: {N}")
    print(f"√N = {sqrt_N}")
    print(f"Expected gap near √N: {expected_prime_gap(sqrt_N):.2f}")
    print(f"Total bands: {len(bands)}")
    print()
    
    inner_bands = [b for b in bands if b["type"] == "inner"]
    outer_bands = [b for b in bands if b["type"] == "outer"]
    
    print(f"Inner bands: {len(inner_bands)}")
    print(f"Outer bands: {len(outer_bands)}")
    print()
    
    total_coverage = sum(b["width"] for b in bands)
    print(f"Total δ coverage: ±{total_coverage // 2:,}")
    print()
    
    print("Top 10 bands by priority:")
    for i, band in enumerate(bands[:10]):
        print(f"  {i+1}. Band {band['id']}: δ ∈ [{band['start']:+,}, {band['end']:+,}] "
              f"(width={band['width']:,}, priority={band['priority']}, type={band['type']})")
    
    print("=" * 70)


if __name__ == "__main__":
    # Generate bands for 127-bit challenge
    print("Z5D Band Oracle - Generating bands for 127-bit challenge")
    print()
    
    # Generate bands
    bands = generate_bands(
        CHALLENGE_127,
        max_delta=10**7,
        inner_band_count=20,
        outer_band_count=10
    )
    
    # Print summary
    print_bands_summary(bands, CHALLENGE_127)
    
    # Export to JSON Lines
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "bands.jsonl")
    
    export_bands_jsonl(bands, CHALLENGE_127, output_path)
    print()
    print(f"Bands exported to: {output_path}")
    
    # Verify known factors are in bands
    sqrt_N = compute_sqrt_n(CHALLENGE_127)
    delta_p = P_EXPECTED - sqrt_N
    delta_q = Q_EXPECTED - sqrt_N
    
    print()
    print("Verification with known factors:")
    print(f"  p = {P_EXPECTED}")
    print(f"  q = {Q_EXPECTED}")
    print(f"  δ_p = p - √N = {delta_p:+,}")
    print(f"  δ_q = q - √N = {delta_q:+,}")
    
    band_p = get_band_for_delta(delta_p, bands)
    band_q = get_band_for_delta(delta_q, bands)
    
    if band_p:
        print(f"  ✓ p is in band {band_p['id']} (priority={band_p['priority']}, type={band_p['type']})")
    else:
        print(f"  ✗ p is NOT in any band (δ_p too large)")
    
    if band_q:
        print(f"  ✓ q is in band {band_q['id']} (priority={band_q['priority']}, type={band_q['type']})")
    else:
        print(f"  ✗ q is NOT in any band (δ_q too large)")
