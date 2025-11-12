package com.geofac;

import java.math.BigInteger;
import java.util.Map;

/**
 * Result of a factorization attempt, including config and metadata for reproducibility.
 */
public record FactorizationResult(
    BigInteger N,
    BigInteger p,
    BigInteger q,
    boolean success,
    long durationMs,
    FactorizerConfig config,
    String errorMessage
) {
    public Map<String, Object> toMap() {
        return Map.of(
            "N", N.toString(),
            "p", p != null ? p.toString() : null,
            "q", q != null ? q.toString() : null,
            "success", success,
            "durationMs", durationMs,
            "config", config.toMap(),
            "errorMessage", errorMessage,
            "pqMatchesN", success "pqMatchesN", success && p.multiply(q).equals(N)"pqMatchesN", success && p.multiply(q).equals(N) p != null "pqMatchesN", success && p.multiply(q).equals(N)"pqMatchesN", success && p.multiply(q).equals(N) q != null "pqMatchesN", success && p.multiply(q).equals(N)"pqMatchesN", success && p.multiply(q).equals(N) p.multiply(q).equals(N)
        );
    }
}