"""
Z5D-GVA Band Oracle Falsification Experiment Runner
====================================================

Main experiment script that:
1. Generates all artifacts (mask.json, bands.jsonl, bins.json)
2. Runs baseline GVA for comparison
3. Runs Z5D-informed band-constrained GVA
4. Runs A/B comparison with density weighting toggle
5. Produces run_log.json with full reproducibility data
6. Outputs executive summary

Falsification Criteria:
- If Z5D band oracle does NOT improve upon baseline GVA
- If density weighting toggle does NOT change outcomes
- If short-circuit does NOT reduce computation
- If all improvements attributable to wheel mask alone

Validation Gate: 127-bit challenge
N = 137524771864208156028430259349934309717
p = 10508623501177419659
q = 13086849276577416863
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from math import isqrt, log

import mpmath as mp

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mask_generator import generate_mask, load_mask, WHEEL_MODULUS, is_admissible
from z5d_band_oracle import generate_bands, export_bands_jsonl, load_bands_jsonl, compute_sqrt_n
from band_constrained_gva import (
    band_constrained_gva, export_peaks_jsonl, quantize_km_grid, export_bins_json,
    adaptive_precision, embed_torus_geodesic, riemannian_distance
)

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717
P_EXPECTED = 10508623501177419659
Q_EXPECTED = 13086849276577416863

# Analysis thresholds
IMPROVEMENT_THRESHOLD = 0.9  # 10% improvement required for significance

# Experiment parameters
EXPERIMENT_CONFIG = {
    "max_delta": 10**7,
    "inner_band_count": 20,
    "outer_band_count": 10,
    "k_values": [0.25, 0.30, 0.35, 0.40, 0.45],
    "m_range": (1, 100),
    "k_bins": 10,
    "m_bins": 20,
    "max_candidates_per_band": 1000,
    "baseline_max_candidates": 50000,
    "baseline_delta_window": 500000,
    "seed": 42
}


def run_baseline_gva(N: int, verbose: bool = False):
    """
    Run baseline GVA without Z5D enhancements.
    
    This is the control group for the falsification experiment.
    """
    import mpmath as mp
    
    sqrt_N = isqrt(N)
    required_dps = adaptive_precision(N)
    
    start_time = time.time()
    
    result = {
        "method": "baseline_gva",
        "N": str(N),
        "sqrt_N": str(sqrt_N),
        "config": {
            "max_candidates": EXPERIMENT_CONFIG["baseline_max_candidates"],
            "delta_window": EXPERIMENT_CONFIG["baseline_delta_window"],
            "k_values": EXPERIMENT_CONFIG["k_values"],
            "precision": required_dps
        },
        "started_at": datetime.now(timezone.utc).isoformat(),
        "success": False,
        "factors": None,
        "candidates_tested": 0,
        "elapsed_seconds": None
    }
    
    if verbose:
        print("=" * 70)
        print("BASELINE GVA (Control)")
        print("=" * 70)
        print(f"N = {N}")
        print(f"Max candidates: {EXPERIMENT_CONFIG['baseline_max_candidates']}")
        print(f"Delta window: ±{EXPERIMENT_CONFIG['baseline_delta_window']}")
        print()
    
    with mp.workdps(required_dps):
        phi = float((1 + mp.sqrt(5)) / 2)
        phi_inv = 1 / phi
        
        delta_window = EXPERIMENT_CONFIG["baseline_delta_window"]
        max_candidates = EXPERIMENT_CONFIG["baseline_max_candidates"]
        
        candidates_tested = 0
        
        for k in EXPERIMENT_CONFIG["k_values"]:
            # Embed N (functions imported at module level)
            N_coords = embed_torus_geodesic(N, k)
            
            for i in range(max_candidates // len(EXPERIMENT_CONFIG["k_values"])):
                alpha = (i * phi_inv) % 1.0
                delta = int(alpha * 2 * delta_window - delta_window)
                candidate = sqrt_N + delta
                
                if candidate <= 1 or candidate >= N:
                    continue
                if candidate % 2 == 0:
                    continue
                
                candidates_tested += 1
                
                if N % candidate == 0:
                    elapsed = time.time() - start_time
                    
                    p = candidate
                    q = N // candidate
                    
                    result["success"] = True
                    result["factors"] = {"p": str(p), "q": str(q)}
                    result["candidates_tested"] = candidates_tested
                    result["elapsed_seconds"] = elapsed
                    result["delta"] = delta
                    result["k"] = k
                    
                    if verbose:
                        print(f"✓ FACTOR FOUND!")
                        print(f"  p = {p}")
                        print(f"  q = {q}")
                        print(f"  Candidates tested: {candidates_tested}")
                        print(f"  Elapsed: {elapsed:.3f}s")
                    
                    return result
        
        elapsed = time.time() - start_time
        result["candidates_tested"] = candidates_tested
        result["elapsed_seconds"] = elapsed
        
        if verbose:
            print(f"✗ No factors found")
            print(f"  Candidates tested: {candidates_tested}")
            print(f"  Elapsed: {elapsed:.3f}s")
    
    return result


def run_z5d_band_oracle_gva(N: int, mask_set, bands, use_density_weight: bool = False, 
                            verbose: bool = False):
    """
    Run Z5D-informed band-constrained GVA.
    
    This is the treatment group for the falsification experiment.
    """
    sqrt_N = isqrt(N)
    
    start_time = time.time()
    
    result = {
        "method": f"z5d_band_oracle_gva_density_{use_density_weight}",
        "N": str(N),
        "sqrt_N": str(sqrt_N),
        "config": {
            "bands": len(bands),
            "mask_residues": len(mask_set),
            "modulus": WHEEL_MODULUS,
            "k_values": EXPERIMENT_CONFIG["k_values"],
            "max_candidates_per_band": EXPERIMENT_CONFIG["max_candidates_per_band"],
            "use_density_weight": use_density_weight,
            "use_short_circuit": True
        },
        "started_at": datetime.now(timezone.utc).isoformat(),
        "success": False,
        "factors": None,
        "candidates_tested": 0,
        "candidates_filtered": 0,
        "bands_explored": 0,
        "short_circuited": 0,
        "elapsed_seconds": None
    }
    
    if verbose:
        label = "WITH" if use_density_weight else "WITHOUT"
        print("=" * 70)
        print(f"Z5D BAND ORACLE GVA ({label} density weighting)")
        print("=" * 70)
        print(f"N = {N}")
        print(f"Bands: {len(bands)}")
        print(f"Mask residues: {len(mask_set)} (mod {WHEEL_MODULUS})")
        print(f"Density weighting: {use_density_weight}")
        print()
    
    factors, peaks = band_constrained_gva(
        N,
        bands,
        mask_set,
        WHEEL_MODULUS,
        k_values=EXPERIMENT_CONFIG["k_values"],
        max_candidates_per_band=EXPERIMENT_CONFIG["max_candidates_per_band"],
        use_density_weight=use_density_weight,
        use_short_circuit=True,
        verbose=verbose
    )
    
    elapsed = time.time() - start_time
    
    result["elapsed_seconds"] = elapsed
    result["peaks_recorded"] = len(peaks)
    
    if factors:
        p, q = factors
        result["success"] = True
        result["factors"] = {"p": str(p), "q": str(q)}
    
    return result, peaks


def generate_artifacts(output_dir: str, verbose: bool = False):
    """Generate all experiment artifacts."""
    artifacts = {}
    
    # 1. Generate mask.json
    if verbose:
        print("Generating mask.json...")
    mask_path = os.path.join(output_dir, "mask.json")
    mask_data = generate_mask(mask_path)
    artifacts["mask"] = mask_path
    
    # 2. Generate bands.jsonl
    if verbose:
        print("Generating bands.jsonl...")
    bands_path = os.path.join(output_dir, "bands.jsonl")
    bands = generate_bands(
        CHALLENGE_127,
        max_delta=EXPERIMENT_CONFIG["max_delta"],
        inner_band_count=EXPERIMENT_CONFIG["inner_band_count"],
        outer_band_count=EXPERIMENT_CONFIG["outer_band_count"]
    )
    export_bands_jsonl(bands, CHALLENGE_127, bands_path)
    artifacts["bands"] = bands_path
    
    # 3. Generate bins.json
    if verbose:
        print("Generating bins.json...")
    bins_path = os.path.join(output_dir, "bins.json")
    bins_data = quantize_km_grid(
        EXPERIMENT_CONFIG["k_values"],
        EXPERIMENT_CONFIG["m_range"],
        EXPERIMENT_CONFIG["k_bins"],
        EXPERIMENT_CONFIG["m_bins"]
    )
    export_bins_json(bins_data, bins_path)
    artifacts["bins"] = bins_path
    
    return artifacts, mask_data, bands, bins_data


def run_experiment(verbose: bool = True):
    """
    Run the full falsification experiment.
    
    Tests whether Z5D-informed GVA upgrades move the needle on 127-bit challenge.
    """
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 70)
    print("Z5D-GVA BAND ORACLE FALSIFICATION EXPERIMENT")
    print("=" * 70)
    print()
    print(f"Target: 127-bit challenge")
    print(f"N = {CHALLENGE_127}")
    print(f"Expected factors:")
    print(f"  p = {P_EXPECTED}")
    print(f"  q = {Q_EXPECTED}")
    print()
    
    # Verify expected factors
    assert P_EXPECTED * Q_EXPECTED == CHALLENGE_127, "Factor verification failed!"
    print("✓ Factor verification passed")
    print()
    
    # Initialize run log
    run_log = {
        "experiment": "z5d-gva-band-oracle-falsification",
        "target": {
            "N": str(CHALLENGE_127),
            "bit_length": CHALLENGE_127.bit_length(),
            "p": str(P_EXPECTED),
            "q": str(Q_EXPECTED)
        },
        "config": EXPERIMENT_CONFIG,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {},
        "results": {},
        "summary": {}
    }
    
    # Generate artifacts
    print("-" * 70)
    print("PHASE 1: Generating Artifacts")
    print("-" * 70)
    artifacts, mask_data, bands, bins_data = generate_artifacts(output_dir, verbose=True)
    run_log["artifacts"] = artifacts
    print()
    
    # Load mask for experiments
    mask_set = set(mask_data["residues"])
    
    # Check if known factors pass mask
    p_admissible = (P_EXPECTED % WHEEL_MODULUS) in mask_set
    q_admissible = (Q_EXPECTED % WHEEL_MODULUS) in mask_set
    print(f"Factor p admissible (mod {WHEEL_MODULUS}): {p_admissible}")
    print(f"Factor q admissible (mod {WHEEL_MODULUS}): {q_admissible}")
    
    if not p_admissible or not q_admissible:
        print("⚠ WARNING: Known factors not in admissible residue classes!")
        print("This indicates the wheel mask may be filtering out valid factors.")
    print()
    
    # Run experiments
    print("-" * 70)
    print("PHASE 2: Running Experiments")
    print("-" * 70)
    print()
    
    # Experiment 1: Baseline GVA
    print("[1/3] Running baseline GVA...")
    baseline_result = run_baseline_gva(CHALLENGE_127, verbose=verbose)
    run_log["results"]["baseline"] = baseline_result
    print()
    
    # Experiment 2: Z5D Band Oracle GVA (without density weighting)
    print("[2/3] Running Z5D band oracle GVA (density_weight=False)...")
    z5d_result_a, peaks_a = run_z5d_band_oracle_gva(
        CHALLENGE_127, mask_set, bands, 
        use_density_weight=False, verbose=verbose
    )
    run_log["results"]["z5d_no_density"] = z5d_result_a
    print()
    
    # Export peaks for experiment 2
    peaks_path_a = os.path.join(output_dir, "peaks.jsonl")
    export_peaks_jsonl(peaks_a, CHALLENGE_127, peaks_path_a, {"experiment": "z5d_no_density"})
    
    # Experiment 3: Z5D Band Oracle GVA (with density weighting)
    print("[3/3] Running Z5D band oracle GVA (density_weight=True)...")
    z5d_result_b, peaks_b = run_z5d_band_oracle_gva(
        CHALLENGE_127, mask_set, bands, 
        use_density_weight=True, verbose=verbose
    )
    run_log["results"]["z5d_with_density"] = z5d_result_b
    print()
    
    # Analysis
    print("-" * 70)
    print("PHASE 3: Analysis")
    print("-" * 70)
    print()
    
    # Compute metrics
    baseline_success = baseline_result["success"]
    z5d_a_success = z5d_result_a["success"]
    z5d_b_success = z5d_result_b["success"]
    
    baseline_time = baseline_result["elapsed_seconds"]
    z5d_a_time = z5d_result_a["elapsed_seconds"]
    z5d_b_time = z5d_result_b["elapsed_seconds"]
    
    baseline_tested = baseline_result["candidates_tested"]
    
    # Determine falsification criteria
    criteria = {
        "z5d_improves_over_baseline": False,
        "density_toggle_changes_outcome": False,
        "short_circuit_reduces_computation": False,
        "improvements_not_just_wheel_mask": False
    }
    
    # Criterion 1: Z5D improves over baseline
    if z5d_a_success and not baseline_success:
        criteria["z5d_improves_over_baseline"] = True
    elif z5d_a_success and baseline_success:
        # Check if Z5D is faster (beyond IMPROVEMENT_THRESHOLD) or tests fewer candidates
        criteria["z5d_improves_over_baseline"] = (z5d_a_time < baseline_time * IMPROVEMENT_THRESHOLD)
    
    # Criterion 2: Density toggle changes outcome
    if z5d_a_success != z5d_b_success:
        criteria["density_toggle_changes_outcome"] = True
    elif z5d_a_success and z5d_b_success:
        # Check if times differ significantly
        if z5d_b_time is not None and z5d_a_time is not None:
            criteria["density_toggle_changes_outcome"] = abs(z5d_a_time - z5d_b_time) > 0.5
    
    # Criterion 3: Short-circuit reduces computation
    # (Would need more detailed metrics to properly assess)
    criteria["short_circuit_reduces_computation"] = z5d_result_a.get("short_circuited", 0) > 0
    
    # Criterion 4: Improvements not just from wheel mask
    # If Z5D succeeds but a wheel-only baseline would also succeed, 
    # then Z5D prior is redundant
    criteria["improvements_not_just_wheel_mask"] = z5d_a_success and not baseline_success
    
    # Determine overall verdict
    hypothesis_supported = any([
        criteria["z5d_improves_over_baseline"],
        criteria["density_toggle_changes_outcome"],
        criteria["improvements_not_just_wheel_mask"]
    ])
    
    hypothesis_falsified = not hypothesis_supported
    
    # Summary
    summary = {
        "hypothesis": "Z5D-informed GVA upgrade improves 127-bit factorization",
        "verdict": "FALSIFIED" if hypothesis_falsified else "SUPPORTED",
        "criteria_results": criteria,
        "baseline_success": baseline_success,
        "z5d_no_density_success": z5d_a_success,
        "z5d_with_density_success": z5d_b_success,
        "baseline_time_s": baseline_time,
        "z5d_no_density_time_s": z5d_a_time,
        "z5d_with_density_time_s": z5d_b_time,
        "factor_p_admissible": p_admissible,
        "factor_q_admissible": q_admissible
    }
    
    run_log["summary"] = summary
    run_log["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    # Export run log
    run_log_path = os.path.join(output_dir, "run_log.json")
    with open(run_log_path, 'w') as f:
        json.dump(run_log, f, indent=2)
    
    # Print summary
    print("=" * 70)
    print("EXECUTIVE SUMMARY")
    print("=" * 70)
    print()
    print(f"Hypothesis: Z5D-informed GVA upgrade improves 127-bit factorization")
    print()
    print(f"Results:")
    print(f"  Baseline GVA: {'SUCCESS' if baseline_success else 'FAILURE'} ({baseline_time:.3f}s)")
    print(f"  Z5D (no density): {'SUCCESS' if z5d_a_success else 'FAILURE'} ({z5d_a_time:.3f}s)")
    print(f"  Z5D (with density): {'SUCCESS' if z5d_b_success else 'FAILURE'} ({z5d_b_time:.3f}s)")
    print()
    print(f"Falsification Criteria:")
    for name, result in criteria.items():
        status = "✓" if result else "✗"
        print(f"  {status} {name}: {result}")
    print()
    print(f"VERDICT: **HYPOTHESIS {'FALSIFIED' if hypothesis_falsified else 'SUPPORTED'}**")
    print()
    
    if hypothesis_falsified:
        print("Interpretation:")
        print("  The Z5D-informed GVA upgrade does NOT demonstrably improve")
        print("  factorization of the 127-bit challenge over baseline methods.")
        print("  The band oracle, density weighting, and short-circuit mechanisms")
        print("  did not produce measurable benefits within the test budget.")
    else:
        print("Interpretation:")
        print("  The Z5D-informed GVA upgrade shows some improvement over baseline.")
        print("  Further investigation needed to quantify the benefit.")
    
    print()
    print("=" * 70)
    print("ARTIFACTS GENERATED")
    print("=" * 70)
    print(f"  mask.json: {artifacts['mask']}")
    print(f"  bands.jsonl: {artifacts['bands']}")
    print(f"  bins.json: {artifacts['bins']}")
    print(f"  peaks.jsonl: {peaks_path_a}")
    print(f"  run_log.json: {run_log_path}")
    print()
    
    return run_log


if __name__ == "__main__":
    run_log = run_experiment(verbose=True)
