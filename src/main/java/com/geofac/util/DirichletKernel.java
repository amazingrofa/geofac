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
        // Reduce to principal range for stability
        BigDecimal t = principalAngle(theta, mc);

        // θ/2 and (2J+1)θ/2
        BigDecimal half = BigDecimal.valueOf(0.5);
        BigDecimal th2 = t.multiply(half, mc);
        BigDecimal a = th2.multiply(BigDecimal.valueOf(2L * J + 1L), mc);

        // Dynamic epsilon relative to precision for guarding removable singularities at multiples of π
        int prec = Math.max(8, mc.getPrecision());
        int epsScale = Math.max(12, prec / 2);
        BigDecimal eps = BigDecimal.ONE.movePointLeft(epsScale);

        // If sin(θ/2) is effectively zero (θ ≈ 2πn), the normalized kernel tends to 1
        BigDecimal sinTh2 = BigDecimalMath.sin(th2, mc).abs(mc);
        if (sinTh2.compareTo(eps) <= 0) {
            return BigDecimal.ONE;
        }

        // Stable evaluation via sinc ratio
        BigDecimal sincA = stableSinc(a, mc);
        BigDecimal sincB = stableSinc(th2, mc);

        // If both are extremely small (0/0 near removable singularity), define as 1
        if (sincB.abs(mc).compareTo(eps) <= 0 && sincA.abs(mc).compareTo(eps) <= 0) {
            return BigDecimal.ONE;
        }

        BigDecimal amp = sincA.divide(sincB, mc).abs(mc);

        // Clamp to [0, 1]
        return (amp.compareTo(BigDecimal.ONE) > 0) ? BigDecimal.ONE : amp;
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

    // Numerically stable sinc(x) = sin(x)/x with series fallback near x ≈ 0
    private static BigDecimal stableSinc(BigDecimal x, MathContext mc) {
        BigDecimal ax = x.abs(mc);
        int prec = Math.max(8, mc.getPrecision());
        int tolScale = Math.max(10, prec / 2);
        BigDecimal tol = BigDecimal.ONE.movePointLeft(tolScale);

        if (ax.compareTo(tol) <= 0) {
            // Series: 1 - x^2/6 + x^4/120 - x^6/5040
            BigDecimal x2 = x.multiply(x, mc);
            BigDecimal term1 = x2.divide(BigDecimal.valueOf(6), mc);
            BigDecimal x4 = x2.multiply(x2, mc);
            BigDecimal term2 = x4.divide(BigDecimal.valueOf(120), mc);
            BigDecimal x6 = x4.multiply(x2, mc);
            BigDecimal term3 = x6.divide(BigDecimal.valueOf(5040), mc);
            return BigDecimal.ONE.subtract(term1, mc).add(term2, mc).subtract(term3, mc);
        }

        return BigDecimalMath.sin(x, mc).divide(x, mc);
    }
}
