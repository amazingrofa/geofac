# Geofac Proof Pack

## Overview

This proof pack provides a ready-to-run demonstration of the geometric resonance factorization algorithm, tailored for Intel Xeon and similar x86-64 architectures.

## Purpose

Following PR #37, which fixed critical timeout configuration issues (15s → 10 minutes), this proof pack:

1. Demonstrates factorization using the updated timeout configuration
2. Targets a semiprime in the Gate 2 validation range [1e14, 1e18]
3. Produces complete, verifiable proof artifacts
4. Documents hardware configuration and environment

## Quick Start

### Prerequisites

- JDK 17 or later
- Bash shell (Linux, macOS, WSL on Windows)
- 2GB RAM minimum (4GB recommended)

### Running the Proof Pack

```bash
# Build the application (if not already built)
./gradlew build

# Run the proof pack
./proof_pack.sh
```

The script will:
1. Detect your hardware configuration
2. Build the application if needed
3. Run factorization with the updated 10-minute timeout
4. Collect all proof artifacts
5. Generate a comprehensive proof package

## Test Case

The proof pack attempts to factor:

```
N = 100000980001501
  = 10000019 × 10000079
```

This is a 47-bit balanced semiprime in the Gate 2 range, matching the test case from `SimpleSemiprimeTest.java` (PR #37).

## Configuration

The proof pack uses the following configuration from PR #37:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `precision` | 240 | Minimum decimal digits for BigDecimal math context |
| `samples` | 5000 | Number of k-samples to explore |
| `m-span` | 180 | Half-width for Dirichlet kernel sweep |
| `j` | 6 | Dirichlet kernel order |
| `threshold` | 0.92 | Normalized amplitude gate |
| `k-lo` | 0.25 | Fractional k-sampling lower bound |
| `k-hi` | 0.45 | Fractional k-sampling upper bound |
| `search-timeout-ms` | 600000 | Max time per attempt (10 minutes) |

## Proof Artifacts

The script generates a timestamped directory under `results/` containing:

- **README.txt**: Summary of the execution
- **env.txt**: Hardware and environment details (CPU, memory, OS, Java version, Git commit)
- **factorization_output.txt**: Complete output from the factorization process
- **timing.txt**: Execution timing information
- **verification.txt**: Verification results (success/failure, factors found, validation)

## Expected Behavior

The geometric resonance algorithm is experimental and may not successfully factor all semiprimes within the configured timeout. This is expected behavior as documented in the validation policy.

**Success case**: The algorithm finds factors within the 10-minute timeout. The proof pack will verify the factors and mark the run as successful.

**Timeout case**: The algorithm times out without finding factors. The proof pack will document this and exit with a note that this is expected behavior for some semiprimes.

## Hardware Considerations

The algorithm's performance varies significantly by hardware:

- **M1/M2 Apple Silicon**: Original successful runs reported on this architecture
- **Intel Xeon**: This proof pack is optimized for Intel Xeon Platinum 8370C and similar processors
- **Other x86-64**: Should work on most modern x86-64 processors

The script automatically detects and documents your hardware configuration in the proof artifacts.

## Validation Gates

This project follows a strict four-gate validation policy defined in `docs/VALIDATION_GATES.md`:

- **Gate 1**: 30-bit quick sanity check (N=1,073,217,479 = 32,749 × 32,771)
- **Gate 2**: 60-bit scaling validation (N=1,152,921,470,247,108,503 = 1,073,741,789 × 1,073,741,827)
- **Gate 3**: 127-bit challenge number (137524771864208156028430259349934309717)
- **Gate 4**: Operational range [1e14, 1e18] for general semiprimes

This proof pack targets Gate 4 as a demonstration of the algorithm's capabilities.

## Troubleshooting

### Build Errors

If you encounter build errors:
```bash
./gradlew clean build
```

### Out of Memory

If you see `OutOfMemoryError`, increase the JVM heap size:
```bash
# Edit proof_pack.sh and add to the java command:
java -Xmx4g ...
```

### Timeout

The 10-minute timeout is intentional. If you want to test with a shorter timeout for faster feedback, edit `proof_pack.sh` and change:
```bash
-Dgeofac.search-timeout-ms=60000  # 1 minute
```

Note: Shorter timeouts reduce the likelihood of success.

## References

- **Repository**: https://github.com/zfifteen/geofac
- **Validation Policy**: [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md)
- **PR #37**: Timeout configuration fix
- **Coding Style**: [CODING_STYLE.md](CODING_STYLE.md)
- **Agent Instructions**: [AGENTS.md](AGENTS.md)

## License

See repository LICENSE file.
