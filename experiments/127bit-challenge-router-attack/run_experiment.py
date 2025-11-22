#!/usr/bin/env python3
"""
127-bit Challenge Router Attack Experiment
===========================================

Attacks the 127-bit challenge semiprime using the portfolio router from PR #96.

Target: N₁₂₇ = 137524771864208156028430259349934309717

Strategy:
1. Compute structural features (bit-length, √N, κ-band)
2. Use router to choose GVA vs FR-GVA
3. Execute chosen engine with 127-bit optimized config
4. Fallback to alternate engine if primary fails
5. Validate factors and generate comprehensive report

Expected factors (for validation):
p = 10508623501177419659
q = 13086849276577416863
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add paths for imports
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

# Challenge constants
CHALLENGE_127 = 137524771864208156028430259349934309717
EXPECTED_P = 10508623501177419659
EXPECTED_Q = 13086849276577416863

# Engine configurations (from tech memo)
CONFIG = {
    'precision': 800,
    'max_candidates': 700000,
    'k_values': [0.30, 0.35, 0.40],
    # FR-GVA specific
    'fr_gva_max_depth': 5,
    'fr_gva_kappa_threshold': 0.525,
}


def build_routing_rules():
    """Build routing rules from PR #93 training data."""
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


def execute_method(n, method, config, verbose=True):
    """Execute factorization method."""
    if verbose:
        print(f"\n{'='*70}")
        print(f"EXECUTING {method}")
        print(f"{'='*70}")
        print(f"Configuration:")
        print(f"  max_candidates: {config['max_candidates']}")
        print(f"  precision: {config['precision']}")
        if method == "FR-GVA":
            print(f"  max_depth: {config['fr_gva_max_depth']}")
            print(f"  kappa_threshold: {config['fr_gva_kappa_threshold']}")
        else:
            print(f"  k_values: {config['k_values']}")
    
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
            factors = fr_gva_factor_search(
                n,
                max_depth=config['fr_gva_max_depth'],
                kappa_threshold=config['fr_gva_kappa_threshold'],
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
        
        elapsed = time.time() - start_time
        
        metrics = {
            'method': method,
            'time': elapsed,
            'precision': actual_precision,
            'success': factors is not None,
        }
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"{method} COMPLETE")
            print(f"{'='*70}")
            print(f"Time: {elapsed:.3f}s")
            print(f"Success: {factors is not None}")
        
        return factors, metrics
        
    except Exception as e:
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"{method} FAILED")
            print(f"{'='*70}")
            print(f"Error: {e}")
            print(f"Time: {elapsed:.3f}s")
        
        metrics = {
            'method': method,
            'time': elapsed,
            'precision': actual_precision,
            'success': False,
            'error': str(e)
        }
        
        return None, metrics


