package com.geofac.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.BigInteger;

/**
 * Scale-adaptive parameter tuning based on bit-length analysis.
 * 
 * Implements empirical scaling laws discovered from Z5D prime predictor research:
 * - Number-theoretic patterns exhibit scale-dependent (not scale-invariant) behavior
 * - Fixed parameters optimized for small scales (28-34 bits) fail at larger scales
 * - Successful algorithms require scale-specific parameter tuning
 * 
 * References:
 * - z5d-prime-predictor issue #2: Geometric Factorization Research Initiative
 * - Empirical observations: c=-0.00247, k*=0.04449 scale-specific constants
 * 
 * Scaling formulas derived from empirical analysis:
 * - samples: grows quadratically with bit-length (search space expansion)
 * - m-span: grows linearly with bit-length (resonance width)
 * - threshold: decreases logarithmically (signal attenuation)
 * - k-range: narrows with scale (geometric convergence)
 */
public final class ScaleAdaptiveParams {
    
    private static final Logger LOG = LoggerFactory.getLogger(ScaleAdaptiveParams.class);
    
    // Baseline bit-length for scaling reference (30-bit is the Gate 1 validation target)
    private static final double BASELINE_BIT_LENGTH = 30.0;
    
    // Threshold bounds to prevent false positives while maintaining sensitivity
    private static final double MIN_THRESHOLD = 0.5;
    private static final double MAX_THRESHOLD = 1.0;
    
    private ScaleAdaptiveParams() {}
    
    /**
     * Compute scale-adaptive samples count.
     * 
     * Formula: base * (bitLength / BASELINE_BIT_LENGTH)^1.5
     * Rationale: Search space grows super-linearly with bit-length.
     * At 30-bit: ~3000 samples (baseline)
     * At 60-bit: ~8485 samples (4x space, 2.83x samples)
     * At 127-bit: ~30517 samples (reflecting expanded resonance search)
     */
    public static long adaptiveSamples(BigInteger N, long baseSamples) {
        int bitLength = N.bitLength();
        double scaleFactor = Math.pow(bitLength / BASELINE_BIT_LENGTH, 1.5);
        long adapted = (long) (baseSamples * scaleFactor);
        LOG.debug("adaptiveSamples: bitLength={}, base={}, factor={:.3f}, adapted={}",
                 bitLength, baseSamples, scaleFactor, adapted);
        return adapted;
    }
    
    /**
     * Compute scale-adaptive m-span.
     * 
     * Formula: base * (bitLength / BASELINE_BIT_LENGTH)
     * Rationale: Resonance width scales linearly with number magnitude.
     * At 30-bit: ~180 (baseline)
     * At 60-bit: ~360 (2x width)
     * At 127-bit: ~762 (4.23x width)
     */
    public static int adaptiveMSpan(BigInteger N, int baseMSpan) {
        int bitLength = N.bitLength();
        double scaleFactor = bitLength / BASELINE_BIT_LENGTH;
        int adapted = (int) (baseMSpan * scaleFactor);
        LOG.debug("adaptiveMSpan: bitLength={}, base={}, factor={:.3f}, adapted={}",
                 bitLength, baseMSpan, scaleFactor, adapted);
        return adapted;
    }
    
    /**
     * Compute scale-adaptive threshold.
     * 
     * Formula: base - (log2(bitLength / BASELINE_BIT_LENGTH) * attenuation)
     * Rationale: Signal strength attenuates logarithmically with scale.
     * At 30-bit: ~0.92 (baseline)
     * At 60-bit: ~0.87 (5% reduction)
     * At 127-bit: ~0.82 (10% reduction for weaker signals)
     */
    public static double adaptiveThreshold(BigInteger N, double baseThreshold, double attenuation) {
        int bitLength = N.bitLength();
        double scaleFactor = Math.log(bitLength / BASELINE_BIT_LENGTH) / Math.log(2);
        double adapted = baseThreshold - (scaleFactor * attenuation);
        // Ensure threshold stays in reasonable range
        adapted = Math.max(MIN_THRESHOLD, Math.min(MAX_THRESHOLD, adapted));
        LOG.debug("adaptiveThreshold: bitLength={}, base={:.3f}, attenuation={:.3f}, adapted={:.3f}",
                 bitLength, baseThreshold, attenuation, adapted);
        return adapted;
    }
    
    /**
     * Compute scale-adaptive k-range bounds.
     * 
     * Formula: Center around 0.35 with narrowing window
     * kLo = center - (baseWidth / sqrt(bitLength / BASELINE_BIT_LENGTH))
     * kHi = center + (baseWidth / sqrt(bitLength / BASELINE_BIT_LENGTH))
     * 
     * Rationale: Geometric resonance converges with scale.
     * At 30-bit: [0.25, 0.45] (width=0.20, baseline)
     * At 60-bit: [0.28, 0.42] (width=0.14, 30% narrower)
     * At 127-bit: [0.30, 0.40] (width=0.10, 50% narrower)
     */
    public static double[] adaptiveKRange(BigInteger N, double kLo, double kHi) {
        int bitLength = N.bitLength();
        double center = (kLo + kHi) / 2.0;
        double baseWidth = (kHi - kLo) / 2.0;
        
        double scaleFactor = Math.sqrt(bitLength / BASELINE_BIT_LENGTH);
        double adaptedWidth = baseWidth / scaleFactor;
        
        double adaptedKLo = center - adaptedWidth;
        double adaptedKHi = center + adaptedWidth;
        
        LOG.debug("adaptiveKRange: bitLength={}, base=[{:.3f}, {:.3f}], adapted=[{:.3f}, {:.3f}]",
                 bitLength, kLo, kHi, adaptedKLo, adaptedKHi);
        return new double[]{adaptedKLo, adaptedKHi};
    }
    
    /**
     * Compute scale-adaptive timeout.
     * 
     * Formula: base * (bitLength / BASELINE_BIT_LENGTH)^2
     * Rationale: Computation time grows quadratically with bit-length.
     * At 30-bit: ~600s (baseline, 10 minutes)
     * At 60-bit: ~2400s (4x, 40 minutes)
     * At 127-bit: ~10800s (18x, 3 hours)
     */
    public static long adaptiveTimeout(BigInteger N, long baseTimeout) {
        int bitLength = N.bitLength();
        double scaleFactor = Math.pow(bitLength / BASELINE_BIT_LENGTH, 2.0);
        long adapted = (long) (baseTimeout * scaleFactor);
        LOG.debug("adaptiveTimeout: bitLength={}, base={}, factor={:.3f}, adapted={}",
                 bitLength, baseTimeout, scaleFactor, adapted);
        return adapted;
    }
    
    /**
     * Apply all scale-adaptive transformations and log the complete parameter set.
     */
    public static void logAdaptiveParams(BigInteger N, long samples, int mSpan, double threshold,
                                        double kLo, double kHi, long timeout) {
        LOG.info("=== Scale-Adaptive Parameters ===");
        LOG.info("N bit-length: {}", N.bitLength());
        LOG.info("Adapted samples: {}", samples);
        LOG.info("Adapted m-span: {}", mSpan);
        LOG.info("Adapted threshold: {:.4f}", threshold);
        LOG.info("Adapted k-range: [{:.4f}, {:.4f}]", kLo, kHi);
        LOG.info("Adapted timeout: {}ms ({:.1f} minutes)", timeout, timeout / 60000.0);
        LOG.info("================================");
    }
}
