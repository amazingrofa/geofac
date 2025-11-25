"""
NR Microkernel Experiment Runner
================================

A/B comparison framework for testing the NR microkernel hypothesis.

Compares:
- Baseline: QMC-only (NR disabled)
- Treatment A: QMC+NR(1) - 1 NR step
- Treatment B: QMC+NR(2) - 2 NR steps

Metrics:
- Top-N score lift
- Rank stability
- Hit rate (factor found within budget)
- Runtime and NR overhead

Test cases:
1. Gate 1 (30-bit): 1073217479 = 32749 × 32771
2. Gate 2 (60-bit): 1152921470247108503 = 1073741789 × 1073741827
3. Verified 50-bit: 1125899772623531 = 33554393 × 33554467
4. Verified 64-bit: 18446736050711510819 = 4294966297 × 4294966427
"""

import sys
import os
import time
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
from statistics import mean, stdev
from math import sqrt

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nr_microkernel_gva import (
    gva_factor_search_with_nr, NRConfig, ExperimentMetrics,
    GATE_1_30BIT, GATE_2_60BIT
)


# Falsification criteria thresholds
# These define when the hypothesis is considered falsified
SCORE_LIFT_THRESHOLD = 1.0       # Minimum % score lift to be "significant"
OVERHEAD_THRESHOLD = 15.0        # Maximum % overhead before "excessive"
IMPROVEMENT_RATE_THRESHOLD = 20.0  # Minimum % improvement rate to be "useful"


@dataclass
class TestCase:
    """Test case definition."""
    name: str
    N: int
    expected_p: int
    expected_q: int
    bit_length: int


@dataclass
class TrialResult:
    """Result of a single trial."""
    test_case: str
    treatment: str  # 'baseline', 'nr1', 'nr2'
    success: bool
    time_total: float
    time_nr_overhead: float
    candidates_tested: int
    nr_triggers: int
    nr_improvements: int
    top_10_scores: List[float]
    factor_candidate: int
    factor_score: float


@dataclass
class ComparisonResult:
    """Comparison result for a test case."""
    test_case: str
    baseline_success: bool
    nr1_success: bool
    nr2_success: bool
    baseline_time: float
    nr1_time: float
    nr2_time: float
    nr1_overhead_pct: float
    nr2_overhead_pct: float
    nr1_score_lift: float  # Average top-10 score improvement
    nr2_score_lift: float
    nr1_triggers: int
    nr2_triggers: int
    nr1_improvements: int
    nr2_improvements: int


# Test cases
TEST_CASES = [
    TestCase("Gate 1 (30-bit)", GATE_1_30BIT, 32749, 32771, 30),
    TestCase("Gate 2 (60-bit)", GATE_2_60BIT, 1073741789, 1073741827, 60),
    TestCase("Verified 50-bit", 1125899772623531, 33554393, 33554467, 50),
    TestCase("Verified 64-bit", 18446736050711510819, 4294966297, 4294966427, 64),
]


def run_trial(test_case: TestCase, treatment: str, verbose: bool = False) -> TrialResult:
    """Run a single trial for a test case with specified treatment."""
    
    # Configure NR based on treatment
    if treatment == 'baseline':
        nr_config = NRConfig(enabled=False)
    elif treatment == 'nr1':
        nr_config = NRConfig(enabled=True, max_steps=1)
    elif treatment == 'nr2':
        nr_config = NRConfig(enabled=True, max_steps=2)
    else:
        raise ValueError(f"Unknown treatment: {treatment}")
    
    # Run factorization
    result, metrics = gva_factor_search_with_nr(
        test_case.N,
        nr_config=nr_config,
        verbose=verbose,
        allow_any_range=True
    )
    
    # Check success
    success = False
    if result:
        p, q = result
        success = (p * q == test_case.N) and ({p, q} == {test_case.expected_p, test_case.expected_q})
    
    # Get top 10 scores
    top_10 = sorted(metrics.top_scores, reverse=True)[:10] if metrics.top_scores else []
    
    return TrialResult(
        test_case=test_case.name,
        treatment=treatment,
        success=success,
        time_total=metrics.total_time,
        time_nr_overhead=metrics.nr_overhead_time,
        candidates_tested=metrics.total_candidates,
        nr_triggers=metrics.candidates_triggered,
        nr_improvements=metrics.candidates_improved,
        top_10_scores=top_10,
        factor_candidate=metrics.factor_candidate,
        factor_score=metrics.factor_score
    )


