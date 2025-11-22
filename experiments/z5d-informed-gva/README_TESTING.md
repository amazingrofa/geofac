# Z5D-Informed GVA Testing Results

**Status**: ✅ COMPLETE  
**Date**: 2025-11-22  
**PR**: Building on #104

## Quick Navigation

### 📊 Main Results
- **[comparison_results.json](comparison_results.json)** - Raw metrics for all 4 experiments (required output)
- **[PERFORMANCE_SUMMARY.txt](PERFORMANCE_SUMMARY.txt)** - Visual performance comparison

### 📖 Analysis Documents
- **[EXPERIMENT_RESULTS.md](EXPERIMENT_RESULTS.md)** - Detailed analysis, hypothesis evaluation, recommendations
- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Executive summary, reproducibility guide
- **[EXECUTION_VERIFICATION.md](EXECUTION_VERIFICATION.md)** - Requirements compliance checklist

### 🧪 Testing Infrastructure
- **[test_z5d_experiment.py](test_z5d_experiment.py)** - Comprehensive test suite (22 tests, 100% passing)
- **[quick_60bit_validation.py](quick_60bit_validation.py)** - Quick validation on 60-bit semiprimes

## TL;DR - What Was Done

### Executed Per Problem Statement:
1. ✅ Quick sanity tests (< 1 minute)
   - `wheel_residues.py` → 77% pruning verified
   - `z5d_density_simulator.py` → 2001 bins generated

2. ✅ Full 4-way comparison on 127-bit challenge
   - Baseline FR-GVA
   - Wheel filter only
   - Z5D prior only
   - Full Z5D (all enhancements)

3. ✅ Generated `comparison_results.json` with:
   - Success flags for all variants
   - Runtime measurements
   - Configuration details
   - Winner identification

## Key Results

### Performance Summary (127-bit Challenge, 20K candidates)

| Variant | Runtime | Speedup | Winner |
|---------|---------|---------|--------|
| Baseline FR-GVA | 34.90s | 1.00× | |
| Wheel Filter Only | 15.98s | 2.18× | |
| Z5D Prior Only | 34.64s | 1.01× | |
| **Full Z5D** | **8.69s** | **4.02×** | 🏆 |

### Visual Comparison

```
Runtime (lower = better):
Baseline    ████████████████████████████████████  34.90s
Wheel Only  ████████████████                      15.98s
Z5D Only    ████████████████████████████████████  34.64s
Full Z5D    █████████                              8.69s ⭐
```

### Key Findings

1. **Wheel filtering is highly effective**: 77% deterministic pruning → 2.18× speedup
2. **Full Z5D achieves best performance**: 4.02× speedup over baseline
3. **Z5D density prior weak standalone**: <1% impact alone
4. **Synergistic effects observed**: Full Z5D beats wheel-only by 45%

### Hypothesis Verdict: ⚠️ PARTIALLY SUPPORTED

**Supported**:
- ✓ Measurable performance improvements (4× speedup)
- ✓ Synergistic effect (Full Z5D > Wheel Only)
- ✓ Wheel filtering + stepping effective

**Not Supported**:
- ✗ Z5D density prior minimal standalone benefit
- ✗ Primary benefit from wheel + stepping, not density

**Inconclusive**:
- ? No factors found within 20K budget (insufficient for definitive success/failure)

## How to Reproduce

```bash
cd experiments/z5d-informed-gva

# Quick sanity tests (< 1 minute)
python3 wheel_residues.py
python3 z5d_density_simulator.py

# Test suite (< 1 minute)
pytest test_z5d_experiment.py -v

# 60-bit validation (~15 seconds)
python3 quick_60bit_validation.py

# Full experiment (~90 seconds)
export NON_INTERACTIVE=1
python3 comparison_experiment.py

# View results
cat comparison_results.json
cat PERFORMANCE_SUMMARY.txt
```

## Dependencies

- Python 3.12.3
- mpmath 1.3.0
- pytest 9.0.1

Install with:
```bash
pip install mpmath pytest
```

## Quality Assurance

- ✅ Code Review: Passed (0 comments)
- ✅ CodeQL Security: 0 vulnerabilities
- ✅ Test Coverage: 22/22 tests passing (100%)
- ✅ All problem statement requirements met

## File Inventory

### Required Deliverables
- `comparison_results.json` (1.2K) - Main results file with all metrics

### Additional Documentation
- `EXPERIMENT_RESULTS.md` (7.1K) - Detailed analysis
- `FINAL_SUMMARY.md` (7.0K) - Executive summary
- `EXECUTION_VERIFICATION.md` (5.0K) - Compliance checklist
- `PERFORMANCE_SUMMARY.txt` (5.6K) - Visual summary
- `README_TESTING.md` (this file) - Navigation guide

### Testing Infrastructure
- `test_z5d_experiment.py` (11K) - Test suite
- `quick_60bit_validation.py` (4.7K) - Quick validation

### Original Framework (from PR #104)
- `comparison_experiment.py` - Main experiment runner
- `baseline_fr_gva.py` - Baseline implementation
- `z5d_enhanced_fr_gva.py` - Enhanced implementation
- `wheel_residues.py` - Wheel filtering utilities
- `z5d_density_simulator.py` - Density simulation
- (Plus documentation from PR #104)

## Recommendations

### Immediate
1. Increase candidate budget to 100K-1M for definitive results
2. Reduce Z5D density weight (β = 0.1 → 0.01) based on weak standalone impact
3. Focus optimization on wheel + stepping combination

### Future Work
1. Test at smaller scales (80-100 bit) to establish success baselines
2. Replace PNT simulation with real Z5D enumeration
3. Parameter sweep for optimal configuration
4. Correlation analysis if factors found

## Contact

For questions about this experiment, see:
- [Original PR #104](https://github.com/zfifteen/geofac/pull/104)
- Repository documentation in `docs/`
- Experiment methodology in `EXPERIMENT_SUMMARY.md`

---

**Status**: ✅ EXPERIMENT COMPLETE  
**Winner**: Full Z5D (8.69s, 4.02× speedup)  
**Verdict**: Hypothesis partially supported
