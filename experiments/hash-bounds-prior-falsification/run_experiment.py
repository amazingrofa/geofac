#!/usr/bin/env python3
"""
Hash-Bounds Prior Falsification Experiment
==========================================

Main experiment runner for testing and attempting to falsify the Hash-Bounds 
hypothesis:

    Z5D prime structure + √p fractional parts can be turned into a 
    probabilistic band on frac(√d) (or d/√N) for a factor d of semiprime N.

Hypothesis claims:
- mean relative error ≈ 22,126 ppm
- average fractional error ≈ 0.237
- width factor ≈ 0.155 giving ≈ 51.5% coverage
- This is NOT deterministic; it's a prior window hitting ~50-80% of cases

Falsification Criteria:
1. If coverage drops significantly below 50% consistently, hypothesis weakened
2. If predictor shows no better than random (50% for 0.5 width), falsified
3. Check if factors land in predicted bands for multiple semiprimes

Test targets:
- 127-bit challenge: N = 137524771864208156028430259349934309717
- Several semiprimes in [10^14, 10^18] operational range

Usage:
    python3 run_experiment.py
"""

import os
import sys
import json
import datetime
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import mpmath as mp
from mpmath import mpf

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(__file__))

from hash_bounds_predictor import (
    HashBoundsPredictor, 
    run_diagnostic, 
    set_precision,
    PredictedBand
)


# =============================================================================
# Constants
# =============================================================================

# 127-bit challenge (whitelisted exception)
CHALLENGE_127 = 137524771864208156028430259349934309717
P_127 = 10508623501177419659
Q_127 = 13086849276577416863

# Semiprimes in [10^14, 10^18] validation range
# Using known balanced semiprimes for testing
TEST_SEMIPRIMES = [
    # (N, p, q, description)
    (100000007 * 1000000007, 100000007, 1000000007, "10^17 scale"),
    # Additional balanced semiprimes
    (10000019 * 10000079, 10000019, 10000079, "10^14 scale"),
    (100003 * 1000000007, 100003, 1000000007, "mixed scale ~10^14"),
    (1000000007 * 1000000009, 1000000007, 1000000009, "10^18 scale - twin primes"),
]

# Random seed for reproducibility
RANDOM_SEED = 20251128


@dataclass
class ExperimentConfig:
    """Configuration for the experiment."""
    width: float = 0.155
    use_sqrt_N: bool = True
    bit_length_scaling: bool = True
    strategies: List[str] = None
    random_seed: int = RANDOM_SEED
    timestamp: str = ""
    
    def __post_init__(self):
        if self.strategies is None:
            self.strategies = ['fracSqrt', 'dOverSqrtN']
        if not self.timestamp:
            self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


@dataclass
class SemiprimeResult:
    """Result for a single semiprime test."""
    N: str
    N_bit_length: int
    p: str
    q: str
    description: str
    band_center: float
    band_lower: float
    band_upper: float
    band_width: float
    checks: Dict[str, Dict]
    hits: int
    total_checks: int
    hit_rate: float
    precision_dps: int


@dataclass
class ExperimentResult:
    """Full experiment results."""
    config: Dict
    semiprime_results: List[Dict]
    aggregate: Dict
    falsification_analysis: Dict
    timestamp: str


def generate_balanced_semiprime(bit_target: int, seed: int) -> Tuple[int, int, int]:
    """
    Generate a balanced semiprime with approximately bit_target bits.
    
    Uses deterministic seeding for reproducibility.
    
    Args:
        bit_target: Target bit length for N
        seed: Random seed
        
    Returns:
        Tuple (N, p, q) where N = p × q
    """
    random.seed(seed)
    
    # For balanced, each factor should be about bit_target/2 bits
    half_bits = bit_target // 2
    
    # Generate candidates in range [2^(half_bits-1), 2^half_bits]
    lo = 2 ** (half_bits - 1)
    hi = 2 ** half_bits
    
    def is_prime(n: int, k: int = 15) -> bool:
        """Miller-Rabin primality test."""
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        
        # Write n-1 as 2^r × d
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2
        
        # Witness loop
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)
            
            if x == 1 or x == n - 1:
                continue
                
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        
        return True
    
    def next_prime(n: int) -> int:
        """Find next prime >= n."""
        if n <= 2:
            return 2
        if n % 2 == 0:
            n += 1
        while not is_prime(n):
            n += 2
        return n
    
    # Generate two primes
    p_candidate = random.randint(lo, hi)
    p = next_prime(p_candidate)
    
    q_candidate = random.randint(lo, hi)
    while q_candidate == p_candidate:
        q_candidate = random.randint(lo, hi)
    q = next_prime(q_candidate)
    
    # Ensure p < q
    if p > q:
        p, q = q, p
    
    N = p * q
    return N, p, q


