# Triangle-Closure Filter

## Executive Summary

The **Triangle-Closure Filter** is a cheap geometric sanity check that rejects obviously invalid factor candidates **before** spending expensive Dirichlet/QMC/precision cycles on them.

For any semiprime N = p · q, the constraint log(p) + log(q) = log(N) defines a line in log-space. Candidates far from this line cannot be valid factors.

## Why It's Safe

**True factors are never rejected.** The filter's balance band constraint is derived from the geometric property that for N = p · q with p ≤ q:

- p ≥ √N / R  (where R = balanceBand)
- p ≤ √N × R

For RSA-style semiprimes where p and q are balanced (within a factor of 2–4 of each other), a `balanceBand` of 4.0 ensures true factors always pass.

## Configuration

Add to `application.yml`:

```yaml
geofac:
  triangle-filter-enabled: false          # disabled by default
  triangle-filter-balance-band: 4.0       # p in [sqrtN/balanceBand, sqrtN*balanceBand]
  triangle-filter-max-log-skew: 2.0       # optional, in log units

## Performance Implications

- **Cost**: ~4–6 comparisons per candidate, plus 2 BigDecimal log computations if `maxLogSkew > 0`
- **Savings**: Avoids expensive `testNeighbors()` calls for degenerate candidates
- **Typical rejection rate**: 10-30% of random candidates (varies by N structure)

## Telemetry

When enabled, the filter logs:
- `triangleFilterChecked`: Total candidates evaluated
- `triangleFilterRejected`: Candidates rejected by filter
- Rejection rate at INFO level when factorization completes

## Theory

In the "right-triangle" view of (log p, log q)-space:
1. Valid factors lie on the line log(p) + log(q) = log(N)
2. The hypotenuse length is √2 × log(N)
3. Balanced semiprimes have p ≈ q ≈ √N (the isosceles case)
4. The balance band defines acceptable deviation from √N

Candidates producing q* = N/p outside reasonable bounds are geometrically impossible factors.
