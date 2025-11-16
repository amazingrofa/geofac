package com.geofac.validation;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.geofac.FactorizerConfig;
import com.geofac.FactorizerService;
import com.geofac.FactorizationResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * Internal record for benchmark run data to avoid race conditions in logging.
 */
record BenchmarkRun(
    SemiprimeGenerator.Semiprime semiprime,
    ValidationBenchmark.ParamConfig paramConfig,
    BenchmarkResult result
) {}

/**
 * Validation benchmark service for systematic testing of geometric resonance factorization.
 * 
 * Runs parameter sweeps against known semiprimes in [1e14, 1e18] range.
 * Exports reproducible artifacts: CSV and JSON results with full config and timing.
 * 
 * Per repository rules:
 * - Tests only in Gate 2 validation window [1e14, 1e18]
 * - Pins seeds and logs all parameters
 * - No classical fallbacks
 * - Exports artifacts for reproducibility
 */
@Service
public class ValidationBenchmark {
    
    private static final Logger log = LoggerFactory.getLogger(ValidationBenchmark.class);
    
    @Autowired
    private FactorizerService factorizerService;
    
    private final ObjectMapper objectMapper = new ObjectMapper()
        .enable(SerializationFeature.INDENT_OUTPUT);
    
    // Cache for reusing computation results (memoization)
    private final Map<String, BenchmarkResult> resultCache = new ConcurrentHashMap<>();
    
    /**
     * Represents a parameter configuration for sweeping.
     */
    public record ParamConfig(
        int precision,
        long samples,
        int mSpan,
        int J,
        double threshold,
        double kLo,
        double kHi
    ) {}
    
    /**
     * Clear the result cache. Use this when starting a new sweep session
     * to ensure fresh computations rather than cached results.
     */
    public void clearCache() {
        resultCache.clear();
        log.info("Result cache cleared");
    }
    
    /**
     * Get current cache size (number of memoized results).
     */
    public int getCacheSize() {
        return resultCache.size();
    }
    
    /**
     * Run a parameter sweep against a list of semiprimes.
     * Tests each semiprime against each configuration using parallel execution.
     *
     * Applies parallelization principle: exploits parallelism via parallel streams
     * to process multiple benchmark runs simultaneously instead of sequentially.
     * 
     * @param semiprimes List of known semiprimes to test
     * @param configs List of parameter configurations to test
     * @param outputDir Directory for artifacts (relative to project root)
     * @return List of benchmark results
     */
    public List<BenchmarkResult> runSweep(
        List<SemiprimeGenerator.Semiprime> semiprimes,
        List<ParamConfig> configs,
        String outputDir
    ) {
        log.info("=== Validation Benchmark Sweep ===");
        log.info("Semiprimes: {}", semiprimes.size());
        log.info("Configurations: {}", configs.size());
        log.info("Total runs: {}", semiprimes.size() * configs.size());
        
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        
        // Parallel execution: process benchmark runs in parallel using multi-threaded parallelism
        List<BenchmarkRun> runs = semiprimes.parallelStream()
            .flatMap(semiprime -> configs.stream()
                .map(paramConfig -> new BenchmarkRun(semiprime, paramConfig, runSingleBenchmark(semiprime, paramConfig))))
            .collect(Collectors.toList());

        // Sequential logging after parallel computation to avoid race conditions
        for (BenchmarkRun run : runs) {
            log.info("Testing N={} ({} bits) with precision={}, samples={}, threshold={}",
                run.semiprime().N(), run.semiprime().bitLength(),
                run.paramConfig().precision, run.paramConfig().samples, run.paramConfig().threshold);

            log.info("Result: success={}, duration={}ms, error={}",
                run.result().success(), run.result().durationMs(), run.result().errorMessage());
        }

        List<BenchmarkResult> results = runs.stream()
            .map(BenchmarkRun::result)
            .collect(Collectors.toList());
        
        // Export artifacts
        try {
            exportResults(results, outputDir, timestamp);
            log.info("Artifacts exported to {}", outputDir);
        } catch (IOException e) {
            log.error("Failed to export artifacts", e);
        }
        
        return results;
    }
    
