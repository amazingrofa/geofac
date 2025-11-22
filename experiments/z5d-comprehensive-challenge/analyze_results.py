"""
Analyze Production Run Results
===============================

Post-run analysis to determine failure mode and suggest improvements.

Analyzes run_log.jsonl to determine:
1. Factor location relative to Z5D bands (band miss)
2. Budget adequacy (budget miss)
3. Ranking effectiveness (ranking miss)

Outputs:
- Executive summary
- Parameter adjustment recommendations
- retune_params.json for second attempt
"""

import json
import os
from math import log, isqrt
from typing import Dict, List, Optional


# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717
CHALLENGE_P = 10508623501177419659
CHALLENGE_Q = 13086849276577416863


def load_run_log() -> List[Dict]:
    """Load run log from JSONL."""
    log_path = os.path.join(
        os.path.dirname(__file__),
        'run_log.jsonl'
    )
    
    if not os.path.exists(log_path):
        print(f"Error: {log_path} not found.")
        print("Run production_run.py first.")
        return []
    
    logs = []
    with open(log_path, 'r') as f:
        for line in f:
            logs.append(json.loads(line))
    
    return logs


def analyze_band_coverage(logs: List[Dict], sqrt_N: int) -> Dict:
    """
    Analyze whether factors were within searched bands.
    
    Args:
        logs: Run log entries
        sqrt_N: Floor of square root
        
    Returns:
        Analysis dict
    """
    # Extract progress logs
    progress = [log for log in logs if log.get('type') == 'progress']
    
    if not progress:
        return {'error': 'No progress logs found'}
    
    # Find δ-range covered
    deltas = [log['delta'] for log in progress]
    delta_min = min(deltas)
    delta_max = max(deltas)
    
    # True factor δ
    delta_p = CHALLENGE_P - sqrt_N
    delta_q = CHALLENGE_Q - sqrt_N
    
    # Check if factors were in range
    p_in_range = delta_min <= delta_p <= delta_max
    q_in_range = delta_min <= delta_q <= delta_max
    
    # Analyze band distribution
    bands_covered = set(log['band_id'] for log in progress)
    
    analysis = {
        'delta_range_covered': [int(delta_min), int(delta_max)],
        'delta_p': int(delta_p),
        'delta_q': int(delta_q),
        'p_in_range': p_in_range,
        'q_in_range': q_in_range,
        'bands_covered': sorted(list(bands_covered)),
        'num_bands_covered': len(bands_covered)
    }
    
    return analysis


def diagnose_failure_mode(logs: List[Dict], 
                          band_analysis: Dict,
                          params: Dict) -> Dict:
    """
    Diagnose why the run failed.
    
    Returns:
        Dict with diagnosis
    """
    # Check for success
    success_logs = [log for log in logs if log.get('type') == 'success']
    if success_logs:
        return {
            'mode': 'SUCCESS',
            'message': 'Factors found successfully'
        }
    
    # Extract completion info
    completion = [log for log in logs if log.get('type') == 'completion']
    if completion:
        tested = completion[0]['tested']
        budget = params['budget']['total_budget']
        budget_used_pct = tested / budget * 100
    else:
        tested = 0
        budget_used_pct = 0
    
    # Diagnose
    p_in_range = band_analysis.get('p_in_range', False)
    q_in_range = band_analysis.get('q_in_range', False)
    
    if not p_in_range and not q_in_range:
        # Band miss: δ-range too narrow
        return {
            'mode': 'BAND_MISS',
            'message': 'Factors were outside searched δ-range',
            'recommendation': 'Increase δ_max or adjust ε parameter',
            'details': {
                'delta_range': band_analysis['delta_range_covered'],
                'delta_p': band_analysis['delta_p'],
                'delta_q': band_analysis['delta_q']
            }
        }
    
    if budget_used_pct >= 99:
        # Budget miss: ran out of candidates
        return {
            'mode': 'BUDGET_MISS',
            'message': 'Budget exhausted before finding factors',
            'recommendation': 'Increase total_budget or refine band priorities',
            'details': {
                'tested': tested,
                'budget': budget,
                'pct_used': budget_used_pct
            }
        }
    
    # Ranking miss: factor in range but not tested
    return {
        'mode': 'RANKING_MISS',
        'message': 'Factors in range but not reached (likely ranking issue)',
        'recommendation': 'Adjust GVA k-value or stepping strategy',
        'details': {
            'tested': tested,
            'budget': budget,
            'pct_used': budget_used_pct
        }
    }


