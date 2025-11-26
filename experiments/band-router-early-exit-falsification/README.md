# Band-First Router + Early-Exit Guard Falsification Experiment

## Overview

This experiment attempts to **falsify** the hypothesis that:

1. **Band-first router**: Dividing the search space into bands based on expected factor gap Δ ≈ ln(√N) with wheel mask (mod-210) prefiltering significantly reduces candidate count while maintaining coverage.

2. **Early-exit guard**: Aborting bands with flat amplitude/curvature surfaces (|∂A|<τ₁ && |∂²A|<τ₂ over L steps) improves efficiency without significant recall loss.

## Quick Start

```bash
# Navigate to experiment directory
cd experiments/band-router-early-exit-falsification

# Run tests
pytest test_band_router.py -v -s

# Run quick validation
python3 band_router.py
```

## Challenge Target

- **N** = 137524771864208156028430259349934309717 (CHALLENGE_127)
- **Bit-length**: 127 bits
- **√N** ≈ 1.17 × 10^19
- **Expected gap**: Δ ≈ ln(√N) ≈ 44

## Hypothesis Details

### Band-First Router

Instead of scanning the entire search space uniformly, we:

1. Compute expected factor gap: Δ ≈ ln(√N)
2. Divide search space into bands of width w = α × Δ
3. Apply wheel mask (mod-210) to eliminate ~77% of candidates
4. Use Z5D density estimates to prioritize bands by expected prime density
5. Scan bands in priority order

**Expected benefit**: Significant reduction in candidates while maintaining factor coverage.

### Early-Exit Guard

During band scanning, monitor the amplitude/curvature surface:

1. Track amplitude values over sliding window of size L
2. Compute gradient (first differences) and curvature (second differences)
3. If |∂A| < τ₁ AND |∂²A| < τ₂ for L consecutive steps, the surface is "flat"
4. Flat surfaces indicate no resonance signal — abort band early

**Expected benefit**: Reduced Z5D steps without losing significant peaks.

## Parameters

### Band Router Parameters
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| C | 0.9 | 0.8–0.98 | Coverage target |
| α | 1.0 | 0.6–1.6 | Inner-band scale factor |
| wheel | 210 | — | Wheel modulus |
| num_bands | 20 | 10–50 | Number of bands |

### Early-Exit Parameters
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| τ_grad | 1e-6 | — | Gradient threshold |
| τ_curv | 1e-8 | — | Curvature threshold |
| L | 8 | 4–16 | Window size |

## Test Cases

### Test A — Band Router Coverage

**Given**: N = CHALLENGE_127, seed=42, C=0.9, α=1.0, wheel=210

**When**: Run router-only planner to emit bands + masked candidates

**Then assert**:
- ≥70% reduction in candidate count vs. unbanded + wheel-only baseline
- Planned bands collectively cover ≥90% of expected gap mass around √N

**Artifact**: `router_A_seed42.jsonl`

### Test B — Early-Exit Efficiency

**Given**: N = CHALLENGE_127, seed=43, τ_grad=1e-6, τ_curv=1e-8, L=8

**When**: Run full scan with early-exit on vs. off

**Then assert**:
- ≤5% loss in recall of top-k resonance peaks (k=20) vs. control
- ≥35% reduction in Z5D steps or wall-time

**Artifacts**: 
- `scan_on_B_seed43.jsonl` (treatment)
- `scan_off_B_seed43.jsonl` (control)
- `diff.jsonl` (comparison)

## Falsification Criteria

The hypothesis is **FALSIFIED** if any of:

1. **Band router fails**: Candidate reduction < 70% compared to unbanded baseline
2. **Coverage loss**: Band coverage < 90% of expected gap mass
3. **No efficiency gain**: Early-exit achieves < 35% step/time reduction
4. **Recall degradation**: Early-exit loses > 5% of top-k peaks

## Implementation Components

### Core Module: `band_router.py`

| Function | Description |
|----------|-------------|
| `plan_bands(N, C, alpha, wheel) -> [Band]` | Plan bands based on expected gap |
| `apply_wheel(candidates, wheel) -> candidates'` | Wheel mask filter |
| `scan_band_Z5D(band, params) -> Peaks` | Z5D intra-band scanning |
| `is_flat(window, tau, L) -> bool` | Flat-surface detector |
| `run_scan(N, params, guards) -> Report` | Full scan with optional early-exit |

### Test Module: `test_band_router.py`

| Test Class | Description |
|------------|-------------|
| `TestBandRouterCoverage` | Test A — validates reduction and coverage |
| `TestEarlyExitEfficiency` | Test B — validates efficiency vs. recall |
| `TestFlatDetection` | Unit tests for flat-surface detection |
| `TestBandPlanning` | Unit tests for band planning |
| `TestWheelFiltering` | Unit tests for wheel filtering |

## JSONL Logging Schema

Each event is logged as one JSON line:

```json
{
  "event": "plan|mask|step|early_exit|peak",
  "seed": 42,
  "C": 0.9,
  "alpha": 1.0,
  "wheel": 210,
  "tau": 1e-6,
  "L": 8,
  "dps": 708,
  "git_head": "abc1234",
  "timestamp_utc": "2025-11-25T12:00:00.000000+00:00",
  ...event-specific fields...
}
```

## Precision

Uses adaptive precision: `max(50, N.bitLength() × 4 + 200)`

For CHALLENGE_127 (127-bit): ≥708 decimal places

## Reproducibility

- All seeds pinned and logged
- Parameters logged in every artifact
- Git HEAD recorded
- UTC timestamps for all events

## Dependencies

- Python 3.12+
- mpmath (arbitrary precision)
- pytest (testing)

Imports from existing experiments:
- `experiments/z5d-informed-gva/wheel_residues.py`
- `experiments/z5d-comprehensive-challenge/z5d_api.py`

## File Manifest

| File | Description |
|------|-------------|
| `band_router.py` | Core implementation |
| `test_band_router.py` | Test suite |
| `README.md` | This file |
| `EXPERIMENT_REPORT.md` | Results and conclusions |
| `router_A_seed42.jsonl` | Test A artifact |
| `scan_on_B_seed43.jsonl` | Test B treatment |
| `scan_off_B_seed43.jsonl` | Test B control |
| `diff.jsonl` | Test B comparison |

## References

- Project `CODING_STYLE.md` — Coding standards
- Project `VALIDATION_GATES.md` — Scale requirements  
- `experiments/z5d-informed-gva/` — Wheel residues
- `experiments/z5d-comprehensive-challenge/` — Z5D pipeline

---

**Status**: Implementation complete, ready for execution  
**Last Updated**: 2025-11-25  
**Experiment**: band-router-early-exit-falsification
