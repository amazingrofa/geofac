package com.geofac;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for policy enforcement - no alternative methods allowed.
 * 
 * These tests verify that:
 * 1. Only the designated target N is accepted
 * 2. Alternative factorization methods are completely disabled
 * 3. Policy constants are correctly defined
 */
@SpringBootTest
public class NoFallbackTest {

    @Test
    void testPolicyTargetIsCorrect() {
        BigInteger expectedTarget = new BigInteger("137524771864208156028430259349934309717");
        assertEquals(expectedTarget, Policy.TARGET, 
            "Policy.TARGET must be the designated 127-bit semiprime");
    }

    @Test
    void testStrictModeEnabled() {
        assertTrue(Policy.STRICT_GEOMETRIC_ONLY, 
            "STRICT_GEOMETRIC_ONLY must be true to enforce geometric resonance only");
    }

    @Test
    void testExitCodesAreDefined() {
        assertEquals(64, Policy.EXIT_TARGET_MISMATCH, 
            "EXIT_TARGET_MISMATCH should be 64");
        assertEquals(2, Policy.EXIT_NO_FACTOR_FOUND, 
            "EXIT_NO_FACTOR_FOUND should be 2");
    }

    @Test
    void testPolicyCannotBeInstantiated() {
        Exception exception = assertThrows(Exception.class, () -> {
            // Use reflection to try to instantiate Policy
            var constructor = Policy.class.getDeclaredConstructor();
            constructor.setAccessible(true);
            constructor.newInstance();
        }, "Policy class should not be instantiable");
        
        // Verify the cause is AssertionError
        assertTrue(exception.getCause() instanceof AssertionError,
            "Policy constructor should throw AssertionError");
    }

    @Test
    void testTargetVerification() {
        // Verify that the target is the known 127-bit semiprime
        BigInteger p = new BigInteger("10508623501177419659");
        BigInteger q = new BigInteger("13086849276577416863");
        BigInteger product = p.multiply(q);
        
        assertEquals(Policy.TARGET, product,
            "Policy.TARGET should equal p × q where p and q are the known factors");
        assertEquals(127, Policy.TARGET.bitLength(),
            "Policy.TARGET should be a 127-bit number");
    }
}
