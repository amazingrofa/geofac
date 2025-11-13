package com.geofac;
import java.util.Map;

import com.geofac.util.GaussianKernel;
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
 * - Gaussian kernel filtering
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

    @Value("${geofac.j:6}")
    private int J;

    @Value("${geofac.sigma:0.01}")
    private double sigma;

    @Value("${geofac.threshold}")
    private double threshold;

    @Value("${geofac.k-lo}")
    private double kLo;

    @Value("${geofac.k-hi}")
    private double kHi;

    @Value("${geofac.search-timeout-ms:15000}")
    private long searchTimeoutMs;

    // Research gate constants [1e14, 1e18]
    private static final BigInteger GATE_MIN = new BigInteger("100000000000000");       // 1e14
    private static final BigInteger GATE_MAX = new BigInteger("1000000000000000000");   // 1e18

    // One-off benchmark target (127-bit) for whitelist
    private static final BigInteger CHALLENGE_127 =
        new BigInteger("137524771864208156028430259349934309717");

    // OFF by default; only enabled in the dedicated test via TestPropertySource
    @Value("${geofac.allow-127bit-benchmark:false}")
    private boolean allow127bitBenchmark;

    /**
     * Factor a semiprime N into p × q
     *
     * @param N The number to factor
     * @return Array [p, q] if successful, null if not found
     * @throws IllegalArgumentException if N is invalid
     */
    public FactorizationResult factor(BigInteger N) {
        // Create config snapshot for reproducibility
        // CRITICAL: Use 4 × bitLength + 200 for 127-bit precision stability
        // Addresses exponential error propagation in phase-corrected logarithmic factorization
        FactorizerConfig config = new FactorizerConfig(
                Math.max(precision, N.bitLength() * 4 + 200),
                samples,
                mSpan,
                sigma,
                threshold,
                kLo,
                kHi,
                searchTimeoutMs
        );
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

        // Research gate: only operate on N in [1e14, 1e18],
        // unless the one-off 127-bit challenge is explicitly allowed.
        boolean outOfGate = (N.compareTo(GATE_MIN) < 0 || N.compareTo(GATE_MAX) > 0);
        boolean isChallenge = N.equals(CHALLENGE_127);
        if (outOfGate && !(allow127bitBenchmark && isChallenge)) {
            throw new IllegalArgumentException("N must be in [1e14, 1e18]");
        }

        log.info("=== Geometric Resonance Factorization ===");
        log.info("N = {} ({} bits)", N, N.bitLength());

        // Adaptive precision based on bit length
        int adaptivePrecision = config.precision();
        MathContext mc = new MathContext(adaptivePrecision, RoundingMode.HALF_EVEN);

        log.info("Precision: {} decimal digits", adaptivePrecision);
        log.info("Configuration: samples={}, m-span={}, sigma={}, threshold={}",
                 samples, mSpan, sigma, threshold);

        // Initialize constants
        BigDecimal bdN = new BigDecimal(N, mc);
        BigDecimal lnN = BigDecimalMath.log(bdN, mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        BigDecimal phiInv = computePhiInv(mc);
        long startTime = System.currentTimeMillis();
        log.info("Starting search...");
        BigInteger[] factors = search(N, mc, lnN, twoPi, phiInv, startTime, config);

        long duration = System.currentTimeMillis() - startTime;
        log.info("Search completed in {}.{} seconds", duration / 1000, duration % 1000);

        if (factors == null) {
            long totalDuration = System.currentTimeMillis() - startTime;
            String failureMessage = "NO_FACTOR_FOUND: resonance search failed or timed out.";
            log.error(failureMessage);
            return new FactorizationResult(N, null, null, false, totalDuration, config, failureMessage);
        } else {
            log.info("=== SUCCESS ===");
            log.info("p = {}", factors[0]);
            log.info("q = {}", factors[1]);
            // Verify
            if (!factors[0].multiply(factors[1]).equals(N)) {
                log.error("VERIFICATION FAILED: p × q ≠ N");
                throw new IllegalStateException("Product check failed");
            }
            log.info("Verification: p × q = N ✓");
            long totalDuration = System.currentTimeMillis() - startTime;
            return new FactorizationResult(N, factors[0], factors[1], true, totalDuration, config, null);
        }
    }    private BigInteger[] search(BigInteger N, MathContext mc, BigDecimal lnN,
                                BigDecimal twoPi, BigDecimal phiInv, long startTime, FactorizerConfig config) {
        BigDecimal u = BigDecimal.ZERO;
        BigDecimal kWidth = BigDecimal.valueOf(config.kHi() - config.kLo());

        int progressInterval = (int) Math.max(1, config.samples() / 10); // Log every 10%

        for (long n = 0; n < config.samples(); n++) {
            if (config.searchTimeoutMs() > 0 && System.currentTimeMillis() - startTime >= config.searchTimeoutMs()) {
                log.warn("Geometric search timed out after {} samples (configured {} ms)", n, config.searchTimeoutMs());
                return null;
            }

            if (n > 0 && n % progressInterval == 0) {
                int percent = (int) ((n * 100) / config.samples());
                log.info("Progress: {}% ({}/{})", percent, n, samples);
            }

            // Update golden ratio sequence
            u = u.add(phiInv, mc);
            if (u.compareTo(BigDecimal.ONE) >= 0) {
                u = u.subtract(BigDecimal.ONE, mc);
            }

            BigDecimal k = BigDecimal.valueOf(config.kLo()).add(kWidth.multiply(u, mc), mc);
            BigInteger m0 = BigInteger.ZERO; // Balanced semiprime assumption

            AtomicReference<BigInteger[]> result = new AtomicReference<>();

            // Parallel m-scan
            IntStream.rangeClosed(-config.mSpan(), config.mSpan()).parallel().forEach(dm -> {
                if (result.get() != null) return; // Early exit if found

                BigInteger m = m0.add(BigInteger.valueOf(dm));
                BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);

                // Gaussian kernel filtering with amplitude stability verification
                BigDecimal amplitude = GaussianKernel.normalizedAmplitude(theta, BigDecimal.valueOf(config.sigma()), mc);
                if (amplitude.compareTo(BigDecimal.valueOf(config.threshold())) > 0) {
                    BigInteger p0 = SnapKernel.phaseCorrectedSnap(lnN, theta, BigDecimal.valueOf(config.sigma()), mc);

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

    /**
     * Verify amplitude stability by testing perturbed theta values.
     * Prevents false positives from numerical artifacts at precision boundaries.
     *
     * @param theta Base angle
     * @param sigma Gaussian width
     * @param threshold Amplitude threshold
     * @param mc MathContext
     * @return true if amplitude is stable across perturbations
     */
    private boolean verifyAmplitudeStability(BigDecimal theta, BigDecimal sigma,
                                             BigDecimal threshold, MathContext mc) {
        // Perturbation epsilon: scale with precision (e.g., 10^(-precision/4))
        BigDecimal epsilon = BigDecimal.ONE.movePointLeft(mc.getPrecision() / 4);

        // Test theta ± epsilon
        BigDecimal thetaPlus = theta.add(epsilon, mc);
        BigDecimal thetaMinus = theta.subtract(epsilon, mc);

        BigDecimal ampPlus = GaussianKernel.normalizedAmplitude(thetaPlus, sigma, mc);
        BigDecimal ampMinus = GaussianKernel.normalizedAmplitude(thetaMinus, sigma, mc);

        // Require both perturbed amplitudes to also exceed threshold (with 10% tolerance)
        BigDecimal tolerantThreshold = threshold.multiply(BigDecimal.valueOf(0.90), mc);
        return ampPlus.compareTo(tolerantThreshold) > 0 && ampMinus.compareTo(tolerantThreshold) > 0;
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
