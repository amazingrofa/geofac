package com.geofac;

import com.geofac.util.DirichletKernel;
import com.geofac.util.SnapKernel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.IntStream;

import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Geometric Resonance Factorization Service
 *
 * Implements platform-independent factorization using:
 * - Dirichlet kernel filtering
 * - Golden-ratio QMC sampling
 * - High-precision BigDecimal arithmetic
 *
 * Ported from: z-sandbox GeometricResonanceFactorizer
 */
@Service
public class FactorizerService {

    private static final Logger log = LoggerFactory.getLogger(FactorizerService.class);

    @Value("${geofac.precision}")
    private int precision;

    @Value("${geofac.samples}")
    private long samples;

    @Value("${geofac.m-span}")
    private int mSpan;

    @Value("${geofac.j}")
    private int J;

    @Value("${geofac.threshold}")
    private double threshold;

    @Value("${geofac.k-lo}")
    private double kLo;

    @Value("${geofac.k-hi}")
    private double kHi;

    /**
     * Factor a semiprime N into p × q
     *
     * @param N The number to factor
     * @return Array [p, q] if successful, null if not found
     * @throws IllegalArgumentException if N is invalid
     */
    public BigInteger[] factor(BigInteger N) {
        // Validation
        if (N == null) {
            throw new IllegalArgumentException("N cannot be null");
        }
        if (N.signum() <= 0) {
            throw new IllegalArgumentException("N must be positive");
        }
        if (N.compareTo(BigInteger.TEN) < 0) {
            throw new IllegalArgumentException("N must be at least 10");
        }

        log.info("=== Geometric Resonance Factorization ===");
        log.info("N = {} ({} bits)", N, N.bitLength());

        // Adaptive precision based on bit length
        int adaptivePrecision = Math.max(precision, N.bitLength() * 2 + 100);
        MathContext mc = new MathContext(adaptivePrecision, RoundingMode.HALF_EVEN);

        log.info("Precision: {} decimal digits", adaptivePrecision);
        log.info("Configuration: samples={}, m-span={}, J={}, threshold={}",
                 samples, mSpan, J, threshold);

        // Initialize constants
        BigDecimal bdN = new BigDecimal(N, mc);
        BigDecimal lnN = BigDecimalMath.log(bdN, mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        BigDecimal phiInv = computePhiInv(mc);

        log.info("Starting search...");
        long startTime = System.currentTimeMillis();

        // Search
        BigInteger[] result = search(N, mc, lnN, twoPi, phiInv);

        long duration = System.currentTimeMillis() - startTime;
        log.info("Search completed in {}.{} seconds", duration / 1000, duration % 1000);

        if (result != null) {
            log.info("=== SUCCESS ===");
            log.info("p = {}", result[0]);
            log.info("q = {}", result[1]);

            // Verify
            if (!result[0].multiply(result[1]).equals(N)) {
                log.error("VERIFICATION FAILED: p × q ≠ N");
                throw new IllegalStateException("Product check failed");
            }
            log.info("Verification: p × q = N ✓");
        } else {
            log.warn("=== NO FACTORS FOUND ===");
            log.warn("Consider: increase samples, m-span, or adjust threshold");
        }

        return result;
    }

    private BigInteger[] search(BigInteger N, MathContext mc, BigDecimal lnN,
                                BigDecimal twoPi, BigDecimal phiInv) {
        BigDecimal u = BigDecimal.ZERO;
        BigDecimal kWidth = BigDecimal.valueOf(kHi - kLo);
        BigDecimal thresholdBd = BigDecimal.valueOf(threshold);

        int progressInterval = (int) (samples / 10); // Log every 10%

        for (long n = 0; n < samples; n++) {
            if (n > 0 && n % progressInterval == 0) {
                int percent = (int) ((n * 100) / samples);
                log.info("Progress: {}% ({}/{})", percent, n, samples);
            }

            // Update golden ratio sequence
            u = u.add(phiInv, mc);
            if (u.compareTo(BigDecimal.ONE) >= 0) {
                u = u.subtract(BigDecimal.ONE, mc);
            }

            BigDecimal k = BigDecimal.valueOf(kLo).add(kWidth.multiply(u, mc), mc);
            BigInteger m0 = BigInteger.ZERO; // Balanced semiprime assumption

            AtomicReference<BigInteger[]> result = new AtomicReference<>();

            // Parallel m-scan
            IntStream.rangeClosed(-mSpan, mSpan).parallel().forEach(dm -> {
                if (result.get() != null) return; // Early exit if found

                BigInteger m = m0.add(BigInteger.valueOf(dm));
                BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);

                // Dirichlet kernel filtering
                BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, J, mc);
                if (amplitude.compareTo(thresholdBd) > 0) {
                    BigInteger p0 = SnapKernel.phaseCorrectedSnap(lnN, theta, mc);

                    // Test candidate and neighbors
                    BigInteger[] hit = testNeighbors(N, p0);
                    if (hit != null) {
                        result.compareAndSet(null, hit);
                    }
                }
            });

            if (result.get() != null) {
                log.info("Factor found at k-sample {}/{}", n + 1, samples);
                return result.get();
            }
        }

        return null;
    }

    private BigInteger[] testNeighbors(BigInteger N, BigInteger pCenter) {
        // Test p, p-1, p+1
        BigInteger[] offsets = { BigInteger.ZERO, BigInteger.valueOf(-1), BigInteger.ONE };
        for (BigInteger off : offsets) {
            BigInteger p = pCenter.add(off);
            if (p.compareTo(BigInteger.ONE) <= 0 || p.compareTo(N) >= 0) {
                continue;
            }
            if (N.mod(p).equals(BigInteger.ZERO)) {
                BigInteger q = N.divide(p);
                return ordered(p, q);
            }
        }
        return null;
    }

    private static BigInteger[] ordered(BigInteger a, BigInteger b) {
        return (a.compareTo(b) <= 0) ? new BigInteger[]{a, b} : new BigInteger[]{b, a};
    }

    private BigDecimal computePhiInv(MathContext mc) {
        // φ⁻¹ = (√5 - 1) / 2
        BigDecimal sqrt5 = BigDecimalMath.sqrt(BigDecimal.valueOf(5), mc);
        return sqrt5.subtract(BigDecimal.ONE, mc).divide(BigDecimal.valueOf(2), mc);
    }

    // Package-private getters for testing
    long getSamples() {
        return samples;
    }

    int getMSpan() {
        return mSpan;
    }
}
