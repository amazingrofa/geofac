package com.geofac.util;

import org.junit.jupiter.api.Test;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for scale-adaptive parameter tuning.
 * 
 * Verifies that parameters scale correctly based on bit-length,
 * implementing empirical scaling laws from Z5D research.
 */
public class ScaleAdaptiveParamsTest {

    // Test constants matching validation gates
    private static final BigInteger GATE_1_N = new BigInteger("1073217479"); // 30-bit
    private static final BigInteger GATE_2_N = new BigInteger("1152921470247108503"); // 60-bit
    private static final BigInteger GATE_3_N = new BigInteger("137524771864208156028430259349934309717"); // 127-bit
    
    // Test tolerance constants
    private static final int SAMPLES_TOLERANCE = 100;
    private static final int MSPAN_TOLERANCE = 10;
    private static final double THRESHOLD_TOLERANCE = 0.01;
    private static final long TIMEOUT_TOLERANCE = 60000; // 1 minute

    @Test
    void testAdaptiveSamples_ScalesWithBitLength() {
        long baseSamples = 3000;
        
        // 30-bit baseline
        long samples30 = ScaleAdaptiveParams.adaptiveSamples(GATE_1_N, baseSamples);
        assertEquals(3000, samples30, SAMPLES_TOLERANCE); // Should be close to baseline
        
        // 60-bit should be ~2.83x higher (quadratic growth)
        long samples60 = ScaleAdaptiveParams.adaptiveSamples(GATE_2_N, baseSamples);
        assertTrue(samples60 > samples30 * 2.5 && samples60 < samples30 * 3.5,
                  "60-bit samples should be ~2.83x baseline");
        
        // 127-bit should be significantly higher
        long samples127 = ScaleAdaptiveParams.adaptiveSamples(GATE_3_N, baseSamples);
        assertTrue(samples127 > samples60 * 2,
                  "127-bit samples should be substantially higher than 60-bit");
    }

    @Test
    void testAdaptiveMSpan_ScalesLinearly() {
        int baseMSpan = 180;
        
        // 30-bit baseline
        int mSpan30 = ScaleAdaptiveParams.adaptiveMSpan(GATE_1_N, baseMSpan);
        assertEquals(180, mSpan30, MSPAN_TOLERANCE); // Should be close to baseline
        
        // 60-bit should be ~2x higher (linear growth)
        int mSpan60 = ScaleAdaptiveParams.adaptiveMSpan(GATE_2_N, baseMSpan);
        assertTrue(mSpan60 > mSpan30 * 1.8 && mSpan60 < mSpan30 * 2.2,
                  "60-bit m-span should be ~2x baseline");
        
        // 127-bit should be ~4.23x higher
        int mSpan127 = ScaleAdaptiveParams.adaptiveMSpan(GATE_3_N, baseMSpan);
        assertTrue(mSpan127 > mSpan30 * 3.5 && mSpan127 < mSpan30 * 5,
                  "127-bit m-span should be ~4.23x baseline");
    }

    @Test
    void testAdaptiveThreshold_DecreasesLogarithmically() {
        double baseThreshold = 0.92;
        double attenuation = 0.05;
        
        // 30-bit baseline
        double threshold30 = ScaleAdaptiveParams.adaptiveThreshold(GATE_1_N, baseThreshold, attenuation);
        assertEquals(0.92, threshold30, THRESHOLD_TOLERANCE); // Should be close to baseline
        
        // 60-bit should be slightly lower (logarithmic decay)
        double threshold60 = ScaleAdaptiveParams.adaptiveThreshold(GATE_2_N, baseThreshold, attenuation);
        assertTrue(threshold60 < threshold30,
                  "60-bit threshold should be lower than 30-bit");
        assertTrue(threshold60 > 0.85 && threshold60 < 0.92,
                  "60-bit threshold should be in reasonable range");
        
        // 127-bit should be even lower but not too much (logarithmic)
        double threshold127 = ScaleAdaptiveParams.adaptiveThreshold(GATE_3_N, baseThreshold, attenuation);
        assertTrue(threshold127 < threshold60,
                  "127-bit threshold should be lower than 60-bit");
        assertTrue(threshold127 > 0.75 && threshold127 < 0.90,
                  "127-bit threshold should be in reasonable range");
    }

    @Test
    void testAdaptiveKRange_NarrowsWithScale() {
        double kLo = 0.25;
        double kHi = 0.45;
        double baseWidth = kHi - kLo; // 0.20
        
        // 30-bit baseline
        double[] kRange30 = ScaleAdaptiveParams.adaptiveKRange(GATE_1_N, kLo, kHi);
        double width30 = kRange30[1] - kRange30[0];
        assertEquals(0.20, width30, THRESHOLD_TOLERANCE); // Should be close to baseline
        
        // 60-bit should be narrower
        double[] kRange60 = ScaleAdaptiveParams.adaptiveKRange(GATE_2_N, kLo, kHi);
        double width60 = kRange60[1] - kRange60[0];
        assertTrue(width60 < width30,
                  "60-bit k-range should be narrower than 30-bit");
        
        // 127-bit should be even narrower
        double[] kRange127 = ScaleAdaptiveParams.adaptiveKRange(GATE_3_N, kLo, kHi);
        double width127 = kRange127[1] - kRange127[0];
        assertTrue(width127 < width60,
                  "127-bit k-range should be narrower than 60-bit");
        
        // All ranges should be centered around the same point
        double center = (kLo + kHi) / 2.0;
        assertEquals(center, (kRange30[0] + kRange30[1]) / 2.0, THRESHOLD_TOLERANCE);
        assertEquals(center, (kRange60[0] + kRange60[1]) / 2.0, THRESHOLD_TOLERANCE);
        assertEquals(center, (kRange127[0] + kRange127[1]) / 2.0, THRESHOLD_TOLERANCE);
    }

    @Test
    void testAdaptiveTimeout_ScalesQuadratically() {
        long baseTimeout = 600000; // 10 minutes
        
        // 30-bit baseline
        long timeout30 = ScaleAdaptiveParams.adaptiveTimeout(GATE_1_N, baseTimeout);
        assertEquals(600000, timeout30, TIMEOUT_TOLERANCE); // Should be close to baseline
        
        // 60-bit should be ~4x higher (quadratic growth)
        long timeout60 = ScaleAdaptiveParams.adaptiveTimeout(GATE_2_N, baseTimeout);
        assertTrue(timeout60 > timeout30 * 3 && timeout60 < timeout30 * 5,
                  "60-bit timeout should be ~4x baseline");
        
        // 127-bit should be substantially higher
        long timeout127 = ScaleAdaptiveParams.adaptiveTimeout(GATE_3_N, baseTimeout);
        assertTrue(timeout127 > timeout60 * 3,
                  "127-bit timeout should be substantially higher than 60-bit");
    }

    @Test
    void testAdaptiveThreshold_BoundsRespected() {
        // Test that threshold stays in [0.5, 1.0] even with extreme values
        BigInteger largeN = BigInteger.TWO.pow(500); // Very large number
        
        double threshold = ScaleAdaptiveParams.adaptiveThreshold(largeN, 0.92, 0.05);
        assertTrue(threshold >= 0.5 && threshold <= 1.0,
                  "Threshold should be bounded in [0.5, 1.0]");
    }
}
