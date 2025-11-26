"""
Test Suite: Band-First Router + Early-Exit Guard Falsification
===============================================================

Two CI performance tests:

Test A — Band Router Coverage:
- Given: N = CHALLENGE_127, seed=42, C=0.9, alpha=1.0, wheel=210
- When: run router-only planner to emit bands + masked candidates
- Then assert:
  - ≥70% reduction in candidate count vs. unbanded + wheel-only baseline
  - Planned bands collectively cover ≥C of expected gap mass around √N
- Artifact: router_A_seed42.jsonl

Test B — Early-Exit Efficiency:
- Given: N = CHALLENGE_127, seed=43, tau/L as specified
- When: run full scan with early-exit on vs. off
- Then assert:
  - ≤5% loss in recall of top-k resonance peaks (k=20) vs. control
  - ≥35% reduction in Z5D steps or wall-time
- Artifacts: scan_on_B_seed43.jsonl, scan_off_B_seed43.jsonl, diff.jsonl
"""

import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from math import isqrt

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(__file__))

from band_router import (
    CHALLENGE_127, RANGE_MIN, RANGE_MAX,
    plan_bands, apply_wheel, run_scan, compute_band_coverage,
    compute_reduction_ratio, count_admissible_in_range,
    expected_gap, is_flat, adaptive_precision, get_git_head,
    timestamp_utc, DEFAULT_C, DEFAULT_ALPHA, DEFAULT_WHEEL,
    DEFAULT_TAU_GRAD, DEFAULT_TAU_CURV, DEFAULT_L
)


# ============================================================================
# Constants
# ============================================================================

ARTIFACT_DIR = Path(__file__).parent


# ============================================================================
# Test A — Band Router Coverage
# ============================================================================

class TestBandRouterCoverage:
    """Test A: Validate band router reduces candidates while maintaining coverage."""
    
    # Test parameters
    SEED = 42
    C = 0.9
    ALPHA = 1.0
    WHEEL = 210
    NUM_BANDS = 20
    
    # Thresholds
    MIN_REDUCTION = 0.70  # ≥70% reduction in candidate count
    MIN_COVERAGE = 0.9    # ≥C coverage of expected gap mass
    
    def test_band_router_coverage(self):
        """
        Test A: Band router achieves ≥70% reduction while maintaining ≥90% coverage.
        
        Hypothesis: Band-first routing with wheel mask reduces candidates significantly
        compared to scanning the entire unbanded range.
        
        Falsification criteria:
        - If reduction < 70%: Hypothesis falsified (no significant improvement)
        - If coverage < 90%: Hypothesis falsified (coverage loss unacceptable)
        """
        N = CHALLENGE_127
        sqrt_N = isqrt(N)
        dps = adaptive_precision(N)
        
        # Plan bands
        bands = plan_bands(N, C=self.C, alpha=self.ALPHA, wheel=self.WHEEL,
                          num_bands=self.NUM_BANDS)
        
        # Calculate total band span
        delta_max = max(max(abs(b.delta_start), abs(b.delta_end)) for b in bands)
        total_band_span = sum(b.width for b in bands)
        
        # Baseline: unbanded + wheel-only
        # Count all wheel-filtered candidates in the full range
        start_range = sqrt_N - delta_max
        end_range = sqrt_N + delta_max
        unbanded_wheel_count = count_admissible_in_range(start_range, end_range)
        
        # Banded: count candidates only within planned bands
        banded_count = 0
        for band in bands:
            band_start = sqrt_N + band.delta_start
            band_end = sqrt_N + band.delta_end
            if band_start > band_end:
                band_start, band_end = band_end, band_start
            banded_count += count_admissible_in_range(band_start, band_end)
        
        # Compute reduction
        reduction = compute_reduction_ratio(banded_count, unbanded_wheel_count)
        
        # Compute coverage
        coverage = compute_band_coverage(bands, sqrt_N)
        
        # Write artifact
        artifact = {
            'event': 'test_A_complete',
            'seed': self.SEED,
            'C': self.C,
            'alpha': self.ALPHA,
            'wheel': self.WHEEL,
            'dps': dps,
            'git_head': get_git_head(),
            'timestamp_utc': timestamp_utc(),
            'N': str(N),
            'sqrt_N': str(sqrt_N),
            'num_bands': len(bands),
            'delta_max': delta_max,
            'total_band_span': total_band_span,
            'unbanded_wheel_count': unbanded_wheel_count,
            'banded_count': banded_count,
            'reduction': reduction,
            'coverage': coverage,
            'min_reduction_threshold': self.MIN_REDUCTION,
            'min_coverage_threshold': self.MIN_COVERAGE,
            'reduction_pass': reduction >= self.MIN_REDUCTION,
            'coverage_pass': coverage >= self.MIN_COVERAGE,
            'hypothesis_supported': reduction >= self.MIN_REDUCTION and coverage >= self.MIN_COVERAGE
        }
        
        artifact_path = ARTIFACT_DIR / f'router_A_seed{self.SEED}.jsonl'
        with open(artifact_path, 'w') as f:
            f.write(json.dumps(artifact) + '\n')
        
        # Report results
        print(f"\n{'='*70}")
        print("Test A — Band Router Coverage Results")
        print(f"{'='*70}")
        print(f"N = {N}")
        print(f"√N = {sqrt_N}")
        print(f"Expected gap = {expected_gap(float(sqrt_N)):.2f}")
        print(f"Bands planned = {len(bands)}")
        print(f"Delta max = {delta_max}")
        print(f"\nCandidate Counts:")
        print(f"  Unbanded + wheel-only = {unbanded_wheel_count:,}")
        print(f"  Banded + wheel-only = {banded_count:,}")
        print(f"  Reduction = {reduction:.1%} (threshold: ≥{self.MIN_REDUCTION:.0%})")
        print(f"\nCoverage:")
        print(f"  Coverage = {coverage:.1%} (threshold: ≥{self.MIN_COVERAGE:.0%})")
        print(f"\nVerdict:")
        print(f"  Reduction: {'PASS' if reduction >= self.MIN_REDUCTION else 'FAIL'}")
        print(f"  Coverage: {'PASS' if coverage >= self.MIN_COVERAGE else 'FAIL'}")
        print(f"  Hypothesis: {'SUPPORTED' if artifact['hypothesis_supported'] else 'FALSIFIED'}")
        print(f"\nArtifact: {artifact_path}")
        
        # Assertions
        assert reduction >= self.MIN_REDUCTION, \
            f"Reduction {reduction:.1%} < {self.MIN_REDUCTION:.0%}: Hypothesis FALSIFIED"
        assert coverage >= self.MIN_COVERAGE, \
            f"Coverage {coverage:.1%} < {self.MIN_COVERAGE:.0%}: Hypothesis FALSIFIED"


