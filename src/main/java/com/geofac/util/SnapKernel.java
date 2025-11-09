package com.geofac.util;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Phase-corrected nearest-integer snap for geometric resonance.
 * Computes p̂ from ln(N) and θ, then applies phase correction before rounding.
 */
public final class SnapKernel {

    private SnapKernel() {} // Utility class

    /**
     * Compute candidate factor using phase-corrected nearest-integer snap.
     *
     * @param lnN ln(N) at given precision
     * @param theta Angular parameter θ
     * @param mc MathContext for precision
     * @return Candidate factor p
     */
    public static BigInteger phaseCorrectedSnap(BigDecimal lnN, BigDecimal theta, MathContext mc) {
        // p̂ = exp((ln(N) - 2π·θ)/2)
        BigDecimal twoPi = BigDecimalMath.pi(mc).multiply(BigDecimal.valueOf(2), mc);
        BigDecimal term = twoPi.multiply(theta, mc);
        BigDecimal expo = lnN.subtract(term, mc).divide(BigDecimal.valueOf(2), mc);
        BigDecimal pHat = BigDecimalMath.exp(expo, mc);

        // Phase correction: adjust based on residual
        BigDecimal correctedPHat = applyPhaseCorrection(pHat, mc);

        // Nearest integer
        return roundToBigInteger(correctedPHat, mc.getRoundingMode());
    }

    /**
     * Apply phase correction to p̂ before rounding.
     * Uses residual analysis to improve integer proximity.
     */
    private static BigDecimal applyPhaseCorrection(BigDecimal pHat, MathContext mc) {
        // For now, simple correction based on fractional part
        // More sophisticated correction would analyze curvature residuals
        BigDecimal fractional = pHat.subtract(
            new BigDecimal(pHat.toBigInteger()), mc
        );

        // If fractional part > 0.5, adjust toward next integer
        if (fractional.compareTo(BigDecimal.valueOf(0.5)) > 0) {
            return pHat.add(BigDecimal.ONE, mc);
        } else {
            return pHat;
        }
    }

    private static BigInteger roundToBigInteger(BigDecimal x, RoundingMode mode) {
        return x.setScale(0, mode).toBigIntegerExact();
    }
}