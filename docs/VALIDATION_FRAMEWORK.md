# Validation Framework

Empirical validation framework for systematic testing of geometric resonance factorization at the 10^14–10^18 scale.

## Purpose

This framework provides infrastructure to:
1. Generate known semiprimes in the [1e14, 1e18] validation window (Gate 2)
2. Run parameter sweeps with different configurations
3. Track success/failure rates, timing, and accuracy
4. Export reproducible artifacts (CSV, JSON, summaries)
5. Document exact boundaries where the method works vs fails

## Components

### SemiprimeGenerator

Generates known semiprimes with deterministic seeds for reproducibility.

**Key methods:**
- `generateSemiprimes(seed, count)` - Generate count semiprimes with given seed
- `generateCuratedSet()` - Get small hardcoded set for quick tests
- `isInGate2Range(N)` - Validate N is in [1e14, 1e18]

**Example:**
```java
// Deterministic generation with seed
List<Semiprime> semiprimes = SemiprimeGenerator.generateSemiprimes(12345L, 5);

// Quick curated set
List<Semiprime> curated = SemiprimeGenerator.generateCuratedSet();
```

### ValidationBenchmark

Spring service that runs parameter sweeps and exports artifacts.

**Key methods:**
- `runSweep(semiprimes, configs, outputDir)` - Run full parameter sweep

**Example:**
```java
@Autowired
private ValidationBenchmark benchmark;

// Define test semiprimes
List<Semiprime> semiprimes = SemiprimeGenerator.generateSemiprimes(12345L, 10);

// Define parameter configurations to test
List<ParamConfig> configs = List.of(
    new ParamConfig(240, 1000, 60, 4, 0.85, 0.25, 0.45),
    new ParamConfig(300, 2000, 100, 5, 0.90, 0.25, 0.45),
    new ParamConfig(360, 3000, 150, 6, 0.92, 0.25, 0.45)
);

// Run sweep and export artifacts
List<BenchmarkResult> results = benchmark.runSweep(
    semiprimes, 
    configs, 
    "results/validation"
);
```

### BenchmarkResult

Record holding benchmark results for a single run.

**Fields:**
- `N` - The semiprime being factored
- `expectedP`, `expectedQ` - Known factors
- `actualP`, `actualQ` - Factors found (if any)
- `success` - Whether factorization succeeded
- `durationMs` - Execution time in milliseconds
- `config` - Full configuration snapshot
- `errorMessage` - Error details if failed

## Performance Optimizations

The validation framework applies two key optimization principles:

### Parallel Execution (Multi-threaded Parallelism)

Benchmark runs are executed in parallel using Java parallel streams. Instead of processing semiprimes and configurations sequentially (O(n×m) serial time), the framework exploits multi-threaded parallelism to process multiple benchmark runs simultaneously. This provides significant throughput improvement by distributing tasks across available CPU cores, leveraging task-level concurrency rather than SIMD vectorization.

### Memoization (Result Caching)

The framework caches benchmark results based on N and configuration parameters. If the same semiprime with identical configuration is tested multiple times, the cached result is returned instantly rather than recomputing. This applies the ergodic sampling principle: once a computation is performed, reuse it rather than regenerating identical deterministic calculations.

**Cache management:**
```java
// Clear cache for fresh sweep session
benchmark.clearCache();

// Check cache size
int cached = benchmark.getCacheSize();
```

These optimizations transform validation sweeps from sequential, repetitive operations into efficient, parallelized computations that avoid redundant work.

## Exported Artifacts

All artifacts are timestamped and exported to the specified output directory.

### JSON Format (`benchmark_YYYYMMDD_HHMMSS.json`)

Full structured data with all parameters and results:
```json
[
  {
    "N": "140737488355327",
    "N_bits": 47,
    "expectedP": "11863301",
    "expectedQ": "11863297",
    "actualP": "11863301",
    "actualQ": "11863297",
    "success": true,
    "factorsMatch": true,
    "durationMs": 1234,
    "precision": 240,
    "samples": 1000,
    "mSpan": 60,
    "J": 4,
    "threshold": 0.85,
    "kLo": 0.25,
    "kHi": 0.45,
    "searchTimeoutMs": 15000,
    "errorMessage": null
  }
]
```

### CSV Format (`benchmark_YYYYMMDD_HHMMSS.csv`)

Tabular data for spreadsheet analysis:
```csv
N,N_bits,expectedP,expectedQ,actualP,actualQ,success,factorsMatch,durationMs,precision,samples,mSpan,J,threshold,kLo,kHi,searchTimeoutMs,errorMessage
140737488355327,47,11863301,11863297,11863301,11863297,true,true,1234,240,1000,60,4,0.85,0.25,0.45,15000,
```

### Summary Format (`summary_YYYYMMDD_HHMMSS.txt`)

Human-readable summary:
```
=== Validation Benchmark Summary ===
Timestamp: 20250114_173000
Total runs: 30

Success: 12
Failure: 18
Success rate: 40.00%

=== Detailed Results ===
N=140737488355327 (47 bits): SUCCESS in 1234ms
N=1125899906842623 (50 bits): FAILED in 5000ms
  Error: No factors found within timeout
...
```

## Parameter Sweep Strategy

### Key Parameters

Parameters to sweep (from `application.yml`):
- **precision** - Decimal digits for BigDecimal math context
- **samples** - Number of k-samples explored
- **m-span** - Half-width for Dirichlet kernel sweep
- **J** - Dirichlet kernel order
- **threshold** - Normalized amplitude gate

