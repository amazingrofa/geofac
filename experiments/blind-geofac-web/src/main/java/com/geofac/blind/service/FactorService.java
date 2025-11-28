package com.geofac.blind.service;

import com.geofac.blind.engine.FactorizationResult;
import com.geofac.blind.engine.FactorizerService;
import com.geofac.blind.model.FactorJob;
import com.geofac.blind.model.FactorRequest;
import com.geofac.blind.model.JobStatus;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.stereotype.Service;

import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

@Service
public class FactorService implements AutoCloseable, DisposableBean {
    public static final String DEFAULT_N = "137524771864208156028430259349934309717";
    private static final long DEFAULT_TIME_LIMIT_MS = Duration.ofMinutes(20).toMillis();
    private static final int DEFAULT_LOG_EVERY = 500;

    private final Map<UUID, FactorJob> jobs = new ConcurrentHashMap<>();
    private final LogStreamRegistry logStreamRegistry;
    private final ThreadPoolTaskExecutor executor;
    private final FactorizerService factorizerService;

    public FactorService(LogStreamRegistry logStreamRegistry, FactorizerService factorizerService) {
        this.logStreamRegistry = logStreamRegistry;
        this.factorizerService = factorizerService;
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

    public Map<String, Object> currentSettings() {
        return factorizerService.currentSettings();
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
        long timeLimit = request.timeLimitOrDefault(DEFAULT_TIME_LIMIT_MS);
        Instant start = Instant.now();

        log(job, "Starting blind geofac on N=" + job.getN());
        log(job, "Bit length: " + job.getN().bitLength());
        log(job, "Delegating to geometric resonance engine (aligned with main repo)");

        FactorizationResult result = factorizerService.factor(job.getN());

        if (Duration.between(start, Instant.now()).toMillis() > timeLimit) {
            job.markFailed("Time limit reached without factor");
            log(job, "Stopped: time limit exceeded");
            logStreamRegistry.close(job.getId());
            return;
        }

        if (result.success()) {
            job.markCompleted(result.p(), result.q());
            log(job, "Factor found: p=" + result.p() + " q=" + result.q() + " duration=" + result.durationMs() + "ms");
            logStreamRegistry.close(job.getId());
        } else {
            job.markFailed(result.errorMessage() != null ? result.errorMessage() : "No factor found");
            log(job, "Geometric engine returned no factor; duration=" + result.durationMs() + "ms");
            logStreamRegistry.close(job.getId());
        }
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

    public record SseSnapshot(JobStatus status, java.util.List<String> logs) {
    }
}
