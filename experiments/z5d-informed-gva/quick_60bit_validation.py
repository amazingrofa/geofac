"""
Quick 60-bit Validation for Z5D Experiment
===========================================

Quick validation using a 60-bit semiprime to verify all experiment variants work
before running the expensive 127-bit challenge.

60-bit test case: N = 1152921470247108503 = 1073741789 × 1073741827
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from baseline_fr_gva import baseline_fr_gva
from z5d_enhanced_fr_gva import z5d_enhanced_fr_gva
import time
from math import isqrt, log

# 60-bit test case (Gate 2)
N_60BIT = 1152921470247108503
P_60BIT = 1073741789
Q_60BIT = 1073741827

def run_60bit_validation():
    """Run quick 60-bit validation on all 4 variants."""
    
    print("=" * 70)
    print("60-bit Validation Test")
    print("=" * 70)
    print(f"N = {N_60BIT}")
    print(f"Expected: p = {P_60BIT}, q = {Q_60BIT}")
    print(f"√N ≈ {isqrt(N_60BIT)}")
    print()
    
    # Reduced parameters for quick test
    MAX_CANDIDATES = 5000
    DELTA_WINDOW = 50000
    Z5D_BETA = 0.1
    
    density_file = os.path.join(os.path.dirname(__file__), "z5d_density_histogram.csv")
    
    results = []
    
    # Test 1: Baseline
    print("Testing 1/4: Baseline FR-GVA...")
    start = time.time()
    result = baseline_fr_gva(
        N_60BIT,
        k_value=0.35,
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        verbose=False
    )
    elapsed = time.time() - start
    success = result is not None and result[0] * result[1] == N_60BIT
    results.append(("Baseline", success, elapsed, result))
    print(f"  Result: {'SUCCESS' if success else 'FAILED'} in {elapsed:.2f}s")
    if success:
        print(f"  Factors: {result[0]} × {result[1]}")
    print()
    
    # Test 2: Wheel filter only
    print("Testing 2/4: Wheel Filter Only...")
    start = time.time()
    result = z5d_enhanced_fr_gva(
        N_60BIT,
        z5d_density_file=None,
        k_value=0.35,
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        z5d_weight_beta=0.0,
        use_wheel_filter=True,
        use_z5d_stepping=False,
        verbose=False
    )
    elapsed = time.time() - start
    success = result is not None and result[0] * result[1] == N_60BIT
    results.append(("Wheel Only", success, elapsed, result))
    print(f"  Result: {'SUCCESS' if success else 'FAILED'} in {elapsed:.2f}s")
    if success:
        print(f"  Factors: {result[0]} × {result[1]}")
    print()
    
    # Test 3: Z5D prior only
    print("Testing 3/4: Z5D Prior Only...")
    start = time.time()
    result = z5d_enhanced_fr_gva(
        N_60BIT,
        z5d_density_file=density_file,
        k_value=0.35,
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        z5d_weight_beta=Z5D_BETA,
        use_wheel_filter=False,
        use_z5d_stepping=False,
        verbose=False
    )
    elapsed = time.time() - start
    success = result is not None and result[0] * result[1] == N_60BIT
    results.append(("Z5D Prior Only", success, elapsed, result))
    print(f"  Result: {'SUCCESS' if success else 'FAILED'} in {elapsed:.2f}s")
    if success:
        print(f"  Factors: {result[0]} × {result[1]}")
    print()
    
    # Test 4: Full Z5D
    print("Testing 4/4: Full Z5D Enhancement...")
    start = time.time()
    result = z5d_enhanced_fr_gva(
        N_60BIT,
        z5d_density_file=density_file,
        k_value=0.35,
        max_candidates=MAX_CANDIDATES,
        delta_window=DELTA_WINDOW,
        z5d_weight_beta=Z5D_BETA,
        use_wheel_filter=True,
        use_z5d_stepping=True,
        verbose=False
    )
    elapsed = time.time() - start
    success = result is not None and result[0] * result[1] == N_60BIT
    results.append(("Full Z5D", success, elapsed, result))
    print(f"  Result: {'SUCCESS' if success else 'FAILED'} in {elapsed:.2f}s")
    if success:
        print(f"  Factors: {result[0]} × {result[1]}")
    print()
    
    # Summary
    print("=" * 70)
    print("60-bit Validation Summary")
    print("=" * 70)
    print(f"{'Variant':<20} {'Success':<10} {'Time (s)':<10}")
    print("-" * 70)
    for name, success, elapsed, result in results:
        status = "✓" if success else "✗"
        print(f"{name:<20} {status:<10} {elapsed:.2f}")
    print("=" * 70)
    print()
    
    # Determine if we're ready for 127-bit
    any_success = any(r[1] for r in results)
    if any_success:
        print("✓ 60-bit validation PASSED - at least one variant succeeded")
        print("  Ready to proceed with 127-bit challenge")
    else:
        print("✗ 60-bit validation FAILED - no variant succeeded")
        print("  Consider adjusting parameters before 127-bit challenge")
    
    return results


if __name__ == "__main__":
    run_60bit_validation()
