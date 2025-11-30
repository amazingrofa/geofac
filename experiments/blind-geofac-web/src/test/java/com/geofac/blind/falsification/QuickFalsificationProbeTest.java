package com.geofac.blind.falsification;

import com.geofac.blind.engine.FactorizationResult;
import com.geofac.blind.engine.FactorizerService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.math.BigInteger;
import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Quick falsification probe - 2 minute base timeout (scale-adaptive may increase).
 * 
 * This runs a shorter probe to collect metrics without waiting 30 minutes.
 * Used to observe the algorithm's behavior and tune parameters.
 * 
 * Run with: ./gradlew test -Dgeofac.runFalsificationIT=true --tests "*QuickFalsificationProbeTest"
 */
@EnabledIfSystemProperty(named = "geofac.runFalsificationIT", matches = "true")
@SpringBootTest(properties = {
        "geofac.allow-127bit-benchmark=true",
        "geofac.enable-fast-path=false",
        "geofac.enable-scale-adaptive=true",
        "geofac.enable-diagnostics=true",
        "geofac.precision=512",
        "geofac.samples=500",
        "geofac.m-span=100",
        "geofac.j=6",
        "geofac.threshold=0.88",
        "geofac.k-lo=0.28",
        "geofac.k-hi=0.42",
        "geofac.search-timeout-ms=120000", // 2 minutes
        "geofac.search-radius-percentage=0.015",
        "geofac.max-search-radius=100000000",
        "geofac.coverage-gate-threshold=0.60",
        "geofac.shell-exclusion-enabled=false"
})
class QuickFalsificationProbeTest {

    private static final BigInteger CHALLENGE_N = new BigInteger("137524771864208156028430259349934309717");
    private static final BigInteger EXPECTED_P = new BigInteger("10508623501177419659");
    private static final BigInteger EXPECTED_Q = new BigInteger("13086849276577416863");
    
    @Autowired
    private FactorizerService factorizerService;

    @Test
    void quickProbe_127BitChallenge_2MinuteWindow() {
        System.out.println("=== QUICK FALSIFICATION PROBE: 127-Bit Challenge (2 min timeout) ===");
        System.out.println("N = " + CHALLENGE_N);
        System.out.println("N.bitLength() = " + CHALLENGE_N.bitLength());
        System.out.println("Expected factors: p=" + EXPECTED_P + ", q=" + EXPECTED_Q);
        System.out.println();
        System.out.println("Parameters:");
        System.out.println("  samples: 500 (base, scale-adaptive increases)");
        System.out.println("  m-span: 100 (base, scale-adaptive increases)");
        System.out.println("  threshold: 0.88");
        System.out.println("  k-range: [0.28, 0.42]");
        System.out.println("  timeout: 2 minutes");
        System.out.println("  precision: 512");
        System.out.println();

        long startTime = System.currentTimeMillis();
        FactorizationResult result = factorizerService.factor(CHALLENGE_N);
        long duration = System.currentTimeMillis() - startTime;

        System.out.println();
        System.out.println("=== RESULT ===");
        System.out.println("Success: " + result.success());
        System.out.println("Duration: " + Duration.ofMillis(duration).toSeconds() + " seconds");
        
        if (result.success()) {
            System.out.println("Found p = " + result.p());
            System.out.println("Found q = " + result.q());
            System.out.println("Verification: p*q == N? " + result.p().multiply(result.q()).equals(CHALLENGE_N));
            assertEquals(CHALLENGE_N, result.p().multiply(result.q()), "p*q must equal N");
        } else {
            System.out.println("Error: " + result.errorMessage());
            System.out.println();
            System.out.println("Note: This is a quick probe with 2-minute timeout.");
            System.out.println("Falsification not complete - need full 30-minute run to conclude.");
        }
        
        // Log config used
        System.out.println();
        System.out.println("Config used: " + result.config());
        
        // This test documents behavior without asserting failure
        // The main falsification test has the 30-minute requirement
    }
}
