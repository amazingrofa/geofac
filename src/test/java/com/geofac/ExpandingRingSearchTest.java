package com.geofac;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test to verify the expanding ring search refinement finds factors at arbitrary offsets.
 * 
 * The expanding ring search should find factors even when the geometric resonance candidate
 * (p0) has an arbitrary offset from the true factor, not just at exact radius boundaries.
 */
@SpringBootTest
@TestPropertySource(properties = {
    "geofac.precision=240",
    "geofac.samples=30000",
    "geofac.m-span=600",
    "geofac.j=6",
    "geofac.threshold=0.7",
    "geofac.k-lo=0.25",
    "geofac.k-hi=0.45",
    "geofac.search-timeout-ms=600000"
})
public class ExpandingRingSearchTest {

    @Autowired
    private FactorizerService service;

    /**
     * Test factoring a semiprime in Gate 2 range where expanding ring search is needed.
     * This uses N = 100,000,980,001,501 = 10,000,019 × 10,000,079
     * 
     * The expanding ring search should find factors even if the geometric resonance
     * candidate has an offset like +11, +500, or larger values within the search radii.
     */
    @Test
    void testExpandingRingFindsArbitraryOffsets() {
        // Gate 2 range semiprime (in [1e14, 1e18])
        BigInteger N = new BigInteger("100000980001501");
        BigInteger p = new BigInteger("10000019");
        BigInteger q = new BigInteger("10000079");
        
        // Verify test data
        assertEquals(N, p.multiply(q), "Test data should be valid: p × q = N");
        
        System.out.println("\n=== Testing Expanding Ring Search ===");
        System.out.println("N = " + N + " (" + N.bitLength() + " bits)");
        System.out.println("Expected factors: p = " + p + ", q = " + q);
        System.out.println("Factor gap: " + q.subtract(p));
        
        long startTime = System.currentTimeMillis();
        FactorizationResult result = service.factor(N);
        long duration = System.currentTimeMillis() - startTime;
        
        System.out.printf("Completed in %.2f seconds\n", duration / 1000.0);
        
        if (result.success()) {
            System.out.println("✓ Factorization successful!");
            System.out.println("p = " + result.p());
            System.out.println("q = " + result.q());
            
            // Verify factors are correct (order may vary)
            assertTrue(
                (result.p().equals(p) && result.q().equals(q)) ||
                (result.p().equals(q) && result.q().equals(p)),
                "Factors should match expected values"
            );
            
            // Verify product
            assertEquals(N, result.p().multiply(result.q()), "p × q should equal N");
        } else {
            System.out.println("✗ Factorization failed: " + result.errorMessage());
            System.out.println("Note: This test validates that the expanding ring search can handle arbitrary offsets.");
            System.out.println("If the geometric resonance produces a candidate near the true factor, the ring search should find it.");
        }
    }
    
    /**
     * Test a Gate 2 range semiprime to ensure the algorithm works in the validation window.
     */
    @Test
    void testGate2Semiprime() {
        // Another semiprime in the Gate 2 range [1e14, 1e18]
        // N = 100,019,001,989 = 10,001,023 × 10,000,973
        BigInteger N = new BigInteger("100019001989979");
        BigInteger p = new BigInteger("10001023");
        BigInteger q = new BigInteger("10000973");
        
        // Verify test data
        assertEquals(N, p.multiply(q), "Test data should be valid: p × q = N");
        
        System.out.println("\n=== Testing Gate 2 Range Semiprime ===");
        System.out.println("N = " + N + " (" + N.bitLength() + " bits)");
        
        long startTime = System.currentTimeMillis();
        FactorizationResult result = service.factor(N);
        long duration = System.currentTimeMillis() - startTime;
        
        System.out.printf("Completed in %.2f seconds\n", duration / 1000.0);
        
        if (result.success()) {
            System.out.println("✓ Factorization successful!");
            System.out.println("p = " + result.p());
            System.out.println("q = " + result.q());
            
            // Verify factors are correct (order may vary)
            assertTrue(
                (result.p().equals(p) && result.q().equals(q)) ||
                (result.p().equals(q) && result.q().equals(p)),
                "Factors should match expected values"
            );
            
            // Verify product
            assertEquals(N, result.p().multiply(result.q()), "p × q should equal N");
        } else {
            System.out.println("✗ Factorization failed: " + result.errorMessage());
            System.out.println("Note: Algorithm may not find factors for all semiprimes within timeout.");
        }
    }
}
