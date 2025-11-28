package com.geofac.blind.util;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;

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
     * Returns {theta_p, theta_q} approximations in [0, 1).
     * Uses a deterministic log approximation: theta = frac(ln(n) / ln(sqrtN)).
     * theta_q is offset by 0.5 on the unit circle to mirror p/q symmetry.
     * TODO: Replace double-based log with BigDecimal precision if/when available.
     */
    public static double[] zNormalize(BigInteger n, BigInteger sqrtN) {
        if (n == null || sqrtN == null || n.signum() <= 0 || sqrtN.signum() <= 0) {
            throw new IllegalArgumentException("n and sqrtN must be positive");
        }

        double lnN = logBigInteger(n);
        double lnSqrtN = logBigInteger(sqrtN);
        if (lnSqrtN == 0.0) {
            return new double[] { 0.0, 0.5 }; // Degenerate, but deterministic
        }

        double theta = frac(lnN / lnSqrtN);
        double thetaP = theta;
        double thetaQ = frac(theta + 0.5); // Opposite phase on the circle
        return new double[] { thetaP, thetaQ };
    }

    private static double frac(double x) {
        double f = x - Math.floor(x);
        return (f == 1.0) ? 0.0 : f;
    }

    /**
     * Deterministic natural log approximation of a BigInteger using high bits and scaling.
     */
    private static double logBigInteger(BigInteger x) {
        int bitLength = x.bitLength();
        // Keep mantissa within double range by shifting if very large
        int shift = Math.max(0, bitLength - 1022);
        BigInteger shifted = shift == 0 ? x : x.shiftRight(shift);
        double mantissa = shifted.doubleValue();
        return Math.log(mantissa) + shift * Math.log(2.0);
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
        if (rem.equals(BigInteger.ZERO)) {
            return 1.0; // perfect hit; no precision loss needed
        }

        BigDecimal remDec = new BigDecimal(rem);
        BigDecimal dDec = new BigDecimal(d);
        BigDecimal ratio = remDec.divide(dDec, MathContext.DECIMAL128);
        double modScore = BigDecimal.ONE.subtract(ratio).doubleValue();

        // Bonus for being a probable prime (factors are likely prime)
        double primeBonus = d.isProbablePrime(10) ? 0.1 : 0.0;

        return Math.max(0.0, Math.min(1.0, modScore + primeBonus));
    }
}
