package com.geofac;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test that the research gate [1e14, 1e18] is enforced properly
 * and that the 127-bit challenge whitelist works as expected.
 */
@SpringBootTest
@TestPropertySource(properties = {
    "geofac.allow-127bit-benchmark=false",  // Gate should block out-of-range
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
    void testGateBlocksTooSmall() {
        BigInteger tooSmall = new BigInteger("1000");  // < 1e14
        Exception ex = assertThrows(IllegalArgumentException.class, () -> service.factor(tooSmall));
        assertTrue(ex.getMessage().contains("[1e14, 1e18]"));
    }

    @Test
    void testGateBlocksTooLarge() {
        BigInteger tooLarge = new BigInteger("10000000000000000000");  // > 1e18
        Exception ex = assertThrows(IllegalArgumentException.class, () -> service.factor(tooLarge));
        assertTrue(ex.getMessage().contains("[1e14, 1e18]"));
    }

    @Test
    void testGateBlocks127BitWhenNotWhitelisted() {
        BigInteger n127 = new BigInteger("137524771864208156028430259349934309717");
        Exception ex = assertThrows(IllegalArgumentException.class, () -> service.factor(n127));
        assertTrue(ex.getMessage().contains("[1e14, 1e18]"));
    }
}
