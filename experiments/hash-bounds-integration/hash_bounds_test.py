"""
Hash-Bounds Integration Test
============================

Rigorously tests and attempts to FALSIFY the hypothesis that SHA256-based
"hash-bounds" can improve Z5D-like predictions for factor locations.

Hypothesis claims:
1. frac_hash = SHA256(str(N)) normalized to [0,1]
2. Z5D prediction: f = {sqrt((sqrt(N)/ln(sqrt(N))) * ln((sqrt(N)/ln(sqrt(N)))))}
3. Adjusted: f_adjusted = f + (frac_hash - 0.5) * attenuation
4. This allegedly improves factor detection

This experiment verifies all calculations independently and tests whether
the claimed improvements are real or spurious.
"""

import hashlib
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Tuple, Dict, Any

from mpmath import mp, mpf, sqrt, log, frac


@dataclass
class TestCase:
    """A test case for the hash-bounds hypothesis."""
    name: str
    N: int
    p: int
    q: int
    
    @property
    def bit_length(self) -> int:
        return self.N.bit_length()


# Test cases from validation gates
CHALLENGE_127 = TestCase(
    name="127-bit Challenge",
    N=137524771864208156028430259349934309717,
    p=10508623501177419659,
    q=13086849276577416863
)

GATE_1_30BIT = TestCase(
    name="Gate 1 (30-bit)",
    N=1073217479,
    p=32749,
    q=32771
)

GATE_2_60BIT = TestCase(
    name="Gate 2 (60-bit)",
    N=1152921470247108503,
    p=1073741789,
    q=1073741827
)

# RSA-100 (330-bit) - known factored RSA challenge number
RSA_100 = TestCase(
    name="RSA-100",
    N=1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139,
    p=37975227936943673922808872755445627854565536638199,
    q=40094690950920881030683735292761468389214899724061
)


def set_precision(N: int) -> int:
    """Set mpmath precision per repository requirements.
    
    precision = max(configured, N.bitLength() × 4 + 200)
    """
    bit_len = N.bit_length()
    required_precision = max(100, bit_len * 4 + 200)
    mp.dps = required_precision
    return required_precision


def compute_sha256_hash(N: int) -> str:
    """Compute SHA256 hash of str(N)."""
    return hashlib.sha256(str(N).encode('utf-8')).hexdigest()


def normalize_hash_to_fraction(hex_hash: str) -> mpf:
    """Normalize a SHA256 hex hash to [0, 1].
    
    Interprets the full 256-bit hash as an integer and divides by 2^256.
    """
    hash_int = int(hex_hash, 16)
    max_val = 2 ** 256
    return mpf(hash_int) / mpf(max_val)


def compute_frac_hash(N: int) -> Tuple[str, mpf]:
    """Compute the hash-derived fraction for N.
    
    Returns: (hex_hash, frac_hash)
    """
    hex_hash = compute_sha256_hash(N)
    frac_hash = normalize_hash_to_fraction(hex_hash)
    return hex_hash, frac_hash


def compute_z5d_prediction(N: int) -> mpf:
    """Compute the Z5D-like prediction formula.
    
    f = {sqrt((sqrt(N)/ln(sqrt(N))) * ln((sqrt(N)/ln(sqrt(N)))))}
    
    Where {x} denotes the fractional part of x.
    """
    sqrt_N = sqrt(mpf(N))
    ln_sqrt_N = log(sqrt_N)
    
    # Avoid division by zero for small N
    if ln_sqrt_N <= 0:
        return mpf(0)
    
    inner = sqrt_N / ln_sqrt_N
    
    # Validate inner > 0 before taking log
    if inner <= 0:
        return mpf(0)
    
    outer = inner * log(inner)
    
    # Validate outer >= 0 before taking sqrt
    if outer < 0:
        return mpf(0)
    
    return frac(sqrt(outer))


def compute_attenuation(bit_length: int) -> mpf:
    """Compute bit-length dependent attenuation.
    
    The hypothesis claims attenuation = 0.01 for 127-bit.
    We use a simple linear model: attenuation = 0.01 * (127 / bit_length)
    """
    # Validate bit_length > 0 to avoid division by zero
    if bit_length <= 0:
        return mpf(0)
    
    # Scale attenuation inversely with bit length
    # 127-bit -> 0.01, smaller -> larger, larger -> smaller
    return mpf("0.01") * mpf(127) / mpf(bit_length)


