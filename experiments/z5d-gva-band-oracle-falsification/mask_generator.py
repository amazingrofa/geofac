"""
Wheel Residue Mask Generator (Modulus 2310)
============================================

Generates allowed residue classes coprime to 2×3×5×7×11 = 2310.

This is an upgrade from the mod 210 wheel used in z5d-informed-gva.
The mod 2310 wheel provides stronger pruning:
  - φ(2310) = 480 residues out of 2310
  - Pruning factor: (2310 - 480) / 2310 ≈ 79.22%
  - Improvement over mod 210: ~2.08% more pruning

Output: mask.json with reproducibility metadata.

Validation: 127-bit challenge N = 137524771864208156028430259349934309717
"""

import json
from math import gcd
from datetime import datetime, timezone
from typing import List, Dict, Set

# Wheel modulus: 2 × 3 × 5 × 7 × 11 = 2310
WHEEL_PRIMES = [2, 3, 5, 7, 11]
WHEEL_MODULUS = 2 * 3 * 5 * 7 * 11  # 2310


def compute_admissible_residues(modulus: int, primes: List[int]) -> List[int]:
    """
    Compute all residues coprime to modulus.
    
    Args:
        modulus: Wheel modulus
        primes: Small primes dividing modulus
        
    Returns:
        Sorted list of residues r such that gcd(r, modulus) = 1
    """
    residues = []
    for r in range(1, modulus):
        if gcd(r, modulus) == 1:
            residues.append(r)
    return residues


def compute_euler_totient(n: int) -> int:
    """Compute φ(n) using factorization."""
    result = n
    p = 2
    while p * p <= n:
        if n % p == 0:
            while n % p == 0:
                n //= p
            result -= result // p
        p += 1
    if n > 1:
        result -= result // n
    return result


def is_admissible(n: int, residue_set: Set[int], modulus: int) -> bool:
    """
    Check if n is in an admissible residue class.
    
    Args:
        n: Integer to check
        residue_set: Set of allowed residues
        modulus: Wheel modulus
        
    Returns:
        True if n ≡ r (mod modulus) for some r in residue_set
    """
    return (n % modulus) in residue_set


def generate_mask(output_path: str) -> Dict:
    """
    Generate wheel mask and export to JSON.
    
    Args:
        output_path: Path to output JSON file
        
    Returns:
        Mask data dictionary
    """
    residues = compute_admissible_residues(WHEEL_MODULUS, WHEEL_PRIMES)
    residue_set = set(residues)
    
    # Compute statistics
    pruning_factor = (WHEEL_MODULUS - len(residues)) / WHEEL_MODULUS
    coverage_factor = len(residues) / WHEEL_MODULUS
    
    # Build mask data with reproducibility metadata
    mask_data = {
        "metadata": {
            "description": "Wheel residue mask for Z5D-GVA Band Oracle experiment",
            "modulus": WHEEL_MODULUS,
            "primes": WHEEL_PRIMES,
            "phi_modulus": len(residues),
            "pruning_factor": pruning_factor,
            "coverage_factor": coverage_factor,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "mask_generator.py",
            "purpose": "Filter candidates to admissible residue classes only"
        },
        "residues": residues,
        "count": len(residues)
    }
    
    # Export to JSON
    with open(output_path, 'w') as f:
        json.dump(mask_data, f, indent=2)
    
    return mask_data


def load_mask(path: str) -> Set[int]:
    """
    Load mask from JSON file.
    
    Args:
        path: Path to mask.json
        
    Returns:
        Set of allowed residues
    """
    with open(path, 'r') as f:
        data = json.load(f)
    return set(data["residues"])


def print_mask_info(mask_data: Dict):
    """Print mask statistics."""
    meta = mask_data["metadata"]
    print("=" * 60)
    print("Wheel Residue Mask (Modulus 2310)")
    print("=" * 60)
    print(f"Modulus: {meta['modulus']}")
    print(f"Small primes: {meta['primes']}")
    print(f"φ(2310) = {meta['phi_modulus']} admissible residues")
    print(f"Pruning factor: {meta['pruning_factor']:.2%}")
    print(f"Coverage factor: {meta['coverage_factor']:.4f}")
    print()
    print(f"First 20 residues: {mask_data['residues'][:20]}...")
    print(f"Last 5 residues: {mask_data['residues'][-5:]}")
    print("=" * 60)


if __name__ == "__main__":
    import os
    
    # Output path
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "mask.json")
    
    print("Generating wheel mask (mod 2310)...")
    print()
    
    mask_data = generate_mask(output_path)
    print_mask_info(mask_data)
    
    print()
    print(f"Mask exported to: {output_path}")
    
    # Verify by loading
    print()
    print("Verification: Loading mask and testing...")
    residue_set = load_mask(output_path)
    
    test_values = [1, 2, 11, 13, 17, 23, 121, 143, 2309, 2310]
    for n in test_values:
        result = is_admissible(n, residue_set, WHEEL_MODULUS)
        expected = gcd(n, WHEEL_MODULUS) == 1
        status = "✓" if result == expected else "✗"
        print(f"  {status} is_admissible({n}) = {result} (expected: {expected})")
