package com.geofac.blind.model;

public record FactorRequest(
        String n,
        Integer maxIterations,
        Long timeLimitMillis,
        Integer logEvery
) {
    public String nOrDefault(String fallback) {
        return (n == null || n.isBlank()) ? fallback : n;
    }

    public int maxIterationsOrDefault(int fallback) {
        return (maxIterations == null || maxIterations <= 0) ? fallback : maxIterations;
    }

    public long timeLimitOrDefault(long fallback) {
        return (timeLimitMillis == null || timeLimitMillis <= 0) ? fallback : timeLimitMillis;
    }

    public int logEveryOrDefault(int fallback) {
        return (logEvery == null || logEvery <= 0) ? fallback : logEvery;
    }
}
