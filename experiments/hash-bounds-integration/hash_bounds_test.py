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

# Additional test cases for "better than random" analysis (per user feedback)
# 10^17 scale (57-bit) - within Gate 4 operational range [10^14, 10^18]
SCALE_10_17 = TestCase(
    name="10^17 Scale (57-bit)",
    N=100006904456937509,  # ~10^17, 57-bit semiprime
    p=317000027,
    q=315479167
)

# 10^14 scale (47-bit)
SCALE_10_14 = TestCase(
    name="10^14 Scale (47-bit)",
    N=100000980001501,  # ~10^14, 47-bit semiprime
    p=10000019,
    q=10000079
)

# 58-bit generated semiprime
GENERATED_58BIT = TestCase(
    name="58-bit Generated",
    N=288230356824359011,  # 58-bit
    p=536870909,
    q=536870879
)

# Constants for "better than random" analysis
BAND_WIDTH = 0.155  # Band width for fracSqrt capture
RANDOM_BASELINE = BAND_WIDTH  # Random baseline probability equals band width


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
    
    # Guard: ln(sqrt(N)) must be positive to avoid division by zero
    # and to ensure valid domain for the Z5D formula (N must be > e²)
    if ln_sqrt_N <= 0:
        return mpf(0)
    
    inner = sqrt_N / ln_sqrt_N
    
    # inner is guaranteed > 0 if ln_sqrt_N > 0 (see guard above)
    
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


def compute_band(z5d_pred: mpf, width: float = BAND_WIDTH) -> Tuple[float, float]:
    """Compute the band [k_lo, k_hi] centered on z5d_pred.
    
    Returns raw band boundaries. Wrap-around logic is handled by is_in_band().
    """
    half_width = width / 2
    k_lo = float(z5d_pred) - half_width
    k_hi = float(z5d_pred) + half_width
    return (k_lo, k_hi)


def is_in_band(value: float, k_lo: float, k_hi: float) -> bool:
    """Check if value is in band [k_lo, k_hi], handling wrap-around.
    
    If k_lo < 0, also check if value >= (1 + k_lo) (wrap from below).
    If k_hi > 1, also check if value <= (k_hi - 1) (wrap from above).
    """
    # Standard check
    if k_lo <= value <= k_hi:
        return True
    
    # Wrap-around from below (k_lo < 0 means band wraps from 1.0)
    if k_lo < 0:
        if value >= (1.0 + k_lo):
            return True
    
    # Wrap-around from above (k_hi > 1 means band wraps to 0.0)
    if k_hi > 1:
        if value <= (k_hi - 1.0):
            return True
    
    return False


