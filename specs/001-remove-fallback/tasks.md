# Tasks for Feature: Refactor: Remove Pollard's Rho Fallback

**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

This task list is generated from the implementation plan and feature specification.

## Phase 1: Foundational (Test Setup)

- [ ] T001 Create test file `src/test/java/com/geofac/NoFallbackTest.java`
- [ ] T002 Add test method to `NoFallbackTest.java` to configure a scenario where resonance fails and assert that the `FactorizationResult` indicates failure without fallback.

## Phase 2: User Story 1 (Remove Fallback Logic)

**User Story**: As a maintainer, I want to remove the Pollard's Rho fallback so that the system adheres to the "Resonance-Only" principle and provides clear, unambiguous failure states.

**Independent Test Criteria**:
- Run the test created in `NoFallbackTest.java`. It should fail before the implementation and pass after.
- Manually verify that `pollardsRhoWithDeadline` and its helper methods are deleted.

### Implementation Tasks

- [ ] T003 [US1] In `src/main/java/com/geofac/FactorizerService.java`, replace the entire `if (factors == null)` block with logic that logs an error and returns a `FactorizationResult` indicating failure.
- [ ] T004 [US1] In `src/main/java/com/geofac/FactorizerService.java`, delete the `pollardsRhoWithDeadline` method.
- [ ] T005 [US1] In `src/main/java/com/geofac/FactorizerService.java`, delete the `f` helper method.

## Phase 3: Polish & Finalization

- [ ] T006 Run all existing and new tests via `./gradlew test` to ensure no regressions were introduced.
- [ ] T007 Review and format the modified code to ensure it adheres to project style guidelines.

## Dependencies

- **US1** is self-contained and has no dependencies on other user stories.

## Parallel Execution

No parallel execution opportunities were identified for this feature, as all code modifications target the same service file and are logically sequential.

## Implementation Strategy

The implementation will follow a test-first approach as outlined:
1.  Create the failing test case that proves the fallback is currently active.
2.  Implement the changes to remove the fallback logic.
3.  Verify that the test now passes and all other tests remain green.
