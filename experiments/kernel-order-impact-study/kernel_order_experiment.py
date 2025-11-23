#!/usr/bin/env python3
"""
Kernel Order (J) Impact Study

Tests whether Dirichlet kernel order J affects factorization success
on validation gate semiprimes.

Hypothesis: J=6 (default) may not be optimal across all scales.
"""

import mpmath as mp
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configure mpmath precision
mp.dps = 100  # Will be adjusted per test case


def dirichlet_amplitude(theta: mp.mpf, J: int) -> mp.mpf:
    """
    Normalized Dirichlet kernel amplitude.
    A(θ) = |sin((2J+1)θ/2) / ((2J+1)sin(θ/2))|
    
    Args:
        theta: Angular parameter
        J: Kernel order (half-width)
    
    Returns:
        Amplitude in [0, 1]
    """
    # Reduce to [-π, π]
    t = theta % (2 * mp.pi)
    if t > mp.pi:
        t -= 2 * mp.pi
    
    th2 = t / 2
    sin_th2 = mp.sin(th2)
    
    # Singularity guard
    eps = mp.mpf(10) ** (-mp.dps + 10)
    if abs(sin_th2) < eps:
        return mp.mpf(1)
    
    two_j_plus_1 = 2 * J + 1
    num = mp.sin(th2 * two_j_plus_1)
    den = sin_th2 * two_j_plus_1
    
    return abs(num / den)


def phase_function(n: int, k: float) -> mp.mpf:
    """
    Geometric phase function φ_k(n) for resonance.
    Simplified version for testing.
    """
    return mp.mpf(2) * mp.pi * ((mp.mpf(n) / mp.phi) ** k)


def try_factor(N: int, p_true: int, q_true: int, J: int, 
               samples: int = 3000, m_span: int = 180,
               threshold: float = 0.92, k_lo: float = 0.25, 
               k_hi: float = 0.45, timeout_sec: int = 120) -> Dict:
    """
    Attempt factorization using geometric resonance with specified kernel order J.
    
    Args:
        N: Semiprime to factor
        p_true: True factor p (for validation)
        q_true: True factor q (for validation)
        J: Dirichlet kernel order
        samples: Number of k-samples
        m_span: Window size for m-sweep
        threshold: Amplitude threshold
        k_lo, k_hi: k-value range
        timeout_sec: Timeout in seconds
    
    Returns:
        Dictionary with metrics
    """
    start_time = time.time()
    sqrt_n = mp.sqrt(mp.mpf(N))
    
    candidates_tested = 0
    amplitudes = []
    max_amplitude = mp.mpf(0)
    factors_found = False
    
    # QMC sampling of k using golden ratio
    phi_inv = mp.mpf(1) / mp.phi
    
    for i in range(samples):
        # Check timeout
        if time.time() - start_time > timeout_sec:
            break
        
        # QMC k-value
        k = k_lo + (k_hi - k_lo) * ((i * phi_inv) % 1)
        
        # Sweep m around sqrt(N)
        for m_offset in range(-m_span, m_span + 1):
            m = int(sqrt_n) + m_offset
            if m < 2:
                continue
            
            # Compute phase
            theta = phase_function(m, k)
            
            # Dirichlet kernel amplitude
            amp = dirichlet_amplitude(theta, J)
            amplitudes.append(float(amp))
            max_amplitude = max(max_amplitude, amp)
            
            # Check threshold
            if amp >= threshold:
                candidates_tested += 1
                
                # Try factorization (simple trial)
                # Check if m is near a factor
                for delta in range(-10, 11):
                    candidate = m + delta
                    if candidate > 1 and N % candidate == 0:
                        factor = candidate
                        other_factor = N // candidate
                        
                        # Verify
                        if factor * other_factor == N:
                            factors_found = True
                            runtime = time.time() - start_time
                            
                            return {
                                'success': True,
                                'runtime_sec': runtime,
                                'candidates_tested': candidates_tested,
                                'max_amplitude': float(max_amplitude),
                                'mean_amplitude_top100': float(mp.fsum(sorted(amplitudes, reverse=True)[:100]) / min(100, len(amplitudes))),
                                'factors_found': [factor, other_factor],
                                'total_samples_evaluated': len(amplitudes)
                            }
    
    # Failed to find factors
    runtime = time.time() - start_time
    
    return {
        'success': False,
        'runtime_sec': runtime,
        'candidates_tested': candidates_tested,
        'max_amplitude': float(max_amplitude),
        'mean_amplitude_top100': float(mp.fsum(sorted(amplitudes, reverse=True)[:100]) / min(100, len(amplitudes))) if amplitudes else 0.0,
        'factors_found': None,
        'total_samples_evaluated': len(amplitudes)
    }


def run_experiment():
    """
    Main experiment: test J ∈ {3, 6, 9, 12, 15} on validation gates.
    """
    print("=" * 70)
    print("Kernel Order (J) Impact Study")
    print("=" * 70)
    print()
    
    # Test cases: (name, N, p, q, bit_length)
    test_cases = [
        ("Gate1_30bit", 1073217479, 32749, 32771, 30),
        ("Gate2_60bit", 1152921470247108503, 1073741789, 1073741827, 60),
    ]
    
    # J values to test
    j_values = [3, 6, 9, 12, 15]
    
    results = {
        'experiment': 'kernel-order-impact-study',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'j_values_tested': j_values,
        'test_cases': [],
        'summary': {}
    }
    
    # Run experiments
    for test_name, N, p, q, bitlen in test_cases:
        print(f"\n{'='*70}")
        print(f"Test Case: {test_name}")
        print(f"N = {N}")
        print(f"p = {p}, q = {q}")
        print(f"Bit length: {bitlen}")
        print(f"{'='*70}\n")
        
        # Set precision adaptively
        precision_dps = max(50, bitlen * 4 + 200)
        mp.dps = precision_dps
        print(f"Precision: {precision_dps} decimal places\n")
        
        test_results = {
            'name': test_name,
            'N': N,
            'p': p,
            'q': q,
            'bit_length': bitlen,
            'precision_dps': precision_dps,
            'j_results': []
        }
        
        for J in j_values:
            print(f"Testing J = {J}...")
            
            result = try_factor(
                N, p, q, J,
                samples=3000,
                m_span=180,
                threshold=0.92,
                k_lo=0.25,
                k_hi=0.45,
                timeout_sec=120
            )
            
            print(f"  Success: {result['success']}")
            print(f"  Runtime: {result['runtime_sec']:.3f}s")
            print(f"  Max amplitude: {result['max_amplitude']:.6f}")
            print(f"  Candidates tested: {result['candidates_tested']}")
            print()
            
            result['J'] = J
            test_results['j_results'].append(result)
        
        results['test_cases'].append(test_results)
    
    # Compute summary statistics
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for test_case in results['test_cases']:
        test_name = test_case['name']
        print(f"\n{test_name}:")
        print(f"{'J':<5} {'Success':<10} {'Runtime (s)':<15} {'Max Amp':<12} {'Candidates':<12}")
        print("-" * 70)
        
        for jr in test_case['j_results']:
            print(f"{jr['J']:<5} {str(jr['success']):<10} {jr['runtime_sec']:<15.3f} {jr['max_amplitude']:<12.6f} {jr['candidates_tested']:<12}")
    
    # Save results
    output_file = 'results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    print("\nExperiment complete.")


if __name__ == '__main__':
    run_experiment()