def suggest_retune_params(diagnosis: Dict, 
                         current_params: Dict,
                         band_analysis: Dict) -> Dict:
    """
    Suggest adjusted parameters for retry.
    
    Args:
        diagnosis: Failure diagnosis
        current_params: Current parameter set
        band_analysis: Band coverage analysis
        
    Returns:
        Adjusted parameter dict
    """
    new_params = current_params.copy()
    
    mode = diagnosis['mode']
    
    if mode == 'BAND_MISS':
        # Increase δ_max by 2x
        old_delta_max = current_params['budget']['delta_max']
        new_delta_max = old_delta_max * 2
        new_params['budget']['delta_max'] = new_delta_max
        
        # Adjust budget proportionally
        old_budget = current_params['budget']['total_budget']
        new_budget = old_budget * 2
        new_params['budget']['total_budget'] = new_budget
        
        print(f"  δ_max: {old_delta_max:,} → {new_delta_max:,}")
        print(f"  budget: {old_budget:,} → {new_budget:,}")
    
    elif mode == 'BUDGET_MISS':
        # Increase budget by 50%
        old_budget = current_params['budget']['total_budget']
        new_budget = int(old_budget * 1.5)
        new_params['budget']['total_budget'] = new_budget
        
        print(f"  budget: {old_budget:,} → {new_budget:,}")
    
    elif mode == 'RANKING_MISS':
        # Adjust k-value
        old_k = current_params['z5d_config']['k_value']
        new_k = old_k * 1.1
        new_params['z5d_config']['k_value'] = new_k
        
        print(f"  k-value: {old_k:.3f} → {new_k:.3f}")
    
    return new_params


