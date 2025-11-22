#!/usr/bin/env python3
"""
Demonstration: Geometric Resonance Factorization of 127-bit Challenge

This script demonstrates the complete factorization pipeline with a small
sample count for quick verification. For the full factorization attempt,
run geometric_resonance_factorization.py directly.
"""

from geometric_resonance_factorization import (
    GeometricResonanceFactorizer,
    CHALLENGE_127,
    CHALLENGE_127_P,
    CHALLENGE_127_Q,
)

def main():
    print("=" * 70)
    print("Geometric Resonance Factorization - Quick Demo")
    print("=" * 70)
    print()
    
    print("Target: 127-bit Challenge Number")
    print(f"N = {CHALLENGE_127}")
    print(f"Expected p = {CHALLENGE_127_P}")
    print(f"Expected q = {CHALLENGE_127_Q}")
    print()
    
    print("Creating factorizer with reduced parameters for demo...")
    print("(For full factorization attempt, use geometric_resonance_factorization.py)")
    print()
    
    # Create factorizer with small sample count for demo
    factorizer = GeometricResonanceFactorizer(
        samples=1000,  # Reduced for demo (full: 3000 baseline → 26130 adaptive)
        m_span=180,    # Baseline (full: → 762 adaptive)
        J=10,
        threshold=0.92,
        k_lo=0.25,
        k_hi=0.45,
        timeout_seconds=60.0,  # 1 minute for demo (full: 10 minutes → 3 hours adaptive)
        attenuation=0.05,
        enable_scale_adaptive=True,
        seed=42
    )
    
    print("Attempting factorization with demo parameters...")
    print("Note: This may timeout as sample count is reduced for demo purposes.")
    print()
    
    result = factorizer.factor(CHALLENGE_127)
    
    print()
    print("=" * 70)
    
    if result:
        p, q = result
        print("SUCCESS: Factors found!")
        print(f"p = {p}")
        print(f"q = {q}")
        print(f"p × q = {p * q}")
        print(f"Verification: {p * q == CHALLENGE_127}")
        
        if p == CHALLENGE_127_P and q == CHALLENGE_127_Q:
            print("✓ Factors match expected values!")
        elif p == CHALLENGE_127_Q and q == CHALLENGE_127_P:
            print("✓ Factors match expected values (reversed order)!")
        else:
            print("⚠ Factors differ from expected (but still valid if product matches)")
    else:
        print("No factors found with demo parameters.")
        print()
        print("This is expected with reduced sample count.")
        print("For a full factorization attempt with scale-adaptive parameters:")
        print("  python geometric_resonance_factorization.py")
        print()
        print("Or run the slow test:")
        print("  pytest test_geometric_resonance.py -v -m slow")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
