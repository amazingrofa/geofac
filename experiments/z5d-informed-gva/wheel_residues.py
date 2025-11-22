"""
Wheel Residue Classes (Modulus 210)
====================================

Implements residue class filtering for candidate pruning.

The wheel of modulus 210 = 2 × 3 × 5 × 7 contains residue classes
coprime to the small primes. Only these residues can be prime (except 2,3,5,7).

Key properties:
- φ(210) = 48 residues coprime to 210
- Pruning factor: (210 - 48) / 210 ≈ 77.14%
- Deterministic: no probabilistic filtering

This is a direct transfer from Z5D Prime Predictor wheel methodology.
"""

from typing import List, Set


# Residues coprime to 210 (mod 210)
WHEEL_210_RESIDUES = [
    1, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103,
    107, 109, 113, 121, 127, 131, 137, 139, 143, 149, 151,
    157, 163, 167, 169, 173, 179, 181, 187, 191, 193, 197,
    199, 209
]

WHEEL_MODULUS = 210
WHEEL_SIZE = len(WHEEL_210_RESIDUES)

# Precompute residue set for O(1) lookup
WHEEL_RESIDUE_SET = set(WHEEL_210_RESIDUES)


def is_admissible(n: int) -> bool:
    """
    Check if n is in an admissible residue class (mod 210).
    
    Args:
        n: Integer to check
        
    Returns:
        True if n ≡ r (mod 210) for some r in WHEEL_210_RESIDUES
    """
    return (n % WHEEL_MODULUS) in WHEEL_RESIDUE_SET


def next_admissible(n: int) -> int:
    """
    Find the next admissible residue ≥ n.
    
    Args:
        n: Starting integer
        
    Returns:
        Smallest m ≥ n such that is_admissible(m)
    """
    residue = n % WHEEL_MODULUS
    
    # Find next admissible residue in this cycle
    for r in WHEEL_210_RESIDUES:
        if r >= residue:
            return n + (r - residue)
    
    # Wrap to next cycle
    return n + (WHEEL_MODULUS - residue) + WHEEL_210_RESIDUES[0]


def prev_admissible(n: int) -> int:
    """
    Find the previous admissible residue ≤ n.
    
    Args:
        n: Starting integer
        
    Returns:
        Largest m ≤ n such that is_admissible(m)
    """
    residue = n % WHEEL_MODULUS
    
    # Find previous admissible residue in this cycle
    for r in reversed(WHEEL_210_RESIDUES):
        if r <= residue:
            return n - (residue - r)
    
    # Wrap to previous cycle
    return n - residue - (WHEEL_MODULUS - WHEEL_210_RESIDUES[-1])


def admissible_in_range(start: int, end: int) -> List[int]:
    """
    Generate all admissible integers in [start, end].
    
    Args:
        start: Range start (inclusive)
        end: Range end (inclusive)
        
    Returns:
        List of admissible integers in [start, end]
    """
    result = []
    current = next_admissible(start)
    
    while current <= end:
        result.append(current)
        # Jump to next residue
        current_residue = current % WHEEL_MODULUS
        residue_idx = WHEEL_210_RESIDUES.index(current_residue)
        
        if residue_idx < WHEEL_SIZE - 1:
            # Next residue in same cycle
            next_residue = WHEEL_210_RESIDUES[residue_idx + 1]
            current += (next_residue - current_residue)
        else:
            # Wrap to next cycle
            current += (WHEEL_MODULUS - current_residue) + WHEEL_210_RESIDUES[0]
    
    return result