# ============================================================================
# Test B — Early-Exit Efficiency
# ============================================================================

class TestEarlyExitEfficiency:
    """Test B: Validate early-exit improves efficiency without significant recall loss."""
    
    # Test parameters
    SEED = 43
    C = 0.9
    ALPHA = 1.0
    WHEEL = 210
    NUM_BANDS = 10
    MAX_STEPS_PER_BAND = 500  # Reduced for CI speed
    K = 0.35
    TAU_GRAD = 1e-6
    TAU_CURV = 1e-8
    L = 8
    TOP_K = 20  # Number of peaks to compare for recall
    
    # Thresholds
    MAX_RECALL_LOSS = 0.05   # ≤5% loss in recall
    MIN_STEP_REDUCTION = 0.35  # ≥35% reduction in steps or wall-time
    
    def test_early_exit_efficiency(self):
        """
        Test B: Early-exit achieves ≥35% step reduction with ≤5% recall loss.
        
        Hypothesis: Early-exit guard detects flat surfaces and aborts bands,
        reducing computation without losing significant resonance peaks.
        
        Falsification criteria:
        - If step reduction < 35%: Hypothesis falsified (no efficiency gain)
        - If recall loss > 5%: Hypothesis falsified (too much signal loss)
        """
        N = CHALLENGE_127
        sqrt_N = isqrt(N)
        
        # Run scan WITHOUT early exit (control)
        scan_off_path = ARTIFACT_DIR / f'scan_off_B_seed{self.SEED}.jsonl'
        report_off = run_scan(
            N=N,
            seed=self.SEED,
            C=self.C,
            alpha=self.ALPHA,
            wheel=self.WHEEL,
            num_bands=self.NUM_BANDS,
            max_steps_per_band=self.MAX_STEPS_PER_BAND,
            k=self.K,
            early_exit=False,
            log_file=str(scan_off_path),
            verbose=False
        )
        
        # Run scan WITH early exit (treatment)
        scan_on_path = ARTIFACT_DIR / f'scan_on_B_seed{self.SEED}.jsonl'
        report_on = run_scan(
            N=N,
            seed=self.SEED,
            C=self.C,
            alpha=self.ALPHA,
            wheel=self.WHEEL,
            num_bands=self.NUM_BANDS,
            max_steps_per_band=self.MAX_STEPS_PER_BAND,
            k=self.K,
            early_exit=True,
            tau_grad=self.TAU_GRAD,
            tau_curv=self.TAU_CURV,
            L=self.L,
            log_file=str(scan_on_path),
            verbose=False
        )
        
        # Compute step reduction
        steps_off = report_off.z5d_steps
        steps_on = report_on.z5d_steps
        
        if steps_off > 0:
            step_reduction = (steps_off - steps_on) / steps_off
        else:
            step_reduction = 0.0
        
        # Compute time reduction
        time_off = report_off.wall_time_sec
        time_on = report_on.wall_time_sec
        
        if time_off > 0:
            time_reduction = (time_off - time_on) / time_off
        else:
            time_reduction = 0.0
        
        # Compute recall of top-k peaks
        # Get peaks sorted by amplitude (lower = better)
        peaks_off = sorted(report_off.peaks, key=lambda p: p['amplitude'])[:self.TOP_K]
        peaks_on = sorted(report_on.peaks, key=lambda p: p['amplitude'])[:self.TOP_K]
        
        # Find overlap (peaks present in both)
        peaks_off_set = {p['candidate'] for p in peaks_off}
        peaks_on_set = {p['candidate'] for p in peaks_on}
        
        if len(peaks_off_set) > 0:
            recall = len(peaks_off_set & peaks_on_set) / len(peaks_off_set)
            recall_loss = 1.0 - recall
        else:
            # No peaks in control - can't measure recall loss
            recall = 1.0
            recall_loss = 0.0
        
        # Use best of step or time reduction for threshold
        best_reduction = max(step_reduction, time_reduction)
        
        # Write diff artifact
        diff_artifact = {
            'event': 'test_B_complete',
            'seed': self.SEED,
            'C': self.C,
            'alpha': self.ALPHA,
            'wheel': self.WHEEL,
            'tau_grad': self.TAU_GRAD,
            'tau_curv': self.TAU_CURV,
            'L': self.L,
            'dps': report_off.dps,
            'git_head': get_git_head(),
            'timestamp_utc': timestamp_utc(),
            'N': str(N),
            'sqrt_N': str(sqrt_N),
            
            # Control (early-exit OFF)
            'steps_off': steps_off,
            'time_off_sec': time_off,
            'peaks_off': len(report_off.peaks),
            'early_exits_off': report_off.early_exits,
            
            # Treatment (early-exit ON)
            'steps_on': steps_on,
            'time_on_sec': time_on,
            'peaks_on': len(report_on.peaks),
            'early_exits_on': report_on.early_exits,
            
            # Metrics
            'step_reduction': step_reduction,
            'time_reduction': time_reduction,
            'best_reduction': best_reduction,
            'top_k': self.TOP_K,
            'recall': recall,
            'recall_loss': recall_loss,
            
            # Thresholds
            'min_step_reduction_threshold': self.MIN_STEP_REDUCTION,
            'max_recall_loss_threshold': self.MAX_RECALL_LOSS,
            
            # Results
            'reduction_pass': best_reduction >= self.MIN_STEP_REDUCTION,
            'recall_pass': recall_loss <= self.MAX_RECALL_LOSS,
            'hypothesis_supported': (best_reduction >= self.MIN_STEP_REDUCTION and 
                                    recall_loss <= self.MAX_RECALL_LOSS)
        }
        
        diff_path = ARTIFACT_DIR / f'diff.jsonl'
        with open(diff_path, 'w') as f:
            f.write(json.dumps(diff_artifact) + '\n')
        
        # Report results
        print(f"\n{'='*70}")
        print("Test B — Early-Exit Efficiency Results")
        print(f"{'='*70}")
        print(f"N = {N}")
        print(f"√N = {sqrt_N}")
        print(f"\nControl (early-exit OFF):")
        print(f"  Steps = {steps_off:,}")
        print(f"  Time = {time_off:.2f}s")
        print(f"  Peaks = {len(report_off.peaks)}")
        print(f"\nTreatment (early-exit ON):")
        print(f"  Steps = {steps_on:,}")
        print(f"  Time = {time_on:.2f}s")
        print(f"  Peaks = {len(report_on.peaks)}")
        print(f"  Early exits = {report_on.early_exits}")
        print(f"\nEfficiency Metrics:")
        print(f"  Step reduction = {step_reduction:.1%} (threshold: ≥{self.MIN_STEP_REDUCTION:.0%})")
        print(f"  Time reduction = {time_reduction:.1%}")
        print(f"  Best reduction = {best_reduction:.1%}")
        print(f"\nRecall Metrics (top-{self.TOP_K} peaks):")
        print(f"  Recall = {recall:.1%}")
        print(f"  Recall loss = {recall_loss:.1%} (threshold: ≤{self.MAX_RECALL_LOSS:.0%})")
        print(f"\nVerdict:")
        print(f"  Reduction: {'PASS' if diff_artifact['reduction_pass'] else 'FAIL'}")
        print(f"  Recall: {'PASS' if diff_artifact['recall_pass'] else 'FAIL'}")
        print(f"  Hypothesis: {'SUPPORTED' if diff_artifact['hypothesis_supported'] else 'FALSIFIED'}")
        print(f"\nArtifacts:")
        print(f"  Control: {scan_off_path}")
        print(f"  Treatment: {scan_on_path}")
        print(f"  Diff: {diff_path}")
        
        # Assertions
        assert best_reduction >= self.MIN_STEP_REDUCTION, \
            f"Best reduction {best_reduction:.1%} < {self.MIN_STEP_REDUCTION:.0%}: Hypothesis FALSIFIED"
        assert recall_loss <= self.MAX_RECALL_LOSS, \
            f"Recall loss {recall_loss:.1%} > {self.MAX_RECALL_LOSS:.0%}: Hypothesis FALSIFIED"


