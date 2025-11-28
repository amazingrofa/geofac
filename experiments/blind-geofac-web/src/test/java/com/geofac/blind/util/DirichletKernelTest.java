package com.geofac.blind.util;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.math.MathContext;

import static org.junit.jupiter.api.Assertions.assertTrue;

class DirichletKernelTest {

    @Test
    void handlesSingularityNearZero() {
        MathContext mc = new MathContext(80);
        BigDecimal tiny = BigDecimal.valueOf(1e-30);
        BigDecimal amp = DirichletKernel.normalizedAmplitude(tiny, 6, mc);
        // Should not blow up; amplitude should be close to 1 for near-zero theta
        assertTrue(amp.doubleValue() < 2.0);
    }
}
