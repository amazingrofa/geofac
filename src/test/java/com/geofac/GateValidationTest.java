package com.geofac;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test that the validation gates (see docs/VALIDATION_GATES.md) are enforced correctly.
 * Gate 4 (operational range) restricts inputs to [10^14, 10^18] by default.
 * Gate 3 (127-bit challenge) requires special permission via allow-127bit-benchmark property.
 */
@SpringBootTest
@TestPropertySource(properties = {
    "geofac.allow-127bit-benchmark=false",  // Ensure Gate 3 (127-bit) is blocked by default
    "geofac.precision=260",
    "geofac.samples=100",
    "geofac.m-span=10",
    "geofac.j=6",
    "geofac.threshold=0.85",
    "geofac.k-lo=0.20",
    "geofac.k-hi=0.50",
    "geofac.search-timeout-ms=5000"
})
public class GateValidationTest {

    @Autowired
    private FactorizerService service;

    @Test
    void testGate4BlocksNumbersBelowRange() {
        BigInteger tooSmall = new BigInteger("1000");
        Exception ex = assertThrows(IllegalArgumentException.class, () -> service.factor(tooSmall));
        assertTrue(ex.getMessage().contains("does not conform to project validation gates"));
    }

    @Test
    void testGate4BlocksNumbersAboveRange() {
        BigInteger tooLarge = new BigInteger("10000000000000000000"); // > 1e18
        Exception ex = assertThrows(IllegalArgumentException.class, () -> service.factor(tooLarge));
        assertTrue(ex.getMessage().contains("does not conform to project validation gates"));
    }

    @Test
    void testGate3IsBlockedWhenNotWhitelisted() {
        BigInteger gate3_challenge = new BigInteger("137524771864208156028430259349934309717");
        Exception ex = assertThrows(IllegalArgumentException.class, () -> service.factor(gate3_challenge));
        assertTrue(ex.getMessage().contains("does not conform to project validation gates"));
    }
}
