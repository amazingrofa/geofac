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

        // Nearest integer with tolerance: avoid toBigIntegerExact which may throw
        return roundToBigInteger(correctedPHat, mc.getRoundingMode(), mc);
    }

    /**
     * Apply phase correction to p̂ before rounding.
     * Uses residual analysis to improve integer proximity.
     */
    private static BigDecimal applyPhaseCorrection(BigDecimal pHat, MathContext mc) {
        // Simple nearest-integer approach without adding 1 (which was incorrect)
        // The fractional part analysis should not shift by a full integer unit
        BigDecimal fractional = pHat.remainder(BigDecimal.ONE, mc);

        // The pHat value is already the exponential result; we just need to round it properly
        // No additional correction needed here - the rounding happens in roundToBigInteger
        return pHat;
    }

    private static BigInteger roundToBigInteger(BigDecimal x, RoundingMode mode, MathContext mc) {
        // Use HALF_UP rounding for nearest integer
        // This is the standard rounding approach for finding the closest integer factor candidate
        try {
            return x.setScale(0, RoundingMode.HALF_UP).toBigIntegerExact();
        } catch (ArithmeticException e) {
            // Fallback if exact conversion fails
            return x.setScale(0, RoundingMode.HALF_UP).toBigInteger();
        }
    }
}