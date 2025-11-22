#!/usr/bin/env python3
"""
Geofac CLI - Router-Based Factorization
========================================

CLI entry point for attacking semiprimes using the portfolio router from PR #96.
Routes between GVA and FR-GVA based on structural features, with fallback support.

Usage:
    python3 geofac.py --n 137524771864208156028430259349934309717 \\
                      --use-router true \\
                      --segments 64 \\
                      --top-k 8 \\
                      --min-random-segments 1 \\
                      --precision 800 \\
                      --max-candidates 700000 \\
                      --k-values 0.30 0.35 0.40
"""

import argparse
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add paths for imports
repo_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'experiments', 'fractal-recursive-gva-falsification'))

import mpmath as mp
from gva_factorization import gva_factor_search, adaptive_precision
from fr_gva_implementation import fr_gva_factor_search, compute_kappa
from portfolio_router import (
    extract_structural_features,
    route_factorization,
    analyze_correlation
)

# Validation constants (from VALIDATION_GATES.md)
CHALLENGE_127 = 137524771864208156028430259349934309717  # Gate 3: 127-bit challenge
RANGE_MIN = 10**14  # Gate 4: Operational range minimum
RANGE_MAX = 10**18  # Gate 4: Operational range maximum


def validate_n(n: int) -> bool:
    """Validate N is in operational range or whitelisted 127-bit challenge."""
    if n == CHALLENGE_127:
        return True
    if RANGE_MIN <= n <= RANGE_MAX:
        return True
    return False


def compute_features(n: int, verbose: bool = True) -> dict:
    """
    Compute structural features for router decision.
    
    Features:
    - bit_length: Number of bits in N
    - approx_sqrt: Approximate integer square root
    - kappa: Curvature metric κ(N)
    - log_N: Natural logarithm of N
    
    Args:
        n: Semiprime to analyze
        verbose: Enable detailed logging
        
    Returns:
        Dictionary of features
    """
    if verbose:
        print(f"\n{'='*70}")
        print("COMPUTING STRUCTURAL FEATURES")
        print(f"{'='*70}")
    
    features = extract_structural_features(n)
    
    if verbose:
        print(f"N: {n}")
        print(f"Bit length: {features['bit_length']}")
        print(f"Approx sqrt(N): {features['approx_sqrt']}")
        print(f"Kappa (κ): {features['kappa']:.6f}")
        print(f"Log(N): {features['log_N']:.2f}")
    
    return features


def build_routing_rules() -> dict:
    """
    Build routing rules from PR #93 training data.
    
    Returns:
        Routing rules dictionary
    """
    training_data = [
        # FR-GVA successes
        {'N': 100000980001501, 'p': 10000019, 'q': 10000079, 
         'gva_success': False, 'fr_gva_success': True},
        {'N': 500000591440213, 'p': 22360687, 'q': 22360699,
         'gva_success': False, 'fr_gva_success': True},
        {'N': 100000010741094833, 'p': 316227767, 'q': 316227799,
         'gva_success': False, 'fr_gva_success': True},
        
        # GVA successes
        {'N': 1000000088437283, 'p': 31622777, 'q': 31622779,
         'gva_success': True, 'fr_gva_success': False},
        {'N': 10000004400000259, 'p': 100000007, 'q': 100000037,
         'gva_success': True, 'fr_gva_success': False},
        {'N': 1000000016000000063, 'p': 1000000007, 'q': 1000000009,
         'gva_success': True, 'fr_gva_success': False},
    ]
    
    analysis = analyze_correlation(training_data)
    return analysis['routing_rules']


def choose_engine(features: dict, routing_rules: dict, use_router: bool, verbose: bool = True) -> str:
    """
    Choose factorization engine using router.
    
    Args:
        features: Structural features of N
        routing_rules: Routing rules from correlation analysis
        use_router: Whether to use router (vs defaulting to GVA)
        verbose: Enable detailed logging
        
    Returns:
        Chosen method: "FR-GVA" or "GVA"
    """
    if not use_router:
        if verbose:
            print(f"\n{'='*70}")
            print("ENGINE SELECTION: Router disabled, defaulting to GVA")
            print(f"{'='*70}")
        return "GVA"
    
    if verbose:
        print(f"\n{'='*70}")
        print("ENGINE SELECTION VIA ROUTER")
        print(f"{'='*70}")
    
    method = route_factorization(features['N'], routing_rules, verbose=verbose)
    
    if verbose:
        print(f"\n→ Router decision: {method}")
        print(f"{'='*70}")
    
    return method


