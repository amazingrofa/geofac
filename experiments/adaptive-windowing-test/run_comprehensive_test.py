"""
Comprehensive Adaptive Windowing Analysis
==========================================

Runs the adaptive windowing test across all validation gates and
documents findings for FINDINGS.md.
"""

import json
import time
from adversarial_test_adaptive import AdaptiveFactorization


# Validation gates from docs/validation/VALIDATION_GATES.md
VALIDATION_GATES = {
    'gate1_30bit': {
        'N': 1073217479,
        'p': 32749,
        'q': 32771,
        'bits': 30,
        'name': 'Gate 1 (30-bit Quick Check)'
    },
    'gate2_60bit': {
        'N': 1152921470247108503,
        'p': 1073741789,
        'q': 1073741827,
        'bits': 60,
        'name': 'Gate 2 (60-bit Scaling)'
    },
    'gate3_127bit': {
        'N': 137524771864208156028430259349934309717,
        'p': 10508623501177419659,
        'q': 13086849276577416863,
        'bits': 127,
        'name': 'Gate 3 (127-bit CHALLENGE)'
    }
}


def run_comprehensive_test(seed=42):
    """Run adaptive windowing test on all validation gates."""
    
    results = {}
    
    print("=" * 80)
    print("COMPREHENSIVE ADAPTIVE WINDOWING FALSIFICATION TEST")
    print("=" * 80)
    print(f"\nSeed: {seed}")
    print(f"Target enrichment: 5.0x")
    print(f"Windows: [0.13, 0.20, 0.30, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0]")
    print("\n")
    
    for gate_id, gate_data in VALIDATION_GATES.items():
        print("=" * 80)
        print(f"{gate_data['name']}")
        print("=" * 80)
        print(f"N = {gate_data['N']}")
        print(f"p = {gate_data['p']}")
        print(f"q = {gate_data['q']}")
        print(f"Bits: {gate_data['bits']}")
        print()
        
        solver = AdaptiveFactorization(
            gate_data['N'],
            target_enrichment=5.0,
            seed=seed
        )
        
        start_time = time.time()
        top_candidates = solver.run(
            p=gate_data['p'],
            q=gate_data['q'],
            verbose=True
        )
        total_time = time.time() - start_time
        
        # Check if true factors were found
        if top_candidates:
            found_p = any(c == gate_data['p'] for c, _ in top_candidates)
            found_q = any(c == gate_data['q'] for c, _ in top_candidates)
            factors_found = found_p or found_q
        else:
            factors_found = False
        
        # Store results
        results[gate_id] = {
            'name': gate_data['name'],
            'N': str(gate_data['N']),
            'p': str(gate_data['p']),
            'q': str(gate_data['q']),
            'bits': gate_data['bits'],
            'signal_lock_achieved': top_candidates is not None,
            'factors_found': factors_found,
            'total_time': total_time,
            'top_3_candidates': [
                {'candidate': str(c), 'score': s}
                for c, s in (top_candidates[:3] if top_candidates else [])
            ]
        }
        
        print(f"\n{'=' * 80}")
        print(f"SUMMARY FOR {gate_data['name']}")
        print(f"{'=' * 80}")
        print(f"Signal lock achieved: {results[gate_id]['signal_lock_achieved']}")
        print(f"True factors found: {results[gate_id]['factors_found']}")
        print(f"Total time: {total_time:.2f}s")
        print("\n")
    
    # Overall summary
    print("=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    
    signal_locks = sum(1 for r in results.values() if r['signal_lock_achieved'])
    factors_found = sum(1 for r in results.values() if r['factors_found'])
    
    print(f"Gates tested: {len(results)}")
    print(f"Signal locks achieved: {signal_locks}/{len(results)}")
    print(f"True factors found: {factors_found}/{len(results)}")
    print()
    
    # Save results
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to results.json")
    
    return results


def analyze_results(results):
    """Analyze results and provide verdict."""
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Check falsification criteria
    signal_locks = sum(1 for r in results.values() if r['signal_lock_achieved'])
    factors_found = sum(1 for r in results.values() if r['factors_found'])
    slow_runs = sum(1 for r in results.values() if r['total_time'] > 60)
    
    print("\nFalsification Criteria:")
    print(f"1. Enrichment score never reaches >5x threshold: {signal_locks == 0}")
    print(f"2. Top candidates do not include true factors: {factors_found == 0}")
    print(f"3. Runtime exceeds 60 seconds: {slow_runs > 0}")
    print(f"4. Method fails on validation gates: {signal_locks < len(results)}")
    
    print("\nObservations:")
    print(f"- Signal locks achieved on {signal_locks}/{len(results)} gates")
    print(f"- True factors found on {factors_found}/{len(results)} gates")
    print(f"- Average runtime: {sum(r['total_time'] for r in results.values()) / len(results):.2f}s")
    
    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    
    if factors_found == 0 and signal_locks > 0:
        print("\nHypothesis PARTIALLY FALSIFIED:")
        print("- Mock Z5D scoring achieves >5x enrichment signal")
        print("- However, true factors are NOT in top-ranked candidates")
        print("- This suggests that random scoring can produce false signal locks")
        print("- The adaptive windowing strategy alone is insufficient")
        print("- Actual geometric resonance scoring is critical for success")
    elif factors_found == 0 and signal_locks == 0:
        print("\nHypothesis DECISIVELY FALSIFIED:")
        print("- Neither signal lock nor factor detection achieved")
        print("- Method provides no predictive signal")
    elif factors_found == len(results):
        print("\nHypothesis SUPPORTED:")
        print("- All gates achieved signal lock and found true factors")
    else:
        print("\nHypothesis PARTIALLY SUPPORTED:")
        print(f"- {factors_found}/{len(results)} gates found true factors")
    
    print()


if __name__ == '__main__':
    results = run_comprehensive_test(seed=42)
    analyze_results(results)
