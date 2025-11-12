# User Story 1: Align Test with Requirements

## Goal

The 127-bit benchmark test must execute the full geometric resonance algorithm without using the fast-path optimization. This ensures the test is a valid benchmark of the core algorithm's performance, as required by the code review.

## Files to Modify

- `src/test/java/com/geofac/FactorizerServiceTest.java`

## Acceptance Criteria

Running the `testFactor127BitSemiprime` test will trigger the full geometric search. This can be confirmed by observing log output indicating a non-trivial execution time (e.g., > 1 second) and the absence of any "Fast-path invoked" warnings.

## Tasks

- [ ] T002 [P] [US1] In `src/test/java/com/geofac/FactorizerServiceTest.java`, ensure the `@TestPropertySource` annotation for the class does not contain `geofac.enable-fast-path=true`.

## Implementation Details

The primary change is to ensure that the test configuration does not enable the fast-path mode. This mode is designed to bypass the computationally expensive factorization for CI/CD environments, but for this specific benchmark, the full execution is required.

**Verification:**

Check the class-level annotations in `FactorizerServiceTest.java`.

**Ensure this property is NOT present in the list:**
```java
@TestPropertySource(properties = {
    "geofac.allow-127bit-benchmark=true",
    // ... other properties
    "geofac.enable-fast-path=true" // <-- THIS LINE SHOULD BE REMOVED
})
public class FactorizerServiceTest {
    // ...
}
```
By removing it, the service will use the default value of `false` for `geofac.enable-fast-path`.
