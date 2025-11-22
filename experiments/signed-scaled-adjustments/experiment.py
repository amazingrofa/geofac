"""
Signed or Scaled Adjustments Experiment
========================================

Objective: Falsify the hypothesis that signed or scaled adjustments to the
geometric parameter k in θ'(n,k) can reduce search iterations in Fermat-style
factorization of semiprimes.

Context:
- Original simulation (k=0.3 positive) overshot, increasing iterations
- Hypothesis: Negative or scaled adjustments could correct this
- Test on semiprimes in [10^14, 10^18] validation range

Method:
- Generate close-prime semiprimes (p ≈ q)
- Apply Fermat's method with various k-adjustment strategies
- Measure iterations to find factors
- Compare: positive k, negative k, scaled k, no adjustment (control)

Hypothesis will be FALSIFIED if:
1. Negative k adjustments also fail to reduce iterations vs. control
2. Scaled adjustments show no consistent improvement
3. Any improvement is within noise/variance bounds

Reproducibility:
- Fixed seed: 42
- mpmath precision: 50 decimal places (target < 1e-16)
- Deterministic semiprime generation
- All parameters logged with timestamps
"""

import mpmath as mp
from mpmath import mpf, sqrt, ceil, floor
import random
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import json

# Set precision
mp.dps = 50

# Golden ratio
PHI = (1 + sqrt(5)) / 2


