package com.geofac.util;

import java.math.BigDecimal;
import java.math.MathContext;
import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Normalized Dirichlet kernel gate for geometric resonance.
 * Returns amplitude normalized to (2J+1) for consistent thresholding.
 */
public final class DirichletKernel {

    private DirichletKernel() {} // Utility class

    /**
     * Compute normalized Dirichlet kernel amplitude A(θ) = |sin((2J+1)θ/2) / ((2J+1) sin(θ/2))|
     * Normalized to (2J+1) for gate thresholding.
     *
     * @param theta Angular parameter θ
     * @param J Half-width of Dirichlet kernel
     * @param mc MathContext for precision
     * @return Normalized amplitude in [0, 1]
     */
    public static BigDecimal normalizedAmplitude(BigDecimal theta, int J, MathContext mc) {
        // Reduce to [-π, π] for stability
        BigDecimal t = principalAngle(theta, mc);

        BigDecimal half = BigDecimal.valueOf(0.5);
        BigDecimal th2 = t.multiply(half, mc); // θ/2
        BigDecimal sinTh2 = BigDecimalMath.sin(th2, mc);

        // Singularity guard: adaptive epsilon based on precision
        int epsScale = PrecisionUtil.epsilonScale(mc);
        BigDecimal eps = BigDecimal.ONE.scaleByPowerOfTen(-epsScale);

        if (sinTh2.abs(mc).compareTo(eps) < 0) {
            return BigDecimal.ONE;
        }

        BigDecimal twoJPlus1 = BigDecimal.valueOf(2 * J + 1);
        BigDecimal num = BigDecimalMath.sin(th2.multiply(twoJPlus1, mc), mc);
        BigDecimal den = sinTh2.multiply(twoJPlus1, mc);
        BigDecimal amplitude = num.divide(den, mc).abs(mc);

        return amplitude;
    }

    /**
     * Principal remainder mod 2π into [-π, π]
     */
    private static BigDecimal principalAngle(BigDecimal x, MathContext mc) {
        BigDecimal twoPi = BigDecimalMath.pi(mc).multiply(BigDecimal.valueOf(2), mc);
        BigDecimal invTwoPi = BigDecimal.ONE.divide(twoPi, mc);

        // r = x - floor(x / 2π) * 2π
        BigDecimal k = floor(x.multiply(invTwoPi, mc), mc);
        BigDecimal r = x.subtract(twoPi.multiply(k, mc), mc);

        // Shift to [-π, π]
        BigDecimal pi = BigDecimalMath.pi(mc);
        if (r.compareTo(pi) > 0) r = r.subtract(twoPi, mc);
        if (r.compareTo(pi.negate()) < 0) r = r.add(twoPi, mc);

        return r;
    }

    private static BigDecimal floor(BigDecimal x, MathContext mc) {
        // Always round toward negative infinity to maintain periodicity math
        return x.setScale(0, java.math.RoundingMode.FLOOR);
    }
}