def run_single_semiprime_test(
    N: int, 
    p: int, 
    q: int, 
    description: str,
    predictor: HashBoundsPredictor
) -> SemiprimeResult:
    """
    Run the Hash-Bounds test on a single semiprime.
    
    Args:
        N: The semiprime
        p: First factor
        q: Second factor
        description: Human-readable description
        predictor: The predictor instance
        
    Returns:
        SemiprimeResult with all diagnostic information
    """
    # Verify N = p × q
    assert N == p * q, f"Invalid factors: {p} × {q} ≠ {N}"
    
    # Get diagnostic results
    results = run_diagnostic(N, p, q, predictor)
    
    return SemiprimeResult(
        N=str(N),
        N_bit_length=N.bit_length(),
        p=str(p),
        q=str(q),
        description=description,
        band_center=results['band']['center'],
        band_lower=results['band']['lower'],
        band_upper=results['band']['upper'],
        band_width=results['band']['width'],
        checks=results['checks'],
        hits=results['summary']['hits'],
        total_checks=results['summary']['total_checks'],
        hit_rate=results['summary']['hit_rate'],
        precision_dps=results['precision_dps']
    )


def compute_aggregate_stats(results: List[SemiprimeResult]) -> Dict:
    """
    Compute aggregate statistics across all semiprimes.
    
    Args:
        results: List of SemiprimeResult objects
        
    Returns:
        Dictionary with aggregate statistics
    """
    total_hits = sum(r.hits for r in results)
    total_checks = sum(r.total_checks for r in results)
    
    # Per-strategy aggregates
    strategy_stats = {}
    for strategy in ['fracSqrt', 'dOverSqrtN']:
        hits = 0
        checks = 0
        for r in results:
            for key, check in r.checks.items():
                if strategy in key:
                    checks += 1
                    if check['in_band']:
                        hits += 1
        strategy_stats[strategy] = {
            'hits': hits,
            'checks': checks,
            'hit_rate': hits / checks if checks > 0 else 0
        }
    
    # Per-factor aggregates (p vs q)
    factor_stats = {}
    for factor in ['p', 'q']:
        hits = 0
        checks = 0
        for r in results:
            for key, check in r.checks.items():
                if key.startswith(factor + '_'):
                    checks += 1
                    if check['in_band']:
                        hits += 1
        factor_stats[factor] = {
            'hits': hits,
            'checks': checks,
            'hit_rate': hits / checks if checks > 0 else 0
        }
    
    return {
        'total_hits': total_hits,
        'total_checks': total_checks,
        'overall_hit_rate': total_hits / total_checks if total_checks > 0 else 0,
        'num_semiprimes': len(results),
        'strategy_stats': strategy_stats,
        'factor_stats': factor_stats
    }