def is_prime_miller_rabin(n: int, k: int = 10) -> bool:
    """Miller-Rabin primality test for generating primes."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Witness loop
    for _ in range(k):
        a = random.randint(2, n - 2)
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


def generate_close_prime_pair(
    base: int, min_gap: int, max_gap: int, seed: int
) -> Tuple[int, int]:
    """
    Generate two close primes p, q where p < q and gap is bounded.

    Args:
        base: Starting point (will search around this)
        min_gap: Minimum gap between primes
        max_gap: Maximum gap between primes
        seed: Random seed for reproducibility

    Returns:
        Tuple (p, q) of close primes
    """
    random.seed(seed)

    # Find first prime near base
    p = base + random.randint(0, max_gap)
    while not is_prime_miller_rabin(p):
        p += 1

    # Find second prime with specified gap range from p
    gap = random.randint(min_gap, max_gap)
    q = p + gap
    while not is_prime_miller_rabin(q):
        q += 2  # Skip evens
        if q - p > max_gap * 3:
            # Start over if we've gone too far
            q = p + min_gap

    return (p, q)


def generate_test_semiprimes(
    count: int, min_val: int, max_val: int, min_gap: int, max_gap: int, seed: int
) -> List[Dict[str, int]]:
    """
    Generate test semiprimes in operational range [10^14, 10^18].

    Args:
        count: Number of semiprimes to generate
        min_val: Minimum value (10^14)
        max_val: Maximum value (10^18)
        min_gap: Minimum gap between prime factors
        max_gap: Maximum gap between prime factors
        seed: Random seed

    Returns:
        List of dicts with n, p, q
    """
    random.seed(seed)
    semiprimes = []

    i = 0
    while len(semiprimes) < count:
        # Generate close primes
        base_sqrt = int(sqrt(random.randint(min_val, max_val)))
        p, q = generate_close_prime_pair(base_sqrt, min_gap, max_gap, seed + i)
        n = p * q

        # Validate in range
        if min_val <= n <= max_val:
            semiprimes.append({"n": n, "p": p, "q": q})
        i += 1

    return semiprimes


def theta_prime(n: int, k: float) -> mpf:
    """
    Geometric prime-density mapping: θ'(n,k) = φ·((n mod φ)/φ)^k

    Args:
        n: Integer parameter
        k: Geodesic exponent

    Returns:
        Geodesic-transformed value
    """
    if PHI == 0:
        return mpf(0)

    n_mod_phi = mpf(n) % PHI
    ratio = n_mod_phi / PHI
    result = PHI * (ratio ** mpf(k))
    return result


def fermat_factorization_with_adjustment(
    n: int,
    k_adjustment: Optional[float] = None,
    adjustment_sign: int = 1,
    adjustment_scale: float = 1.0,
    max_iterations: int = 100000,
) -> Tuple[Optional[int], Optional[int], int]:
    """
    Fermat's factorization method with optional k-based geometric adjustment.

    Args:
        n: Semiprime to factor
        k_adjustment: Geodesic exponent k (None for no adjustment)
        adjustment_sign: +1 for positive, -1 for negative adjustment
        adjustment_scale: Scaling factor for adjustment magnitude
        max_iterations: Iteration limit

    Returns:
        Tuple (p, q, iterations) where p,q are factors or None if not found
    """
    sqrt_n = sqrt(mpf(n))

    # Starting point: ceil(√n)
    if k_adjustment is None:
        # Control: no adjustment
        a_start = int(ceil(sqrt_n))
    else:
        # Apply k-based adjustment: a = ceil(√n + sign × scale × θ'(floor(√n), k))
        sqrt_n_floor = int(floor(sqrt_n))
        theta_val = theta_prime(sqrt_n_floor, k_adjustment)
        adjustment = adjustment_sign * adjustment_scale * theta_val
        a_start = int(ceil(sqrt_n + adjustment))

    # Guard: a must be >= ceil(√n)
    a_start = max(a_start, int(ceil(sqrt_n)))

    # Fermat's method: find a such that a² - n = b²
    for i in range(max_iterations):
        a = a_start + i
        a_squared = a * a
        diff = a_squared - n

        if diff < 0:
            continue

        # Check if diff is perfect square
        b = int(sqrt(mpf(diff)))
        if b * b == diff:
            # Found factors
            p = a - b
            q = a + b

            # Verify
            if p * q == n and p > 1 and q > 1:
                return (min(p, q), max(p, q), i)

    return (None, None, max_iterations)


def run_single_test(
    semiprime: Dict[str, int],
    k_value: Optional[float],
    adjustment_sign: int,
    adjustment_scale: float,
    label: str,
    max_iterations: int = 100000,
) -> Dict[str, Any]:
    """
    Run single factorization test with specified adjustment strategy.

    Returns:
        Dict with test results
    """
    n = semiprime["n"]
    expected_p = semiprime["p"]
    expected_q = semiprime["q"]

    start_time = datetime.now()

    p_found, q_found, iterations = fermat_factorization_with_adjustment(
        n, k_value, adjustment_sign, adjustment_scale, max_iterations
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    success = (p_found == expected_p and q_found == expected_q) if p_found else False

    return {
        "label": label,
        "n": n,
        "expected_p": expected_p,
        "expected_q": expected_q,
        "found_p": p_found,
        "found_q": q_found,
        "iterations": iterations,
        "success": success,
        "elapsed_seconds": elapsed,
        "k_value": k_value,
        "adjustment_sign": adjustment_sign,
        "adjustment_scale": adjustment_scale,
    }


def run_experiment(
    num_semiprimes: int = 10, seed: int = 42, max_iterations: int = 100000
) -> Dict[str, Any]:
    """
    Run complete experiment testing various k-adjustment strategies.

    Tests:
    1. Control: No adjustment
    2. Positive k=0.3 (original, expected to overshoot)
    3. Negative k=0.3 (corrective hypothesis)
    4. Scaled positive k=0.3 × 0.1 (reduced magnitude)
    5. Scaled negative k=0.3 × 0.1 (reduced corrective)

    Returns:
        Complete experiment results
    """
    print("=" * 80)
    print("SIGNED OR SCALED ADJUSTMENTS EXPERIMENT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Seed: {seed}")
    print(f"mpmath precision: {mp.dps} decimal places")
    print(f"Number of test semiprimes: {num_semiprimes}")
    print(f"Max iterations per test: {max_iterations}")
    print(f"Operational range: [10^14, 10^18]")
    print()

    # Generate test semiprimes
    print("Generating test semiprimes...")
    min_val = 10**14
    max_val = 10**18
    min_gap = 100  # Ensure some iterations needed
    max_gap = 10000

    semiprimes = generate_test_semiprimes(
        num_semiprimes, min_val, max_val, min_gap, max_gap, seed
    )

    print(f"Generated {len(semiprimes)} semiprimes")
    for i, sp in enumerate(semiprimes):
        print(f"  {i + 1}. n={sp['n']} (p={sp['p']}, q={sp['q']})")
    print()

    # Define test strategies
    strategies = [
        # (k_value, sign, scale, label)
        (None, 1, 1.0, "Control (no adjustment)"),
        (0.3, +1, 1.0, "Positive k=0.3 (original)"),
        (0.3, -1, 1.0, "Negative k=0.3 (corrective)"),
        (0.3, +1, 0.1, "Scaled positive k=0.3×0.1"),
        (0.3, -1, 0.1, "Scaled negative k=0.3×0.1"),
        (0.3, +1, 0.5, "Scaled positive k=0.3×0.5"),
        (0.3, -1, 0.5, "Scaled negative k=0.3×0.5"),
    ]

    # Run tests
    all_results = []

    for k_val, sign, scale, label in strategies:
        print(f"Testing strategy: {label}")
        print(f"  k={k_val}, sign={sign}, scale={scale}")

        strategy_results = []

        for i, sp in enumerate(semiprimes):
            result = run_single_test(sp, k_val, sign, scale, label, max_iterations)
            strategy_results.append(result)

            status = "✓" if result["success"] else "✗"
            print(
                f"    {i + 1}. {status} n={sp['n']}: {result['iterations']} iterations"
            )

        all_results.extend(strategy_results)

        # Strategy summary
        successes = sum(1 for r in strategy_results if r["success"])
        avg_iterations = sum(r["iterations"] for r in strategy_results) / len(
            strategy_results
        )
        print(
            f"  Summary: {successes}/{len(strategy_results)} successful, "
            f"avg {avg_iterations:.1f} iterations"
        )
        print()

    # Aggregate analysis
    print("=" * 80)
    print("AGGREGATE ANALYSIS")
    print("=" * 80)

    strategy_summaries = []

    for k_val, sign, scale, label in strategies:
        strategy_data = [r for r in all_results if r["label"] == label]

        total_tests = len(strategy_data)
        successes = sum(1 for r in strategy_data if r["success"])
        success_rate = successes / total_tests if total_tests > 0 else 0

        avg_iterations = sum(r["iterations"] for r in strategy_data) / total_tests

        # Only successful tests
        successful_tests = [r for r in strategy_data if r["success"]]
        avg_success_iterations = (
            sum(r["iterations"] for r in successful_tests) / len(successful_tests)
            if successful_tests
            else None
        )

        summary = {
            "label": label,
            "k_value": k_val,
            "adjustment_sign": sign,
            "adjustment_scale": scale,
            "total_tests": total_tests,
            "successes": successes,
            "success_rate": success_rate,
            "avg_iterations_all": avg_iterations,
            "avg_iterations_successful": avg_success_iterations,
        }

        strategy_summaries.append(summary)

        print(f"{label}:")
        print(f"  Success rate: {successes}/{total_tests} ({100 * success_rate:.1f}%)")
        print(f"  Avg iterations (all): {avg_iterations:.1f}")
        if avg_success_iterations is not None:
            print(f"  Avg iterations (successful): {avg_success_iterations:.1f}")
        print()

    # Compile experiment output
    experiment_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "seed": seed,
            "precision_dps": mp.dps,
            "num_semiprimes": num_semiprimes,
            "max_iterations": max_iterations,
            "operational_range": [min_val, max_val],
        },
        "semiprimes": semiprimes,
        "strategies": [
            {"k": k, "sign": s, "scale": sc, "label": l} for k, s, sc, l in strategies
        ],
        "detailed_results": all_results,
        "strategy_summaries": strategy_summaries,
    }

    return experiment_results


def save_results(results: Dict[str, Any], output_path: str):
    """Save experiment results to JSON file."""
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    # Run experiment
    results = run_experiment(num_semiprimes=10, seed=42, max_iterations=100000)

    # Save results
    output_path = "results.json"
    save_results(results, output_path)

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)