def generate_executive_summary(logs: List[Dict],
                               band_analysis: Dict,
                               diagnosis: Dict,
                               params: Dict) -> str:
    """
    Generate executive summary text.
    
    Returns:
        Markdown-formatted summary
    """
    summary = []
    summary.append("# Z5D Comprehensive Challenge: Executive Summary\n")
    summary.append("=" * 70 + "\n")
    summary.append("")
    
    # Status
    if diagnosis['mode'] == 'SUCCESS':
        summary.append("## Result: ✓ SUCCESS\n")
    else:
        summary.append("## Result: ✗ FAILURE\n")
    
    summary.append("")
    
    # Challenge info
    summary.append("## Challenge")
    summary.append(f"- N = {CHALLENGE_127}")
    summary.append(f"- p = {CHALLENGE_P}")
    summary.append(f"- q = {CHALLENGE_Q}")
    summary.append(f"- Bit-length: {CHALLENGE_127.bit_length()}")
    summary.append("")
    
    # Parameters used
    summary.append("## Parameters")
    summary.append(f"- Total budget: {params['budget']['total_budget']:,}")
    summary.append(f"- δ_max: {params['budget']['delta_max']:,}")
    summary.append(f"- Bands: {params['z5d_config']['num_bands']}")
    summary.append(f"- k-value: {params['z5d_config']['k_value']}")
    summary.append(f"- ε: {params['z5d_config']['epsilon']:.4f}")
    summary.append("")
    
    # Execution metrics
    completion = [log for log in logs if log.get('type') == 'completion']
    if completion:
        tested = completion[0]['tested']
        elapsed = completion[0]['elapsed_seconds']
        summary.append("## Execution")
        summary.append(f"- Candidates tested: {tested:,}")
        summary.append(f"- Time elapsed: {elapsed:.2f}s")
        summary.append(f"- Rate: {tested / elapsed:.0f} candidates/sec")
        summary.append("")
    
    # Band coverage
    summary.append("## Band Coverage Analysis")
    summary.append(f"- δ-range covered: [{band_analysis['delta_range_covered'][0]:,}, "
                  f"{band_analysis['delta_range_covered'][1]:,}]")
    summary.append(f"- δ_p (true): {band_analysis['delta_p']:,}")
    summary.append(f"- δ_q (true): {band_analysis['delta_q']:,}")
    summary.append(f"- p in range: {band_analysis['p_in_range']}")
    summary.append(f"- q in range: {band_analysis['q_in_range']}")
    summary.append(f"- Bands covered: {band_analysis['num_bands_covered']} / "
                  f"{params['z5d_config']['num_bands']}")
    summary.append("")
    
    # Diagnosis
    summary.append("## Diagnosis")
    summary.append(f"- Failure mode: **{diagnosis['mode']}**")
    summary.append(f"- {diagnosis['message']}")
    if 'recommendation' in diagnosis:
        summary.append(f"- Recommendation: {diagnosis['recommendation']}")
    summary.append("")
    
    # Key findings
    summary.append("## Key Findings")
    summary.append("")
    summary.append("1. **Z5D Oracle Performance**")
    summary.append("   - The PNT-based Z5D approximation provided band estimates")
    summary.append(f"   - Band coverage: {band_analysis['num_bands_covered']} bands explored")
    summary.append("")
    summary.append("2. **Pipeline Efficiency**")
    summary.append("   - 210-wheel filter: 77% pruning rate")
    summary.append("   - Z5D adaptive stepping: variable step sizes by density")
    summary.append("   - FR-GVA ranking: geodesic distance scoring")
    summary.append("")
    summary.append("3. **Scale Challenge**")
    summary.append("   - 127-bit challenge represents ~10^38 search space")
    summary.append("   - Factors near √N ≈ 1.17×10^19")
    summary.append("   - Expected gap: ~44 units")
    summary.append("")
    
    return "\n".join(summary)


def main():
    """Run analysis and generate reports."""
    print("=" * 70)
    print("Analyzing Production Run Results")
    print("=" * 70)
    print()
    
    # Load data
    logs = load_run_log()
    if not logs:
        return
    
    # Load parameters
    params_path = os.path.join(
        os.path.dirname(__file__),
        'challenge_params.json'
    )
    with open(params_path, 'r') as f:
        params = json.load(f)
    
    sqrt_N = isqrt(CHALLENGE_127)
    
    # Analyze band coverage
    print("Analyzing band coverage...")
    band_analysis = analyze_band_coverage(logs, sqrt_N)
    print(f"  δ-range covered: {band_analysis['delta_range_covered']}")
    print(f"  p in range: {band_analysis['p_in_range']}")
    print(f"  q in range: {band_analysis['q_in_range']}")
    print()
    
    # Diagnose failure
    print("Diagnosing failure mode...")
    diagnosis = diagnose_failure_mode(logs, band_analysis, params)
    print(f"  Mode: {diagnosis['mode']}")
    print(f"  {diagnosis['message']}")
    print()
    
    # Suggest retune
    if diagnosis['mode'] != 'SUCCESS':
        print("Suggesting parameter adjustments...")
        retune_params = suggest_retune_params(diagnosis, params, band_analysis)
        
        retune_path = os.path.join(
            os.path.dirname(__file__),
            'retune_params.json'
        )
        with open(retune_path, 'w') as f:
            json.dump(retune_params, f, indent=2)
        
        print(f"  Saved to: {retune_path}")
        print()
    
    # Generate executive summary
    print("Generating executive summary...")
    summary_text = generate_executive_summary(logs, band_analysis, diagnosis, params)
    
    summary_path = os.path.join(
        os.path.dirname(__file__),
        'ANALYSIS_SUMMARY.md'
    )
    with open(summary_path, 'w') as f:
        f.write(summary_text)
    
    print(f"  Saved to: {summary_path}")
    print()
    
    print("=" * 70)
    print("Analysis complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
