package com.geofac.validation;

import com.geofac.FactorizerConfig;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.Map;

/**
 * Holds the result of a single benchmark run for validation purposes.
 * Records input, expected factors, configuration, outcome, and timing.
 */
public record BenchmarkResult(
    BigInteger N,
    BigInteger expectedP,
    BigInteger expectedQ,
    BigInteger actualP,
    BigInteger actualQ,
    boolean success,
    long durationMs,
    FactorizerConfig config,
    String errorMessage
) {
    /**
     * Convert benchmark result to a map for JSON/CSV serialization.
     */
    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("N", N.toString());
        map.put("N_bits", N.bitLength());
        map.put("expectedP", expectedP != null ? expectedP.toString() : null);
        map.put("expectedQ", expectedQ != null ? expectedQ.toString() : null);
        map.put("actualP", actualP != null ? actualP.toString() : null);
        map.put("actualQ", actualQ != null ? actualQ.toString() : null);
        map.put("success", success);
        map.put("factorsMatch", success
            && actualP != null && actualQ != null
            && expectedP != null && expectedQ != null
            && actualP.multiply(actualQ).equals(N));
        map.put("durationMs", durationMs);
        map.put("errorMessage", errorMessage);
        
        // Flatten config for easier CSV export
        if (config != null) {
            map.put("precision", config.precision());
            map.put("samples", config.samples());
            map.put("mSpan", config.mSpan());
            map.put("J", config.J());
            map.put("threshold", config.threshold());
            map.put("kLo", config.kLo());
            map.put("kHi", config.kHi());
            map.put("searchTimeoutMs", config.searchTimeoutMs());
        }
        
        return map;
    }
}
