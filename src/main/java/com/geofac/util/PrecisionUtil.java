// filepath: /Users/velocityworks/IdeaProjects/geofac/src/main/java/com/geofac/util/PrecisionUtil.java
package com.geofac.util;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.Instant;

import ch.obermuhlner.math.big.BigDecimalMath;
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

    /**
     * Reduce angle to principal value in [-π, π].
     * This is essential for phase-corrected snap and other trigonometric operations to work correctly.
     *
     * @param x angle to reduce
     * @param mc MathContext for precision
     * @return principal angle in [-π, π]
     */
    public static BigDecimal principalAngle(BigDecimal x, MathContext mc) {
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        BigDecimal invTwoPi = BigDecimal.ONE.divide(twoPi, mc);

        // r = x - floor(x / 2π) * 2π, which gives r ∈ [0, 2π)
        BigDecimal k = floor(x.multiply(invTwoPi, mc));
        BigDecimal r = x.subtract(twoPi.multiply(k, mc), mc);

        // Shift to [-π, π]. After reduction, r ∈ [0, 2π), so only need to adjust r > π.
        if (r.compareTo(pi) > 0) r = r.subtract(twoPi, mc);

        return r;
    }

    /**
     * Floor function for BigDecimal.
     * Always rounds toward negative infinity to maintain periodicity math.
     *
     * @param x value to floor
     * @return floored value
     */
    public static BigDecimal floor(BigDecimal x) {
        return x.setScale(0, RoundingMode.FLOOR);
    }
}

