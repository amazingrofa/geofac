package com.geofac.blind.service;

import com.geofac.blind.model.Band;
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
        if (job == null) return null;
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

        List<Band> bands = scoreBands(job.getN(), maxIter);
        if (bands.isEmpty()) {
            job.markFailed("No viable bands produced by geofac scorer");
            log(job, "Stopped: no bands to scan");
            logStreamRegistry.close(job.getId());
            return;
        }

        log(job, "Generated " + bands.size() + " bands. Scanning with trial division...");

        for (Band band : bands) {
            if (Duration.between(start, Instant.now()).toMillis() > timeLimit) {
                job.markFailed("Time limit reached without factor");
                log(job, "Stopped: time limit exceeded before finishing bands");
                logStreamRegistry.close(job.getId());
                return;
            }
            log(job, "Band from scorer ('" + band.source() + "'): center=" + band.center()
                    + " width=" + band.end().subtract(band.start()) + " score=" + band.score());

            BigInteger candidate = scanBand(job, band, logEvery, maxIter, start, timeLimit);
            if (candidate != null) {
                BigInteger q = job.getN().divide(candidate);
                job.markCompleted(candidate, q);
                log(job, "Factor found via trial division inside band: p=" + candidate + " q=" + q);
                log(job, "Verification: p*q == N? " + candidate.multiply(q).equals(job.getN()));
                logStreamRegistry.close(job.getId());
                return;
            }
        }

        job.markFailed("Reached iteration budget without factor");
        log(job, "Stopped: all bands scanned, no factor");
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

    private List<Band> scoreBands(BigInteger n, int maxIter) {
        List<Band> bands = new ArrayList<>();

        // 1) Attempt Pollard Rho to get a high-confidence center
        BigInteger rhoHit = pollardRho(n, 2_000); // iteration cap inside
        if (rhoHit != null && !rhoHit.equals(BigInteger.ONE) && !rhoHit.equals(n)) {
            BigInteger start = rhoHit.subtract(BigInteger.valueOf(BAND_WIDTH_DIVISIONS)).max(BigInteger.TWO);
            BigInteger end = rhoHit.add(BigInteger.valueOf(BAND_WIDTH_DIVISIONS));
            bands.add(new Band(start, end, rhoHit, "pollard-rho", 1.0));
        }

        // 2) Heuristic bands around sqrt with expanding deltas
        BigInteger sqrt = BigIntMath.sqrtFloor(n);
        long[] deltas = {100_000L, 1_000_000L, 10_000_000L};
        double baseScore = 0.5;
        for (long d : deltas) {
            BigInteger delta = BigInteger.valueOf(d);
            BigInteger start = sqrt.subtract(delta).max(BigInteger.TWO);
            BigInteger end = sqrt.add(delta);
            bands.add(new Band(start, end, sqrt, "sqrt-band-" + d, baseScore));
            baseScore -= 0.05;
        }

        // 3) Random resonance probes: pick random multipliers, score by |N mod k|
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        for (int i = 0; i < 3; i++) {
            long k = rnd.nextLong(100_000L, 5_000_000L);
            BigInteger K = BigInteger.valueOf(k);
            BigInteger mod = n.mod(K);
            double score = 0.3 + (1.0 - mod.doubleValue() / k); // smaller mod → higher score
            BigInteger center = sqrt.add(BigInteger.valueOf(rnd.nextLong(-5_000_000L, 5_000_000L)));
            BigInteger width = BigInteger.valueOf(500_000L);
            BigInteger start = center.subtract(width);
            BigInteger end = center.add(width);
            bands.add(new Band(start.max(BigInteger.TWO), end, center, "resonance-k=" + k, score));
        }

        // keep top bands by score and limit to MAX_BANDS
        return bands.stream()
                .sorted(Comparator.comparingDouble(Band::score).reversed())
                .limit(MAX_BANDS)
                .toList();
    }

    private BigInteger scanBand(FactorJob job, Band band, int logEvery, int maxIter, Instant start, long timeLimit) {
        BigInteger width = band.end().subtract(band.start());
        BigInteger limit = band.start().add(width);
        BigInteger n = job.getN();
        int checked = 0;

        for (BigInteger candidate = band.start(); candidate.compareTo(limit) <= 0; candidate = candidate.add(BigInteger.ONE)) {
            if (Duration.between(start, Instant.now()).toMillis() > timeLimit) {
                log(job, "Band scan stopped: time limit");
                return null;
            }
            if (checked >= maxIter) {
                log(job, "Band scan stopped: iteration budget for band reached");
                return null;
            }
            if (n.mod(candidate).equals(BigInteger.ZERO)) {
                return candidate;
            }
            checked++;
            if (checked % logEvery == 0) {
                log(job, "Band '" + band.source() + "' checked " + checked + " candidates; latest=" + candidate);
            }
        }
        return null;
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

    public record SseSnapshot(JobStatus status, java.util.List<String> logs) {}
}
