package com.geofac.blind.util;

import java.math.BigInteger;

public final class BigIntMath {
    private BigIntMath() {}

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
}