def analyze_falsification(aggregate: Dict, config: ExperimentConfig) -> Dict:
    """
    Analyze whether the hypothesis is falsified.
    
    Falsification criteria:
    1. If coverage drops significantly below 50% consistently → weakened
    2. If predictor shows no better than random (50% for 0.5 width) → falsified
    3. Check expected coverage vs actual coverage
    
    Args:
        aggregate: Aggregate statistics
        config: Experiment configuration
        
    Returns:
        Dictionary with falsification analysis
    """
    overall_rate = aggregate['overall_hit_rate']
    
    # Expected random hit rate for given width
    # Random would hit approximately `width` fraction of the time
    random_hit_rate = config.width  # ~0.155 for default
    
    # Hypothesis claims ~50-80% coverage
    hypothesis_lower = 0.50
    hypothesis_upper = 0.80
    
    # Threshold multipliers for falsification analysis
    outperform_random_threshold = 1.5  # Must be 50% better than random to "outperform"
    worse_than_random_threshold = 0.8  # Below 80% of random = performing worse
    significantly_below_threshold = 0.7  # 30% below minimum = significant
    
    # Statistical analysis
    analysis = {
        'overall_hit_rate': overall_rate,
        'random_hit_rate': random_hit_rate,
        'hypothesis_expected_range': [hypothesis_lower, hypothesis_upper],
        'width_used': config.width,
        'outperforms_random': overall_rate > random_hit_rate * outperform_random_threshold,
        'within_hypothesis_range': hypothesis_lower <= overall_rate <= hypothesis_upper,
        'below_hypothesis_minimum': overall_rate < hypothesis_lower,
        'conclusion': '',
        'evidence_strength': ''
    }
    
    # Determine conclusion
    if overall_rate < random_hit_rate * worse_than_random_threshold:
        # Performing worse than random would suggest
        analysis['conclusion'] = 'FALSIFIED'
        analysis['evidence_strength'] = 'Strong - performance worse than random chance'
    elif overall_rate < hypothesis_lower * significantly_below_threshold:
        # Significantly below hypothesis minimum (30% below 50%)
        analysis['conclusion'] = 'LIKELY FALSIFIED'
        analysis['evidence_strength'] = 'Moderate - significantly below claimed 50% minimum'
    elif overall_rate < hypothesis_lower:
        # Below hypothesis minimum but within reasonable variance
        analysis['conclusion'] = 'WEAKLY FALSIFIED'
        analysis['evidence_strength'] = 'Weak - below 50% but could be variance'
    elif analysis['within_hypothesis_range']:
        analysis['conclusion'] = 'NOT FALSIFIED'
        analysis['evidence_strength'] = 'Supports hypothesis - within claimed 50-80% range'
    elif overall_rate > hypothesis_upper:
        analysis['conclusion'] = 'EXCEEDED HYPOTHESIS'
        analysis['evidence_strength'] = 'Unexpectedly good - above claimed 80% maximum'
    else:
        analysis['conclusion'] = 'INCONCLUSIVE'
        analysis['evidence_strength'] = 'Insufficient data for strong conclusion'
    
    # Per-strategy analysis
    analysis['strategy_analysis'] = {}
    for strategy, stats in aggregate['strategy_stats'].items():
        rate = stats['hit_rate']
        analysis['strategy_analysis'][strategy] = {
            'hit_rate': rate,
            'outperforms_random': rate > random_hit_rate * 1.5,
            'within_range': hypothesis_lower <= rate <= hypothesis_upper
        }
    
    return analysis


