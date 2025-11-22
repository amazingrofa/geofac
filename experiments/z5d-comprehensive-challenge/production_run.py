"""
Production Run for 127-bit Challenge
=====================================

Implements optimized Z5D-guided factorization run with heavy instrumentation.

Features:
- Full Z5D mode: wheel + Z5D stepping + FR-GVA ranking
- Z5D prior as metadata for stepping (NOT in score)
- Tight loop optimization
- Heavy instrumentation: log every 10^3 candidates
- Exports run_log.jsonl with per-candidate metrics
- Configurable timeout

Run format:
- Load parameters from challenge_params.json
- Execute search with instrumentation
- Export detailed log for post-analysis
"""

import json
import os
import time
from math import log, isqrt
from typing import Optional, Tuple, Dict
from z5d_pipeline import generate_z5d_candidates


# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717


def load_parameters() -> Dict:
    """Load parameters from challenge_params.json."""
    params_path = os.path.join(
        os.path.dirname(__file__),
        'challenge_params.json'
    )
    
    if not os.path.exists(params_path):
        print(f"Error: {params_path} not found.")
        print("Run parameterize_127bit.py first.")
        exit(1)
    
    with open(params_path, 'r') as f:
        return json.load(f)


def production_run(N: int,
                  params: Dict,
                  timeout_seconds: int = 3600,
                  log_interval: int = 1000) -> Optional[Tuple[int, int]]:
    """
    Execute production factorization run.
    
    Args:
        N: Semiprime to factor
        params: Parameter dict from parameterize_127bit
        timeout_seconds: Maximum runtime
        log_interval: Log every N candidates
        
    Returns:
        Tuple (p, q) if factors found, None otherwise
    """
    print("=" * 70)
    print("Production Run: 127-bit Challenge")
    print("=" * 70)
    print()
    
    sqrt_N = isqrt(N)
    
    # Extract parameters
    total_budget = params['budget']['total_budget']
    delta_max = params['budget']['delta_max']
    num_bands = params['z5d_config']['num_bands']
    k_value = params['z5d_config']['k_value']
    
    print(f"N = {N}")
    print(f"√N = {sqrt_N}")
    print(f"Bit-length: {N.bit_length()}")
    print()
    print("Parameters:")
    print(f"  Total budget: {total_budget:,} candidates")
    print(f"  δ_max: {delta_max:,}")
    print(f"  Bands: {num_bands}")
    print(f"  k-value: {k_value}")
    print(f"  Timeout: {timeout_seconds}s")
    print(f"  Log interval: every {log_interval} candidates")
    print()
    
    # Open log file
    log_path = os.path.join(
        os.path.dirname(__file__),
        'run_log.jsonl'
    )
    
    with open(log_path, 'w') as log_file:
        # Write header
        log_file.write(json.dumps({
            'type': 'header',
            'N': str(N),
            'sqrt_N': str(sqrt_N),
            'params': params,
            'start_time': time.time()
        }) + '\n')
        log_file.flush()
        
        print("Starting search...")
        print()
        
        start_time = time.time()
        tested = 0
        last_log_time = start_time
        
        # Generate candidates
        for cand_data in generate_z5d_candidates(
            N, sqrt_N, delta_max, num_bands, k_value, verbose=False
        ):
            candidate = cand_data['candidate']
            
            # Test divisibility
            if N % candidate == 0:
                p = candidate
                q = N // p
                
                elapsed = time.time() - start_time
                
                # Log success
                success_record = {
                    'type': 'success',
                    'p': str(p),
                    'q': str(q),
                    'candidate': str(candidate),
                    'tested': tested + 1,
                    'elapsed_seconds': elapsed,
                    'metadata': cand_data
                }
                log_file.write(json.dumps(success_record) + '\n')
                log_file.flush()
                
                print(f"\n{'*' * 70}")
                print("FACTOR FOUND!")
                print('*' * 70)
                print(f"p = {p}")
                print(f"q = {q}")
                print(f"N = p × q = {N}")
                print(f"Verified: {p * q == N}")
                print()
                print(f"Candidates tested: {tested + 1:,}")
                print(f"Time elapsed: {elapsed:.2f}s")
                print(f"Rate: {(tested + 1) / elapsed:.0f} candidates/sec")
                print('*' * 70)
                
                return (p, q)
            
            tested += 1
            
            # Instrumentation logging
            if tested % log_interval == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                rate = tested / elapsed if elapsed > 0 else 0
                
                log_record = {
                    'type': 'progress',
                    'tested': tested,
                    'elapsed_seconds': elapsed,
                    'rate_per_sec': rate,
                    'candidate': str(candidate),
                    'delta': cand_data['delta'],
                    'residue': cand_data['residue'],
                    'density': cand_data['density'],
                    'amplitude': cand_data['amplitude'],
                    'band_id': cand_data['band_id'],
                    'step': cand_data['step']
                }
                log_file.write(json.dumps(log_record) + '\n')
                log_file.flush()
                
                # Console progress every 10k
                if tested % (log_interval * 10) == 0:
                    print(f"Progress: {tested:,} candidates, "
                          f"{elapsed:.1f}s, {rate:.0f}/sec, "
                          f"δ={cand_data['delta']}, "
                          f"band={cand_data['band_id']}")
            
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                print(f"\nTimeout reached after {tested:,} candidates")
                break
            
            # Check budget
            if tested >= total_budget:
                print(f"\nBudget exhausted after {tested:,} candidates")
                break
        
        # Log completion
        elapsed = time.time() - start_time
        completion_record = {
            'type': 'completion',
            'tested': tested,
            'elapsed_seconds': elapsed,
            'success': False
        }
        log_file.write(json.dumps(completion_record) + '\n')
        log_file.flush()
    
    print(f"\nSearch completed without finding factors")
    print(f"Tested: {tested:,} candidates in {elapsed:.2f}s")
    print(f"Log saved to: {log_path}")
    
    return None


def main():
    """Execute production run."""
    # Load parameters
    params = load_parameters()
    
    # Run with 1-hour timeout
    result = production_run(
        CHALLENGE_127,
        params,
        timeout_seconds=3600,
        log_interval=1000
    )
    
    # Export summary
    summary = {
        'challenge_N': str(CHALLENGE_127),
        'success': result is not None,
        'factors': {
            'p': str(result[0]) if result else None,
            'q': str(result[1]) if result else None
        } if result else None
    }
    
    summary_path = os.path.join(
        os.path.dirname(__file__),
        'production_summary.json'
    )
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print()
    print(f"Summary saved to: {summary_path}")
    
    if result:
        print("\n✓ SUCCESS: 127-bit challenge factored!")
        return 0
    else:
        print("\n✗ FAILED: Could not factor within constraints")
        return 1


if __name__ == "__main__":
    exit(main())
