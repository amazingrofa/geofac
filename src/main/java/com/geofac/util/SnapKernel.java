package com.geofac.util;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Phase-corrected nearest-integer snap, aligned with a Gaussian kernel.
 */
public final class SnapKernel {

    private SnapKernel() {} // Utility class

    /**
     * Computes a candidate factor using a phase correction model adapted for a Gaussian kernel.
     * The correction is proportional to theta and the kernel width (sigma).
     *
     * @param lnN   ln(N) at the given precision
     * @param theta Angular parameter θ from the kernel peak
     * @param sigma The standard deviation (width) of the Gaussian kernel
     * @param mc    MathContext for precision
     * @return A candidate factor p
     */
    public static BigInteger phaseCorrectedSnap(BigDecimal lnN, BigDecimal theta, BigDecimal sigma, MathContext mc) {
        // The phase offset (dPhi) is modeled as being proportional to the detected phase (theta)
        // and the kernel width (sigma). A wider kernel implies a larger potential phase shift.
        BigDecimal dPhi = principalAngle(theta, mc).multiply(sigma, mc);

        // Apply the correction to the exponent: p̂ ≈ exp((ln(N) + dPhi) / 2)
        BigDecimal exponent = lnN.add(dPhi, mc).divide(BigDecimal.valueOf(2), mc);
        BigDecimal pHat = BigDecimalMath.exp(exponent, mc);

        // With a clean Gaussian kernel and a first-order phase correction,
        // a direct snap to the nearest integer is the most robust approach.
        return pHat.setScale(0, RoundingMode.HALF_UP).toBigIntegerExact();
    }

    // Principal angle mapping to [-π, π]
    private static BigDecimal principalAngle(BigDecimal x, MathContext mc) {
        BigDecimal twoPi = BigDecimalMath.pi(mc).multiply(BigDecimal.valueOf(2), mc);
        BigDecimal invTwoPi = BigDecimal.ONE.divide(twoPi, mc);
        BigDecimal k = x.multiply(invTwoPi, mc).setScale(0, RoundingMode.FLOOR);
        BigDecimal r = x.subtract(twoPi.multiply(k, mc), mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        if (r.compareTo(pi) > 0) {
            r = r.subtract(twoPi, mc);
        }
        return r;
    }
}
