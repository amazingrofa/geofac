package com.geofac.blind.falsification;

import com.geofac.blind.engine.FactorizationResult;
import com.geofac.blind.engine.FactorizerService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * A/B test for shell-exclusion feature.
 * 
 * Tests shell-exclusion enabled vs disabled on a Gate-4 range semiprime
 * to measure impact on hit rate and latency.
 * 
 * Run with: ./gradlew test -Dgeofac.runFalsificationIT=true --tests "*ShellExclusionABTest*"
 */
class ShellExclusionABTest {

    // Gate-4 range semiprime (~10^14)
    private static final BigInteger TEST_P = BigInteger.valueOf(10000019L);
    private static final BigInteger TEST_Q = BigInteger.valueOf(10000079L);
    private static final BigInteger TEST_N = TEST_P.multiply(TEST_Q); // 100001980001501 ≈ 10^14.9

    @EnabledIfSystemProperty(named = "geofac.runFalsificationIT", matches = "true")
    @SpringBootTest(properties = {
            "geofac.allow-127bit-benchmark=true",
            "geofac.enable-fast-path=false",
            "geofac.enable-scale-adaptive=true",
            "geofac.enable-diagnostics=true",
            "geofac.precision=320",
            "geofac.samples=1000",
            "geofac.m-span=150",
            "geofac.j=6",
            "geofac.threshold=0.90",
            "geofac.k-lo=0.28",
            "geofac.k-hi=0.42",
            "geofac.search-timeout-ms=120000", // 2 minutes
            "geofac.shell-exclusion-enabled=false"
    })
    static class ShellExclusionDisabledTest {
        
        @Autowired
        private FactorizerService factorizerService;

        @Test
        void testWithShellExclusionDisabled() {
            System.out.println("=== A/B TEST: Shell Exclusion DISABLED ===");
            System.out.println("N = " + TEST_N + " (" + TEST_N.bitLength() + " bits)");
            System.out.println("Expected: p=" + TEST_P + ", q=" + TEST_Q);
            System.out.println();

            long startTime = System.currentTimeMillis();
            FactorizationResult result = factorizerService.factor(TEST_N);
            long duration = System.currentTimeMillis() - startTime;

            System.out.println("=== RESULT (Shell Exclusion OFF) ===");
            System.out.println("Success: " + result.success());
            System.out.println("Duration: " + duration + " ms");
            
            if (result.success()) {
                System.out.println("Found: p=" + result.p() + ", q=" + result.q());
                assertEquals(TEST_N, result.p().multiply(result.q()));
            } else {
                System.out.println("Failed: " + result.errorMessage());
            }
            
            // Record metrics for comparison
            System.out.println();
            System.out.println("METRICS [shell-exclusion=OFF]: duration_ms=" + duration 
                    + ", success=" + result.success());
        }
    }

    @EnabledIfSystemProperty(named = "geofac.runFalsificationIT", matches = "true")
    @SpringBootTest(properties = {
            "geofac.allow-127bit-benchmark=true",
            "geofac.enable-fast-path=false",
            "geofac.enable-scale-adaptive=true",
            "geofac.enable-diagnostics=true",
            "geofac.precision=320",
            "geofac.samples=1000",
            "geofac.m-span=150",
            "geofac.j=6",
            "geofac.threshold=0.90",
            "geofac.k-lo=0.28",
            "geofac.k-hi=0.42",
            "geofac.search-timeout-ms=120000", // 2 minutes
            "geofac.shell-exclusion-enabled=true",
            "geofac.shell-delta=500",
            "geofac.shell-count=15",
            "geofac.shell-tau=0.12",
            "geofac.shell-tau-spike=0.18",
            "geofac.shell-overlap-percent=0.08",
            "geofac.shell-k-samples=8"
    })
    static class ShellExclusionEnabledTest {
        
        @Autowired
        private FactorizerService factorizerService;

        @Test
        void testWithShellExclusionEnabled() {
            System.out.println("=== A/B TEST: Shell Exclusion ENABLED ===");
            System.out.println("N = " + TEST_N + " (" + TEST_N.bitLength() + " bits)");
            System.out.println("Expected: p=" + TEST_P + ", q=" + TEST_Q);
            System.out.println("Shell params: delta=500, count=15, tau=0.12, tauSpike=0.18");
            System.out.println();

            long startTime = System.currentTimeMillis();
            FactorizationResult result = factorizerService.factor(TEST_N);
            long duration = System.currentTimeMillis() - startTime;

            System.out.println("=== RESULT (Shell Exclusion ON) ===");
            System.out.println("Success: " + result.success());
            System.out.println("Duration: " + duration + " ms");
            
            if (result.success()) {
                System.out.println("Found: p=" + result.p() + ", q=" + result.q());
                assertEquals(TEST_N, result.p().multiply(result.q()));
            } else {
                System.out.println("Failed: " + result.errorMessage());
            }
            
            // Record metrics for comparison
            System.out.println();
            System.out.println("METRICS [shell-exclusion=ON]: duration_ms=" + duration 
                    + ", success=" + result.success());
        }
    }
}