Fixed parameters:
- **kLo, kHi** - Fractional k-sampling range (typically 0.25–0.45)
- **searchTimeoutMs** - Max time per attempt

### Example Sweep

Test hypothesis: "Higher precision improves success rate for 50+ bit semiprimes"

```java
// Generate 50-bit semiprimes
List<Semiprime> semiprimes = SemiprimeGenerator.generateSemiprimes(12345L, 20)
    .stream()
    .filter(sp -> sp.bitLength() >= 50 && sp.bitLength() <= 53)
    .toList();

// Sweep precision while holding other params constant
List<ParamConfig> configs = List.of(
    new ParamConfig(240, 3000, 180, 6, 0.92, 0.25, 0.45),  // baseline
    new ParamConfig(300, 3000, 180, 6, 0.92, 0.25, 0.45),  // +60 precision
    new ParamConfig(360, 3000, 180, 6, 0.92, 0.25, 0.45),  // +120 precision
    new ParamConfig(420, 3000, 180, 6, 0.92, 0.25, 0.45)   // +180 precision
);

List<BenchmarkResult> results = benchmark.runSweep(semiprimes, configs, "results/precision_sweep");
```

Analyze results:
- Success rate vs precision
- Average duration vs precision
- Identify minimum effective precision for 50-bit range

## Reproducibility

### Seeds

All semiprime generation uses deterministic seeds:
```java
// Always use explicit seeds for reproducibility
long seed = 12345L;
List<Semiprime> semiprimes = SemiprimeGenerator.generateSemiprimes(seed, count);

// Document seed in experiment logs
log.info("Using seed: {}", seed);
```

### Configuration Snapshot

Every `BenchmarkResult` includes full config:
- Precision, samples, m-span, J, threshold
- k-lo, k-hi ranges
- Search timeout

This ensures exact reproduction of any run.

### Timestamps

All artifacts include ISO timestamps:
- File names: `benchmark_20250114_173000.json`
- Summary headers: `Timestamp: 20250114_173000`

## Running Tests

Fast unit tests (< 30 seconds):
```bash
./gradlew test --tests ValidationBenchmarkTest
```

Full validation suite:
```bash
./gradlew test
```

## Interpreting Results

### Success Metrics
- **Success rate** - Percentage of semiprimes successfully factored
- **Duration** - Time to factor (lower is better)
- **Factors match** - Verify actualP × actualQ = N

### Failure Analysis
- Check `errorMessage` for specific failures
- Common errors:
  - "No factors found within timeout" - Need more samples or higher threshold
  - "Input N does not conform to validation gates" - N outside [1e14, 1e18]
  - Timeout - Increase `searchTimeoutMs` or reduce `samples`

### Parameter Boundaries

Document in sweep results:
- Minimum precision needed for given bit length
- Sample count vs success rate
- Threshold sensitivity
- Time-accuracy tradeoffs

## Repository Constraints

Per [CODING_STYLE.md](../CODING_STYLE.md) and [VALIDATION_GATES.md](VALIDATION_GATES.md):

1. **Gate 2 validation window**: All tests must use N in [1e14, 1e18]
2. **No classical fallbacks**: Only geometric resonance methods
3. **Deterministic methods**: Use Sobol/Halton, not random sampling
4. **Explicit precision**: Log precision settings and adapt to N.bitLength()
5. **Reproducibility**: Pin seeds, log configs, export artifacts

## Example Complete Workflow

```java
@SpringBootTest
public class MyValidationExperiment {
    
    @Autowired
    private ValidationBenchmark benchmark;
    
    @Test
    public void testThresholdSensitivity() {
        // 1. Generate test semiprimes with pinned seed
        long seed = 98765L;
        List<Semiprime> semiprimes = SemiprimeGenerator.generateSemiprimes(seed, 15);
        
        // 2. Define parameter sweep over threshold
        List<ParamConfig> configs = List.of(
            new ParamConfig(300, 3000, 180, 6, 0.80, 0.25, 0.45),
            new ParamConfig(300, 3000, 180, 6, 0.85, 0.25, 0.45),
            new ParamConfig(300, 3000, 180, 6, 0.90, 0.25, 0.45),
            new ParamConfig(300, 3000, 180, 6, 0.92, 0.25, 0.45),
            new ParamConfig(300, 3000, 180, 6, 0.95, 0.25, 0.45)
        );
        
        // 3. Run sweep
        String outputDir = "results/validation/threshold_sensitivity";
        List<BenchmarkResult> results = benchmark.runSweep(semiprimes, configs, outputDir);
        
        // 4. Analyze (artifacts auto-exported)
        long successCount = results.stream().filter(BenchmarkResult::success).count();
        double successRate = 100.0 * successCount / results.size();
        
        System.out.println("Success rate: " + successRate + "%");
        System.out.println("Artifacts in: " + outputDir);
    }
}
```

## Future Enhancements

Potential additions (out of scope for initial implementation):
- Statistical analysis (confidence intervals, hypothesis tests)
- Visualization generation (success rate heatmaps, duration distributions)
- Automated boundary detection (binary search for minimum effective precision)
- Integration with CI for regression detection

## References

- [VALIDATION_GATES.md](VALIDATION_GATES.md) - Official validation policy
- [CODING_STYLE.md](../CODING_STYLE.md) - Repository coding standards
- [README.md](../README.md) - Project overview
- Application config: `src/main/resources/application.yml`