def generate_report(features, routing_decision, primary_result, fallback_result=None):
    """Generate comprehensive markdown report."""
    factors, primary_metrics = primary_result
    
    report = []
    report.append("# 127-bit Challenge Router Attack Experiment")
    report.append("")
    report.append(f"**Date:** {datetime.now().isoformat()}")
    report.append(f"**Experiment:** Attack N₁₂₇ using PR #96 portfolio router")
    report.append("")
    
    # Executive Summary
    report.append("## Executive Summary")
    report.append("")
    
    if factors:
        p, q = factors
        valid = (p * q == CHALLENGE_127)
        expected = ((p == EXPECTED_P and q == EXPECTED_Q) or 
                   (p == EXPECTED_Q and q == EXPECTED_P))
        
        report.append(f"**✓ SUCCESS** - Factors found via {primary_metrics['method']}")
        report.append("")
        report.append(f"- **Primary engine:** {routing_decision}")
        report.append(f"- **Result:** Succeeded")
        report.append(f"- **Time:** {primary_metrics['time']:.3f}s")
        report.append(f"- **Factors:** p = {p}, q = {q}")
        report.append(f"- **Validation:** p × q = N₁₂₇ → {valid} ✓")
        report.append(f"- **Expected factors:** {expected} ✓")
        
    elif fallback_result:
        fallback_factors, fallback_metrics = fallback_result
        
        if fallback_factors:
            p, q = fallback_factors
            valid = (p * q == CHALLENGE_127)
            expected = ((p == EXPECTED_P and q == EXPECTED_Q) or 
                       (p == EXPECTED_Q and q == EXPECTED_P))
            other_method = "GVA" if routing_decision == "FR-GVA" else "FR-GVA"
            
            report.append(f"**✓ SUCCESS VIA FALLBACK** - Factors found via {fallback_metrics['method']}")
            report.append("")
            report.append(f"- **Primary engine:** {routing_decision} (failed)")
            report.append(f"- **Primary time:** {primary_metrics['time']:.3f}s")
            report.append(f"- **Fallback engine:** {other_method} (succeeded)")
            report.append(f"- **Fallback time:** {fallback_metrics['time']:.3f}s")
            report.append(f"- **Factors:** p = {p}, q = {q}")
            report.append(f"- **Validation:** p × q = N₁₂₇ → {valid} ✓")
            report.append(f"- **Expected factors:** {expected} ✓")
            
        else:
            report.append(f"**✗ FAILURE** - Both engines failed")
            report.append("")
            report.append(f"- **Primary engine:** {routing_decision}")
            report.append(f"- **Primary time:** {primary_metrics['time']:.3f}s")
            report.append(f"- **Fallback engine:** {'GVA' if routing_decision == 'FR-GVA' else 'FR-GVA'}")
            report.append(f"- **Fallback time:** {fallback_metrics['time']:.3f}s")
            
            if 'error' in primary_metrics:
                report.append(f"- **Primary error:** {primary_metrics['error']}")
            if 'error' in fallback_metrics:
                report.append(f"- **Fallback error:** {fallback_metrics['error']}")
    else:
        report.append(f"**✗ FAILURE** - Primary engine failed, no fallback attempted")
        report.append("")
        report.append(f"- **Engine:** {routing_decision}")
        report.append(f"- **Time:** {primary_metrics['time']:.3f}s")
        
        if 'error' in primary_metrics:
            report.append(f"- **Error:** {primary_metrics['error']}")
    
    report.append("")
    
    # Target Details
    report.append("## Target Semiprime")
    report.append("")
    report.append("```")
    report.append(f"N₁₂₇ = {CHALLENGE_127}")
    report.append(f"Expected p = {EXPECTED_P}")
    report.append(f"Expected q = {EXPECTED_Q}")
    report.append("```")
    report.append("")
    
    # Structural Features
    report.append("## Structural Features")
    report.append("")
    report.append(f"Computed before router decision:")
    report.append("")
    report.append(f"- **Bit length:** {features['bit_length']}")
    report.append(f"- **Approx sqrt(N):** {features['approx_sqrt']}")
    report.append(f"- **Kappa (κ):** {features['kappa']:.6f}")
    report.append(f"- **Log(N):** {features['log_N']:.2f}")
    report.append("")
    
    # Router Decision
    report.append("## Router Decision")
    report.append("")
    report.append(f"Based on structural feature analysis using PR #96 router:")
    report.append("")
    report.append(f"- **Selected method:** {routing_decision}")
    report.append(f"- **Reasoning:** Feature-based scoring using bit length and κ proximity to training data")
    report.append("")
    
    # Execution Details
    report.append("## Execution Details")
    report.append("")
    report.append("### Configuration (per Tech Memo)")
    report.append("")
    report.append("```python")
    report.append(f"precision: {CONFIG['precision']}")
    report.append(f"max_candidates: {CONFIG['max_candidates']}")
    report.append(f"k_values: {CONFIG['k_values']}")
    report.append(f"fr_gva_max_depth: {CONFIG['fr_gva_max_depth']}")
    report.append(f"fr_gva_kappa_threshold: {CONFIG['fr_gva_kappa_threshold']}")
    report.append("```")
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
        _, fallback_metrics = fallback_result
        report.append("### Fallback Attempt")
        report.append(f"- **Method:** {fallback_metrics['method']}")
        report.append(f"- **Precision:** {fallback_metrics['precision']} dps")
        report.append(f"- **Time:** {fallback_metrics['time']:.3f}s")
        report.append(f"- **Result:** {'Success' if fallback_metrics['success'] else 'Failed'}")
        
        if 'error' in fallback_metrics:
            report.append(f"- **Error:** {fallback_metrics['error']}")
        
        report.append("")
    
    # Validation
    final_factors = factors if factors else (fallback_result[0] if fallback_result else None)
    
    if final_factors:
        p, q = final_factors
        report.append("## Validation")
        report.append("")
        report.append("```python")
        report.append(f"p = {p}")
        report.append(f"q = {q}")
        report.append(f"p * q = {p * q}")
        report.append(f"N₁₂₇ = {CHALLENGE_127}")
        report.append(f"Valid: {p * q == CHALLENGE_127}")
        report.append("")
        report.append(f"Expected p = {EXPECTED_P}")
        report.append(f"Expected q = {EXPECTED_Q}")
        report.append(f"Match: {(p == EXPECTED_P and q == EXPECTED_Q) or (p == EXPECTED_Q and q == EXPECTED_P)}")
        report.append("```")
        report.append("")
    
    # Methodology
    report.append("## Methodology")
    report.append("")
    report.append("### Router Approach (PR #96)")
    report.append("")
    report.append("The portfolio router analyzes structural features to predict which method")
    report.append("(FR-GVA or GVA) is likely to succeed:")
    report.append("")
    report.append("1. **Feature extraction:** bit length, κ curvature, √N")
    report.append("2. **Distance-based scoring:** Compare features to known success patterns")
    report.append("3. **Weighted decision:** Bit length (2x weight) + κ (1x weight)")
    report.append("4. **Fallback strategy:** Try alternate method if first choice fails")
    report.append("")
    report.append("Training data from PR #93 shows complementary success patterns:")
    report.append("- GVA: 50% success (larger bit lengths, larger gaps)")
    report.append("- FR-GVA: 50% success (smaller bit lengths, tighter factors)")
    report.append("- Router with fallback: 100% success (6/6 test cases)")
    report.append("")
    
    # Reproducibility
    report.append("## Reproducibility")
    report.append("")
    report.append("This experiment uses deterministic/quasi-deterministic methods:")
    report.append("")
    report.append("- **Adaptive precision:** max(800, bitLength × 4 + 200) = max(800, 708) = 800 dps")
    report.append("- **No stochastic elements:** Sobol/Halton QMC sequences, phase-corrected snapping")
    report.append("- **Fixed parameters:** All configuration values logged")
    report.append("- **Validation gates:** Whitelist for 127-bit challenge")
    report.append("")
    report.append("To reproduce:")
    report.append("")
    report.append("```bash")
    report.append("cd /home/runner/work/geofac/geofac")
    report.append("python3 geofac.py --n 137524771864208156028430259349934309717 \\")
    report.append("                  --use-router true \\")
    report.append("                  --precision 800 \\")
    report.append("                  --max-candidates 700000 \\")
    report.append("                  --k-values 0.30 0.35 0.40")
    report.append("```")
    report.append("")
    
    # References
    report.append("## References")
    report.append("")
    report.append("- **PR #93:** FR-GVA implementation and complementary success analysis")
    report.append("- **PR #96:** Portfolio router implementation and validation")
    report.append("- **Tech Memo:** Router-based 127-bit attack strategy")
    report.append("- **CODING_STYLE.md:** Validation gates and reproducibility requirements")
    
    return "\n".join(report)


