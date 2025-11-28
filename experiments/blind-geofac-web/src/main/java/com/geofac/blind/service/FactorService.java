package com.geofac.blind.service;

import com.geofac.blind.model.Candidate;
import com.geofac.blind.model.FactorJob;
import com.geofac.blind.model.FactorRequest;
import com.geofac.blind.model.JobStatus;
import com.geofac.blind.util.BigIntMath;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.stereotype.Service;

import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

@Service
public class FactorService implements AutoCloseable, DisposableBean {
    public static final String DEFAULT_N = "137524771864208156028430259349934309717";
    private static final int DEFAULT_MAX_ITER = 500_000;
    private static final long DEFAULT_TIME_LIMIT_MS = Duration.ofMinutes(2).toMillis();
    private static final int DEFAULT_LOG_EVERY = 1_000;
    private static final int MAX_BANDS = 6;
    private static final int BAND_WIDTH_DIVISIONS = 10_000; // half-width for trial division around center

    private final Map<UUID, FactorJob> jobs = new ConcurrentHashMap<>();
    private final LogStreamRegistry logStreamRegistry;
    private final ThreadPoolTaskExecutor executor;

    public FactorService(LogStreamRegistry logStreamRegistry) {
        this.logStreamRegistry = logStreamRegistry;
        this.executor = new ThreadPoolTaskExecutor();
        this.executor.setCorePoolSize(2);
        this.executor.setMaxPoolSize(4);
        this.executor.setThreadNamePrefix("factor-");
        this.executor.initialize();
    }

    public UUID startJob(FactorRequest request) {
        BigInteger n = new BigInteger(request.nOrDefault(DEFAULT_N));
        FactorJob job = new FactorJob(UUID.randomUUID(), n);
        jobs.put(job.getId(), job);
        executor.submit(() -> runBlindGeofac(job, request));
        return job.getId();
    }

    public FactorJob getJob(UUID jobId) {
        return jobs.get(jobId);
    }

    public SseSnapshot logsSnapshot(UUID jobId) {
        FactorJob job = jobs.get(jobId);
        if (job == null)
            return null;
        return new SseSnapshot(job.getStatus(), job.getLogsSnapshot());
    }

    private void runBlindGeofac(FactorJob job, FactorRequest request) {
        job.markRunning();
        int logEvery = request.logEveryOrDefault(DEFAULT_LOG_EVERY);
        int maxIter = request.maxIterationsOrDefault(DEFAULT_MAX_ITER);
        long timeLimit = request.timeLimitOrDefault(DEFAULT_TIME_LIMIT_MS);
        Instant start = Instant.now();

        log(job, "Starting blind geofac on N=" + job.getN());
        log(job, "Bit length: " + job.getN().bitLength());

        List<Candidate> top = scoreBands(job.getN(), maxIter);
        job.setTopCandidates(top);
        log(job, "Generated " + top.size() + " top candidates via GeoFac resonance.");

        int checked = 0;
        for (Candidate cand : top) {
            if (Duration.between(start, Instant.now()).toMillis() > timeLimit) {
                job.markFailed("Time limit reached without factor");
                log(job, "Stopped: time limit exceeded");
                logStreamRegistry.close(job.getId());
                return;
            }

            if (checked >= maxIter) {
                job.markFailed("Reached iteration budget without factor");
                log(job, "Stopped: iteration budget reached");
                logStreamRegistry.close(job.getId());
                return;
            }

            if (job.getN().mod(cand.d()).equals(BigInteger.ZERO)) {
                BigInteger q = job.getN().divide(cand.d());
                job.markCompleted(cand.d(), q);
                log(job, "Factor found at rank " + (checked + 1) + ": p=" + cand.d() + " q=" + q + " (score="
                        + cand.score() + ")");
                logStreamRegistry.close(job.getId());
                return;
            }

            checked++;
            if (checked % logEvery == 0) {
                log(job, "Checked rank " + checked + ": d=" + cand.d() + " score=" + cand.score());
            }
        }

        job.markFailed("No factor in top candidates");
        log(job, "Stopped: all candidates scanned, no factor");
        logStreamRegistry.close(job.getId());
    }