# ============================================================================
# Flat Detection Unit Tests
# ============================================================================

class TestFlatDetection:
    """Unit tests for is_flat() function."""
    
    def test_flat_surface_detected(self):
        """Flat amplitude surface triggers early exit."""
        # Nearly constant amplitudes
        amplitudes = [0.5 + 1e-9 * i for i in range(10)]
        assert is_flat(amplitudes, tau_grad=1e-6, tau_curv=1e-8, L=8), \
            "Flat surface should be detected"
    
    def test_varying_surface_not_detected(self):
        """Varying amplitude surface does not trigger early exit."""
        # Clearly varying amplitudes
        amplitudes = [0.5 + 0.1 * (i % 2) for i in range(10)]
        assert not is_flat(amplitudes, tau_grad=1e-6, tau_curv=1e-8, L=8), \
            "Varying surface should not be detected as flat"
    
    def test_insufficient_window(self):
        """Insufficient data returns False."""
        amplitudes = [0.5, 0.5, 0.5]  # Only 3 points, L=8
        assert not is_flat(amplitudes, tau_grad=1e-6, tau_curv=1e-8, L=8), \
            "Insufficient window should return False"
    
    def test_gradient_threshold(self):
        """Gradient above threshold prevents flat detection."""
        # Linear increase with significant gradient
        amplitudes = [0.5 + 0.01 * i for i in range(10)]
        assert not is_flat(amplitudes, tau_grad=1e-6, tau_curv=1e-8, L=8), \
            "Surface with significant gradient should not be detected as flat"