def execute_engine(n: int, method: str, config: dict, verbose: bool = True) -> tuple:
    """
    Execute chosen factorization engine.
    
    Args:
        n: Semiprime to factor
        method: "FR-GVA" or "GVA"
        config: Configuration parameters
        verbose: Enable detailed logging
        
    Returns:
        Tuple of (factors, metrics)
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"EXECUTING {method}")
        print(f"{'='*70}")
        print(f"Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
    
    # Set adaptive precision
    precision = adaptive_precision(n)
    actual_precision = max(config['precision'], precision)
    mp.mp.dps = actual_precision
    
    if verbose:
        print(f"  adaptive_precision: {precision}")
        print(f"  actual_precision: {actual_precision}")
    
    start_time = time.time()
    
    try:
        if method == "FR-GVA":
            # NOTE: Current FR-GVA implementation (fr_gva_implementation.py) uses
            # max_depth and kappa_threshold parameters, not segments/top-k/min-random-segments.
            # CLI parameters (--segments, --top-k, --min-random-segments) are provided
            # for compatibility with the tech memo specification but are not currently
            # used. Future implementations may adopt these parameters.
            factors = fr_gva_factor_search(
                n,
                max_depth=5,
                kappa_threshold=0.525,
                max_candidates=config['max_candidates'],
                verbose=verbose,
                allow_any_range=True
            )
        else:  # GVA
            factors = gva_factor_search(
                n,
                k_values=config['k_values'],
                max_candidates=config['max_candidates'],
                verbose=verbose,
                allow_any_range=True
            )
        
        elapsed_time = time.time() - start_time
        
        metrics = {
            'method': method,
            'time': elapsed_time,
            'precision': actual_precision,
            'success': factors is not None
        }
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"{method} EXECUTION COMPLETE")
            print(f"{'='*70}")
            print(f"Time: {elapsed_time:.3f}s")
            print(f"Success: {factors is not None}")
        
        return factors, metrics
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"{method} EXECUTION FAILED")
            print(f"{'='*70}")
            print(f"Error: {e}")
            print(f"Time: {elapsed_time:.3f}s")
        
        metrics = {
            'method': method,
            'time': elapsed_time,
            'precision': actual_precision,
            'success': False,
            'error': str(e)
        }
        
        return None, metrics


def validate_factors(n: int, p: int, q: int, verbose: bool = True) -> bool:
    """
    Validate that p * q = N.
    
    Args:
        n: Original semiprime
        p: First factor
        q: Second factor
        verbose: Enable detailed logging
        
    Returns:
        True if valid
    """
    if verbose:
        print(f"\n{'='*70}")
        print("FACTOR VALIDATION")
        print(f"{'='*70}")
    
    valid = (p * q == n)
    
    if verbose:
        print(f"p: {p}")
        print(f"q: {q}")
        print(f"p * q: {p * q}")
        print(f"N: {n}")
        print(f"Valid: {valid}")
    
    return valid


def save_results(output_dir: Path, n: int, features: dict, routing_decision: str, 
                 primary_result: tuple, fallback_result: tuple = None):
    """
    Save experiment results to output directory.
    
    Args:
        output_dir: Directory to save results
        n: Semiprime
        features: Structural features
        routing_decision: Primary method chosen by router
        primary_result: (factors, metrics) from primary attempt
        fallback_result: Optional (factors, metrics) from fallback attempt
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    factors, primary_metrics = primary_result
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'n': str(n),
        'features': {k: str(v) if isinstance(v, (int, float)) else v 
                    for k, v in features.items()},
        'routing_decision': routing_decision,
        'primary_attempt': primary_metrics
    }
    
    if factors:
        p, q = factors
        results['factors'] = {
            'p': str(p),
            'q': str(q),
            'valid': p * q == n,
            'source': 'primary'
        }
    elif fallback_result:
        fallback_factors, fallback_metrics = fallback_result
        results['fallback_attempt'] = fallback_metrics
        
        if fallback_factors:
            p, q = fallback_factors
            results['factors'] = {
                'p': str(p),
                'q': str(q),
                'valid': p * q == n,
                'source': 'fallback'
            }
    
    # Save JSON results
    with open(output_dir / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save human-readable report
    with open(output_dir / 'REPORT.md', 'w') as f:
        f.write(generate_report(n, features, routing_decision, primary_result, fallback_result))


def generate_report(n: int, features: dict, routing_decision: str,
                   primary_result: tuple, fallback_result: tuple = None) -> str:
    """
    Generate human-readable experiment report.
    
    Args:
        n: Semiprime
        features: Structural features
        routing_decision: Primary method chosen by router
        primary_result: (factors, metrics) from primary attempt
        fallback_result: Optional (factors, metrics) from fallback attempt
        
    Returns:
        Markdown-formatted report
    """
    factors, primary_metrics = primary_result
    
    report = []
    report.append("# 127-bit Challenge Router Attack Experiment")
    report.append("")
    report.append(f"**Date:** {datetime.now().isoformat()}")
    report.append("")
    
    # Executive Summary
    report.append("## Executive Summary")
    report.append("")
    
    if factors:
        p, q = factors
        report.append(f"✓ **SUCCESS** - Factors found via {primary_metrics['method']}")
        report.append(f"- Primary engine ({routing_decision}) succeeded")
        report.append(f"- Time: {primary_metrics['time']:.3f}s")
        report.append(f"- Factors: {p} × {q}")
        report.append(f"- Validation: p × q = N ✓")
    elif fallback_result:
        fallback_factors, fallback_metrics = fallback_result
        if fallback_factors:
            p, q = fallback_factors
            other_method = "GVA" if routing_decision == "FR-GVA" else "FR-GVA"
            report.append(f"✓ **SUCCESS VIA FALLBACK** - Factors found via {fallback_metrics['method']}")
            report.append(f"- Primary engine ({routing_decision}) failed after {primary_metrics['time']:.3f}s")
            report.append(f"- Fallback engine ({other_method}) succeeded")
            report.append(f"- Time: {fallback_metrics['time']:.3f}s (fallback only)")
            report.append(f"- Factors: {p} × {q}")
            report.append(f"- Validation: p × q = N ✓")
        else:
            report.append(f"✗ **FAILURE** - Both engines failed")
            report.append(f"- Primary engine ({routing_decision}) failed after {primary_metrics['time']:.3f}s")
            report.append(f"- Fallback engine failed after {fallback_metrics['time']:.3f}s")
    else:
        report.append(f"✗ **FAILURE** - Primary engine failed")
        report.append(f"- Engine ({routing_decision}) failed after {primary_metrics['time']:.3f}s")
        report.append(f"- No fallback attempted")
    
    report.append("")
    
    # Target Details
    report.append("## Target Semiprime")
    report.append("")
    report.append(f"```")
    report.append(f"N = {n}")
    report.append(f"```")
    report.append("")
    
    # Structural Features
    report.append("## Structural Features")
    report.append("")
    report.append(f"- **Bit length:** {features['bit_length']}")
    report.append(f"- **Approx sqrt(N):** {features['approx_sqrt']}")
    report.append(f"- **Kappa (κ):** {features['kappa']:.6f}")
    report.append(f"- **Log(N):** {features['log_N']:.2f}")
    report.append("")
    
    # Router Decision
    report.append("## Router Decision")
    report.append("")
    report.append(f"Based on structural feature analysis, the router selected: **{routing_decision}**")
    report.append("")
    
    # Execution Details
    report.append("## Execution Details")
    report.append("")
    report.append("### Primary Attempt")
    report.append(f"- **Method:** {primary_metrics['method']}")
    report.append(f"- **Precision:** {primary_metrics['precision']} dps")
    report.append(f"- **Time:** {primary_metrics['time']:.3f}s")
    report.append(f"- **Result:** {'Success' if primary_metrics['success'] else 'Failed'}")
    
    if 'error' in primary_metrics:
        report.append(f"- **Error:** {primary_metrics['error']}")
    
    report.append("")
    
    if fallback_result:
        fallback_factors, fallback_metrics = fallback_result
        report.append("### Fallback Attempt")
        report.append(f"- **Method:** {fallback_metrics['method']}")
        report.append(f"- **Precision:** {fallback_metrics['precision']} dps")
        report.append(f"- **Time:** {fallback_metrics['time']:.3f}s")
        report.append(f"- **Result:** {'Success' if fallback_metrics['success'] else 'Failed'}")
        
        if 'error' in fallback_metrics:
            report.append(f"- **Error:** {fallback_metrics['error']}")
        
        report.append("")
    
    # Validation
    if factors or (fallback_result and fallback_result[0]):
        p, q = factors if factors else fallback_result[0]
        report.append("## Validation")
        report.append("")
        report.append("```python")
        report.append(f"p = {p}")
        report.append(f"q = {q}")
        report.append(f"p * q = {p * q}")
        report.append(f"N = {n}")
        report.append(f"Valid: {p * q == n}")
        report.append("```")
        report.append("")
    
    # Reproducibility
    report.append("## Reproducibility")
    report.append("")
    report.append("This experiment uses deterministic methods:")
    report.append("- Fixed precision (adaptive based on bit length)")
    report.append("- Quasi-Monte Carlo sampling (Sobol/Halton sequences)")
    report.append("- No stochastic elements")
    report.append("")
    report.append("All parameters and results are logged for full reproducibility.")
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description='Geofac - Router-based factorization for semiprimes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--n', type=int, required=True,
                       help='Semiprime to factor')
    parser.add_argument('--use-router', type=lambda x: x.lower() == 'true',
                       default=True,
                       help='Use router to choose engine (default: true)')
    parser.add_argument('--segments', type=int, default=64,
                       help='FR-GVA: Number of segments (default: 64)')
    parser.add_argument('--top-k', type=int, default=8,
                       help='FR-GVA: Number of top segments to search (default: 8)')
    parser.add_argument('--min-random-segments', type=int, default=1,
                       help='FR-GVA: Minimum random segments (default: 1)')
    parser.add_argument('--precision', type=int, default=800,
                       help='Minimum decimal precision (default: 800)')
    parser.add_argument('--max-candidates', type=int, default=700000,
                       help='Maximum candidates to test (default: 700000)')
    parser.add_argument('--k-values', type=float, nargs='+',
                       default=[0.30, 0.35, 0.40],
                       help='GVA: k-values to try (default: 0.30 0.35 0.40)')
    parser.add_argument('--no-fallback', action='store_true',
                       help='Disable fallback to alternate engine')
    parser.add_argument('--output-dir', type=str,
                       default='experiments/127bit-challenge-router-attack/run',
                       help='Output directory for results')
    parser.add_argument('--verbose', action='store_true', default=True,
                       help='Enable verbose logging (default: true)')
    
    args = parser.parse_args()
    
    # Validate N
    if not validate_n(args.n):
        print(f"ERROR: N must be in range [{RANGE_MIN}, {RANGE_MAX}] or be the 127-bit challenge")
        print(f"N = {args.n}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print("GEOFAC - ROUTER-BASED FACTORIZATION")
    print(f"{'='*70}")
    print(f"Target: N = {args.n}")
    print(f"Bit length: {args.n.bit_length()}")
    print(f"Use router: {args.use_router}")
    print(f"Fallback enabled: {not args.no_fallback}")
    print(f"{'='*70}")
    
    # Step 1: Compute features
    features = compute_features(args.n, verbose=args.verbose)
    
    # Step 2: Build routing rules
    routing_rules = build_routing_rules()
    
    # Step 3: Choose engine
    primary_method = choose_engine(features, routing_rules, args.use_router, verbose=args.verbose)
    
    # Step 4: Configure engines
    config = {
        'segments': args.segments,
        'top_k': args.top_k,
        'min_random_segments': args.min_random_segments,
        'precision': args.precision,
        'max_candidates': args.max_candidates,
        'k_values': args.k_values
    }
    
    # Step 5: Execute primary engine
    primary_result = execute_engine(args.n, primary_method, config, verbose=args.verbose)
    factors, primary_metrics = primary_result
    
    fallback_result = None
    
    # Step 6: Fallback if needed
    if not factors and not args.no_fallback:
        fallback_method = "GVA" if primary_method == "FR-GVA" else "FR-GVA"
        
        if args.verbose:
            print(f"\n{'='*70}")
            print(f"PRIMARY ENGINE FAILED - ATTEMPTING FALLBACK")
            print(f"{'='*70}")
            print(f"Fallback method: {fallback_method}")
        
        fallback_result = execute_engine(args.n, fallback_method, config, verbose=args.verbose)
        factors, _ = fallback_result
    
    # Step 7: Validate factors
    if factors:
        p, q = factors
        valid = validate_factors(args.n, p, q, verbose=args.verbose)
        
        if valid:
            print(f"\n{'='*70}")
            print("✓ SUCCESS - FACTORS FOUND AND VALIDATED")
            print(f"{'='*70}")
            print(f"p = {p}")
            print(f"q = {q}")
            print(f"p * q = {args.n}")
            
            source = "primary" if primary_metrics['success'] else "fallback"
            method = primary_metrics['method'] if primary_metrics['success'] else fallback_result[1]['method']
            print(f"Source: {source} ({method})")
        else:
            print(f"\n{'='*70}")
            print("✗ VALIDATION FAILED")
            print(f"{'='*70}")
            print(f"p * q ≠ N")
            sys.exit(1)
    else:
        print(f"\n{'='*70}")
        print("✗ FAILURE - NO FACTORS FOUND")
        print(f"{'='*70}")
        if not args.no_fallback:
            print("Both primary and fallback engines failed")
        else:
            print("Primary engine failed, fallback disabled")
        sys.exit(1)
    
    # Step 8: Save results
    output_dir = Path(args.output_dir)
    save_results(output_dir, args.n, features, primary_method, primary_result, fallback_result)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