def run_experiment() -> ExperimentResult:
    """
    Run the full Hash-Bounds falsification experiment.
    
    Returns:
        ExperimentResult with all results and analysis
    """
    print("=" * 70)
    print("Hash-Bounds Prior Falsification Experiment")
    print("=" * 70)
    print()
    
    # Configuration
    config = ExperimentConfig()
    print(f"Configuration:")
    print(f"  width: {config.width}")
    print(f"  use_sqrt_N: {config.use_sqrt_N}")
    print(f"  bit_length_scaling: {config.bit_length_scaling}")
    print(f"  strategies: {config.strategies}")
    print(f"  random_seed: {config.random_seed}")
    print(f"  timestamp: {config.timestamp}")
    print()
    
    # Initialize predictor
    predictor = HashBoundsPredictor(
        width=config.width,
        use_sqrt_N=config.use_sqrt_N,
        bit_length_scaling=config.bit_length_scaling
    )
    
    results: List[SemiprimeResult] = []
    
    # ==========================================================================
    # Test 1: 127-bit Challenge (whitelisted)
    # ==========================================================================
    print("-" * 70)
    print("Test 1: 127-bit Challenge (whitelisted)")
    print("-" * 70)
    
    result_127 = run_single_semiprime_test(
        CHALLENGE_127, P_127, Q_127,
        "127-bit challenge (whitelisted)",
        predictor
    )
    results.append(result_127)
    
    print(f"  N = {result_127.N}")
    print(f"  bit_length = {result_127.N_bit_length}")
    print(f"  band = [{result_127.band_lower:.6f}, {result_127.band_upper:.6f}] (center: {result_127.band_center:.6f})")
    print(f"  hits = {result_127.hits}/{result_127.total_checks} ({result_127.hit_rate:.1%})")
    for key, check in result_127.checks.items():
        status = "✓" if check['in_band'] else "✗"
        print(f"    {status} {key}: {check['factor_value']:.6f}")
    print()
    
    # ==========================================================================
    # Test 2: Known semiprimes in [10^14, 10^18]
    # ==========================================================================
    print("-" * 70)
    print("Test 2: Known semiprimes in [10^14, 10^18] range")
    print("-" * 70)
    
    for N, p, q, desc in TEST_SEMIPRIMES:
        # Verify within validation range
        if not (10**14 <= N <= 10**18):
            print(f"  SKIPPED: {desc} - N={N} outside [10^14, 10^18]")
            continue
        
        result = run_single_semiprime_test(N, p, q, desc, predictor)
        results.append(result)
        
        print(f"  {desc}:")
        print(f"    N = {result.N} ({result.N_bit_length} bits)")
        print(f"    band = [{result.band_lower:.6f}, {result.band_upper:.6f}]")
        print(f"    hits = {result.hits}/{result.total_checks} ({result.hit_rate:.1%})")
        for key, check in result.checks.items():
            status = "✓" if check['in_band'] else "✗"
            print(f"      {status} {key}: {check['factor_value']:.6f}")
        print()
    
    # ==========================================================================
    # Test 3: Generated balanced semiprimes
    # ==========================================================================
    print("-" * 70)
    print("Test 3: Generated balanced semiprimes")
    print("-" * 70)
    
    # Generate a few balanced semiprimes at different scales
    for bit_target, seed_offset in [(50, 1), (55, 2), (58, 3)]:
        seed = config.random_seed + seed_offset
        N, p, q = generate_balanced_semiprime(bit_target, seed)
        
        # Verify within validation range or adjust
        if N < 10**14:
            print(f"  SKIPPED: {bit_target}-bit generated - N={N} below 10^14")
            continue
        if N > 10**18:
            print(f"  SKIPPED: {bit_target}-bit generated - N={N} above 10^18")
            continue
        
        desc = f"{bit_target}-bit generated (seed={seed})"
        result = run_single_semiprime_test(N, p, q, desc, predictor)
        results.append(result)
        
        print(f"  {desc}:")
        print(f"    N = {result.N} ({result.N_bit_length} bits)")
        print(f"    p = {result.p}, q = {result.q}")
        print(f"    band = [{result.band_lower:.6f}, {result.band_upper:.6f}]")
        print(f"    hits = {result.hits}/{result.total_checks} ({result.hit_rate:.1%})")
    print()
    
    # ==========================================================================
    # Aggregate Analysis
    # ==========================================================================
    print("=" * 70)
    print("Aggregate Results")
    print("=" * 70)
    
    aggregate = compute_aggregate_stats(results)
    
    print(f"Total semiprimes tested: {aggregate['num_semiprimes']}")
    print(f"Total checks: {aggregate['total_checks']}")
    print(f"Total hits: {aggregate['total_hits']}")
    print(f"Overall hit rate: {aggregate['overall_hit_rate']:.1%}")
    print()
    print("Per-strategy breakdown:")
    for strategy, stats in aggregate['strategy_stats'].items():
        print(f"  {strategy}: {stats['hits']}/{stats['checks']} ({stats['hit_rate']:.1%})")
    print()
    print("Per-factor breakdown:")
    for factor, stats in aggregate['factor_stats'].items():
        print(f"  {factor}: {stats['hits']}/{stats['checks']} ({stats['hit_rate']:.1%})")
    print()
    
    # ==========================================================================
    # Falsification Analysis
    # ==========================================================================
    print("=" * 70)
    print("Falsification Analysis")
    print("=" * 70)
    
    falsification = analyze_falsification(aggregate, config)
    
    print(f"Hypothesis claims: {falsification['hypothesis_expected_range'][0]:.0%} - {falsification['hypothesis_expected_range'][1]:.0%} coverage")
    print(f"Random baseline (width={falsification['width_used']}): {falsification['random_hit_rate']:.1%}")
    print(f"Observed hit rate: {falsification['overall_hit_rate']:.1%}")
    print()
    print(f"Outperforms random: {falsification['outperforms_random']}")
    print(f"Within hypothesis range: {falsification['within_hypothesis_range']}")
    print()
    print(f"CONCLUSION: {falsification['conclusion']}")
    print(f"Evidence strength: {falsification['evidence_strength']}")
    print("=" * 70)
    
    # ==========================================================================
    # Build final result
    # ==========================================================================
    experiment_result = ExperimentResult(
        config=asdict(config) if hasattr(config, '__dataclass_fields__') else {
            'width': config.width,
            'use_sqrt_N': config.use_sqrt_N,
            'bit_length_scaling': config.bit_length_scaling,
            'strategies': config.strategies,
            'random_seed': config.random_seed,
            'timestamp': config.timestamp
        },
        semiprime_results=[asdict(r) for r in results],
        aggregate=aggregate,
        falsification_analysis=falsification,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    )
    
    return experiment_result


def save_results(results: ExperimentResult, filepath: str):
    """Save experiment results to JSON file."""
    data = asdict(results)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to: {filepath}")


def main():
    """Main entry point."""
    # Run experiment
    results = run_experiment()
    
    # Save results
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'run_log.json')
    save_results(results, log_path)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