# ============================================================================
# Band Planning Unit Tests
# ============================================================================

class TestBandPlanning:
    """Unit tests for plan_bands() function."""
    
    def test_band_count(self):
        """Correct number of bands created."""
        bands = plan_bands(CHALLENGE_127, num_bands=10)
        assert len(bands) == 10, f"Expected 10 bands, got {len(bands)}"
    
    def test_bands_sorted_by_density(self):
        """Bands are sorted by density (descending)."""
        bands = plan_bands(CHALLENGE_127, num_bands=10)
        densities = [b.expected_density for b in bands]
        assert densities == sorted(densities, reverse=True), \
            "Bands should be sorted by density descending"
    
    def test_band_priorities_assigned(self):
        """Priorities match sorted order."""
        bands = plan_bands(CHALLENGE_127, num_bands=10)
        for i, band in enumerate(bands):
            assert band.priority == i, \
                f"Band {band.id} should have priority {i}, got {band.priority}"
    
    def test_band_width_scales_with_alpha(self):
        """Band width scales with alpha parameter."""
        bands_low = plan_bands(CHALLENGE_127, alpha=0.6, num_bands=5)
        bands_high = plan_bands(CHALLENGE_127, alpha=1.6, num_bands=5)
        
        width_low = bands_low[0].width
        width_high = bands_high[0].width
        
        assert width_high > width_low, \
            f"Higher alpha should give wider bands: {width_high} vs {width_low}"


# ============================================================================
# Wheel Filtering Unit Tests
# ============================================================================

class TestWheelFiltering:
    """Unit tests for apply_wheel() function."""
    
    def test_wheel_reduction(self):
        """Wheel filtering achieves expected reduction."""
        candidates = list(range(1000, 2000))
        filtered = apply_wheel(candidates, wheel=210)
        
        # Wheel 210 should reduce by ~77%
        reduction = 1.0 - len(filtered) / len(candidates)
        assert 0.70 < reduction < 0.80, \
            f"Wheel 210 reduction should be ~77%, got {reduction:.1%}"
    
    def test_all_filtered_admissible(self):
        """All filtered candidates are admissible mod 210."""
        candidates = list(range(1000, 2000))
        filtered = apply_wheel(candidates, wheel=210)
        
        from band_router import is_admissible
        for c in filtered:
            assert is_admissible(c), f"{c} should be admissible mod 210"
    
    def test_unsupported_wheel_raises(self):
        """Non-210 wheel raises ValueError."""
        candidates = [100, 200, 300]
        with pytest.raises(ValueError):
            apply_wheel(candidates, wheel=30)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
