package com.geofac.blind.util;

/**
 * Configuration for the Triangle-Closure Filter.
 * <p>
 * The filter rejects candidates that would create degenerate triangles
 * in log-space, based on the constraint log(p) + log(q) = log(N).
 *
 * @param enabled      Whether the filter is active
 * @param balanceBand  Ratio R such that p must be in [sqrtN/R, sqrtN*R]
 * @param maxLogSkew   Maximum allowed |log(p) - log(q*)| where q* = N/p
 */
public record TriangleFilterConfig(
        boolean enabled,
        double balanceBand,
        double maxLogSkew
) {
    /**
     * Default configuration with filter disabled.
     */
    public static TriangleFilterConfig disabled() {
        return new TriangleFilterConfig(false, 4.0, 0.0);
    }
}
