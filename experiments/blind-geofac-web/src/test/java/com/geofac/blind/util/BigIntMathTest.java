package com.geofac.blind.util;

import org.junit.jupiter.api.Test;
import java.math.BigInteger;
import static org.junit.jupiter.api.Assertions.*;

class BigIntMathTest {

    @Test
    void testSqrtFloor() {
        assertEquals(BigInteger.valueOf(3), BigIntMath.sqrtFloor(BigInteger.valueOf(9)));
        assertEquals(BigInteger.valueOf(3), BigIntMath.sqrtFloor(BigInteger.valueOf(10)));
        assertEquals(BigInteger.valueOf(4), BigIntMath.sqrtFloor(BigInteger.valueOf(16)));
    }

    @Test
    void testResonanceScore() {
        BigInteger n = BigInteger.valueOf(15);
        BigInteger d = BigInteger.valueOf(5); // Factor
        // 15 mod 5 = 0. Score = 1.0 - 0 + 0.1 (prime) = 1.1, capped to 1.0 via Math.min.
        assertEquals(1.0, BigIntMath.resonanceScore(n, d), 0.001);

        BigInteger d2 = BigInteger.valueOf(4); // Not factor, not prime
        // 15 mod 4 = 3. Score = 1.0 - (3/4) = 0.25.
        assertEquals(0.25, BigIntMath.resonanceScore(n, d2), 0.001);
    }

    @Test
    void testZNormalize() {
        BigInteger n = BigInteger.valueOf(100);
        BigInteger sqrt = BigInteger.valueOf(10);
        double[] phases = BigIntMath.zNormalize(n, sqrt);
        assertEquals(2, phases.length);
        // thetaP = frac(ln(100)/ln(10)) = frac(2*ln(10)/ln(10)) = frac(2.0) = 0.0
        // thetaQ = frac(thetaP + 0.5) = frac(0.5) = 0.5
        assertEquals(0.0, phases[0], 0.001);
        assertEquals(0.5, phases[1], 0.001);
    }
}
