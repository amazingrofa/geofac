# Feature Specification: Make Factor-Finding Process More Direct and Transparent

**Date**: 2025-11-12
**Branch**: `001-remove-fallback`
**Track**: `refactor`

## 1. Goals

The primary goal is to make the factor-finding process more direct and transparent by removing the Pollard's Rho fallback mechanism. This aligns with the project's constitution, which mandates that factorization must be achieved through geometric resonance alone.

The current system uses Pollard's Rho as a backup if the primary resonance method fails. This can obscure issues in the main algorithm and violates the principle of having a clear success or failure outcome for the resonance method.

## 2. Functional Requirements

1.  **Eliminate Fallback**: The code path that invokes the Pollard's Rho algorithm as a backup must be removed from `FactorizerService`.
2.  **Report Clear Failure**: If the primary resonance search does not find a factor within the configured timeout, the service must return a result indicating failure. It must not attempt any other factorization method.
3.  **Remove Dead Code**: The `pollardsRhoWithDeadline` method and any helper methods used exclusively by it must be deleted from the codebase.

## 3. Non-Functional Requirements

- **Performance**: The change must not negatively impact the performance of the primary resonance search algorithm. This will be verified by running existing benchmarks and ensuring no statistically significant regression.
- **Clarity**: The resulting code should be clearer and easier to understand, with a more linear control flow.
- **Compliance**: The final implementation must be fully compliant with the project's constitution, especially the "Resonance-Only Factorization" principle.

## 4. Out of Scope

-   No changes will be made to the primary geometric resonance algorithm itself.
-   No new dependencies will be added.
-   No changes will be made to the public API contract of the `FactorizerService`, other than the behavior of the failure case.

## 5. Acceptance Criteria

-   When `FactorizerService.factor()` is called and the resonance search fails, the returned `FactorizationResult` must indicate failure, and no fallback method is attempted.
-   The `pollardsRhoWithDeadline` method no longer exists in the `FactorizerService` class.
-   All existing tests must continue to pass, and a new test **must** be added to verify the explicit failure case without fallback.
-   The project must build and run successfully after the changes.

## Clarifications

### Session 2025-11-12

- Q: The spec's acceptance criteria states a new test "may be added," which is ambiguous and conflicts with the "Test-First Development" principle in the project's constitution. How should we proceed? → A: The new test is mandatory to prove the fallback is removed.
- Q: How should we verify the non-functional requirement that performance is 'not negatively impacted'? → A: Run existing benchmarks and ensure no statistically significant regression.
