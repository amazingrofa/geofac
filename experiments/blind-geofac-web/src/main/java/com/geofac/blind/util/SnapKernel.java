package com.geofac.blind.util;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;

import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Phase-corrected nearest-integer snap for geometric resonance.
 */
public final class SnapKernel {

    private SnapKernel() {}

    /**
     * Compute candidate factor using phase-corrected snap.
     *
     * Formula: p̂ = exp((ln(N) - θ')/2) where θ' = principal angle of theta in [-π, π]
     */
    public static BigInteger phaseCorrectedSnap(BigDecimal lnN, BigDecimal theta, MathContext mc) {
        BigDecimal thetaPrincipal = PrecisionUtil.principalAngle(theta, mc);
        BigDecimal expo = lnN.subtract(thetaPrincipal, mc).divide(BigDecimal.valueOf(2), mc);
        BigDecimal pHat = BigDecimalMath.exp(expo, mc);
        return roundToBigInteger(pHat);
    }

    private static BigInteger roundToBigInteger(BigDecimal x) {
        try {
            return x.setScale(0, RoundingMode.FLOOR).toBigIntegerExact();
        } catch (ArithmeticException e) {
            return x.setScale(0, RoundingMode.FLOOR).toBigInteger();
        }
    }
}
