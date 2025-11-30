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
 * Falsification attempt for the 127-bit challenge.
 * 
 * Hypothesis: The geometric resonance method can factor the 127-bit semiprime
 * N = 137524771864208156028430259349934309717 within 30 minutes using tuned parameters.
 * 
 * This test runs with extended parameters to give the algorithm maximal opportunity:
 * - samples: 5000 (up from 3000)
 * - m-span: 250 (up from 180)
 * - threshold: 0.88 (down from 0.92)
 * - k-range: [0.28, 0.42] (narrowed from [0.25, 0.45])
 * - timeout: 30 minutes
 * 
 * Run with: ./gradlew test -Dgeofac.runFalsificationIT=true --tests "*FalsificationIT127Bit"
 */
@EnabledIfSystemProperty(named = "geofac.runFalsificationIT", matches = "true")
@SpringBootTest(properties = {
        "geofac.allow-127bit-benchmark=true",
        "geofac.enable-fast-path=false",
        "geofac.enable-scale-adaptive=false",
        "geofac.enable-diagnostics=true",
        "geofac.precision=512",
        "geofac.samples=5000",
        "geofac.m-span=250",
        "geofac.j=6",
        "geofac.threshold=0.88",
        "geofac.k-lo=0.28",
        "geofac.k-hi=0.42",
        "geofac.search-timeout-ms=1800000", // 30 minutes
        "geofac.search-radius-percentage=0.015",
        "geofac.max-search-radius=200000000",
        "geofac.coverage-gate-threshold=0.60",
        "geofac.shell-exclusion-enabled=false"
})
class FalsificationIT127Bit {

    private static final BigInteger CHALLENGE_N = new BigInteger("137524771864208156028430259349934309717");
    private static final BigInteger EXPECTED_P = new BigInteger("10508623501177419659");
    private static final BigInteger EXPECTED_Q = new BigInteger("13086849276577416863");
    
    @Autowired
    private FactorizerService factorizerService;

    @Test
    void falsification_127BitChallenge_TunedParameters() {
        System.out.println("=== FALSIFICATION ATTEMPT: 127-Bit Challenge ===");
        System.out.println("N = " + CHALLENGE_N);
        System.out.println("N.bitLength() = " + CHALLENGE_N.bitLength());
        System.out.println("Expected factors: p=" + EXPECTED_P + ", q=" + EXPECTED_Q);
        System.out.println();
        System.out.println("Tuned parameters:");
        System.out.println("  samples: 5000 (base, scale-adaptive will increase)");
        System.out.println("  m-span: 250 (base, scale-adaptive will increase)");
        System.out.println("  threshold: 0.88");
        System.out.println("  k-range: [0.28, 0.42]");
        System.out.println("  timeout: 30 minutes");
        System.out.println("  precision: 512");
        System.out.println();

        long startTime = System.currentTimeMillis();
        FactorizationResult result = factorizerService.factor(CHALLENGE_N);
        long duration = System.currentTimeMillis() - startTime;

        System.out.println();
        System.out.println("=== RESULT ===");
        System.out.println("Success: " + result.success());
        System.out.println("Duration: " + Duration.ofMillis(duration).toMinutes() + " minutes, " 
                + (duration / 1000 % 60) + " seconds");
        
        if (result.success()) {
            System.out.println("Found p = " + result.p());
            System.out.println("Found q = " + result.q());
            System.out.println("Verification: p*q == N? " + result.p().multiply(result.q()).equals(CHALLENGE_N));
            
            // HYPOTHESIS VALIDATED
            assertEquals(CHALLENGE_N, result.p().multiply(result.q()), "p*q must equal N");
            assertTrue(result.success(), "Factorization should succeed");
        } else {
            System.out.println("Error: " + result.errorMessage());
            System.out.println();
            System.out.println("=== HYPOTHESIS STATUS: FALSIFIED ===");
            System.out.println("The geometric resonance method did NOT factor the 127-bit challenge");
            System.out.println("within 30 minutes using the tuned parameters.");
            
            // Mark as failure - this is the expected outcome for falsification
            fail("Falsification confirmed: geometric resonance did not factor N within timeout. " 
                    + "Error: " + result.errorMessage());
        }
    }
}