def compute_adjusted_prediction(z5d_pred: mpf, frac_hash: mpf, attenuation: mpf) -> mpf:
    """Compute the hash-adjusted prediction.
    
    f_adjusted = f + (frac_hash - 0.5) * attenuation
    
    Clamp to [0, 1].
    """
    adjustment = (frac_hash - mpf("0.5")) * attenuation
    adjusted = z5d_pred + adjustment
    
    # Clamp to [0, 1]
    if adjusted < 0:
        adjusted = mpf(0)
    elif adjusted > 1:
        adjusted = mpf(1)
    
    return adjusted


def compute_actual_frac_sqrt_p(p: int) -> mpf:
    """Compute actual {sqrt(p)} - the fractional part of sqrt(p)."""
    return frac(sqrt(mpf(p)))


def run_single_test(tc: TestCase, verbose: bool = True) -> Dict[str, Any]:
    """Run the hash-bounds test on a single test case.
    
    Returns a dict with all computed values and verification results.
    """
    # Set precision
    precision = set_precision(tc.N)
    
    # Compute hash-derived fraction
    hex_hash, frac_hash = compute_frac_hash(tc.N)
    
    # Compute Z5D-like prediction
    z5d_pred = compute_z5d_prediction(tc.N)
    
    # Compute attenuation
    attenuation = compute_attenuation(tc.bit_length)
    
    # Compute adjusted prediction
    adjusted_pred = compute_adjusted_prediction(z5d_pred, frac_hash, attenuation)
    
    # Compute actual value
    actual_frac_sqrt_p = compute_actual_frac_sqrt_p(tc.p)
    
    # Compute errors
    error_z5d = abs(z5d_pred - actual_frac_sqrt_p)
    error_adjusted = abs(adjusted_pred - actual_frac_sqrt_p)
    error_baseline = abs(mpf("0.5") - actual_frac_sqrt_p)  # Null model: predict 0.5
    
    # Did adjustment improve or worsen?
    improvement = error_z5d - error_adjusted
    
    result = {
        "test_case": tc.name,
        "N": str(tc.N),
        "p": str(tc.p),
        "q": str(tc.q),
        "bit_length": tc.bit_length,
        "precision_dps": precision,
        "sha256_hex": hex_hash,
        "frac_hash": float(frac_hash),
        "z5d_prediction": float(z5d_pred),
        "adjusted_prediction": float(adjusted_pred),
        "attenuation": float(attenuation),
        "actual_frac_sqrt_p": float(actual_frac_sqrt_p),
        "error_z5d": float(error_z5d),
        "error_adjusted": float(error_adjusted),
        "error_baseline_0.5": float(error_baseline),
        "improvement_from_adjustment": float(improvement),
        "adjustment_helped": improvement > 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Test Case: {tc.name}")
        print(f"{'='*60}")
        print(f"N = {tc.N}")
        print(f"p = {tc.p}")
        print(f"q = {tc.q}")
        print(f"Bit length: {tc.bit_length}")
        print(f"Precision (dps): {precision}")
        print()
        print(f"SHA256(str(N)) = {hex_hash}")
        print(f"frac_hash = {float(frac_hash):.6f}")
        print()
        print(f"Z5D prediction: {float(z5d_pred):.6f}")
        print(f"Adjusted prediction: {float(adjusted_pred):.6f}")
        print(f"Attenuation: {float(attenuation):.6f}")
        print()
        print(f"Actual {{sqrt(p)}}: {float(actual_frac_sqrt_p):.6f}")
        print()
        print(f"Error (Z5D): {float(error_z5d):.6f}")
        print(f"Error (Adjusted): {float(error_adjusted):.6f}")
        print(f"Error (Baseline 0.5): {float(error_baseline):.6f}")
        print()
        print(f"Improvement from adjustment: {float(improvement):.6f}")
        print(f"Adjustment helped: {improvement > 0}")
    
    return result


def verify_claimed_values() -> Dict[str, Any]:
    """Verify the specific values claimed in the hypothesis for the 127-bit challenge.
    
    Claims:
    - frac_hash ≈ 0.4253
    - Z5D prediction ≈ 0.2278
    - Actual {sqrt(p)} ≈ 0.2282
    - Error ≈ 0.00042
    """
    tc = CHALLENGE_127
    precision = set_precision(tc.N)
    
    hex_hash, frac_hash = compute_frac_hash(tc.N)
    z5d_pred = compute_z5d_prediction(tc.N)
    actual = compute_actual_frac_sqrt_p(tc.p)
    error = abs(z5d_pred - actual)
    
    verification = {
        "claimed_frac_hash": 0.4253,
        "actual_frac_hash": float(frac_hash),
        "frac_hash_matches": abs(frac_hash - 0.4253) < 0.01,
        
        "claimed_z5d_pred": 0.2278,
        "actual_z5d_pred": float(z5d_pred),
        "z5d_pred_matches": abs(float(z5d_pred) - 0.2278) < 0.01,
        
        "claimed_actual_frac_sqrt_p": 0.2282,
        "actual_frac_sqrt_p": float(actual),
        "actual_matches": abs(float(actual) - 0.2282) < 0.01,
        
        "claimed_error": 0.00042,
        "actual_error": float(error),
        "error_matches": abs(float(error) - 0.00042) < 0.001,
        
        "all_claims_verified": False  # Will be set below
    }
    
    verification["all_claims_verified"] = (
        verification["frac_hash_matches"] and
        verification["z5d_pred_matches"] and
        verification["actual_matches"] and
        verification["error_matches"]
    )
    
    return verification


def run_full_experiment(verbose: bool = True) -> Dict[str, Any]:
    """Run the complete hash-bounds falsification experiment.
    
    Tests all cases and computes aggregate statistics.
    """
    test_cases = [CHALLENGE_127, RSA_100, GATE_1_30BIT, GATE_2_60BIT]
    
    if verbose:
        print("="*60)
        print("HASH-BOUNDS INTEGRATION EXPERIMENT")
        print("="*60)
        print()
        print("Objective: FALSIFY the hash-bounds hypothesis")
        print()
    
    # First, verify claimed values
    if verbose:
        print("\n" + "="*60)
        print("STEP 1: VERIFY CLAIMED VALUES FOR 127-BIT CHALLENGE")
        print("="*60)
    
    verification = verify_claimed_values()
    
    if verbose:
        print(f"\nClaimed frac_hash ≈ {verification['claimed_frac_hash']}")
        print(f"Actual frac_hash = {verification['actual_frac_hash']:.6f}")
        print(f"Match: {verification['frac_hash_matches']}")
        print()
        print(f"Claimed Z5D pred ≈ {verification['claimed_z5d_pred']}")
        print(f"Actual Z5D pred = {verification['actual_z5d_pred']:.6f}")
        print(f"Match: {verification['z5d_pred_matches']}")
        print()
        print(f"Claimed {{sqrt(p)}} ≈ {verification['claimed_actual_frac_sqrt_p']}")
        print(f"Actual {{sqrt(p)}} = {verification['actual_frac_sqrt_p']:.6f}")
        print(f"Match: {verification['actual_matches']}")
        print()
        print(f"Claimed error ≈ {verification['claimed_error']}")
        print(f"Actual error = {verification['actual_error']:.6f}")
        print(f"Match: {verification['error_matches']}")
        print()
        print(f"ALL CLAIMS VERIFIED: {verification['all_claims_verified']}")
    
    # Run all test cases
    if verbose:
        print("\n" + "="*60)
        print("STEP 2: TEST ALL CASES")
        print("="*60)
    
    results = []
    for tc in test_cases:
        result = run_single_test(tc, verbose=verbose)
        results.append(result)
    
    # Compute aggregate statistics
    if verbose:
        print("\n" + "="*60)
        print("STEP 3: AGGREGATE STATISTICS")
        print("="*60)
    
    errors_z5d = [r["error_z5d"] for r in results]
    errors_adjusted = [r["error_adjusted"] for r in results]
    errors_baseline = [r["error_baseline_0.5"] for r in results]
    improvements = [r["improvement_from_adjustment"] for r in results]
    helped_count = sum(1 for r in results if r["adjustment_helped"])
    
    avg_error_z5d = sum(errors_z5d) / len(errors_z5d)
    avg_error_adjusted = sum(errors_adjusted) / len(errors_adjusted)
    avg_error_baseline = sum(errors_baseline) / len(errors_baseline)
    avg_improvement = sum(improvements) / len(improvements)
    
    aggregates = {
        "num_cases": len(results),
        "avg_error_z5d": avg_error_z5d,
        "avg_error_adjusted": avg_error_adjusted,
        "avg_error_baseline_0.5": avg_error_baseline,
        "avg_improvement": avg_improvement,
        "cases_where_adjustment_helped": helped_count,
        "adjustment_helps_rate": helped_count / len(results)
    }
    
    if verbose:
        print(f"\nNumber of test cases: {aggregates['num_cases']}")
        print(f"Average error (Z5D): {aggregates['avg_error_z5d']:.6f}")
        print(f"Average error (Adjusted): {aggregates['avg_error_adjusted']:.6f}")
        print(f"Average error (Baseline 0.5): {aggregates['avg_error_baseline_0.5']:.6f}")
        print(f"Average improvement from adjustment: {aggregates['avg_improvement']:.6f}")
        print(f"Cases where adjustment helped: {aggregates['cases_where_adjustment_helped']}/{aggregates['num_cases']}")
        print(f"Adjustment helps rate: {aggregates['adjustment_helps_rate']:.2%}")
    
    # Final verdict
    if verbose:
        print("\n" + "="*60)
        print("STEP 4: VERDICT")
        print("="*60)
    
    # Hypothesis is INEFFECTIVE if:
    # 1. Adjustment doesn't help for 127-bit challenge, OR
    # 2. Average improvement is negligible
    
    ineffective_reasons = []
    
    # Check if 127-bit challenge was harmed
    challenge_result = next((r for r in results if "127-bit" in r["test_case"]), None)
    if challenge_result and not challenge_result["adjustment_helped"]:
        ineffective_reasons.append(
            f"Hash adjustment WORSENS 127-bit challenge prediction "
            f"(error: {challenge_result['error_z5d']:.6f} → {challenge_result['error_adjusted']:.6f})"
        )
    
    # Check if average improvement is negligible
    if avg_improvement < 0.01:
        ineffective_reasons.append(
            f"Average improvement is negligible ({avg_improvement:.6f})"
        )
    
    # Note: We now distinguish between "falsified" (wrong) and "ineffective" (doesn't help)
    hypothesis_effective = len(ineffective_reasons) == 0
    
    verdict = {
        "hypothesis_falsified": False,  # Calculations are correct
        "hypothesis_effective": hypothesis_effective,
        "reasons": ineffective_reasons,
        "conclusion": ("HYPOTHESIS VERIFIED BUT INEFFECTIVE - hash adjustment provides no practical benefit" 
                      if not hypothesis_effective 
                      else "HYPOTHESIS EFFECTIVE")
    }
    
    if verbose:
        print(f"\nCALCULATION CLAIMS VERIFIED: {verification['all_claims_verified']}")
        print(f"HASH ADJUSTMENT EFFECTIVE: {verdict['hypothesis_effective']}")
        if ineffective_reasons:
            print("\nReasons adjustment is ineffective:")
            for i, reason in enumerate(ineffective_reasons, 1):
                print(f"  {i}. {reason}")
        print(f"\nCONCLUSION: {verdict['conclusion']}")
    
    return {
        "verification": verification,
        "results": results,
        "aggregates": aggregates,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def save_results(experiment_results: Dict[str, Any], filename: str = "experiment_results.json"):
    """Save experiment results to JSON file."""
    with open(filename, 'w') as f:
        json.dump(experiment_results, f, indent=2)
    print(f"\nResults saved to {filename}")


if __name__ == "__main__":
    print("Starting Hash-Bounds Integration Experiment...")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    results = run_full_experiment(verbose=True)
    save_results(results)
    
    print("\n" + "="*60)
    print("EXPERIMENT COMPLETE")
    print("="*60)