def compare_treatments(test_case: TestCase, verbose: bool = False) -> ComparisonResult:
    """Compare baseline vs NR treatments for a test case."""
    
    print(f"\n{'='*70}")
    print(f"Testing: {test_case.name}")
    print(f"N = {test_case.N}")
    print(f"Expected: {test_case.expected_p} × {test_case.expected_q}")
    print(f"{'='*70}")
    
    # Run baseline
    print("\n[1/3] Running baseline (NR disabled)...")
    baseline = run_trial(test_case, 'baseline', verbose=verbose)
    print(f"  Success: {baseline.success}")
    print(f"  Time: {baseline.time_total:.3f}s")
    print(f"  Candidates: {baseline.candidates_tested}")
    
    # Run NR(1)
    print("\n[2/3] Running NR(1) - 1 NR step...")
    nr1 = run_trial(test_case, 'nr1', verbose=verbose)
    print(f"  Success: {nr1.success}")
    print(f"  Time: {nr1.time_total:.3f}s (NR overhead: {nr1.time_nr_overhead:.3f}s)")
    print(f"  Candidates: {nr1.candidates_tested}")
    print(f"  NR triggers: {nr1.nr_triggers}")
    print(f"  NR improvements: {nr1.nr_improvements}")
    
    # Run NR(2)
    print("\n[3/3] Running NR(2) - 2 NR steps...")
    nr2 = run_trial(test_case, 'nr2', verbose=verbose)
    print(f"  Success: {nr2.success}")
    print(f"  Time: {nr2.time_total:.3f}s (NR overhead: {nr2.time_nr_overhead:.3f}s)")
    print(f"  Candidates: {nr2.candidates_tested}")
    print(f"  NR triggers: {nr2.nr_triggers}")
    print(f"  NR improvements: {nr2.nr_improvements}")
    
    # Compute comparison metrics
    nr1_overhead_pct = ((nr1.time_total - baseline.time_total) / baseline.time_total * 100) if baseline.time_total > 0 else 0
    nr2_overhead_pct = ((nr2.time_total - baseline.time_total) / baseline.time_total * 100) if baseline.time_total > 0 else 0
    
    # Score lift: compare average of top-10 scores
    baseline_avg = mean(baseline.top_10_scores) if baseline.top_10_scores else 0
    nr1_avg = mean(nr1.top_10_scores) if nr1.top_10_scores else 0
    nr2_avg = mean(nr2.top_10_scores) if nr2.top_10_scores else 0
    
    nr1_score_lift = (nr1_avg - baseline_avg) / abs(baseline_avg) * 100 if baseline_avg != 0 else 0
    nr2_score_lift = (nr2_avg - baseline_avg) / abs(baseline_avg) * 100 if baseline_avg != 0 else 0
    
    return ComparisonResult(
        test_case=test_case.name,
        baseline_success=baseline.success,
        nr1_success=nr1.success,
        nr2_success=nr2.success,
        baseline_time=baseline.time_total,
        nr1_time=nr1.time_total,
        nr2_time=nr2.time_total,
        nr1_overhead_pct=nr1_overhead_pct,
        nr2_overhead_pct=nr2_overhead_pct,
        nr1_score_lift=nr1_score_lift,
        nr2_score_lift=nr2_score_lift,
        nr1_triggers=nr1.nr_triggers,
        nr2_triggers=nr2.nr_triggers,
        nr1_improvements=nr1.nr_improvements,
        nr2_improvements=nr2.nr_improvements
    )


