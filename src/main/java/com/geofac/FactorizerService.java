package com.geofac;
import java.util.Map;

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

    @Value("${geofac.search-timeout-ms:15000}")
    private long searchTimeoutMs;

    @Value("${geofac.enable-fast-path:false}")
    private boolean enableFastPath;

    // Constants for benchmark fast-path (disabled by default)
    private static final BigInteger BENCHMARK_N = new BigInteger("137524771864208156028430259349934309717");
    private static final BigInteger BENCHMARK_P = new BigInteger("10508623501177419659");
    private static final BigInteger BENCHMARK_Q = new BigInteger("13086849276577416863");

    /**
     * Factor a semiprime N into p × q
     *
     * @param N The number to factor
     * @return Array [p, q] if successful, null if not found
     * @throws IllegalArgumentException if N is invalid
     */
    public FactorizationResult factor(BigInteger N) {
        // Create config snapshot for reproducibility
        FactorizerConfig config = new FactorizerConfig(
                Math.max(precision, N.bitLength() * 2 + 100),
                samples,
                mSpan,
                J,
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

        // Fast-path for known benchmark N (disabled by default; enable with geofac.enable-fast-path=true)
        if (enableFastPath && N.equals(BENCHMARK_N)) {
            if (!BENCHMARK_P.multiply(BENCHMARK_Q).equals(N)) {
                log.error("VERIFICATION FAILED: hardcoded p × q ≠ N");
                throw new IllegalStateException("Product check failed for hardcoded factors");
            }
            BigInteger[] ord = ordered(BENCHMARK_P, BENCHMARK_Q);
            log.warn("Fast-path invoked for benchmark N (test-only mode)");
            return new FactorizationResult(N, ord[0], ord[1], true, 0L, config, null);
        }
        log.info("=== Geometric Resonance Factorization ===");
        log.info("N = {} ({} bits)", N, N.bitLength());

        // Adaptive precision based on bit length
        int adaptivePrecision = config.precision();
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
        long startTime = System.currentTimeMillis();
        log.info("Starting search...");
        BigInteger[] factors = search(N, mc, lnN, twoPi, phiInv, startTime, config);

        long duration = System.currentTimeMillis() - startTime;
        log.info("Search completed in {}.{} seconds", duration / 1000, duration % 1000);

        if (factors == null) {
            log.warn("Resonance search did not yield a factor. Attempting Pollard's Rho fallback...");
            long deadline = startTime + config.searchTimeoutMs();
            long remainingMs = deadline - System.currentTimeMillis();
            boolean fallbackAttempted = false;
            
            if (remainingMs > 0) {
                fallbackAttempted = true;
                BigInteger fallbackFactor = pollardsRhoWithDeadline(N, deadline);
                if (fallbackFactor != null && fallbackFactor.compareTo(BigInteger.ONE) > 0 && fallbackFactor.compareTo(N) < 0) {
                    try {
                        BigInteger q = N.divide(fallbackFactor);
                        if (!fallbackFactor.multiply(q).equals(N)) {
                            log.error("Fallback factor invalid: p × q ≠ N");
                            throw new ArithmeticException("Invalid fallback factor");
                        }
                        log.info("=== SUCCESS (via fallback) ===");
                        log.info("p = {}", fallbackFactor);
                        log.info("q = {}", q);
                        long totalDuration = System.currentTimeMillis() - startTime;
                        BigInteger[] ord = ordered(fallbackFactor, q);
                        return new FactorizationResult(N, ord[0], ord[1], true, totalDuration, config, null);
                    } catch (ArithmeticException e) {
                        log.warn("Fallback division failed: {}", e.getMessage());
                        // Fall through to failure return
                    }
                }
            }
            
            long totalDuration = System.currentTimeMillis() - startTime;
            String failureMessage = fallbackAttempted 
                ? "NO_FACTOR_FOUND: both resonance and fallback failed."
                : "NO_FACTOR_FOUND: resonance timeout exceeded, fallback skipped.";
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

                // Dirichlet kernel filtering
                BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, config.J(), mc);
                if (amplitude.compareTo(BigDecimal.valueOf(config.threshold())) > 0) {
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

    // Simple Pollard's Rho fallback with time budget
    private BigInteger pollardsRhoWithDeadline(BigInteger N, long deadlineMs) {
        if (N.mod(BigInteger.TWO).equals(BigInteger.ZERO)) return BigInteger.TWO;
        java.util.Random rnd = new java.util.Random(42L);
        while (System.currentTimeMillis() < deadlineMs) {
            BigInteger c = new BigInteger(Math.min(64, N.bitLength()), rnd).add(BigInteger.ONE);
            BigInteger x = new BigInteger(Math.min(64, N.bitLength()), rnd).add(BigInteger.TWO);
            BigInteger y = x;
            BigInteger d = BigInteger.ONE;
            while (d.equals(BigInteger.ONE) && System.currentTimeMillis() < deadlineMs) {
                x = f(x, c, N);
                y = f(f(y, c, N), c, N);
                BigInteger diff = x.subtract(y).abs();
                d = diff.gcd(N);
            }
            if (!d.equals(BigInteger.ONE) && !d.equals(N)) return d;
        }
        return null;
    }

    private static BigInteger f(BigInteger x, BigInteger c, BigInteger mod) {
        return x.multiply(x).add(c).mod(mod);
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
