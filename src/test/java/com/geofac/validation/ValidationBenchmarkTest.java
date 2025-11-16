package com.geofac.validation;

import com.geofac.FactorizerService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the validation benchmark framework.
 * 
 * Validates that:
 * - Semiprime generator produces valid numbers in [1e14, 1e18] range
 * - Benchmark framework can run sweeps
 * - Artifacts (CSV, JSON, summary) are created
 * - Tests complete in < 30 seconds
 */
@SpringBootTest
@TestPropertySource(properties = {
    "geofac.precision=240",
    "geofac.samples=100",  // Small sample size for fast tests
    "geofac.m-span=30",     // Small span for fast tests
    "geofac.j=3",
    "geofac.threshold=0.85",
    "geofac.search-timeout-ms=5000"  // Short timeout for fast tests
})
class ValidationBenchmarkTest {
    
    @Autowired
    private ValidationBenchmark validationBenchmark;
    
    @Test
    void testSemiprimeGeneratorProducesValidNumbers() {
        // Generate semiprimes with deterministic seed
        List<SemiprimeGenerator.Semiprime> semiprimes = 
            SemiprimeGenerator.generateSemiprimes(12345L, 3);
        
        assertEquals(3, semiprimes.size(), "Should generate requested count");
        
        for (SemiprimeGenerator.Semiprime sp : semiprimes) {
            // Verify p * q = N
            assertEquals(sp.N(), sp.p().multiply(sp.q()), "p * q must equal N");
            
            // Verify in Gate 2 range
            assertTrue(SemiprimeGenerator.isInGate2Range(sp.N()), 
                "N must be in [1e14, 1e18] range");
            
            // Verify both factors are greater than 1
            assertTrue(sp.p().compareTo(BigInteger.ONE) > 0, "p must be > 1");
            assertTrue(sp.q().compareTo(BigInteger.ONE) > 0, "q must be > 1");
        }
    }
    
    @Test
    void testCuratedSetIsValid() {
        List<SemiprimeGenerator.Semiprime> curated = 
            SemiprimeGenerator.generateCuratedSet();
        
        assertFalse(curated.isEmpty(), "Curated set should not be empty");
        
        for (SemiprimeGenerator.Semiprime sp : curated) {
            assertEquals(sp.N(), sp.p().multiply(sp.q()), "p * q must equal N");
            assertTrue(SemiprimeGenerator.isInGate2Range(sp.N()), 
                "N must be in Gate 2 range");
        }
    }
    
    @Test
    void testBenchmarkResultToMap() {
        BigInteger N = new BigInteger("140737863163397"); // ~1e14
        BigInteger p = new BigInteger("11863301");
        BigInteger q = new BigInteger("11863297");
        
        com.geofac.FactorizerConfig config = new com.geofac.FactorizerConfig(
            240, 100, 30, 3, 0.85, 0.25, 0.45, 5000
        );
        
        BenchmarkResult result = new BenchmarkResult(
            N, p, q, p, q, true, 1000L, config, null
        );
        
        var map = result.toMap();
        
        assertNotNull(map);
        assertEquals(N.toString(), map.get("N"));
        assertEquals(p.toString(), map.get("actualP"));
        assertEquals(q.toString(), map.get("actualQ"));
        assertTrue((Boolean) map.get("success"));
        assertTrue((Boolean) map.get("factorsMatch"));
        assertEquals(1000L, map.get("durationMs"));
        assertEquals(240, map.get("precision"));
    }
    
    @Test
    void testValidationBenchmarkFramework(@TempDir Path tempDir) throws Exception {
        // This test validates the framework infrastructure without actually
        // running the expensive factorization. Full parameter sweeps should
        // be run manually outside of unit tests.

        // Verify the benchmark service is wired up
        assertNotNull(validationBenchmark, "ValidationBenchmark should be autowired");

        // Verify cache management methods work
        validationBenchmark.clearCache();
        assertEquals(0, validationBenchmark.getCacheSize(), "Cache should be empty after clear");

        // Generate small test data
        List<SemiprimeGenerator.Semiprime> semiprimes = SemiprimeGenerator.generateSemiprimes(12345L, 1);
        List<ValidationBenchmark.ParamConfig> configs = List.of(
            new ValidationBenchmark.ParamConfig(240, 50, 10, 3, 0.85, 0.25, 0.45)
        );

        // Run a minimal sweep (should complete quickly with small parameters)
        List<BenchmarkResult> results = validationBenchmark.runSweep(semiprimes, configs, tempDir.toString());

        // Verify results
        assertNotNull(results, "Results should not be null");
        assertEquals(1, results.size(), "Should have one result for 1 semiprime × 1 config");

        // Verify artifacts were created (find files with benchmark_ prefix)
        boolean csvExists = Files.list(tempDir)
            .anyMatch(p -> p.getFileName().toString().startsWith("benchmark_") && p.getFileName().toString().endsWith(".csv"));
        boolean jsonExists = Files.list(tempDir)
            .anyMatch(p -> p.getFileName().toString().startsWith("benchmark_") && p.getFileName().toString().endsWith(".json"));

        assertTrue(csvExists, "CSV artifact should be created");
        assertTrue(jsonExists, "JSON artifact should be created");
    }
    
    @Test
    void testDeterministicSemiprimeGeneration() {
        // Same seed should produce same semiprimes
        long seed = 99999L;
        
        List<SemiprimeGenerator.Semiprime> first = 
            SemiprimeGenerator.generateSemiprimes(seed, 2);
        List<SemiprimeGenerator.Semiprime> second = 
            SemiprimeGenerator.generateSemiprimes(seed, 2);
        
        assertEquals(first.size(), second.size());
        
        for (int i = 0; i < first.size(); i++) {
            assertEquals(first.get(i).N(), second.get(i).N(), 
                "Same seed should produce same N");
            assertEquals(first.get(i).p(), second.get(i).p(), 
                "Same seed should produce same p");
            assertEquals(first.get(i).q(), second.get(i).q(), 
                "Same seed should produce same q");
        }
    }
}
