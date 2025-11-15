# Proof Pack Demonstration

This document shows the proof pack in action on Intel Xeon Platinum 8370C hardware.

## Environment

- **CPU**: Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz
- **Cores**: 4
- **Memory**: 15 GB
- **OS**: Ubuntu 24.04.3 LTS
- **Java**: 17.0.17

## Test Case

Factorizing: `N = 100000980001501` (47 bits, Gate 2 range)

Expected factors: `10000019 × 10000079`

## Configuration (from PR #37)

| Parameter | Value |
|-----------|-------|
| precision | 240 |
| samples | 5000 |
| m-span | 180 |
| j | 6 |
| threshold | 0.92 |
| k-lo | 0.25 |
| k-hi | 0.45 |
| search-timeout-ms | 600000 (10 minutes) |

## Running the Proof Pack

```bash
$ ./proof_pack.sh
```

The script will:
1. Detect hardware configuration
2. Verify build artifacts exist
3. Create timestamped results directory
4. Save environment information
5. Run factorization with 10-minute timeout
6. Verify results
7. Create complete proof package

## Artifacts Generated

The proof pack creates a directory `results/proof_pack_<timestamp>/` containing:

- **README.txt**: Summary of execution
- **env.txt**: Hardware and environment details
- **factorization_output.txt**: Complete output from factorization
- **timing.txt**: Execution timing information
- **verification.txt**: Verification results

## Expected Behavior

The geometric resonance algorithm is experimental. On this hardware configuration:

- **Timeout case** (most common): The algorithm searches for 10 minutes and times out. This is expected and documented behavior for many semiprimes.
- **Success case** (less common): The algorithm finds factors within the timeout.

Both cases produce complete proof artifacts that can be independently verified.

## Verification

To independently verify results when factors are found:

```python
# Verify multiplication
p = 10000019
q = 10000079
N = 100000980001501
assert p * q == N

# Verify primality
from sympy import isprime
assert isprime(p) and isprime(q)

# Verify range
assert 1e14 <= N <= 1e18  # Gate 2 range
```

## References

- PR #37: https://github.com/zfifteen/geofac/pull/37
- Validation Policy: [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md)
- Full documentation: [PROOF_PACK_README.md](PROOF_PACK_README.md)
