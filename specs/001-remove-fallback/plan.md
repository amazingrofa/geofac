# Implementation Plan: Refactor: Remove Pollard's Rho Fallback

**Branch**: `001-remove-fallback` | **Date**: 2025-11-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-remove-fallback/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The goal is to remove the Pollard's Rho fallback from `FactorizerService` to align with the project constitution. When the primary resonance search fails, the service will now report a clear failure instead of attempting a backup method. This involves deleting the fallback logic and associated dead code.

## Technical Context

**Language/Version**: Java 17+
**Primary Dependencies**: Spring Boot 3.2.0, ch.obermuhlner:big-math
**Storage**: Files (for run artifacts)
**Testing**: JUnit 5 with Spring Boot Test
**Target Platform**: JVM
**Project Type**: Single Project
**Performance Goals**: Neutral performance impact on the primary resonance search. The change simplifies control flow, which is a performance improvement in terms of maintainability.
**Constraints**: N/A
**Scale/Scope**: The change is limited to `FactorizerService.java` and its corresponding tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|---|---|---|
| **I. Resonance-Only Factorization** | ✅ **PASS** | This change is the explicit implementation of this principle, removing the prohibited fallback. |
| **II. Performance-First Optimization** | ✅ **PASS** | The change simplifies control flow and removes dead code, which has a positive impact on code clarity and maintainability without affecting the core algorithm's performance. |
| **III. Reproducibility** | ✅ **PASS** | Not affected. Failure cases will now be more explicit but still reproducible. |
| **IV. Test-First Development** | 🟡 **NEEDS VERIFICATION** | The specification requires verifying the explicit failure case. A test will be created to confirm that a failure occurs without triggering a fallback. |
| **V. High-Precision Arithmetic** | ✅ **PASS** | Not affected. |
| **VI. Deterministic Configuration** | ✅ **PASS** | Not affected. |

## Project Structure

### Documentation (this feature)

```text
specs/001-remove-fallback/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
src/
└── main/
    └── java/
        └── com/
            └── geofac/
                ├── FactorizerService.java  # To be modified
                └── ...
src/
└── test/
    └── java/
        └── com/
            └── geofac/
                ├── FactorizerServiceTest.java # May need modification/addition
                └── NoFallbackTest.java        # To be created
```

**Structure Decision**: The project follows a standard single-project Java layout. This refactoring will modify `FactorizerService.java` and add a new test `NoFallbackTest.java` to verify the removal of the fallback mechanism.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       | N/A        | N/A                                 |