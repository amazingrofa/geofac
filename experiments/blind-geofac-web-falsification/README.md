# Blind Geofac Web Falsification Experiment

This directory contains the findings and artifacts from a falsification attempt against the 127-bit challenge using the blind-geofac-web geometric resonance factorization method.

## Quick Summary

**Result**: Hypothesis likely false - critical coverage gap identified in ring search.

**Key Finding**: The ring search radius is capped at 100M, but candidates are ~10^17 away from √N. This creates effectively zero coverage of the factor space.

See [FINDINGS.md](FINDINGS.md) for complete analysis and metrics.

## Running the Tests

### Quick Probe (2 minutes)
```bash
cd experiments/blind-geofac-web
../../gradlew test -Dgeofac.runFalsificationIT=true --tests "*QuickFalsificationProbeTest*"
```

### Full Falsification (30 minutes)
```bash
cd experiments/blind-geofac-web
../../gradlew test -Dgeofac.runFalsificationIT=true --tests "*FalsificationIT127Bit"
```

### Micro-Tests (Edge Cases)
```bash
cd experiments/blind-geofac-web
../../gradlew test --tests "*MicroEdgeCaseTests*"
```

### Shell Exclusion A/B Test
```bash
cd experiments/blind-geofac-web
../../gradlew test -Dgeofac.runFalsificationIT=true --tests "*ShellExclusionABTest*"
```

## Test Files

Tests are located in the parent project at `experiments/blind-geofac-web/src/test/java/com/geofac/blind/falsification/`:

| File | Description |
|------|-------------|
| `FalsificationIT127Bit.java` | 30-minute full falsification attempt |
| `QuickFalsificationProbeTest.java` | 2-minute quick probe for rapid feedback |
| `ShellExclusionABTest.java` | A/B comparison of shell-exclusion feature |
| `MicroEdgeCaseTests.java` | Unit tests for singularity guards, precision, scaling |

## Related Documentation

- [Parent Project README](../blind-geofac-web/README.md)
- [Validation Gates](../../docs/validation/VALIDATION_GATES.md)
- [Repository Coding Style](../../README.md)