    /**
     * Run a single benchmark with given semiprime and configuration.
     * 
     * Applies memoization: cache results based on N and config to avoid
     * recomputing identical benchmark runs (ergodic sampling principle).
     */
    private BenchmarkResult runSingleBenchmark(
        SemiprimeGenerator.Semiprime semiprime,
        ParamConfig paramConfig
    ) {
        BigInteger N = semiprime.N();
        BigInteger expectedP = semiprime.p();
        BigInteger expectedQ = semiprime.q();
        
        // Create cache key from N and config parameters
        String cacheKey = String.format("%s_%d_%d_%d_%d_%.2f_%.2f_%.2f",
            N, paramConfig.precision, paramConfig.samples, paramConfig.mSpan,
            paramConfig.J, paramConfig.threshold, paramConfig.kLo, paramConfig.kHi);
        
        // Check cache first (memoization: reuse previous computation)
        if (resultCache.containsKey(cacheKey)) {
            log.debug("Cache hit for N={}, reusing previous result", N);
            return resultCache.get(cacheKey);
        }
        
        // Create a temporary FactorizerService with custom config
        // Note: This requires using Spring's application properties
        // For now, we'll call the existing service and log the config used
        
        long startTime = System.currentTimeMillis();
        FactorizationResult factResult;
        
        try {
            // Call factorizer service with custom configuration
            FactorizerConfig customConfig = new FactorizerConfig(
                paramConfig.precision,
                paramConfig.samples,
                paramConfig.mSpan,
                paramConfig.J,
                paramConfig.threshold,
                paramConfig.kLo,
                paramConfig.kHi,
                15000L // default timeout for validation runs
            );
            factResult = factorizerService.factor(N, customConfig);
            
            long duration = System.currentTimeMillis() - startTime;
            
            BenchmarkResult result = new BenchmarkResult(
                N,
                expectedP,
                expectedQ,
                factResult.p(),
                factResult.q(),
                factResult.success(),
                duration,
                factResult.config(),
                factResult.errorMessage()
            );
            
            // Cache result for potential reuse
            resultCache.put(cacheKey, result);
            
            return result;
            
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            
            // Create a config snapshot for failed attempts
            FactorizerConfig config = new FactorizerConfig(
                paramConfig.precision,
                paramConfig.samples,
                paramConfig.mSpan,
                paramConfig.J,
                paramConfig.threshold,
                paramConfig.kLo,
                paramConfig.kHi,
                15000L // default timeout
            );
            
            BenchmarkResult result = new BenchmarkResult(
                N,
                expectedP,
                expectedQ,
                null,
                null,
                false,
                duration,
                config,
                e.getMessage()
            );
            
            // Cache even failed results
            resultCache.put(cacheKey, result);
            
            return result;
        }
    }
    
    /**
     * Export benchmark results to CSV and JSON artifacts.
     */
    private void exportResults(
        List<BenchmarkResult> results,
        String outputDir,
        String timestamp
    ) throws IOException {
        Path dir = Paths.get(outputDir);
        Files.createDirectories(dir);
        
        // Export JSON
        Path jsonPath = dir.resolve("benchmark_" + timestamp + ".json");
        List<Map<String, Object>> jsonData = results.stream()
            .map(BenchmarkResult::toMap)
            .collect(Collectors.toList());
        objectMapper.writeValue(jsonPath.toFile(), jsonData);
        log.info("JSON exported: {}", jsonPath);
        
        // Export CSV
        Path csvPath = dir.resolve("benchmark_" + timestamp + ".csv");
        exportCsv(results, csvPath);
        log.info("CSV exported: {}", csvPath);
        
        // Export summary
        Path summaryPath = dir.resolve("summary_" + timestamp + ".txt");
        exportSummary(results, summaryPath, timestamp);
        log.info("Summary exported: {}", summaryPath);
    }
    
    /**
     * Export results to CSV format.
     */
    private void exportCsv(List<BenchmarkResult> results, Path path) throws IOException {
        StringBuilder csv = new StringBuilder();
        
        // CSV header
        csv.append("N,N_bits,expectedP,expectedQ,actualP,actualQ,success,factorsMatch,durationMs,");
        csv.append("precision,samples,mSpan,J,threshold,kLo,kHi,searchTimeoutMs,errorMessage\n");
        
        // CSV rows
        for (BenchmarkResult result : results) {
            Map<String, Object> map = result.toMap();
            csv.append(String.format("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\"%s\"\n",
                map.get("N"),
                map.get("N_bits"),
                map.get("expectedP"),
                map.get("expectedQ"),
                map.get("actualP"),
                map.get("actualQ"),
                map.get("success"),
                map.get("factorsMatch"),
                map.get("durationMs"),
                map.get("precision"),
                map.get("samples"),
                map.get("mSpan"),
                map.get("J"),
                map.get("threshold"),
                map.get("kLo"),
                map.get("kHi"),
                map.get("searchTimeoutMs"),
                map.get("errorMessage") != null ? map.get("errorMessage") : ""
            ));
        }
        
        Files.writeString(path, csv.toString());
    }
    
    /**
     * Export human-readable summary.
     */
    private void exportSummary(List<BenchmarkResult> results, Path path, String timestamp) throws IOException {
        StringBuilder summary = new StringBuilder();
        
        summary.append("=== Validation Benchmark Summary ===\n");
        summary.append("Timestamp: ").append(timestamp).append("\n");
        summary.append("Total runs: ").append(results.size()).append("\n\n");
        
        long successCount = results.stream().filter(BenchmarkResult::success).count();
        long failureCount = results.size() - successCount;
        
        summary.append("Success: ").append(successCount).append("\n");
        summary.append("Failure: ").append(failureCount).append("\n");
        summary.append("Success rate: ").append(
            String.format("%.2f%%", 100.0 * successCount / results.size())
        ).append("\n\n");
        
        summary.append("=== Detailed Results ===\n");
        for (BenchmarkResult result : results) {
            summary.append(String.format("N=%s (%d bits): %s in %dms\n",
                result.N(), result.N().bitLength(),
                result.success() ? "SUCCESS" : "FAILED",
                result.durationMs()
            ));
            if (!result.success() && result.errorMessage() != null) {
                summary.append("  Error: ").append(result.errorMessage()).append("\n");
            }
        }
        
        Files.writeString(path, summary.toString());
    }
}
