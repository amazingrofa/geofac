# User Story 2: Enforce Resonance-Only Algorithm

## Goal

The `FactorizerService` must exclusively use the geometric resonance algorithm and not attempt any fallback methods like Pollard's Rho. This aligns the codebase with its core mandate of being a pure geometric factorization tool.

## Files to Modify

- `src/main/java/com/geofac/FactorizerService.java`

## Acceptance Criteria

A code inspection of `FactorizerService.java` confirms that no fallback code paths exist. Specifically, the `pollardsRhoWithDeadline` and its helper method `f` are completely removed, and the main `factor` method does not attempt to call them.

## Tasks

- [ ] T003 [US2] In `src/main/java/com/geofac/FactorizerService.java`, replace the `if (factors == null)` block that initiates the Pollard's Rho fallback with a simple error-logging and failure-return block.
- [ ] T004 [US2] In `src/main/java/com/geofac/FactorizerService.java`, remove the now-unused private methods `pollardsRhoWithDeadline` and `f`.

## Implementation Details

### Part 1: Remove Fallback Logic from `factor` method

The primary modification is within the `factor` method. The block of code that executes after the main resonance search fails must be replaced.

**This entire block will be removed:**
```java
if (factors == null) {
    log.warn("Resonance search did not yield a factor. Attempting Pollard's Rho fallback...");
    long deadline = startTime + config.searchTimeoutMs();
    long remainingMs = deadline - System.currentTimeMillis();
    boolean fallbackAttempted = false;
    
    if (remainingMs > 0) {
        fallbackAttempted = true;
        BigInteger fallbackFactor = pollardsRhoWithDeadline(N, deadline);
        if (fallbackFactor != null && /* ... */) {
            // ... logic to process fallback result
        }
    }
    
    // ... logic to create failure message
    return new FactorizationResult(/* ... */);
}
```

**It will be replaced with this simpler failure path:**
```java
if (factors == null) {
    long totalDuration = System.currentTimeMillis() - startTime;
    String failureMessage = "NO_FACTOR_FOUND: resonance search failed or timed out.";
    log.error(failureMessage);
    return new FactorizationResult(N, null, null, false, totalDuration, config, failureMessage);
}
```

### Part 2: Remove Unused Helper Methods

The following two methods, which are now dead code, must be deleted entirely from the `FactorizerService.java` file.

```java
// Simple Pollard's Rho fallback with time budget
private BigInteger pollardsRhoWithDeadline(BigInteger N, long deadlineMs) {
    // ... method implementation
}

private static BigInteger f(BigInteger x, BigInteger c, BigInteger mod) {
    // ... method implementation
}
```
