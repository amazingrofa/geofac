package com.geofac.blind.util;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;

import ch.obermuhlner.math.big.BigDecimalMath;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class PrecisionUtilTest {

    @Test
    void principalAngleNormalizesToRange() {
        MathContext mc = new MathContext(50);
        BigDecimal twoPi = BigDecimalMath.pi(mc).multiply(BigDecimal.valueOf(2), mc);
        BigDecimal angle = twoPi.multiply(BigDecimal.valueOf(3), mc); // 6π → should map to 0
        BigDecimal normalized = PrecisionUtil.principalAngle(angle, mc);
        assertTrue(normalized.abs().compareTo(BigDecimal.valueOf(1e-40)) < 0, "6π should map to ~0");
    }

    @Test
    void mathContextUsesBitLengthRule() {
        BigInteger n = new BigInteger("12345678901234567890");
        MathContext mc = PrecisionUtil.mathContextFor(n, 100);
        int expected = Math.max(100, n.bitLength() * 4 + 200);
        assertEquals(expected, mc.getPrecision());
    }
}
