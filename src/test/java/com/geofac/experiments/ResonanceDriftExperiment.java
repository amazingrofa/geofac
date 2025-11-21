package com.geofac.experiments;

import com.geofac.FactorizerService;
import com.geofac.FactorizerConfig;
import com.geofac.FactorizationResult;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Resonance Drift Hypothesis Experiment
 * 
 * Tests whether optimal k values scale with N according to k_opt = k_base * ln(N)^S
 * Collects empirical k-success data across multiple bit-widths for regression analysis.
 */
@SpringBootTest
public class ResonanceDriftExperiment {

    @Autowired
    private FactorizerService factorizerService;

    private static final String EXPERIMENT_DIR = "experiments/resonance-drift-hypothesis";
    private static final String DATA_FILE = EXPERIMENT_DIR + "/data_collection.log";

    /**
     * Known semiprimes across bit-width spectrum for calibration
     */
    private static class TestCase {
        final String name;
        final BigInteger n;
        final BigInteger p;
        final BigInteger q;
        final int bitLength;

        TestCase(String name, String nStr, String pStr, String qStr) {
            this.name = name;
            this.n = new BigInteger(nStr);
            this.p = new BigInteger(pStr);
            this.q = new BigInteger(qStr);
            this.bitLength = n.bitLength();
        }
    }

    private static final List<TestCase> TEST_CASES = List.of(
        // Operational range 10^14 - 10^18 (Gate 4)
        // Using semiprimes within validation gates
        new TestCase("OpRange_47bit", "100000000000861", "10000007", "10000079"),
        new TestCase("OpRange_50bit", "1000000000000363", "31622843", "31622993"),
        new TestCase("OpRange_54bit", "10000000000000087", "100000007", "100000037"),
        new TestCase("OpRange_57bit", "100000000000000117", "316227767", "316227773"),
        new TestCase("OpRange_60bit", "1000000000000000117", "1000000007", "1000000009")
    );

    @Test
    public void collectResonanceDriftData() throws IOException {
        ensureExperimentDir();
        
        try (PrintWriter writer = new PrintWriter(new FileWriter(DATA_FILE))) {
            writer.println("# Resonance Drift Data Collection");
            writer.println("# Format: name, bitLength, N, ln(N), k_lo, k_hi, success, k_optimal_estimate, duration_ms");
            writer.println();

            for (TestCase tc : TEST_CASES) {
                System.out.println("\n=== Testing: " + tc.name + " ===");
                System.out.println("N = " + tc.n + " (" + tc.bitLength + " bits)");
                
                double lnN = Math.log(tc.n.doubleValue());
                
                // Run multiple k-window scans to find optimal region
                List<ScanResult> scanResults = performKWindowScan(tc);
                
                for (ScanResult result : scanResults) {
                    writer.printf("%s, %d, %s, %.6f, %.6f, %.6f, %b, %.6f, %d%n",
                        tc.name,
                        tc.bitLength,
                        tc.n.toString(),
                        lnN,
                        result.kLo,
                        result.kHi,
                        result.success,
                        result.kOptimalEstimate,
                        result.durationMs
                    );
                }
                
                writer.flush();
            }
            
            writer.println();
            writer.println("# Data collection complete");
        }
        
        System.out.println("\nData collection complete. Results written to: " + DATA_FILE);
    }

    private static class ScanResult {
        final double kLo;
        final double kHi;
        final boolean success;
        final double kOptimalEstimate;
        final long durationMs;

        ScanResult(double kLo, double kHi, boolean success, double kOptimalEstimate, long durationMs) {
            this.kLo = kLo;
            this.kHi = kHi;
            this.success = success;
            this.kOptimalEstimate = kOptimalEstimate;
            this.durationMs = durationMs;
        }
    }

    /**
     * Perform multiple k-window scans to locate the resonance region
     */
    private List<ScanResult> performKWindowScan(TestCase tc) {
        List<ScanResult> results = new ArrayList<>();
        
        // Scan strategy: start with baseline window, then refine if needed
        double[][] windows = {
            {0.25, 0.35},  // Lower third of default range
            {0.30, 0.40},  // Middle of default range
            {0.35, 0.45},  // Upper third of default range
        };
        
        for (double[] window : windows) {
            double kLo = window[0];
            double kHi = window[1];
            double kCenter = (kLo + kHi) / 2.0;
            
            System.out.printf("Scanning k-window [%.3f, %.3f]...%n", kLo, kHi);
            
            FactorizerConfig customConfig = new FactorizerConfig(
                240,      // precision
                3000,     // samples
                180,      // mSpan
                6,        // J
                0.92,     // threshold
                kLo,
                kHi,
                60000     // timeout: 60 seconds
            );
            
            long startTime = System.currentTimeMillis();
            FactorizationResult result = factorizerService.factor(tc.n, customConfig);
            long duration = System.currentTimeMillis() - startTime;
            
            boolean success = result.success();
            System.out.printf("Result: %s (%.2f seconds)%n", 
                success ? "SUCCESS" : "FAILURE", duration / 1000.0);
            
            results.add(new ScanResult(kLo, kHi, success, kCenter, duration));
            
            if (success) {
                // Found it in this window; can potentially narrow further
                System.out.println("Resonance found in window [" + kLo + ", " + kHi + "]");
                break;
            }
        }
        
        return results;
    }

    private void ensureExperimentDir() throws IOException {
        Path dir = Paths.get(EXPERIMENT_DIR);
        if (!Files.exists(dir)) {
            Files.createDirectories(dir);
        }
        
        Path plotsDir = Paths.get(EXPERIMENT_DIR + "/plots");
        if (!Files.exists(plotsDir)) {
            Files.createDirectories(plotsDir);
        }
    }
}
