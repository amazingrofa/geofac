package com.geofac.blind.model;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedDeque;

public class FactorJob {
    private static final int MAX_LOG_HISTORY = 5000;
    private final UUID id;
    private final BigInteger n;
    private volatile JobStatus status;
    private final Instant createdAt;
    private volatile Instant completedAt;
    private volatile BigInteger foundP;
    private volatile BigInteger foundQ;
    private final ConcurrentLinkedDeque<String> logs = new ConcurrentLinkedDeque<>();
    private volatile List<Candidate> topCandidates = Collections.emptyList();

    public FactorJob(UUID id, BigInteger n) {
        this.id = id;
        this.n = n;
        this.status = JobStatus.QUEUED;
        this.createdAt = Instant.now();
    }

    public UUID getId() {
        return id;
    }

    public BigInteger getN() {
        return n;
    }

    public JobStatus getStatus() {
        return status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getCompletedAt() {
        return completedAt;
    }

    public BigInteger getFoundP() {
        return foundP;
    }

    public BigInteger getFoundQ() {
        return foundQ;
    }

    public List<Candidate> getTopCandidates() {
        return topCandidates;
    }

    public void setTopCandidates(List<Candidate> candidates) {
        this.topCandidates = candidates;
    }

    public List<String> getLogsSnapshot() {
        return Collections.unmodifiableList(new ArrayList<>(logs));
    }

    public void appendLog(String line) {
        logs.add(line);
        while (logs.size() > MAX_LOG_HISTORY) {
            logs.pollFirst();
        }
    }

    public void markRunning() {
        this.status = JobStatus.RUNNING;
    }

    public void markCompleted(BigInteger p, BigInteger q) {
        this.status = JobStatus.COMPLETED;
        this.foundP = p;
        this.foundQ = q;
        this.completedAt = Instant.now();
    }

    public void markFailed(String reason) {
        appendLog("FAILED: " + reason);
        this.status = JobStatus.FAILED;
        this.completedAt = Instant.now();
    }

    public void markCancelled() {
        this.status = JobStatus.CANCELLED;
        this.completedAt = Instant.now();
    }
}