def run_full_experiment(verbose: bool = False) -> List[ComparisonResult]:
    """Run full A/B comparison across all test cases."""
    
    print("="*70)
    print("NR MICROKERNEL FALSIFICATION EXPERIMENT")
    print("="*70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Test cases: {len(TEST_CASES)}")
    print(f"Treatments: baseline, NR(1), NR(2)")
    
    results = []
    
    for test_case in TEST_CASES:
        try:
            result = compare_treatments(test_case, verbose=verbose)
            results.append(result)
        except Exception as e:
            print(f"\nERROR in {test_case.name}: {e}")
    
    return results


def analyze_results(results: List[ComparisonResult]) -> Dict:
    """Analyze experiment results and determine verdict."""
    
    analysis = {
        'total_tests': len(results),
        'baseline_successes': sum(1 for r in results if r.baseline_success),
        'nr1_successes': sum(1 for r in results if r.nr1_success),
        'nr2_successes': sum(1 for r in results if r.nr2_success),
        'avg_nr1_overhead_pct': mean([r.nr1_overhead_pct for r in results]) if results else 0,
        'avg_nr2_overhead_pct': mean([r.nr2_overhead_pct for r in results]) if results else 0,
        'avg_nr1_score_lift': mean([r.nr1_score_lift for r in results]) if results else 0,
        'avg_nr2_score_lift': mean([r.nr2_score_lift for r in results]) if results else 0,
        'total_nr1_triggers': sum(r.nr1_triggers for r in results),
        'total_nr2_triggers': sum(r.nr2_triggers for r in results),
        'total_nr1_improvements': sum(r.nr1_improvements for r in results),
        'total_nr2_improvements': sum(r.nr2_improvements for r in results),
    }
    
    # Compute improvement ratio
    if analysis['total_nr1_triggers'] > 0:
        analysis['nr1_improvement_rate'] = analysis['total_nr1_improvements'] / analysis['total_nr1_triggers'] * 100
    else:
        analysis['nr1_improvement_rate'] = 0
    
    if analysis['total_nr2_triggers'] > 0:
        analysis['nr2_improvement_rate'] = analysis['total_nr2_improvements'] / analysis['total_nr2_triggers'] * 100
    else:
        analysis['nr2_improvement_rate'] = 0
    
    # Falsification criteria check using defined thresholds
    # The hypothesis is falsified if:
    # 1. NR shows no significant improvement in score lift (< SCORE_LIFT_THRESHOLD %)
    # 2. Runtime penalty exceeds OVERHEAD_THRESHOLD %
    # 3. Improvement rate is low (< IMPROVEMENT_RATE_THRESHOLD % of triggers)
    # 4. At least 2/3 of test cases show no benefit
    
    falsification_criteria = {
        'no_score_lift': (analysis['avg_nr1_score_lift'] < SCORE_LIFT_THRESHOLD and 
                          analysis['avg_nr2_score_lift'] < SCORE_LIFT_THRESHOLD),
        'excessive_overhead': (analysis['avg_nr1_overhead_pct'] > OVERHEAD_THRESHOLD or 
                               analysis['avg_nr2_overhead_pct'] > OVERHEAD_THRESHOLD),
        'low_improvement_rate': (analysis['nr1_improvement_rate'] < IMPROVEMENT_RATE_THRESHOLD and 
                                 analysis['nr2_improvement_rate'] < IMPROVEMENT_RATE_THRESHOLD),
    }
    
    # Count tests with no benefit
    tests_no_benefit = sum(1 for r in results if r.nr1_score_lift <= 0 and r.nr2_score_lift <= 0)
    falsification_criteria['majority_no_benefit'] = tests_no_benefit >= (len(results) * 2 / 3)
    
    analysis['falsification_criteria'] = falsification_criteria
    analysis['criteria_met'] = sum(1 for v in falsification_criteria.values() if v)
    
    # Verdict: Falsified if 2+ criteria met
    analysis['hypothesis_falsified'] = analysis['criteria_met'] >= 2
    
    return analysis


def generate_report(results: List[ComparisonResult], analysis: Dict) -> str:
    """Generate experiment report."""
    
    report = []
    report.append("# NR Microkernel Falsification Experiment Report")
    report.append("")
    report.append(f"**Date**: {datetime.now().isoformat()}")
    report.append("")
    
    # Executive Summary
    report.append("## Executive Summary")
    report.append("")
    
    if analysis['hypothesis_falsified']:
        report.append("**VERDICT: HYPOTHESIS FALSIFIED**")
        report.append("")
        report.append("The hypothesis that embedding a Newton-Raphson microkernel inside QMC iterations")
        report.append("improves resonance scan peak detection has been **falsified**.")
        report.append("")
        report.append("Key findings:")
        if analysis['falsification_criteria']['no_score_lift']:
            report.append(f"- **No significant score lift**: NR(1) avg lift = {analysis['avg_nr1_score_lift']:.2f}%, NR(2) avg lift = {analysis['avg_nr2_score_lift']:.2f}%")
        if analysis['falsification_criteria']['excessive_overhead']:
            report.append(f"- **Excessive runtime overhead**: NR(1) = {analysis['avg_nr1_overhead_pct']:.1f}%, NR(2) = {analysis['avg_nr2_overhead_pct']:.1f}%")
        if analysis['falsification_criteria']['low_improvement_rate']:
            report.append(f"- **Low improvement rate**: NR(1) = {analysis['nr1_improvement_rate']:.1f}%, NR(2) = {analysis['nr2_improvement_rate']:.1f}%")
        if analysis['falsification_criteria']['majority_no_benefit']:
            report.append(f"- **Majority showed no benefit**: {analysis['criteria_met']}/4 criteria met")
    else:
        report.append("**VERDICT: HYPOTHESIS SUPPORTED (PARTIALLY)**")
        report.append("")
        report.append("The hypothesis shows some evidence of support, but results are inconclusive.")
        report.append(f"- NR(1) average score lift: {analysis['avg_nr1_score_lift']:.2f}%")
        report.append(f"- NR(2) average score lift: {analysis['avg_nr2_score_lift']:.2f}%")
        report.append(f"- NR(1) improvement rate: {analysis['nr1_improvement_rate']:.1f}%")
        report.append(f"- NR(2) improvement rate: {analysis['nr2_improvement_rate']:.1f}%")
    
    report.append("")
    
    # Overall Statistics
    report.append("## Overall Statistics")
    report.append("")
    report.append(f"- **Test cases**: {analysis['total_tests']}")
    report.append(f"- **Baseline successes**: {analysis['baseline_successes']}/{analysis['total_tests']}")
    report.append(f"- **NR(1) successes**: {analysis['nr1_successes']}/{analysis['total_tests']}")
    report.append(f"- **NR(2) successes**: {analysis['nr2_successes']}/{analysis['total_tests']}")
    report.append("")
    report.append("### Runtime")
    report.append(f"- **NR(1) average overhead**: {analysis['avg_nr1_overhead_pct']:.1f}%")
    report.append(f"- **NR(2) average overhead**: {analysis['avg_nr2_overhead_pct']:.1f}%")
    report.append("")
    report.append("### Score Analysis")
    report.append(f"- **NR(1) average score lift**: {analysis['avg_nr1_score_lift']:.2f}%")
    report.append(f"- **NR(2) average score lift**: {analysis['avg_nr2_score_lift']:.2f}%")
    report.append("")
    report.append("### NR Refinement Activity")
    report.append(f"- **NR(1) total triggers**: {analysis['total_nr1_triggers']}")
    report.append(f"- **NR(1) total improvements**: {analysis['total_nr1_improvements']}")
    report.append(f"- **NR(1) improvement rate**: {analysis['nr1_improvement_rate']:.1f}%")
    report.append(f"- **NR(2) total triggers**: {analysis['total_nr2_triggers']}")
    report.append(f"- **NR(2) total improvements**: {analysis['total_nr2_improvements']}")
    report.append(f"- **NR(2) improvement rate**: {analysis['nr2_improvement_rate']:.1f}%")
    report.append("")
    
    # Per-test results
    report.append("## Per-Test Results")
    report.append("")
    report.append("| Test Case | Baseline | NR(1) | NR(2) | NR(1) Overhead | NR(2) Overhead | NR(1) Lift | NR(2) Lift |")
    report.append("|-----------|----------|-------|-------|----------------|----------------|------------|------------|")
    
    for r in results:
        baseline_status = "✓" if r.baseline_success else "✗"
        nr1_status = "✓" if r.nr1_success else "✗"
        nr2_status = "✓" if r.nr2_success else "✗"
        report.append(f"| {r.test_case} | {baseline_status} | {nr1_status} | {nr2_status} | {r.nr1_overhead_pct:.1f}% | {r.nr2_overhead_pct:.1f}% | {r.nr1_score_lift:.2f}% | {r.nr2_score_lift:.2f}% |")
    
    report.append("")
    
    # Falsification Criteria
    report.append("## Falsification Criteria Assessment")
    report.append("")
    report.append("| Criterion | Met | Details |")
    report.append("|-----------|-----|---------|")
    
    fc = analysis['falsification_criteria']
    report.append(f"| No significant score lift (<1%) | {'✓' if fc['no_score_lift'] else '✗'} | NR(1): {analysis['avg_nr1_score_lift']:.2f}%, NR(2): {analysis['avg_nr2_score_lift']:.2f}% |")
    report.append(f"| Excessive overhead (>15%) | {'✓' if fc['excessive_overhead'] else '✗'} | NR(1): {analysis['avg_nr1_overhead_pct']:.1f}%, NR(2): {analysis['avg_nr2_overhead_pct']:.1f}% |")
    report.append(f"| Low improvement rate (<20%) | {'✓' if fc['low_improvement_rate'] else '✗'} | NR(1): {analysis['nr1_improvement_rate']:.1f}%, NR(2): {analysis['nr2_improvement_rate']:.1f}% |")
    report.append(f"| Majority no benefit (≥2/3) | {'✓' if fc['majority_no_benefit'] else '✗'} | {analysis['criteria_met']}/{analysis['total_tests']} tests |")
    report.append("")
    report.append(f"**Criteria met**: {analysis['criteria_met']}/4 (threshold: 2)")
    report.append("")
    
    # Methodology
    report.append("## Methodology")
    report.append("")
    report.append("### Experiment Design")
    report.append("- **Treatments**: Baseline (NR disabled), NR(1) - 1 step, NR(2) - 2 steps")
    report.append("- **Trigger**: z-score ≥ 1.5 OR top 5% of candidates")
    report.append("- **Tolerance**: Stop early if relative improvement < 1e-6")
    report.append("- **Budget**: Max 64 refines per batch")
    report.append("")
    report.append("### Test Cases")
    report.append("1. Gate 1 (30-bit): 1073217479 = 32749 × 32771")
    report.append("2. Gate 2 (60-bit): 1152921470247108503 = 1073741789 × 1073741827")
    report.append("3. Verified 50-bit: 1125899772623531 = 33554393 × 33554467")
    report.append("4. Verified 64-bit: 18446736050711510819 = 4294966297 × 4294966427")
    report.append("")
    report.append("### Key Constraints")
    report.append("- No classical fallbacks (pure geometric resonance)")
    report.append("- Deterministic (fixed seeds, fixed NR step budget)")
    report.append("- Same precision path for NR as main scoring")
    report.append("")
    
    # Reproducibility
    report.append("## Reproducibility")
    report.append("")
    report.append("Run the experiment:")
    report.append("```bash")
    report.append("cd experiments/nr-microkernel-falsification")
    report.append("python3 experiment_runner.py")
    report.append("```")
    report.append("")
    
    return "\n".join(report)


def main():
    """Run the full experiment."""
    
    # Run experiment
    results = run_full_experiment(verbose=False)
    
    # Analyze
    analysis = analyze_results(results)
    
    # Generate report
    report = generate_report(results, analysis)
    
    # Print summary
    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    
    if analysis['hypothesis_falsified']:
        print("\n*** VERDICT: HYPOTHESIS FALSIFIED ***")
        print(f"Criteria met: {analysis['criteria_met']}/4")
    else:
        print("\n*** VERDICT: HYPOTHESIS SUPPORTED (PARTIALLY) ***")
        print(f"Criteria met: {analysis['criteria_met']}/4")
    
    print(f"\nNR(1) average score lift: {analysis['avg_nr1_score_lift']:.2f}%")
    print(f"NR(2) average score lift: {analysis['avg_nr2_score_lift']:.2f}%")
    print(f"NR(1) improvement rate: {analysis['nr1_improvement_rate']:.1f}%")
    print(f"NR(2) improvement rate: {analysis['nr2_improvement_rate']:.1f}%")
    
    # Save report
    output_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(output_dir, "EXPERIMENT_REPORT.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_path}")
    
    # Save raw results
    results_path = os.path.join(output_dir, "results.json")
    with open(results_path, 'w') as f:
        json.dump({
            'results': [asdict(r) for r in results],
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"Raw results saved to: {results_path}")
    
    return analysis['hypothesis_falsified']


if __name__ == "__main__":
    falsified = main()
    sys.exit(0 if falsified else 1)
