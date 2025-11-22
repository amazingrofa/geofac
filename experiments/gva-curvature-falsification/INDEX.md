# GVA Curvature Falsification — Index

**Status:** Complete — Hypothesis decisively falsified

**Quick Links:**
- [Executive Summary](EXECUTIVE_SUMMARY.md) — Start here for TL;DR
- [Detailed Results](DETAILED_RESULTS.md) — Full metrics and analysis
- [Experiment Design](README.md) — Setup and methodology
- [Implementation](run_experiment.py) — Python code

## TL;DR

**Hypothesis:** Curvature metrics (second-order differences) of GVA amplitude/phase reveal geometric structure that raw amplitude misses at distant-factor scales (|δ| ≳ 0.1·√N).

**Verdict:** **FALSIFIED**

- Curvature surface is as flat as raw amplitude (variations ~10^{-26})
- No correlation between curvature and factor locations
- Signal-to-noise ratio insufficient for factor discrimination
- Proves GVA kernel family has no usable gradient for distant factors

**Implication:** GVA is fundamentally non-informative beyond local band near √N. Method should detect this condition and exit early rather than burning budget.

## Context

This experiment follows PR #103 (shell-geometry-scan-01), which demonstrated:
- ✅ φ-shells correctly identified S₅ as factor-containing shell
- ❌ Raw amplitude flat everywhere (0.997-0.999)
- ❌ No usable gradient for search guidance

This experiment tests whether higher-order derivatives (curvature) provide signal where amplitude fails.

## Scientific Value

Provides definitive negative result: if both amplitude and curvature are flat, the kernel embedding itself doesn't encode distant-factor structure. This defines a hard boundary for GVA's applicability and justifies treating distant-factor cases as out-of-scope.
