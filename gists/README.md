# Geofac Gists

This directory contains standalone validation gists for hypotheses and experiments related to the geofac geometric resonance factorization project.

Each gist is a self-contained analysis with its own documentation, validation scripts, and artifacts.

## Available Gists

### [geometric-resonance-hypothesis](geometric-resonance-hypothesis/)

**Status**: FALSIFIED  
**Date**: 2025-11-16

Validates the curvature-guided geometric resonance hypothesis from `.github/conversations.md` against the Gate 1 challenge semiprime.

**Key findings**:
- Curvature hypothesis: |κ(p) - κ(q)| = 0.059 (fails 1e-16 threshold)
- Geometric resolution hypothesis: 19.85% relative difference (fails 1% threshold)

See [geometric-resonance-hypothesis/README.md](geometric-resonance-hypothesis/README.md) for details.

---

## Purpose

Gists serve as lightweight, reproducible experiments that:
1. Validate or falsify specific hypotheses before integration
2. Document empirical findings with exact parameters and artifacts
3. Provide standalone artifacts for review and verification
4. Follow the project's reproducibility and precision requirements

## Structure

Each gist typically includes:
- `README.md` - Summary, methodology, and conclusions
- Validation script(s) - Executable code for reproduction
- `results.json` - Structured numerical results
- Log files - Complete console output from runs

## Adding New Gists

When creating a new gist:
1. Create a descriptive subdirectory under `gists/`
2. Include a comprehensive README with hypothesis, methodology, and conclusions
3. Ensure scripts use appropriate precision (typically N.bitLength() × 4 + 200)
4. Export structured artifacts (JSON, CSV, etc.)
5. Document exact parameters, seeds, and thresholds
6. Update this index with a brief summary
