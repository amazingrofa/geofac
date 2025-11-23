# INDEX: GVA Root-Cause Analysis

## Metadata

- **Experiment ID**: `gva-root-cause-analysis`
- **Created**: 2025-11-23
- **Status**: IN_PROGRESS
- **Phase**: 1 (Signal Decay and Parameter Sensitivity)
- **Verdict**: PENDING

## Compliance Checklist

### CODING_STYLE.md Compliance

- [x] **Validation Gates**: All test cases in [10^14, 10^18] or 20-50 bit balanced semiprimes
- [x] **No Classical Fallbacks**: Pure GVA geodesic distance only
- [x] **Adaptive Precision**: max(50, N.bitLength() × 4 + 200) dps, logged per test
- [x] **Reproducibility**: Deterministic seeds, logged parameters, timestamps
- [x] **Minimal Code**: Surgical implementations, no speculative branches
- [x] **Natural Names**: Clear function/variable names
- [x] **Linear Flow**: Guard clauses, early returns, flat control flow

### Experiment Design

- [x] **Clear Hypothesis**: SNR decay and parameter sensitivity
- [x] **Measurable Success Criteria**: SNR curves, success rates, runtime
- [x] **Documented Methodology**: Phase 1.1 and 1.2 protocols
- [x] **Reproducible**: Seeds, parameters, exact test cases
- [x] **Diagnostic Focus**: Understanding failures, not finding successes

## Related Experiments

- **Predecessor**: `experiments/8d-imbalance-tuned-gva/` - Hypothesis falsified
- **Motivation**: Why does GVA fail in operational range even for balanced cases?
- **Question**: Is it signal decay, parameter sensitivity, or fundamental limitation?

## Files

### Code
- `geodesic_signal_decay.py` - Phase 1.1: SNR measurement across bit-length gradient
- `parameter_sensitivity_sweep.py` - Phase 1.2: Grid search k and candidate budgets
- `generate_visualizations.py` - Plot generation from experimental data

### Data (Generated)
- `signal_decay_data.json` - Phase 1.1 measurements
- `parameter_sweep_results.json` - Phase 1.2 grid search results
- `snr_vs_bitlength.png` - Signal decay visualization
- `parameter_sensitivity_heatmap.png` - Parameter sweep visualization

### Documentation
- `README.md` - Quick start and reproduction instructions
- `EXECUTIVE_SUMMARY.md` - Findings and conclusions (after experiments run)
- `INDEX.md` - This file

## Expected Outcomes

### If SNR Decays Exponentially
- Explains why GVA succeeds on Gate 1 (30-bit) but fails at 47+ bits
- Suggests GVA cannot scale to operational range without fundamental changes
- Geodesic signal becomes too weak to distinguish factors from noise

### If Parameters Show No Success Region
- Confirms that parameter tuning cannot solve the problem
- Rules out "wrong k" or "insufficient candidates" as root cause
- Points to fundamental limitation in torus embedding approach

### Combined Result
- Provides clear evidence for WHY GVA fails
- Informs decision: abandon GVA or explore fundamentally different geometric frameworks
- Prevents wasted effort on parameter optimization or dimension expansion

## Notes

This is a DIAGNOSTIC experiment. Success means clear understanding of failure modes, not successful factorization.
