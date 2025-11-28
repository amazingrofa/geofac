package com.geofac.blind.engine;

import ch.obermuhlner.math.big.BigDecimalMath;
import com.geofac.blind.util.TriangleFilterConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the Triangle-Closure Filter.
 */
@SpringBootTest(properties = {
        "geofac.triangle-filter-enabled=true",
        "geofac.triangle-filter-balance-band=4.0",
        "geofac.triangle-filter-max-log-skew=0.0",
        "geofac.samples=100",
        "geofac.m-span=60",
        "geofac.search-timeout-ms=30000",
        "geofac.enable-scale-adaptive=false"
})
class TriangleFilterTest {

    @Autowired
    private FactorizerService factorizerService;

    private static final MathContext MC = new MathContext(100, RoundingMode.HALF_EVEN);

    // Gate 4 semiprime for testing
    private static final BigInteger TEST_P = BigInteger.valueOf(10000019L);
    private static final BigInteger TEST_Q = BigInteger.valueOf(10000079L);
    private static final BigInteger TEST_N = TEST_P.multiply(TEST_Q);

    private BigDecimal sqrtN;

    @BeforeEach
    void setUp() {
        sqrtN = BigDecimalMath.sqrt(new BigDecimal(TEST_N, MC), MC);
    }

    @Test
    void trueFactor_isNeverRejected() {
        // True factors of a semiprime must always pass the triangle filter
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);

        boolean pAccepted = factorizerService.triangleFilterAccepts(TEST_N, TEST_P, sqrtN, config, MC);
        boolean qAccepted = factorizerService.triangleFilterAccepts(TEST_N, TEST_Q, sqrtN, config, MC);

        assertTrue(pAccepted, "True factor p should pass triangle filter");
        assertTrue(qAccepted, "True factor q should pass triangle filter");
    }

    @Test
    void extremelySmallCandidate_isRejected() {
        // A candidate that's far smaller than sqrtN/R should be rejected
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);
        BigInteger tinyCandidate = BigInteger.valueOf(2); // Way too small

        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, tinyCandidate, sqrtN, config, MC);

        assertFalse(accepted, "Extremely small candidate should be rejected");
    }

    @Test
    void extremelyLargeCandidate_isRejected() {
        // A candidate that's far larger than sqrtN*R should be rejected
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);
        BigInteger hugeCandidate = TEST_N.subtract(BigInteger.ONE); // Almost N itself

        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, hugeCandidate, sqrtN, config, MC);

        assertFalse(accepted, "Extremely large candidate should be rejected");
    }

    @Test
    void filterDisabled_acceptsAll() {
        // When filter is disabled, all candidates should pass
        TriangleFilterConfig config = TriangleFilterConfig.disabled();

        BigInteger tinyCandidate = BigInteger.valueOf(2);
        BigInteger hugeCandidate = TEST_N.subtract(BigInteger.ONE);

        assertTrue(factorizerService.triangleFilterAccepts(TEST_N, tinyCandidate, sqrtN, config, MC),
                "Tiny candidate should pass when filter disabled");
        assertTrue(factorizerService.triangleFilterAccepts(TEST_N, hugeCandidate, sqrtN, config, MC),
                "Huge candidate should pass when filter disabled");
    }

    @Test
    void candidateNearSqrtN_isAccepted() {
        // A candidate near sqrt(N) should always be accepted
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);
        BigInteger nearSqrt = sqrtN.toBigInteger();

        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, nearSqrt, sqrtN, config, MC);

        assertTrue(accepted, "Candidate near sqrt(N) should be accepted");
    }

    @Test
    void zeroCandidateIsRejected() {
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);

        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, BigInteger.ZERO, sqrtN, config, MC);

        assertFalse(accepted, "Zero candidate should be rejected");
    }

    @Test
    void negativeCandidateIsRejected() {
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);

        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, BigInteger.valueOf(-5), sqrtN, config, MC);

        assertFalse(accepted, "Negative candidate should be rejected");
    }

    @Test
    void candidateEqualToN_isRejected() {
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);

        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, TEST_N, sqrtN, config, MC);

        assertFalse(accepted, "Candidate equal to N should be rejected");
    }

    @Test
    void candidateGreaterThanN_isRejected() {
        TriangleFilterConfig config = new TriangleFilterConfig(true, 4.0, 0.0);
        BigInteger biggerThanN = TEST_N.add(BigInteger.ONE);

        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, biggerThanN, sqrtN, config, MC);

        assertFalse(accepted, "Candidate greater than N should be rejected");
    }

    @Test
    void bandEdgeFactors_acceptedWithoutSkewCheck() {
        // Test that band-edge factors pass when skew check is disabled (default)
        // This ensures the "true factors never rejected" invariant holds
        double balanceBand = 4.0;
        TriangleFilterConfig config = new TriangleFilterConfig(true, balanceBand, 0.0);
        
        // Create a candidate slightly inside the band edge (sqrtN/R + 1)
        // This avoids rounding issues from BigInteger truncation
        BigInteger lowerBoundEdge = sqrtN.divide(BigDecimal.valueOf(balanceBand), MC).toBigInteger().add(BigInteger.ONE);
        
        // Should pass because it's within [sqrtN/R, sqrtN*R]
        boolean accepted = factorizerService.triangleFilterAccepts(TEST_N, lowerBoundEdge, sqrtN, config, MC);
        
        assertTrue(accepted, "Band-edge factor should be accepted when skew check disabled");
    }

    @Test
    void integrationTest_factorizationWithFilterEnabled() throws Exception {
        // Verify that factorization still works with the triangle filter enabled
        // The config is already set via @SpringBootTest properties
        var result = factorizerService.factor(TEST_N);

        assertTrue(result.success(), "Factorization should succeed with filter enabled");
        assertNotNull(result.p(), "Factor p should be found");
        assertNotNull(result.q(), "Factor q should be found");
        assertEquals(TEST_N, result.p().multiply(result.q()), "p * q should equal N");
    }
}
