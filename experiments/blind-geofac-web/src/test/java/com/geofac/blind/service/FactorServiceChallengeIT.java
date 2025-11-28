package com.geofac.blind.service;

import com.geofac.blind.engine.FactorizationResult;
import com.geofac.blind.engine.FactorizerService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@EnabledIfSystemProperty(named = "geofac.runLongChallengeIT", matches = "true")
@SpringBootTest(properties = {
        // Full-budget settings intended to mirror main repo for the 127-bit challenge.
        "geofac.allow-127bit-benchmark=true",
        "geofac.enable-fast-path=false",
        "geofac.enable-scale-adaptive=true",
        "geofac.precision=320",
        "geofac.samples=3000",
        "geofac.m-span=220",
        "geofac.j=6",
        "geofac.threshold=0.92",
        "geofac.k-lo=0.28",
        "geofac.k-hi=0.42",
        "geofac.search-timeout-ms=900000", // 15 minutes
        "geofac.search-radius-percentage=0.012",
        "geofac.max-search-radius=100000000",
        "geofac.coverage-gate-threshold=0.70"
})
class FactorServiceChallengeIT {

    @Autowired
    private FactorizerService factorizerService;

    @Test
    void factorsChallengeWithFullBudget() {
        BigInteger n = new BigInteger(FactorService.DEFAULT_N);

        FactorizationResult result = factorizerService.factor(n);

        System.out.println("127-bit benchmark result: success=" + result.success()
                + " p=" + result.p() + " q=" + result.q()
                + " durationMs=" + result.durationMs());

        assertTrue(result.success(), "Factorization should succeed on the 127-bit benchmark");
        assertNotNull(result.p());
        assertNotNull(result.q());
        assertEquals(n, result.p().multiply(result.q()), "p*q must equal N");
    }
}
