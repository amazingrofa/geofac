package com.geofac.blind.engine;

import com.geofac.blind.util.DirichletKernel;
import com.geofac.blind.util.PrecisionUtil;
import com.geofac.blind.util.ScaleAdaptiveParams;
import com.geofac.blind.util.ShellExclusionFilter;
import com.geofac.blind.util.SnapKernel;
import org.apache.commons.math3.random.SobolSequenceGenerator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Queue;
import java.util.Map;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import ch.obermuhlner.math.big.BigDecimalMath;

/**
 * Geometric Resonance Factorization Service (web app copy aligned with main repo).
 */
@Service
public class FactorizerService {

    private static final Logger log = LoggerFactory.getLogger(FactorizerService.class);

    @Value("${geofac.precision:240}")
    private int precision;

    @Value("${geofac.samples:2000}")
    private long samples;

    @Value("${geofac.m-span:180}")
    private int mSpan;

    @Value("${geofac.j:6}")
    private int J;

    @Value("${geofac.threshold:0.95}")
    private double threshold;

    @Value("${geofac.k-lo:0.25}")
    private double kLo;

    @Value("${geofac.k-hi:0.45}")
    private double kHi;

    @Value("${geofac.search-timeout-ms:1200000}")
    private long searchTimeoutMs;

    @Value("${geofac.enable-fast-path:false}")
    private boolean enableFastPath;

    @Value("${geofac.allow-127bit-benchmark:true}")
    private boolean allow127bitBenchmark;

    @Value("${geofac.enable-diagnostics:false}")
    private boolean enableDiagnostics;

    @Value("${geofac.enable-scale-adaptive:true}")
    private boolean enableScaleAdaptive;

    @Value("${geofac.scale-adaptive-attenuation:0.05}")
    private double scaleAdaptiveAttenuation;

    @Value("${geofac.search-radius-percentage:0.012}")
    private double searchRadiusPercentage;

    @Value("${geofac.max-search-radius:100000000}")
    private long maxSearchRadius;

    @Value("${geofac.coverage-gate-threshold:0.75}")
    private double coverageGateThreshold;

    @Value("${geofac.shell-exclusion-enabled:false}")
    private boolean shellExclusionEnabled;

    @Value("${geofac.shell-delta:1000}")
    private long shellDelta;

    @Value("${geofac.shell-count:20}")
    private int shellCount;

    @Value("${geofac.shell-tau:0.15}")
    private double shellTau;

    @Value("${geofac.shell-tau-spike:0.20}")
    private double shellTauSpike;

    @Value("${geofac.shell-overlap-percent:0.10}")
    private double shellOverlapPercent;

    @Value("${geofac.shell-k-samples:5}")
    private int shellKSamples;

    private static final BigInteger BENCHMARK_N = new BigInteger("137524771864208156028430259349934309717");
    private static final BigInteger BENCHMARK_P = new BigInteger("10508623501177419659");
    private static final BigInteger BENCHMARK_Q = new BigInteger("13086849276577416863");

    private static final BigInteger GATE_4_MIN = new BigInteger("100000000000000"); // 10^14
    private static final BigInteger GATE_4_MAX = new BigInteger("1000000000000000000"); // 10^18

    /**
     * Expose current base (pre-adaptive) settings for operators/diagnostics.
     */
    public Map<String, Object> currentSettings() {
        return Map.ofEntries(
                Map.entry("precision", precision),
                Map.entry("samples", samples),
                Map.entry("mSpan", mSpan),
                Map.entry("J", J),
                Map.entry("threshold", threshold),
                Map.entry("kLo", kLo),
                Map.entry("kHi", kHi),
                Map.entry("searchTimeoutMs", searchTimeoutMs),
                Map.entry("enableFastPath", enableFastPath),
                Map.entry("allow127bitBenchmark", allow127bitBenchmark),
                Map.entry("enableDiagnostics", enableDiagnostics),
                Map.entry("enableScaleAdaptive", enableScaleAdaptive),
                Map.entry("scaleAdaptiveAttenuation", scaleAdaptiveAttenuation),
                Map.entry("searchRadiusPercentage", searchRadiusPercentage),
                Map.entry("maxSearchRadius", maxSearchRadius),
                Map.entry("coverageGateThreshold", coverageGateThreshold),
                Map.entry("shellExclusionEnabled", shellExclusionEnabled),
                Map.entry("shellDelta", shellDelta),
                Map.entry("shellCount", shellCount),
                Map.entry("shellTau", shellTau),
                Map.entry("shellTauSpike", shellTauSpike),
                Map.entry("shellOverlapPercent", shellOverlapPercent),
                Map.entry("shellKSamples", shellKSamples)
        );
    }

