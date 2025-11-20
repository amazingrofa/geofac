# Project Validation Gates

This document defines the official validation gates for the `geofac` project. The project follows a sequential, four-gate validation process designed to build confidence through progressively challenging tests. All experiments, claims, and code must adhere to this policy.

## Progressive Validation Framework

The geometric resonance algorithm is validated through four increasingly difficult gates, each serving a specific purpose:

1. **Gate 1 (30-bit)**: Quick sanity check - proves basic algorithm correctness
2. **Gate 2 (60-bit)**: Scaling validation - demonstrates algorithm handles larger bit sizes  
3. **Gate 3 (127-bit)**: Challenge verification - the canonical RSA-style challenge
4. **Gate 4 (Operational)**: Production range - validates practical applicability

## Gate 1: 30-Bit Validation Test

The first gate establishes basic algorithm correctness with a manageable semiprime that can be factored in seconds.

- **Target Number (N):** `1073676287` (30-bit semiprime)
- **Factors (p, q):**
  - `p = 32749`
  - `q = 32771`
- **Bit size:** ~30 bits
- **Expected runtime:** < 5 seconds

### Success Criteria

Gate 1 verifies the core algorithm mechanics work correctly:

1. The factorization completes successfully using standard parameters
2. The result is deterministic and reproducible across runs
3. No fallback to Pollard Rho is required

## Gate 2: 60-Bit Validation Test  

The second gate demonstrates the algorithm scales appropriately to mid-sized semiprimes.

- **Target Number (N):** `1152921504606846883` (60-bit semiprime)
- **Factors (p, q):**
  - `p = 1073741789`
  - `q = 1073741827`
- **Bit size:** ~60 bits
- **Expected runtime:** < 30 seconds

### Success Criteria

Gate 2 validates scaling properties:

1. The geometric resonance maintains effectiveness at 60 bits
2. Parameter tuning (samples, precision) scales appropriately
3. Memory usage remains reasonable

## Gate 3: 127-Bit Challenge Verification

The third gate is the canonical validation target: deterministic factorization of a 127-bit semiprime.

- **Target Number (N):** `137524771864208156028430259349934309717`
- **Factors (p, q):**
  - `p = 10508623501177419659`
  - `q = 13086849276577416863`
- **Bit size:** 127 bits
- **Expected runtime:** 3-5 minutes

### Success Criteria

Gate 3 represents the primary project goal:

1. The factorization is successful using the canonical algorithm
2. The result is independently verified by at least three (3) designated reviewers
3. The "fast path" or any other short-circuit mechanism is disabled

## Gate 4: Operational Range

Once Gates 1-3 are passed, the project's operational scope expands to a defined range.

- **Operational Range:** `[10^14, 10^18]` (i.e., numbers between 10^14 and 10^18)
- **Exclusions:** The specific challenge numbers from Gates 1-3
- **Expected success rate:** > 80% within timeout

### Success Criteria

Gate 4 validates general applicability:

1. Consistent performance across the range
2. Predictable scaling of runtime with input size
3. Graceful fallback behavior when geometric search fails

## Testing Protocol

All gates must be passed sequentially. Researchers should:

1. Begin with Gate 1 to verify setup correctness
2. Progress to Gate 2 only after Gate 1 passes consistently  
3. Attempt Gate 3 only after Gates 1-2 demonstrate stability
4. Explore Gate 4 range after all previous gates pass

This progressive approach ensures robust validation while catching issues early in the testing cycle.
