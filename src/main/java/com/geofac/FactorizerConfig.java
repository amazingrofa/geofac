package com.geofac;

import java.util.Map;

/**
 * Configuration holder for factorization parameters.
 * Used for serialization in artifacts.
 */
public record FactorizerConfig(
    int precision,
    long samples,
    int mSpan,
    int J,
    double threshold,
    double kLo,
    double kHi,
    long searchTimeoutMs
) {
    public Map<String, Object> toMap() {
        return Map.of(
            "precision", precision,
            "samples", samples,
            "mSpan", mSpan,
            "J", J,
            "threshold", threshold,
            "kLo", kLo,
            "kHi", kHi,
            "searchTimeoutMs", searchTimeoutMs
        );
    }
}