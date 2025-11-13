package com.geofac.util;

import java.math.BigDecimal;
import java.math.MathContext;
import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Gaussian kernel for geometric resonance.
 * Provides a numerically stable alternative to the Dirichlet kernel,
 * leveraging the optimal localization properties of a Gaussian function.
 */
public final class GaussianKernel {

    private GaussianKernel() {} // Utility class

    /**
     * Compute normalized Gaussian kernel amplitude A(θ) = exp(-θ² / (2σ²)).
     * The peak is already normalized to 1 at θ=0.
     *
     * @param theta Angular parameter θ
     * @param sigma Standard deviation (width) of the Gaussian
     * @param mc    MathContext for precision
     * @return Normalized amplitude in (0, 1]
     */
    public static BigDecimal normalizedAmplitude(BigDecimal theta, BigDecimal sigma, MathContext mc) {
        // Reduce to the principal angle in [-π, π] for stability and proper centering.
        BigDecimal t = principalAngle(theta, mc);

        BigDecimal t_squared = t.multiply(t, mc);
        BigDecimal two_sigma_squared = BigDecimal.valueOf(2).multiply(sigma.multiply(sigma, mc), mc);

        // Guard against division by zero if sigma is ever zero, though it shouldn't be.
        if (two_sigma_squared.signum() == 0) {
            return t.signum() == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
        }

        BigDecimal exponent = t_squared.divide(two_sigma_squared, mc).negate();

        return BigDecimalMath.exp(exponent, mc);
    }

    /**
     * Calculates the principal angle of x, mapping it to the range [-π, π].
     * This is crucial for ensuring the kernel is evaluated on the primary peak.
     */
    private static BigDecimal principalAngle(BigDecimal x, MathContext mc) {
        BigDecimal twoPi = BigDecimalMath.pi(mc).multiply(BigDecimal.valueOf(2), mc);
        BigDecimal invTwoPi = BigDecimal.ONE.divide(twoPi, mc);

        // r = x - floor(x / 2π) * 2π
        BigDecimal k = x.multiply(invTwoPi, mc).setScale(0, java.math.RoundingMode.FLOOR);
        BigDecimal r = x.subtract(twoPi.multiply(k, mc), mc);

        // Shift from [0, 2π] to [-π, π]
        BigDecimal pi = BigDecimalMath.pi(mc);
        if (r.compareTo(pi) > 0) {
            r = r.subtract(twoPi, mc);
        }
        return r;
    }
}
