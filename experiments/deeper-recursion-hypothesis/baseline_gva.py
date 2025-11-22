"""
Baseline GVA adapter for deeper recursion experiment.

Provides simplified interface to gva_factorization.py for comparison
with multi-stage approaches.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import mpmath as mp
import time
from typing import Tuple, Optional, Dict, Any
from gva_factorization import (
    gva_factor_search,
    adaptive_precision,
    embed_torus_geodesic,
    riemannian_distance
)


def baseline_gva(N: int, verbose: bool = False) -> Dict[str, Any]:
    """
    Run baseline GVA factorization and collect metrics.
    
    Args:
        N: Semiprime to factor
        verbose: Enable detailed logging
        
    Returns:
        Dictionary with:
        - success: bool
        - factors: Tuple[int, int] or None
        - runtime: float (seconds)
        - candidates_tested: int (estimated)
        - coverage: float (100% for baseline)
        - method: str
    """
    start_time = time.time()
    
    # Set adaptive precision
    required_dps = adaptive_precision(N)
    mp.mp.dps = required_dps
    
    if verbose:
        print(f"\n=== Baseline GVA ===")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Precision: {required_dps} dps")
    
    # Run GVA with standard parameters
    k_values = [0.30, 0.35, 0.40]
    max_candidates = 50000
    
    result = gva_factor_search(
        N,
        k_values=k_values,
        max_candidates=max_candidates,
        verbose=verbose,
        allow_any_range=True,  # Allow 110-bit test case
        use_geodesic_guidance=True
    )
    
    runtime = time.time() - start_time
    
    # Package results
    output = {
        'success': result is not None,
        'factors': result,
        'runtime': runtime,
        'candidates_tested': max_candidates if result else 0,  # Estimate
        'coverage': 100.0,  # Full window search
        'method': 'baseline_gva',
        'k_values': k_values
    }
    
    if verbose:
        print(f"\nBaseline Results:")
        print(f"  Success: {output['success']}")
        if result:
            p, q = result
            print(f"  p = {p}")
            print(f"  q = {q}")
            print(f"  Verification: {p} × {q} = {p * q} {'✓' if p * q == N else '✗'}")
        print(f"  Runtime: {runtime:.3f}s")
        print(f"  Coverage: {output['coverage']:.1f}%")
    
    return output


if __name__ == "__main__":
    # Test on the 110-bit case from PR #92
    N = 1296000000000003744000000000001183
    # Expected factors: 36000000000000013 × 36000000000000091
    
    result = baseline_gva(N, verbose=True)
    
    if result['success']:
        p, q = result['factors']
        print(f"\n✓ Factorization successful!")
        print(f"p = {p}")
        print(f"q = {q}")
        print(f"Gap: {abs(q - p)}")
    else:
        print(f"\n✗ Factorization failed")