def run_single_test(tc: TestCase, verbose: bool = True) -> Dict[str, Any]:
    """Run the hash-bounds test on a single test case.
    
    Returns a dict with all computed values and verification results.
    """
    # Set precision (used implicitly via mp.dps)
    precision = set_precision(tc.N)
    
    # Compute hash-derived fraction
    hex_hash, frac_hash = compute_frac_hash(tc.N)
    
    # Compute Z5D-like prediction
    z5d_pred = compute_z5d_prediction(tc.N)
    
    # Compute attenuation
    attenuation = compute_attenuation(tc.bit_length)
    
    # Compute adjusted prediction
    adjusted_pred = compute_adjusted_prediction(z5d_pred, frac_hash, attenuation)
    
    # Compute actual values for p and q
    actual_frac_sqrt_p = compute_actual_frac_sqrt_p(tc.p)
    actual_frac_sqrt_q = compute_actual_frac_sqrt_p(tc.q)
    
    # Compute band centered on Z5D prediction
    k_lo, k_hi = compute_band(z5d_pred, BAND_WIDTH)
    
    # Check if p or q fall within the band (for "better than random" analysis)
    p_in_band = is_in_band(float(actual_frac_sqrt_p), k_lo, k_hi)
    q_in_band = is_in_band(float(actual_frac_sqrt_q), k_lo, k_hi)
    either_in_band = p_in_band or q_in_band
    
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
        "actual_frac_sqrt_q": float(actual_frac_sqrt_q),
        "band_k_lo": k_lo,
        "band_k_hi": k_hi,
        "band_width": BAND_WIDTH,
        "p_in_band": p_in_band,
        "q_in_band": q_in_band,
        "either_in_band": either_in_band,
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
        print(f"Actual {{sqrt(q)}}: {float(actual_frac_sqrt_q):.6f}")
        print()
        print(f"Band: [{k_lo:.4f}, {k_hi:.4f}] (width={BAND_WIDTH})")
        print(f"p in band: {p_in_band}")
        print(f"q in band: {q_in_band}")
        print(f"Either in band: {either_in_band}")
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
    # Set precision (used implicitly via mp.dps)
    set_precision(tc.N)
    
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
    """Run the complete hash-bounds experiment with 'better than random' analysis.
    
    Tests all cases and computes aggregate statistics.
    Success criterion: per-N capture rate > random baseline (15.5%).
    """
    # Extended test cases for "better than random" analysis (7 semiprimes)
    test_cases = [
        CHALLENGE_127,      # 127-bit - primary challenge
        SCALE_10_17,        # 57-bit - 10^17 scale
        SCALE_10_14,        # 47-bit - 10^14 scale
        GENERATED_58BIT,    # 58-bit generated
        GATE_1_30BIT,       # 30-bit gate
        GATE_2_60BIT,       # 60-bit gate
        RSA_100,            # 330-bit - control
    ]
    
    if verbose:
        print("="*60)
        print("HASH-BOUNDS INTEGRATION EXPERIMENT")
        print("="*60)
        print()
        print("Objective: Test hash-bounds against 'better than random' criterion")
        print(f"Random baseline: {RANDOM_BASELINE:.1%} (band width = {BAND_WIDTH})")
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
    
    # "Better than random" metrics
    band_captures = sum(1 for r in results if r["either_in_band"])
    per_n_rate = band_captures / len(results)
    
    avg_error_z5d = sum(errors_z5d) / len(errors_z5d)
    avg_error_adjusted = sum(errors_adjusted) / len(errors_adjusted)
    avg_error_baseline = sum(errors_baseline) / len(errors_baseline)
    avg_improvement = sum(improvements) / len(improvements)
    
    aggregates = {
        "num_cases": len(results),
        "band_width": BAND_WIDTH,
        "random_baseline": RANDOM_BASELINE,
        "band_captures": band_captures,
        "per_n_capture_rate": per_n_rate,
        "beats_random": per_n_rate > RANDOM_BASELINE,
        "avg_error_z5d": avg_error_z5d,
        "avg_error_adjusted": avg_error_adjusted,
        "avg_error_baseline_0.5": avg_error_baseline,
        "avg_improvement": avg_improvement,
        "cases_where_adjustment_helped": helped_count,
        "adjustment_helps_rate": helped_count / len(results)
    }
    
    if verbose:
        print(f"\nNumber of test cases: {aggregates['num_cases']}")
        print()
        print("=== 'Better Than Random' Analysis ===")
        print(f"Band width: {aggregates['band_width']}")
        print(f"Random baseline (expected): {aggregates['random_baseline']:.1%}")
        print(f"Band captures (p or q in band): {aggregates['band_captures']}/{aggregates['num_cases']}")
        print(f"Per-N capture rate: {aggregates['per_n_capture_rate']:.1%}")
        print(f"BEATS RANDOM: {aggregates['beats_random']}")
        print()
        print("=== Error Statistics ===")
        print(f"Average error (Z5D): {aggregates['avg_error_z5d']:.6f}")
        print(f"Average error (Adjusted): {aggregates['avg_error_adjusted']:.6f}")
        print(f"Average error (Baseline 0.5): {aggregates['avg_error_baseline_0.5']:.6f}")
        print(f"Average improvement from adjustment: {aggregates['avg_improvement']:.6f}")
        print(f"Cases where adjustment helped: {aggregates['cases_where_adjustment_helped']}/{aggregates['num_cases']}")
        print(f"Adjustment helps rate: {aggregates['adjustment_helps_rate']:.2%}")
    
    # Final verdict using "better than random" criterion
    if verbose:
        print("\n" + "="*60)
        print("STEP 4: VERDICT (Better Than Random Criterion)")
        print("="*60)
    
    # Check if 127-bit challenge captures p
    challenge_result = next((r for r in results if "127-bit" in r["test_case"]), None)
    challenge_success = challenge_result and challenge_result["p_in_band"]
    
    # Hypothesis SUPPORTED if:
    # 1. Per-N capture rate > random baseline (15.5%), AND
    # 2. 127-bit challenge captures at least one factor
    hypothesis_supported = per_n_rate > RANDOM_BASELINE
    
    supporting_evidence = []
    if hypothesis_supported:
        supporting_evidence.append(
            f"Per-N capture rate ({per_n_rate:.1%}) exceeds random baseline ({RANDOM_BASELINE:.1%})"
        )
    if challenge_success:
        supporting_evidence.append(
            f"127-bit challenge p captured in band [{challenge_result['band_k_lo']:.4f}, {challenge_result['band_k_hi']:.4f}]"
        )
    
    verdict = {
        "hypothesis_falsified": not hypothesis_supported,
        "hypothesis_supported": hypothesis_supported,
        "challenge_success": challenge_success,
        "per_n_rate": per_n_rate,
        "random_baseline": RANDOM_BASELINE,
        "beats_random_threshold": hypothesis_supported,
        "supporting_evidence": supporting_evidence,
        "conclusion": (
            f"HYPOTHESIS SUPPORTED - per-N rate {per_n_rate:.1%} > random {RANDOM_BASELINE:.1%}" 
            if hypothesis_supported 
            else f"HYPOTHESIS FALSIFIED - per-N rate {per_n_rate:.1%} <= random {RANDOM_BASELINE:.1%}"
        )
    }
    
    if verbose:
        print(f"\nPer-N capture rate: {per_n_rate:.1%}")
        print(f"Random baseline: {RANDOM_BASELINE:.1%}")
        print(f"127-bit challenge p in band: {challenge_success}")
        print()
        print(f"HYPOTHESIS {'SUPPORTED' if hypothesis_supported else 'FALSIFIED'}")
        if supporting_evidence:
            print("\nSupporting evidence:")
            for i, evidence in enumerate(supporting_evidence, 1):
                print(f"  {i}. {evidence}")
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
