package com.geofac.blind.util;

import java.math.BigDecimal;
import java.math.MathContext;

import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Normalized Dirichlet kernel gate for geometric resonance.
 * Returns amplitude normalized to (2J+1) for consistent thresholding.
 */
public final class DirichletKernel {

    private DirichletKernel() {
        // utility
    }

    /**
     * Compute normalized Dirichlet kernel amplitude
     * A(θ) = |sin((2J+1)θ/2) / ((2J+1) sin(θ/2))|
     * Normalized to (2J+1) for gate thresholding.
     */
    public static BigDecimal normalizedAmplitude(BigDecimal theta, int J, MathContext mc) {
        // Reduce to [-π, π] for stability
        BigDecimal t = PrecisionUtil.principalAngle(theta, mc);

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
}
