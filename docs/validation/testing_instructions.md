# Instructions for Testing and Tweaking Geometric Resonance Factorization

## Objective
Successfully factorize the official Gate 1 challenge number using the geometric resonance algorithm. The exact number (N) and its factors (p, q) are defined in **[docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md)**. The test must pass within the configured timeout without failing.

## Current Status
The test `com.geofac.FactorizerServiceTest.testFactor127BitSemiprime` is configured with parameters tuned for success:
- Timeout: 10 minutes (600,000 ms)
- Samples: 3,000
- M-span: 220
- Threshold: 0.90
- Other parameters as per test configuration

Run the test first to verify current behavior. If it fails (timeout or wrong factors), proceed to tweaking.

## Key Files
- **Test File**: `src/test/java/com/geofac/FactorizerServiceTest.java` - Contains the unit test, expected factors, and test-specific configuration overrides.
- **Service Implementation**: `src/main/java/com/geofac/FactorizerService.java` - Core factorization logic, parameter injection, and search algorithm.
- **Default Configuration**: `src/main/resources/application.yml` - Default parameter values for the service.
- **Utility Classes**:
  - `src/main/java/com/geofac/util/DirichletKernel.java` - Dirichlet kernel amplitude calculation.
  - `src/main/java/com/geofac/util/SnapKernel.java` - Phase-corrected snapping for candidate generation.
- **Build File**: `build.gradle` - Dependencies and build configuration.
- **Plan Document**: `mvp-plan.md` - Overview of the project and implementation details.

## Running the Test
1. Ensure the project is built: `./gradlew build`
2. Run the specific test: `./gradlew test --tests com.geofac.FactorizerServiceTest.testFactor127BitSemiprime -i`
   - The `-i` flag enables info-level logging for detailed output.
3. Observe the output:
   - Progress logs every 10% of samples.
   - If successful, it will log the factors and verification.
   - If failed, it will indicate timeout or no factors found.

## Parameters to Tweak
The algorithm's success depends on the following parameters (injected via Spring properties):

- **`geofac.precision`**: Decimal precision for BigDecimal calculations (e.g., 240). Increase if numerical instability is suspected.
- **`geofac.samples`**: Number of k-samples in the search loop (e.g., 3000). Increase for broader search if factors are missed.
- **`geofac.m-span`**: Range for the parallel m-scan (e.g., 220). Wider range covers more m-values but increases computation.
- **`geofac.j`**: Parameter for Dirichlet kernel (e.g., 6). Adjust for filtering sensitivity.
- **`geofac.threshold`**: Amplitude gate threshold (e.g., 0.90). Lower values are more permissive, allowing more candidates.
- **`geofac.k-lo`** and **`geofac.k-hi`**: Bounds for k (e.g., 0.25 to 0.45). Narrow or shift if the resonance is outside this range.
- **`geofac.search-timeout-ms`**: Timeout in milliseconds (e.g., 600000 for 10 minutes). Increase if more time is needed.

## Tweaking Strategy
1. **Start with Current Config**: Run the test as-is. If it succeeds, no changes needed.
2. **If Timeout**: Increase `samples` by 50% (e.g., to 4500) or `search-timeout-ms` further. Also, widen `m-span` (e.g., to 250).
3. **If No Factors Found**: Lower `threshold` (e.g., to 0.85) to be more permissive. Increase `precision` (e.g., to 260) for better accuracy.
4. **Iterative Adjustment**:
   - Modify parameters in `src/test/java/com/geofac/FactorizerServiceTest.java` under `@TestPropertySource`.
   - Re-run the test after each change.
   - Log the config snapshot in the test output for reproducibility.
5. **Debugging Tips**:
   - Enable DEBUG logging in `application.yml` for `com.geofac` to see more details.
   - Check progress logs to estimate completion time.
   - If factors are found but incorrect, verify the math in `FactorizerService.java` (e.g., phase correction).
   - Test with smaller numbers first to validate the algorithm.

## Expected Outcomes
- **Success**: Test passes, logs "SUCCESS", verifies p × q = N, and matches expected factors.
- **Failure Scenarios**:
  - Timeout: Increase timeout/samples.
  - Wrong Factors: Rare, but check candidate testing logic.
  - No Factors: Adjust threshold, m-span, or k-bounds.

## Additional Notes
- The algorithm uses parallel processing for m-scans, so CPU cores impact speed.
- BigDecimal precision is adaptive based on N's bit length.
- If major changes are needed, reference `mvp-plan.md` for implementation details.
- After successful tweaks, update the default config in `application.yml` if applicable.