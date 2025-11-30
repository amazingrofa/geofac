package com.geofac.blind.falsification;

import com.geofac.blind.util.DirichletKernel;
import com.geofac.blind.util.PrecisionUtil;
import com.geofac.blind.util.ScaleAdaptiveParams;
import com.geofac.blind.util.SnapKernel;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Micro-tests for edge cases in the geometric resonance pipeline.
 * 
 * These tests verify:
 * 1. Singularity guard (theta=0) behavior in Dirichlet kernel
 * 2. Precision/angle adaptive scaling
 * 3. Scale-adaptive parameter tuning
 */
class MicroEdgeCaseTests {

    private static final BigInteger CHALLENGE_N = new BigInteger("137524771864208156028430259349934309717");
    
    /** 
     * Upper bound for normalized Dirichlet amplitude. Numerical precision near singularities
     * can cause amplitudes slightly above 1.0; 1.05 allows 5% tolerance for edge cases.
     */
    private static final BigDecimal NORMALIZED_AMPLITUDE_UPPER_BOUND = BigDecimal.valueOf(1.05);
    private static final BigInteger GATE4_N = new BigInteger("100001980001501"); // ~10^14

    @Test
    void singularityGuard_thetaZero_returnsOne() {
        // When theta = 0, sin(theta/2) = 0 which would cause division by zero
        // The Dirichlet kernel should return 1.0 (normalized amplitude at singularity)
        
        MathContext mc = new MathContext(240);
        BigDecimal theta = BigDecimal.ZERO;
        int J = 6;
        
        BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, J, mc);
        
        System.out.println("Singularity test: theta=0, J=" + J);
        System.out.println("Amplitude: " + amplitude);
        
