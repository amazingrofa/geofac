// filepath: /Users/velocityworks/IdeaProjects/geofac/src/main/java/com/geofac/util/PrecisionUtil.java
package com.geofac.util;

import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.Instant;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Precision utility following repository rule:
 * precision = max(configured, N.bitLength() * 2 + 150)
 *
 * Produces a shared MathContext and logs the chosen precision for reproducibility.
 */
public final class PrecisionUtil {

    private static final Logger LOG = LoggerFactory.getLogger(PrecisionUtil.class);

    private PrecisionUtil() {}

    public static MathContext mathContextFor(BigInteger N, int configuredPrecision) {
        int bitlen = N.bitLength();
        int required = bitlen * 2 + 150;
        int precision = Math.max(configuredPrecision, required);
        MathContext mc = new MathContext(precision, RoundingMode.HALF_EVEN);
        LOG.info("PrecisionUtil: chosen precision={} (configured={}, bitlen={}, required={}) at {}",
                precision, configuredPrecision, bitlen, required, Instant.now());
        return mc;
    }

    /**
     * Provide a safe scale for epsilon/tolerance choices derived from MathContext.
     * Caps the scale to 50 digits to avoid absurdly tiny epsilons.
     */
    public static int epsilonScale(MathContext mc) {
        return Math.min(mc.getPrecision(), 50);
    }
}

