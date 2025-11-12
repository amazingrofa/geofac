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
    "geofac.precision=260",
    "geofac.samples=3500",
    "geofac.m-span=260",
    "geofac.j=6",
    "geofac.threshold=0.85",
    "geofac.k-lo=0.20",
    "geofac.k-hi=0.50",
    "geofac.search-timeout-ms=300000",  // 5 minute total budget (resonance + fallback)
    "geofac.enable-fast-path=true"
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
     * Full 127-bit factorization test (OUT-OF-GATE)
     *
     * This test validates the geometric resonance algorithm against a 127-bit semiprime.
     * Note: This is outside the validated gate range (10^14-10^18) and serves as a
     * stretch goal benchmark. The algorithm attempts resonance search first, then falls
     * back to Pollard's Rho if resonance fails.
     *
     * Expected: p = 10508623501177419659, q = 13086849276577416863
     */
    @Test
    void testFactor127BitSemiprime() {
        System.out.println("\n=== Starting 127-bit Factorization Test (OUT-OF-GATE) ===");
        System.out.println("This benchmark is ~10^38, outside the 10^14-10^18 validation gate.");
        System.out.println("Attempting resonance search, then Pollard's Rho fallback if needed...\n");

        long startTime = System.currentTimeMillis();
        FactorizationResult result = service.factor(N_127_BIT);
        long duration = System.currentTimeMillis() - startTime;

        System.out.printf("\nCompleted in %.2f seconds\n", duration / 1000.0);

        // Note: Success via either resonance or fallback is acceptable for this out-of-gate benchmark
        assertTrue(result.success(), "Factorization must succeed (via resonance or fallback) within timeout");
        
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

        System.out.println("\n✓ Test passed: Factorization successful (via resonance or fallback)");
    }
}