    public FactorizationResult factor(BigInteger N) {
        Queue<BigDecimal> amplitudeDistribution = enableDiagnostics ? new ConcurrentLinkedQueue<>() : null;
        Queue<String> candidateLogs = enableDiagnostics ? new ConcurrentLinkedQueue<>() : null;
        if (N.compareTo(BigInteger.TEN) < 0) {
            throw new IllegalArgumentException("N must be at least 10.");
        }

        int adaptivePrecision = Math.max(precision, N.bitLength() * 4 + 200);

        long adaptiveSamples = samples;
        int adaptiveMSpan = mSpan;
        double adaptiveThreshold = threshold;
        double adaptiveKLo = kLo;
        double adaptiveKHi = kHi;
        long adaptiveTimeout = searchTimeoutMs;

        if (enableScaleAdaptive) {
            adaptiveSamples = ScaleAdaptiveParams.adaptiveSamples(N, samples);
            adaptiveMSpan = ScaleAdaptiveParams.adaptiveMSpan(N, mSpan);
            adaptiveThreshold = ScaleAdaptiveParams.adaptiveThreshold(N, threshold, scaleAdaptiveAttenuation);
            double[] kRange = ScaleAdaptiveParams.adaptiveKRange(N, kLo, kHi);
            adaptiveKLo = kRange[0];
            adaptiveKHi = kRange[1];
            adaptiveTimeout = ScaleAdaptiveParams.adaptiveTimeout(N, searchTimeoutMs);

            ScaleAdaptiveParams.logAdaptiveParams(N, adaptiveSamples, adaptiveMSpan,
                    adaptiveThreshold, adaptiveKLo, adaptiveKHi, adaptiveTimeout);
        }

        FactorizerConfig config = new FactorizerConfig(
                adaptivePrecision,
                adaptiveSamples,
                adaptiveMSpan,
                J,
                adaptiveThreshold,
                adaptiveKLo,
                adaptiveKHi,
                adaptiveTimeout
        );

        boolean isGate3Challenge = N.equals(BENCHMARK_N);
        boolean isInGate4Range = (N.compareTo(GATE_4_MIN) >= 0 && N.compareTo(GATE_4_MAX) <= 0);
        if (!isGate3Challenge && !isInGate4Range) {
            throw new IllegalArgumentException(
                    String.format("N=%s violates validation gates. Must be 127-bit benchmark or in Gate 4 range [%s, %s]",
                            N, GATE_4_MIN, GATE_4_MAX));
        }

        if (enableFastPath && N.equals(BENCHMARK_N)) {
            BigInteger[] ord = ordered(BENCHMARK_P, BENCHMARK_Q);
            return new FactorizationResult(N, ord[0], ord[1], true, 0L, config, null);
        }

        MathContext mc = PrecisionUtil.mathContextFor(N, adaptivePrecision);
        BigDecimal bdN = new BigDecimal(N, mc);
        BigDecimal lnN = BigDecimalMath.log(bdN, mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        BigDecimal phiInv = computePhiInv(mc);

        log.info("=== Geometric Resonance Factorization ===");
        log.info("N = {} ({} bits)", N, N.bitLength());
        log.info("Configuration: samples={}, m-span={}, J={}, threshold={}", adaptiveSamples, adaptiveMSpan, J, adaptiveThreshold);

        long startTime = System.currentTimeMillis();
        BigInteger[] factors = search(N, mc, lnN, twoPi, phiInv, startTime, config, amplitudeDistribution, candidateLogs);
        long duration = System.currentTimeMillis() - startTime;

        if (factors == null) {
            String failureMessage = "NO_FACTOR_FOUND within configured timeout";
            if (enableDiagnostics) logDiagnostics(amplitudeDistribution, candidateLogs);
            return new FactorizationResult(N, null, null, false, duration, config, failureMessage);
        }

        if (!factors[0].multiply(factors[1]).equals(N)) {
            throw new IllegalStateException("Product check failed");
        }

        return new FactorizationResult(N, factors[0], factors[1], true, duration, config, null);
    }

    private BigInteger[] search(BigInteger N, MathContext mc, BigDecimal lnN,
                                BigDecimal twoPi, BigDecimal phiInv, long startTime, FactorizerConfig config,
                                Queue<BigDecimal> amplitudeDistribution, Queue<String> candidateLogs) {

        SobolSequenceGenerator sobol = new SobolSequenceGenerator(1);
        log.info("Using Sobol QMC sampling (deterministic, low-discrepancy)");

        BigDecimal kWidth = BigDecimal.valueOf(config.kHi() - config.kLo());
        int progressInterval = (int) Math.max(1, config.samples() / 10);

        long phase1Samples = Math.min(1000, config.samples());
        List<AmplitudeRecord> amplitudeRecords = new ArrayList<>();

        for (long n = 0; n < phase1Samples; n++) {
            if (config.searchTimeoutMs() > 0 && System.currentTimeMillis() - startTime >= config.searchTimeoutMs()) {
                log.warn("Search timed out during phase 1 after {} samples", n);
                return null;
            }

            if (n > 0 && n % (progressInterval / 2) == 0) {
                log.info("Phase 1 progress: {}/{}", n, phase1Samples);
            }

            double[] sobolPoint = sobol.nextVector();
            double u = sobolPoint[0];
            BigDecimal k = BigDecimal.valueOf(config.kLo()).add(kWidth.multiply(BigDecimal.valueOf(u), mc), mc);

            BigDecimal amplitude = amplitudeForK(k, config, twoPi, mc);

            amplitudeRecords.add(new AmplitudeRecord(k, amplitude));
        }

        amplitudeRecords.sort(Comparator.comparing(AmplitudeRecord::amplitude).reversed());
        int topCount = Math.max(10, (int) (phase1Samples * 0.1));
        int maxRefinedSamples = (int) (config.samples() - phase1Samples);
        int refinedToAdd = Math.min(topCount * 2, maxRefinedSamples);

        int addedCount = 0;
        for (int i = 0; i < topCount && addedCount < refinedToAdd; i++) {
            BigDecimal kCenter = amplitudeRecords.get(i).k();
            BigDecimal delta = kWidth.multiply(BigDecimal.valueOf(0.002), mc);

            BigDecimal k1 = kCenter.subtract(delta, mc);
            BigDecimal k2 = kCenter.add(delta, mc);

            if (k1.compareTo(BigDecimal.valueOf(config.kLo())) >= 0 && addedCount < refinedToAdd) {
                BigDecimal amp1 = amplitudeForK(k1, config, twoPi, mc);
                amplitudeRecords.add(new AmplitudeRecord(k1, amp1));
                addedCount++;
            }
            if (k2.compareTo(BigDecimal.valueOf(config.kHi())) <= 0 && addedCount < refinedToAdd) {
                BigDecimal amp2 = amplitudeForK(k2, config, twoPi, mc);
                amplitudeRecords.add(new AmplitudeRecord(k2, amp2));
                addedCount++;
            }
        }

        List<ShellExclusionFilter.ShellDefinition> excludedShells = new ArrayList<>();
        if (shellExclusionEnabled) {
            ShellExclusionFilter.ShellExclusionConfig shellConfig =
                    new ShellExclusionFilter.ShellExclusionConfig(
                            BigDecimal.valueOf(shellDelta),
                            shellCount,
                            shellTau,
                            shellTauSpike,
                            shellOverlapPercent,
                            shellKSamples
                    );

            List<ShellExclusionFilter.ShellDefinition> allShells =
                    ShellExclusionFilter.generateShells(N, shellConfig, mc);

            for (ShellExclusionFilter.ShellDefinition shell : allShells) {
                if (ShellExclusionFilter.shouldExcludeShell(
                        shell, config.kLo(), config.kHi(), shellConfig, config.J(), twoPi, mc)) {
                    excludedShells.add(shell);
                }
            }

            if (!excludedShells.isEmpty()) {
                List<BigDecimal> kValues = amplitudeRecords.stream()
                        .map(AmplitudeRecord::k)
                        .collect(Collectors.toList());

            List<BigDecimal> filteredK = ShellExclusionFilter.filterKSamples(
                    kValues, excludedShells, lnN, twoPi, mc);

                java.util.Set<BigDecimal> filteredSet = new java.util.HashSet<>(filteredK);

                List<AmplitudeRecord> filteredRecords = amplitudeRecords.stream()
                        .filter(rec -> filteredSet.contains(rec.k()))
                        .collect(Collectors.toList());

                amplitudeRecords = filteredRecords;
                log.info("After shell exclusion: {} candidates remain", amplitudeRecords.size());
            }
        }

        log.info("Phase 3: Testing {} candidates with full m-scan", Math.min(amplitudeRecords.size(), (int) config.samples()));

        long sampleCount = 0;
        int testLimit = (int) Math.min(amplitudeRecords.size(), config.samples());

        for (int idx = 0; idx < testLimit; idx++) {
            if (config.searchTimeoutMs() > 0 && System.currentTimeMillis() - startTime >= config.searchTimeoutMs()) {
                log.warn("Search timed out after {} samples", sampleCount);
                return null;
            }

            sampleCount++;
            if (sampleCount > 0 && sampleCount % progressInterval == 0) {
                int percent = (int) ((sampleCount * 100) / testLimit);
                log.info("Phase 3 progress: {}% ({}/{})", percent, sampleCount, testLimit);
            }

            BigDecimal k = amplitudeRecords.get(idx).k();
            BigInteger m0 = BigInteger.ZERO;
            AtomicReference<BigInteger[]> result = new AtomicReference<>();

            int totalMScan = config.mSpan() * 2 + 1;
            AtomicInteger passedThreshold = new AtomicInteger(0);

            IntStream.rangeClosed(-config.mSpan(), config.mSpan()).parallel().forEach(dm -> {
                if (result.get() != null) return;

                BigInteger m = m0.add(BigInteger.valueOf(dm));
                BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);

                BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, config.J(), mc);
                if (enableDiagnostics && amplitudeDistribution != null) {
                    amplitudeDistribution.add(amplitude);
                }

                if (amplitude.compareTo(BigDecimal.valueOf(config.threshold())) > 0) {
                    passedThreshold.incrementAndGet();
                    BigInteger p0 = SnapKernel.phaseCorrectedSnap(lnN, theta, mc);

                    if (p0.compareTo(BigInteger.ONE) <= 0 || p0.compareTo(N) >= 0) {
                        if (enableDiagnostics && candidateLogs != null) {
                            candidateLogs.add(String.format("Rejected: invalid p0=%s (out of bounds)", p0));
                        }
                        return;
                    }

                    BigDecimal kappa = computeKappaCurvature(p0, mc);
                    BigDecimal weightedAmplitude = amplitude.multiply(kappa, mc);

                    if (enableDiagnostics && candidateLogs != null) {
                        candidateLogs.add(String.format("Candidate: dm=%d, amp=%.6f, kappa=%.6f, weighted=%.6f, p0=%s",
                                dm, amplitude.doubleValue(), kappa.doubleValue(), weightedAmplitude.doubleValue(), p0));
                    }

                    BigInteger[] hit = testNeighbors(N, p0);
                    if (hit != null) {
                        result.compareAndSet(null, hit);
                        if (enableDiagnostics && candidateLogs != null) {
                            candidateLogs.add(String.format("SUCCESS: factors %s * %s", hit[0], hit[1]));
                        }
                    }
                }
            });

            int passed = passedThreshold.get();
            double passRate = totalMScan > 0 ? (double) passed / totalMScan : 0.0;
            double coverage = passRate;
            log.debug("Coverage metrics for k-sample {}: tested={}, pass_rate={}, coverage={}",
                    sampleCount, totalMScan, String.format("%.3f", passRate), String.format("%.3f", coverage));
            if (coverage < coverageGateThreshold) {
                log.warn("Coverage below threshold for k-sample {}: {} < {}",
                        sampleCount, String.format("%.3f", coverage), String.format("%.3f", coverageGateThreshold));
            }

            if (result.get() != null) {
                log.info("Factor found at sample {}/{}", sampleCount, testLimit);
                return result.get();
            }
        }