def main():
    output_dir = Path("experiments/127bit-challenge-router-attack/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("127-BIT CHALLENGE ROUTER ATTACK EXPERIMENT")
    print("="*70)
    print(f"Target: N₁₂₇ = {CHALLENGE_127}")
    print(f"Bit length: {CHALLENGE_127.bit_length()}")
    print("="*70)
    
    # Step 1: Compute features
    print(f"\n{'='*70}")
    print("STEP 1: COMPUTE STRUCTURAL FEATURES")
    print(f"{'='*70}")
    
    features = extract_structural_features(CHALLENGE_127)
    
    print(f"Bit length: {features['bit_length']}")
    print(f"Approx sqrt(N): {features['approx_sqrt']}")
    print(f"Kappa (κ): {features['kappa']:.6f}")
    print(f"Log(N): {features['log_N']:.2f}")
    
    # Step 2: Build routing rules
    print(f"\n{'='*70}")
    print("STEP 2: BUILD ROUTING RULES")
    print(f"{'='*70}")
    
    routing_rules = build_routing_rules()
    print("Routing rules built from PR #93 training data")
    
    # Step 3: Router decision
    print(f"\n{'='*70}")
    print("STEP 3: ROUTER DECISION")
    print(f"{'='*70}")
    
    primary_method = route_factorization(CHALLENGE_127, routing_rules, verbose=True)
    
    print(f"\n→ Router selected: {primary_method}")
    
    # Step 4: Execute primary method
    print(f"\n{'='*70}")
    print("STEP 4: EXECUTE PRIMARY ENGINE")
    print(f"{'='*70}")
    
    primary_result = execute_method(CHALLENGE_127, primary_method, CONFIG, verbose=True)
    factors, primary_metrics = primary_result
    
    fallback_result = None
    
    # Step 5: Fallback if needed
    if not factors:
        fallback_method = "GVA" if primary_method == "FR-GVA" else "FR-GVA"
        
        print(f"\n{'='*70}")
        print("STEP 5: FALLBACK TO ALTERNATE ENGINE")
        print(f"{'='*70}")
        print(f"Primary engine failed, trying fallback: {fallback_method}")
        
        fallback_result = execute_method(CHALLENGE_127, fallback_method, CONFIG, verbose=True)
        factors, _ = fallback_result
    
    # Step 6: Validate
    if factors:
        p, q = factors
        valid = (p * q == CHALLENGE_127)
        expected = ((p == EXPECTED_P and q == EXPECTED_Q) or 
                   (p == EXPECTED_Q and q == EXPECTED_P))
        
        print(f"\n{'='*70}")
        print("✓ SUCCESS - FACTORS FOUND")
        print(f"{'='*70}")
        print(f"p = {p}")
        print(f"q = {q}")
        print(f"p × q = N₁₂₇: {valid}")
        print(f"Expected factors: {expected}")
        
        source = "primary" if primary_metrics['success'] else "fallback"
        method = primary_metrics['method'] if primary_metrics['success'] else fallback_result[1]['method']
        print(f"Source: {source} ({method})")
        
    else:
        print(f"\n{'='*70}")
        print("✗ FAILURE - NO FACTORS FOUND")
        print(f"{'='*70}")
        print("Both primary and fallback engines failed")
    
    # Step 7: Generate report
    print(f"\n{'='*70}")
    print("STEP 6: GENERATE REPORT")
    print(f"{'='*70}")
    
    report = generate_report(features, primary_method, primary_result, fallback_result)
    
    # Save report
    report_path = output_dir / "EXPERIMENT_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to: {report_path}")
    
    # Save JSON results
    results = {
        'timestamp': datetime.now().isoformat(),
        'target': str(CHALLENGE_127),
        'expected_p': str(EXPECTED_P),
        'expected_q': str(EXPECTED_Q),
        'features': {k: str(v) if isinstance(v, (int, float)) and k != 'N' 
                    else v for k, v in features.items()},
        'routing_decision': primary_method,
        'primary_attempt': primary_metrics,
    }
    
    if fallback_result:
        _, fallback_metrics = fallback_result
        results['fallback_attempt'] = fallback_metrics
    
    if factors:
        p, q = factors
        results['success'] = True
        results['factors'] = {
            'p': str(p),
            'q': str(q),
            'valid': p * q == CHALLENGE_127,
            'expected': (p == EXPECTED_P and q == EXPECTED_Q) or (p == EXPECTED_Q and q == EXPECTED_P),
            'source': 'primary' if primary_metrics['success'] else 'fallback'
        }
    else:
        results['success'] = False
    
    json_path = output_dir / "results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"JSON results saved to: {json_path}")
    
    print(f"\n{'='*70}")
    print("EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    
    return 0 if factors else 1


if __name__ == '__main__':
    sys.exit(main())