def count_admissible_in_range(start: int, end: int) -> int:
    """
    Count admissible integers in [start, end] without generating them.
    
    More efficient than len(admissible_in_range(start, end)) for large ranges.
    
    Args:
        start: Range start (inclusive)
        end: Range end (inclusive)
        
    Returns:
        Number of admissible integers in range
    """
    if start > end:
        return 0
    
    # Check if start and end are in same cycle
    start_cycle = start // WHEEL_MODULUS
    end_cycle = end // WHEEL_MODULUS
    
    if start_cycle == end_cycle:
        # Single partial cycle
        start_residue = start % WHEEL_MODULUS
        end_residue = end % WHEEL_MODULUS
        count = sum(1 for r in WHEEL_210_RESIDUES if start_residue <= r <= end_residue)
        return count
    
    # Multiple cycles: count full cycles + partial ends
    full_cycles = end_cycle - start_cycle - 1
    count = full_cycles * WHEEL_SIZE
    
    # Add partial cycle at start (from start_residue to end of cycle)
    start_residue = start % WHEEL_MODULUS
    start_in_cycle = sum(1 for r in WHEEL_210_RESIDUES if r >= start_residue)
    count += start_in_cycle
    
    # Add partial cycle at end (from start of cycle to end_residue)
    end_residue = end % WHEEL_MODULUS
    end_in_cycle = sum(1 for r in WHEEL_210_RESIDUES if r <= end_residue)
    count += end_in_cycle
    
    return count


def effective_coverage(delta_span: int) -> float:
    """
    Compute effective coverage after wheel filtering.
    
    For window×wheel gap rule: effective_span × (48/210) ≫ expected_gap
    
    Args:
        delta_span: Width of δ-window
        
    Returns:
        Effective span = delta_span × (φ(210) / 210)
    """
    return delta_span * (WHEEL_SIZE / WHEEL_MODULUS)


def meets_gap_rule(delta_span: int, expected_gap: float, safety_factor: float = 3.0) -> bool:
    """
    Check if δ-span meets window×wheel ≥ expected gap rule.
    
    From Z5D: "window×wheel modulus ≫ average prime gap" ensures coverage.
    For √N₁₂₇ ≈ 1.17×10^19, expected gap ḡ ≈ log(√N) ≈ 43.67.
    
    Args:
        delta_span: Width of δ-window
        expected_gap: Expected prime gap (typically log(p))
        safety_factor: Multiplicative safety margin (default 3.0 for "≫")
        
    Returns:
        True if effective coverage ≥ safety_factor × expected_gap
    """
    eff_coverage = effective_coverage(delta_span)
    threshold = safety_factor * expected_gap
    return eff_coverage >= threshold


# Module-level diagnostic information
def print_wheel_info():
    """Print wheel statistics."""
    print("Wheel Modulus 210 Information")
    print("=" * 50)
    print(f"Modulus: {WHEEL_MODULUS}")
    print(f"Admissible residues: {WHEEL_SIZE}")
    print(f"Pruning factor: {(WHEEL_MODULUS - WHEEL_SIZE) / WHEEL_MODULUS:.2%}")
    print(f"Coverage factor: {WHEEL_SIZE / WHEEL_MODULUS:.4f}")
    print()
    print(f"Residues: {WHEEL_210_RESIDUES[:12]}...")
    print("=" * 50)


if __name__ == "__main__":
    # Diagnostic tests
    print_wheel_info()
    print()
    
    # Test admissibility
    print("Admissibility tests:")
    test_vals = [1, 2, 11, 12, 210, 211, 221]
    for n in test_vals:
        print(f"  is_admissible({n}) = {is_admissible(n)}")
    print()
    
    # Test range counting
    print("Range counting tests:")
    ranges = [(0, 210), (1000, 2000), (10**6, 10**6 + 10000)]
    for start, end in ranges:
        count = count_admissible_in_range(start, end)
        span = end - start + 1
        print(f"  [{start}, {end}]: {count} admissible ({count/span:.2%} of span)")
    print()
    
    # Test gap rule
    print("Gap rule tests (√N₁₂₇ context):")
    expected_gap = 43.67  # log(√N₁₂₇)
    test_spans = [100, 200, 500, 1000, 2000]
    for span in test_spans:
        meets = meets_gap_rule(span, expected_gap)
        eff = effective_coverage(span)
        print(f"  Δ={span}: effective={eff:.2f}, meets_rule={meets}")