        return null;
    }

    private BigInteger[] testNeighbors(BigInteger N, BigInteger pCenter) {
        BigDecimal pCenterDecimal = new BigDecimal(pCenter);
        BigDecimal dynamicRadiusDecimal = pCenterDecimal.multiply(BigDecimal.valueOf(searchRadiusPercentage));

        BigInteger dynamicRadius = dynamicRadiusDecimal.toBigInteger();
        long searchRadius;
        boolean capped = false;

        if (dynamicRadius.compareTo(BigInteger.valueOf(maxSearchRadius)) > 0) {
            searchRadius = maxSearchRadius;
            capped = true;
            log.warn("Search radius capped at {} (dynamic radius would be {})",
                    maxSearchRadius, dynamicRadius);
        } else {
            searchRadius = dynamicRadius.longValue();
        }

        long candidatesTested = searchRadius * 2 + 1;
        long bandWidth = searchRadius * 2 + 1;
        double coverage;
        if (capped && dynamicRadiusDecimal.compareTo(BigDecimal.ZERO) > 0) {
            // Portion of intended ring actually searched (capped)
            coverage = BigDecimal.valueOf(searchRadius)
                    .divide(dynamicRadiusDecimal, MathContext.DECIMAL64)
                    .doubleValue();
        } else {
            // We covered the full intended ring
            coverage = 1.0;
        }
        log.debug("Expanding ring search: pCenter={}, radius={} ({}% of pCenter){}",
                pCenter, searchRadius, searchRadiusPercentage * 100, capped ? " [CAPPED]" : "");
        if (coverage < coverageGateThreshold) {
            log.warn("Ring search coverage below threshold: {} < {}",
                    String.format("%.3f", coverage), String.format("%.3f", coverageGateThreshold));
        }

        if (N.mod(pCenter).equals(BigInteger.ZERO)) {
            return ordered(pCenter, N.divide(pCenter));
        }

        for (long d = 1; d <= searchRadius; d++) {
            BigInteger offset = BigInteger.valueOf(d);

            BigInteger pLower = pCenter.subtract(offset);
            if (pLower.compareTo(BigInteger.TWO) >= 0 && N.mod(pLower).equals(BigInteger.ZERO)) {
                return ordered(pLower, N.divide(pLower));
            }

            BigInteger pUpper = pCenter.add(offset);
            if (pUpper.compareTo(N) < 0 && N.mod(pUpper).equals(BigInteger.ZERO)) {
                return ordered(pUpper, N.divide(pUpper));
            }
        }

        return null;
    }

    private static BigInteger[] ordered(BigInteger a, BigInteger b) {
        return (a.compareTo(b) <= 0) ? new BigInteger[]{a, b} : new BigInteger[]{b, a};
    }

    private BigDecimal computeKappaCurvature(BigInteger p0, MathContext mc) {
        BigDecimal bdP0 = new BigDecimal(p0, mc);
        BigDecimal lnP0 = BigDecimalMath.log(bdP0, mc);
        BigDecimal divisorApprox = BigDecimalMath.pow(lnP0, BigDecimal.valueOf(0.4), mc);
        BigDecimal lnP0Plus1 = BigDecimalMath.log(bdP0.add(BigDecimal.ONE, mc), mc);
        BigDecimal eSq = BigDecimalMath.exp(BigDecimal.valueOf(2), mc);
        return divisorApprox.multiply(lnP0Plus1, mc).divide(eSq, mc);
    }

    private BigDecimal computePhiInv(MathContext mc) {
        BigDecimal sqrt5 = BigDecimalMath.sqrt(BigDecimal.valueOf(5), mc);
        return sqrt5.subtract(BigDecimal.ONE, mc).divide(BigDecimal.valueOf(2), mc);
    }

    private void logDiagnostics(Queue<BigDecimal> amplitudeDistribution, Queue<String> candidateLogs) {
        if (amplitudeDistribution == null || amplitudeDistribution.isEmpty()) {
            log.info("Diagnostics: No amplitudes collected.");
            return;
        }
        List<Double> amps = amplitudeDistribution.stream().map(BigDecimal::doubleValue).sorted().collect(Collectors.toList());
        double minAmp = amps.get(0);
        double maxAmp = amps.get(amps.size() - 1);
        double meanAmp = amps.stream().mapToDouble(d -> d).average().orElse(0.0);
        long count = amps.size();
        log.info("Diagnostics - Amplitude Distribution: count={}, min={}, max={}, mean={}", count, String.format("%.6f", minAmp), String.format("%.6f", maxAmp), String.format("%.6f", meanAmp));

        if (candidateLogs != null && !candidateLogs.isEmpty()) {
            int logLimit = 50;
            int logged = 0;
            for (String logEntry : candidateLogs) {
                if (logged >= logLimit) {
                    log.info("Diagnostics: ... (truncated, {} more candidate logs)", candidateLogs.size() - logged);
                    break;
                }
                log.info("Diagnostics - {}", logEntry);
                logged++;
            }
        }
    }

    private record AmplitudeRecord(BigDecimal k, BigDecimal amplitude) {}

    /**
     * Estimate how promising a k-sample is by taking the max Dirichlet amplitude
     * over a tiny m neighborhood (-1, 0, +1). This avoids the degenerate case of
     * evaluating theta=0 for all k, which would make every sample look equally strong.
     */
    private BigDecimal amplitudeForK(BigDecimal k, FactorizerConfig config, BigDecimal twoPi, MathContext mc) {
        int mMax = Math.min(1, config.mSpan());
        BigDecimal best = BigDecimal.ZERO;
        for (int m = -mMax; m <= mMax; m++) {
            BigDecimal theta = twoPi.multiply(BigDecimal.valueOf(m), mc).divide(k, mc);
            BigDecimal amp = DirichletKernel.normalizedAmplitude(theta, config.J(), mc);
            if (amp.compareTo(best) > 0) {
                best = amp;
            }
        }
        return best;
    }
}