    private void log(FactorJob job, String line) {
        String stamped = Instant.now() + " | " + line;
        job.appendLog(stamped);
        logStreamRegistry.send(job.getId(), stamped);
    }

    @Override
    public void close() {
        shutdownExecutor();
    }

    @Override
    public void destroy() {
        shutdownExecutor();
    }

    private void shutdownExecutor() {
        executor.shutdown();
        try {
            if (!executor.getThreadPoolExecutor().awaitTermination(5, TimeUnit.SECONDS)) {
                executor.getThreadPoolExecutor().shutdownNow();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            executor.getThreadPoolExecutor().shutdownNow();
        }
    }

    private List<Candidate> scoreBands(BigInteger n, int maxIter) {
        BigInteger sqrtN = BigIntMath.sqrtFloor(n);
        double[] basePhases = BigIntMath.zNormalize(n, sqrtN); // Approx {θ_p, θ_q}
        List<Candidate> candidates = new ArrayList<>();
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        int numProbes = Math.min(1000, maxIter / 10);

        for (int i = 0; i < numProbes; i++) {
            double thetaX = rnd.nextDouble(0, 2 * Math.PI);
            double thetaY = rnd.nextDouble(0, 2 * Math.PI);

            for (int t = 0; t < 50; t++) { // Orbit: Ergodic flow
                thetaX = (thetaX + Math.sqrt(2) * (t + 1)) % (2 * Math.PI); // Irrational rotation
                thetaY = (thetaY + Math.PI * (t + 1)) % (2 * Math.PI);

                // Φ: Phase to offset
                // Map phase [-PI, PI] to offset width.
                // We want to map thetaX to an offset from sqrtN.
                // Let's treat thetaX as a normalized position in a "window" around sqrtN.
                // Window size = 2e6, or smaller if sqrtN is small
                long window = 1_000_000L;
                if (sqrtN.bitLength() < 30) { // Small N
                    window = Math.max(10, sqrtN.longValue());
                }
                long offset = Math.round((thetaX - Math.PI) * window / Math.PI);

                BigInteger d = sqrtN.add(BigInteger.valueOf(offset)).max(BigInteger.TWO)
                        .min(n.subtract(BigInteger.ONE));

                if (d.compareTo(BigInteger.TWO) > 0 && !d.testBit(0)) {
                    continue; // Skip evens
                }

                double resScore = BigIntMath.resonanceScore(n, d);
                double geoBonus = 1 - Math.abs(Math.sin(thetaX - basePhases[0] * 2 * Math.PI)); // Align to θ_p
                double score = resScore * (0.7 + 0.3 * geoBonus);

                candidates.add(new Candidate(d, score, "orbit-" + i + "-t" + t));
            }
        }

        return candidates.stream()
                .sorted(Comparator.comparingDouble(Candidate::score).reversed())
                .limit(20)
                .toList(); // Top m=20
    }

    // Lightweight Pollard Rho (Brent variant) to suggest a narrow band
    private BigInteger pollardRho(BigInteger n, int iterations) {
        if (n.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
            return BigInteger.TWO;
        }
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        BigInteger c = new BigInteger(n.bitLength(), rnd).mod(n);
        if (c.equals(BigInteger.ZERO)) {
            c = BigInteger.ONE;
        }
        BigInteger x = new BigInteger(n.bitLength(), rnd).mod(n);
        BigInteger y = x;
        BigInteger d = BigInteger.ONE;

        for (int i = 0; i < iterations && d.equals(BigInteger.ONE); i++) {
            x = f(x, c, n);
            y = f(f(y, c, n), c, n);
            d = x.subtract(y).abs().gcd(n);
        }
        if (d.equals(n) || d.equals(BigInteger.ONE)) {
            return null;
        }
        return d;
    }

    private BigInteger f(BigInteger x, BigInteger c, BigInteger n) {
        return x.multiply(x).add(c).mod(n);
    }

    public record SseSnapshot(JobStatus status, java.util.List<String> logs) {
    }
}
