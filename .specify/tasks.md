# Tasks: Align 127-bit Benchmark Test with Requirements

This document outlines the tasks required to complete the feature described in GitHub issue [#17](https://github.com/zfifteen/geofac/issues/17).

## Implementation Strategy

The change is confined to a single test configuration file. The plan is to first read the file to confirm its current state, then apply the required change, and finally run the build to validate the solution.

## Dependencies

There are no external dependencies for this task.

## Parallel Execution

The tasks are sequential and should be performed in order.

---

## Phase 1: Setup

- [ ] T001 Read the content of `src/test/java/com/geofac/FactorizerServiceTest.java` to understand the current test configuration.

## Phase 2: User Story 1: Align Test with Requirements

**Goal:** The 127-bit benchmark test must execute the full geometric resonance algorithm without using the fast-path optimization.
**Independent Test Criteria:** Running the `testFactor127BitSemiprime` test will trigger the full geometric search, confirmed by observing log output and a non-trivial execution time.

- [ ] T002 [US1] In `src/test/java/com/geofac/FactorizerServiceTest.java`, ensure the `@TestPropertySource` annotation for the class does not contain the `geofac.enable-fast-path=true` property. If it exists, remove it.

## Phase 3: Polish & Final Validation

- [ ] T003 Run `./gradlew build` to ensure the change compiles and all tests, including the benchmark test, pass successfully.
- [ ] T004 Review the modified file to ensure it adheres to project coding standards and correctly implements the required change.