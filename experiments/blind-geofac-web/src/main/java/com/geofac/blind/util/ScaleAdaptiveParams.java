package com.geofac.blind.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.BigInteger;

/**
 * Scale-adaptive parameter tuning based on bit-length analysis.
 */
public final class ScaleAdaptiveParams {

    private static final Logger LOG = LoggerFactory.getLogger(ScaleAdaptiveParams.class);
    private static final double BASELINE_BIT_LENGTH = 30.0;
    private static final double MIN_THRESHOLD = 0.5;
    private static final double MAX_THRESHOLD = 1.0;

    private ScaleAdaptiveParams() {}

    public static long adaptiveSamples(BigInteger N, long baseSamples) {
        int bitLength = N.bitLength();
        double scaleFactor = Math.pow(bitLength / BASELINE_BIT_LENGTH, 1.5);
        long adapted = (long) (baseSamples * scaleFactor);
        LOG.debug("adaptiveSamples: bitLength={}, base={}, factor={}", bitLength, baseSamples, scaleFactor);
        return adapted;
    }

    public static int adaptiveMSpan(BigInteger N, int baseMSpan) {
        int bitLength = N.bitLength();
        double scaleFactor = bitLength / BASELINE_BIT_LENGTH;
        int adapted = (int) (baseMSpan * scaleFactor);
        LOG.debug("adaptiveMSpan: bitLength={}, base={}, factor={}", bitLength, baseMSpan, scaleFactor);
        return adapted;
    }

    public static double adaptiveThreshold(BigInteger N, double baseThreshold, double attenuation) {
        int bitLength = N.bitLength();
        double scaleFactor = Math.log(bitLength / BASELINE_BIT_LENGTH) / Math.log(2);
        double adapted = baseThreshold - (scaleFactor * attenuation);
        adapted = Math.max(MIN_THRESHOLD, Math.min(MAX_THRESHOLD, adapted));
        LOG.debug("adaptiveThreshold: bitLength={}, base={}, attenuation={}, adapted={}",
                bitLength, baseThreshold, attenuation, adapted);
        return adapted;
    }

    public static double[] adaptiveKRange(BigInteger N, double kLo, double kHi) {
        int bitLength = N.bitLength();
        double center = (kLo + kHi) / 2.0;
        double baseWidth = (kHi - kLo) / 2.0;

        double scaleFactor = Math.sqrt(bitLength / BASELINE_BIT_LENGTH);
        double adaptedWidth = baseWidth / scaleFactor;

        double adaptedKLo = center - adaptedWidth;
        double adaptedKHi = center + adaptedWidth;

        LOG.debug("adaptiveKRange: bitLength={}, base=[{}, {}], adapted=[{}, {}]",
                bitLength, kLo, kHi, adaptedKLo, adaptedKHi);
        return new double[]{adaptedKLo, adaptedKHi};
    }

    public static long adaptiveTimeout(BigInteger N, long baseTimeout) {
        int bitLength = N.bitLength();
        double scaleFactor = Math.pow(bitLength / BASELINE_BIT_LENGTH, 2.0);
        long adapted = (long) (baseTimeout * scaleFactor);
        LOG.debug("adaptiveTimeout: bitLength={}, base={}, factor={}, adapted={}",
                bitLength, baseTimeout, scaleFactor, adapted);
        return adapted;
    }

    public static void logAdaptiveParams(BigInteger N, long samples, int mSpan, double threshold,
                                         double kLo, double kHi, long timeout) {
        LOG.info("=== Scale-Adaptive Parameters ===");
        LOG.info("N bit-length: {}", N.bitLength());
        LOG.info("Adapted samples: {}", samples);
        LOG.info("Adapted m-span: {}", mSpan);
        LOG.info("Adapted threshold: {}", threshold);
        LOG.info("Adapted k-range: [{}, {}]", kLo, kHi);
        LOG.info("Adapted timeout: {}ms ({:.1f} minutes)", timeout, timeout / 60000.0);
        LOG.info("================================");
    }
}