        assertEquals(0, BigDecimal.ONE.compareTo(amplitude), 
                "Amplitude at theta=0 should be 1.0 (singularity handled)");
    }

    @Test
    void singularityGuard_thetaNearZero_handledGracefully() {
        // Test very small theta values near the singularity
        
        MathContext mc = new MathContext(240);
        int J = 6;
        
        // Test values near singularity - values smaller than precision epsilon will 
        // hit the guard and return 1.0; larger values show graceful degradation.
        // These values span different orders of magnitude to test the singularity guard
        // across various precision thresholds (e.g., double precision ~1e-16, BigDecimal precision ~1e-50).
        double[] smallThetas = {1e-10, 1e-20, 1e-50};
        
        System.out.println("Near-singularity tests (J=" + J + "):");
        for (double thetaVal : smallThetas) {
            BigDecimal theta = new BigDecimal(String.valueOf(thetaVal));
            BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, J, mc);
            
            System.out.println("  theta=" + thetaVal + " -> amplitude=" + amplitude);
            
            // Should not throw and should be close to 1.0
            assertTrue(amplitude.compareTo(BigDecimal.ZERO) >= 0, 
                    "Amplitude should be non-negative");
            assertTrue(amplitude.compareTo(BigDecimal.valueOf(2)) <= 0, 
                    "Amplitude should be bounded (normalized)");
        }
    }

    @Test
    void precisionScaling_127Bit_sufficientPrecision() {
        // Verify precision is sufficient for 127-bit challenge
        // Formula: precision = max(configured, N.bitLength() * 4 + 200)
        
        int configuredPrecision = 240;
        int expectedMinPrecision = CHALLENGE_N.bitLength() * 4 + 200; // 127*4 + 200 = 708
        
        MathContext mc = PrecisionUtil.mathContextFor(CHALLENGE_N, configuredPrecision);
        
        System.out.println("Precision scaling for 127-bit N:");
        System.out.println("  N.bitLength() = " + CHALLENGE_N.bitLength());
        System.out.println("  Configured precision = " + configuredPrecision);
        System.out.println("  Expected min precision = " + expectedMinPrecision);
        System.out.println("  Actual MathContext precision = " + mc.getPrecision());
        
        assertTrue(mc.getPrecision() >= expectedMinPrecision, 
                "Precision should be at least " + expectedMinPrecision + " for 127-bit N");
    }

    @Test
    void scaleAdaptiveParams_127Bit_scalingApplied() {
        // Verify scale-adaptive parameters are applied for 127-bit challenge
        
        long baseSamples = 2000;
        int baseMSpan = 180;
        double baseThreshold = 0.95;
        double attenuation = 0.05;
        double kLo = 0.25, kHi = 0.45;
        long baseTimeout = 600000;
        
        long adaptedSamples = ScaleAdaptiveParams.adaptiveSamples(CHALLENGE_N, baseSamples);
        int adaptedMSpan = ScaleAdaptiveParams.adaptiveMSpan(CHALLENGE_N, baseMSpan);
        double adaptedThreshold = ScaleAdaptiveParams.adaptiveThreshold(CHALLENGE_N, baseThreshold, attenuation);
        double[] adaptedKRange = ScaleAdaptiveParams.adaptiveKRange(CHALLENGE_N, kLo, kHi);
        long adaptedTimeout = ScaleAdaptiveParams.adaptiveTimeout(CHALLENGE_N, baseTimeout);
        
        System.out.println("Scale-adaptive parameters for 127-bit N:");
        System.out.println("  samples: " + baseSamples + " -> " + adaptedSamples);
        System.out.println("  m-span: " + baseMSpan + " -> " + adaptedMSpan);
        System.out.println("  threshold: " + baseThreshold + " -> " + adaptedThreshold);
        System.out.println("  k-range: [" + kLo + ", " + kHi + "] -> [" + adaptedKRange[0] + ", " + adaptedKRange[1] + "]");
        System.out.println("  timeout: " + baseTimeout + "ms -> " + adaptedTimeout + "ms");
        
        // Samples should increase significantly for larger bit-lengths
        assertTrue(adaptedSamples > baseSamples, 
                "Samples should scale up for 127-bit N");
        
        // M-span should increase
        assertTrue(adaptedMSpan > baseMSpan, 
                "M-span should scale up for 127-bit N");
        
        // Threshold should decrease (attenuate)
        assertTrue(adaptedThreshold < baseThreshold, 
                "Threshold should attenuate for 127-bit N");
        assertTrue(adaptedThreshold >= 0.5, 
                "Threshold should stay above minimum 0.5");
        
        // K-range should narrow
        double baseWidth = kHi - kLo;
        double adaptedWidth = adaptedKRange[1] - adaptedKRange[0];
        assertTrue(adaptedWidth < baseWidth, 
                "K-range should narrow for larger N");
        
        // Timeout should increase
        assertTrue(adaptedTimeout > baseTimeout, 
                "Timeout should scale up for 127-bit N");
    }

    @Test
    void scaleAdaptiveParams_Gate4_moderateScaling() {
        // Verify scale-adaptive parameters for Gate-4 range (~50-bit N)
        
        long baseSamples = 2000;
        int baseMSpan = 180;
        
        long adaptedSamples = ScaleAdaptiveParams.adaptiveSamples(GATE4_N, baseSamples);
        int adaptedMSpan = ScaleAdaptiveParams.adaptiveMSpan(GATE4_N, baseMSpan);
        
        System.out.println("Scale-adaptive parameters for Gate-4 N (" + GATE4_N.bitLength() + " bits):");
        System.out.println("  samples: " + baseSamples + " -> " + adaptedSamples);
        System.out.println("  m-span: " + baseMSpan + " -> " + adaptedMSpan);
        
        // Scaling should be present but more moderate than 127-bit
        assertTrue(adaptedSamples > baseSamples, 
                "Samples should scale for Gate-4 N");
        assertTrue(adaptedSamples < ScaleAdaptiveParams.adaptiveSamples(CHALLENGE_N, baseSamples), 
                "Gate-4 scaling should be less than 127-bit scaling");
    }

    @Test
    void snapKernel_validRange_producesReasonableCandidate() {
        // Verify snap kernel produces reasonable candidates
        
        MathContext mc = new MathContext(320);
        // Compute ln(CHALLENGE_N) programmatically for consistency
        BigDecimal lnN = ch.obermuhlner.math.big.BigDecimalMath.log(new BigDecimal(CHALLENGE_N), mc);
        BigDecimal theta = BigDecimal.valueOf(Math.PI / 4); // π/4
        
        BigInteger candidate = SnapKernel.phaseCorrectedSnap(lnN, theta, mc);
        
        System.out.println("Snap kernel test:");
        System.out.println("  lnN = " + lnN.setScale(6, java.math.RoundingMode.HALF_UP));
        System.out.println("  theta = π/4");
        System.out.println("  candidate = " + candidate);
        System.out.println("  candidate bits = " + candidate.bitLength());
        
        // Candidate should be positive and reasonable
        assertTrue(candidate.compareTo(BigInteger.ONE) > 0, 
                "Candidate should be greater than 1");
        assertTrue(candidate.bitLength() > 0, 
                "Candidate should have positive bit length");
    }

    @Test
    void dirichletKernel_variousJ_amplitudesNormalized() {
        // Test Dirichlet kernel with various J values
        
        MathContext mc = new MathContext(240);
        BigDecimal theta = BigDecimal.valueOf(Math.PI / 6); // π/6
        
        System.out.println("Dirichlet kernel J-sweep (theta=π/6):");
        for (int J = 2; J <= 10; J++) {
            BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, J, mc);
            System.out.println("  J=" + J + " -> amplitude=" + amplitude.setScale(6, java.math.RoundingMode.HALF_UP));
            
            // Amplitude should be bounded [0, ~1] after normalization
            // The Dirichlet kernel normalizes to (2J+1), so amplitude ≤ 1.0 except for 
            // numerical edge cases near singularities
            assertTrue(amplitude.compareTo(BigDecimal.ZERO) >= 0, 
                    "Amplitude should be non-negative");
            assertTrue(amplitude.compareTo(NORMALIZED_AMPLITUDE_UPPER_BOUND) <= 0, 
                    "Normalized amplitude should be bounded near 1.0");
        }
    }
}
