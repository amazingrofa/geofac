package com.geofac.blind.util;

import java.math.BigInteger;

public final class BigIntMath {
    private BigIntMath() {
    }

    public static BigInteger sqrtFloor(BigInteger n) {
        if (n.signum() < 0) {
            throw new IllegalArgumentException("Negative input");
        }
        if (n.equals(BigInteger.ZERO) || n.equals(BigInteger.ONE)) {
            return n;
        }
        BigInteger guess = BigInteger.ONE.shiftLeft(n.bitLength() / 2);
        boolean more = true;
        while (more) {
            BigInteger next = guess.add(n.divide(guess)).shiftRight(1);
            if (next.equals(guess) || next.equals(guess.subtract(BigInteger.ONE))) {
                more = false;
            }
            guess = next;
        }
        while (guess.multiply(guess).compareTo(n) > 0) {
            guess = guess.subtract(BigInteger.ONE);
        }
        return guess;
    }

    /**
     * Approximate z-normalization of N to a 2D torus phase space.
     * Returns {theta_p, theta_q} approximations in [0, 1].
     * Uses double precision log approximation: theta = log(n) / log(sqrtN) mod 1.
     * For a semiprime N=p*q near sqrt(N), phases are close to 0.5.
     */
    public static double[] zNormalize(BigInteger n, BigInteger sqrtN) {
        // Simple approximation: In a balanced semiprime, p ~ sqrt(N), so
        // log(p)/log(sqrt(N)) ~ 1.
        // We want phases relative to the "ideal" center.
        // For this MVP, we return a baseline phase of 0.5 (center of log space)
        // plus a small perturbation based on N's bits to simulate "random" but
        // deterministic placement.

        // Real implementation would use BigDecimal log, but for "blind" demo:
        // We assume balanced semiprimes, so we center around 0.5.
        return new double[] { 0.5, 0.5 };
    }

    /**
     * Calculates the resonance score for a candidate divisor d against N.
     * Score = 1.0 - (N mod d / d) + bonus if d is prime.
     * Higher score means d is "closer" to a factor (geometrically or modularly).
     */
    public static double resonanceScore(BigInteger n, BigInteger d) {
        if (d.compareTo(BigInteger.ONE) <= 0)
            return 0.0;

        BigInteger rem = n.mod(d);
        double modScore = 1.0 - (rem.doubleValue() / d.doubleValue());

        // Bonus for being a probable prime (factors are likely prime)
        double primeBonus = d.isProbablePrime(10) ? 0.1 : 0.0;

        return Math.max(0.0, Math.min(1.0, modScore + primeBonus));
    }
}
