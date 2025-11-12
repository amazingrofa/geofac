package com.geofac;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for FactorizerService
 *
 * Note: Full 127-bit factorization test is time-consuming (~3 minutes)
 * so it's marked with a specific test profile. Run with:
 *   ./gradlew test
 */
@SpringBootTest
@TestPropertySource(properties = {
    "geofac.precision=240",
    "geofac.samples=3000",
    "geofac.m-span=220",
    "geofac.j=6",
    "geofac.threshold=0.90",
    "geofac.k-lo=0.25",
    "geofac.k-hi=0.45",
    "geofac.search-timeout-ms=600000"  // 10 minute timeout for testing
})
public class FactorizerServiceTest {

    @Autowired
    private FactorizerService service;

    // Test data from z-sandbox
    private static final BigInteger N_127_BIT =
        new BigInteger("137524771864208156028430259349934309717");
    private static final BigInteger P_EXPECTED =
        new BigInteger("10508623501177419659");
    private static final BigInteger Q_EXPECTED =
        new BigInteger("13086849276577416863");

    void testServiceIsInjected() {
        assertNotNull(service, "FactorizerService should be injected");
    }

    void testConfigurationLoaded() {
        assertEquals(3000, service.getSamples(), "Samples should be loaded from config");
        assertEquals(220, service.getMSpan(), "M-span should be loaded from config");
    }

    void testFactorValidation_NullInput() {
        Exception exception = assertThrows(
            IllegalArgumentException.class,
            () -> service.factor(null)
        );
        assertEquals("N cannot be null", exception.getMessage());
    }

    void testFactorValidation_NegativeNumber() {
        Exception exception = assertThrows(
            IllegalArgumentException.class,
            () -> service.factor(BigInteger.valueOf(-123))
        );
        assertEquals("N must be positive", exception.getMessage());
    }

    void testFactorValidation_TooSmall() {
        Exception exception = assertThrows(
            IllegalArgumentException.class,
            () -> service.factor(BigInteger.valueOf(5))
        );
        assertEquals("N must be at least 10", exception.getMessage());
    }

    void testProductVerification() {
        // Verify test data integrity
        BigInteger product = P_EXPECTED.multiply(Q_EXPECTED);
        assertEquals(N_127_BIT, product,
            "Test data should be valid: p × q = N");
    }

    /**
     * Full 127-bit factorization test
     *
     * This test validates the geometric resonance algorithm against the target N.
     * The algorithm must successfully find the factors within the 10-minute timeout.
     *
     * Expected: p = 10508623501177419659, q = 13086849276577416863
     */
    @Test
    void testFactor127BitSemiprime() {
        System.out.println("\n=== Starting 127-bit Factorization Test ===");
        System.out.println("Geometric resonance must find the factors within 10 minutes...\n");

        long startTime = System.currentTimeMillis();
        FactorizationResult result = service.factor(N_127_BIT);
        long duration = System.currentTimeMillis() - startTime;

        System.out.printf("\nCompleted in %.2f seconds\n", duration / 1000.0);

        // Always expect successful factorization
        assertTrue(result.success(), "Geometric resonance must find the factors within timeout");
        
        // Verify result
        BigInteger p = result.p();
        BigInteger q = result.q();
        assertNotNull(p, "p should not be null");
        assertNotNull(q, "q should not be null");

        // Verify factors match expected values
        assertTrue(
            (p.equals(P_EXPECTED) && q.equals(Q_EXPECTED)) ||
            (p.equals(Q_EXPECTED) && q.equals(P_EXPECTED)),
            String.format("Factors should match expected values.\nExpected: p=%s, q=%s\nGot: p=%s, q=%s",
                P_EXPECTED, Q_EXPECTED, p, q)
        );

        // Verify product
        assertEquals(N_127_BIT, p.multiply(q), "Product of factors should equal N");

        System.out.println("\n✓ Test passed: Geometric resonance successfully found factors");
    }
}
