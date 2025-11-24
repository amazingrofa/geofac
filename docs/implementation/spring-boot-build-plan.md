# Plan: Port GeometricResonanceFactorizer to Modern Spring Boot Terminal Application

## Overview

This plan outlines the migration of `GeometricResonanceFactorizer.java` from the z-sandbox project to a modern Spring Boot terminal application using Spring Shell. The goal is to create a production-quality, interactive factorization tool with proper dependency injection, configuration management, and testing.

**Source:** `/Users/velocityworks/IdeaProjects/z-sandbox/src/main/java/org/zfifteen/sandbox/GeometricResonanceFactorizer.java`
**Target:** `/Users/velocityworks/IdeaProjects/geofac` (Spring Boot application)

---

## Phase 1: Project Foundation & Dependencies

### 1.1 Initialize Spring Boot Project
```bash
# Create Spring Boot project structure
cd /Users/velocityworks/IdeaProjects/geofac
mkdir -p src/main/java/com/geofac
mkdir -p src/main/resources
mkdir -p src/test/java/com/geofac
```

### 1.2 Create Gradle Build File (`build.gradle`)
```gradle
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
}

group = 'com.geofac'
version = '1.0.0-SNAPSHOT'
java.sourceCompatibility = JavaVersion.VERSION_17

repositories {
    mavenCentral()
}

dependencies {
    // Spring Boot
    implementation 'org.springframework.boot:spring-boot-starter'
    implementation 'org.springframework.shell:spring-shell-starter:3.2.0'

    // High-precision math (existing dependency)
    implementation 'ch.obermuhlner:big-math:2.3.2'

    // Logging
    implementation 'org.slf4j:slf4j-api'

    // Testing
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.junit.jupiter:junit-jupiter'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

### 1.3 Create Application Configuration (`src/main/resources/application.yml`)
```yaml
spring:
  application:
    name: geofac
  shell:
    interactive:
      enabled: true
    noninteractive:
      enabled: false

geofac:
  factorizer:
    default-precision: 240
    default-samples: 3000
    default-m-span: 180
    default-j: 6
    default-threshold: 0.92
    default-k-lo: 0.25
    default-k-hi: 0.45

logging:
  level:
    com.geofac: INFO
    org.springframework.shell: WARN
```

---

## Phase 2: Package Structure & Core Classes

### 2.1 Package Organization
```
com.geofac/
├── GeofacApplication.java              # Spring Boot main class
├── config/
│   └── FactorizerConfig.java           # Configuration properties
├── domain/
│   ├── FactorizationRequest.java       # Input model
│   ├── FactorizationResult.java        # Output model
│   └── FactorizationStatus.java        # Status enum
├── service/
│   ├── GeometricResonanceService.java  # Main business logic
│   └── ResultExporter.java             # Export artifacts
├── util/
│   ├── DirichletKernel.java            # Ported from DirichletGate
│   └── SnapKernel.java                 # Ported as-is
└── shell/
    └── FactorizerCommands.java          # Spring Shell commands
```

### 2.2 Key Class Responsibilities

- **GeofacApplication**: Spring Boot entry point
- **FactorizerConfig**: Externalize all parameters (precision, samples, etc.)
- **GeometricResonanceService**: Core factorization logic (ported from GeometricResonanceFactorizer)
- **FactorizerCommands**: Interactive shell interface
- **DirichletKernel & SnapKernel**: Pure utility classes (no Spring dependencies)

---

## Phase 3: Code Migration Strategy

### 3.1 Direct Ports (Minimal Changes)
- `DirichletGate.java` → `com.geofac.util.DirichletKernel.java` (rename only)
- `SnapKernel.java` → `com.geofac.util.SnapKernel.java` (package change only)

### 3.2 Refactor GeometricResonanceFactorizer

**Before (current):**
- Standalone class with `main()` method
- CLI argument parsing
- Direct System.out printing
- File I/O in main class

**After (Spring Boot):**
- `@Service` annotated service class
- `@ConfigurationProperties` for parameters
- Injected `Logger` for output
- Separate `ResultExporter` service for file I/O
- Return structured `FactorizationResult` objects

### 3.3 Modernization Improvements

| Current | Modern Spring Boot |
|---------|-------------------|
| `System.out.println()` | `log.info()` with SLF4J |
| CLI argument parsing | Spring Shell commands |
| Hardcoded defaults | `application.yml` configuration |
| Direct file writes | Service-layer abstraction |
| Single-threaded | Optional `@Async` support for parallel m-scan |
| No validation | Bean Validation (`@Valid`) |

---

## Phase 4: Spring Shell Command Interface

### 4.1 Interactive Commands

```bash
# Start the application
./gradlew bootRun

# Shell commands
shell> factor <official-challenge-number>
shell> factor --n <official-challenge-number> --precision 300
shell> config set samples 5000
shell> config show
shell> export results/latest
shell> help
```

### 4.2 Command Structure (`FactorizerCommands.java`)

```java
@ShellComponent
public class FactorizerCommands {

    @ShellMethod(value = "Factor a semiprime using geometric resonance", key = "factor")
    public String factor(
        @ShellOption String n,
        @ShellOption(defaultValue = "240") int precision,
        @ShellOption(defaultValue = "3000") long samples
    ) {
        // Delegate to service
    }

    @ShellMethod(value = "Show current configuration", key = "config show")
    public String showConfig() { ... }

    @ShellMethod(value = "Export results to directory", key = "export")
    public String export(String directory) { ... }
}
```

---

## Phase 5: Testing Strategy

### 5.1 Unit Tests
- `DirichletKernelTest.java`: Test normalized amplitude calculation
- `SnapKernelTest.java`: Test snap formula
- `GeometricResonanceServiceTest.java`: Test factorization logic with mock data

### 5.2 Integration Tests
- `GeometricResonanceIntegrationTest.java`: Test full factorization of the official challenge number.
- `ShellCommandsIntegrationTest.java`: Test Spring Shell commands

### 5.3 Test Data
The official test case is defined in `docs/VALIDATION_GATES.md`. Test classes will reference this data.
```java
@TestConfiguration
class TestFactorizationData {
    // Values will be loaded from a test resource or constant file
    // that reflects the definitions in VALIDATION_GATES.md
    public static final BigInteger N_CHALLENGE = ...;
    public static final BigInteger P_EXPECTED = ...;
    public static final BigInteger Q_EXPECTED = ...;
}
```

---

## Phase 6: Migration Checklist

### 6.1 Code Porting Tasks

- [ ] Create Spring Boot project structure
- [ ] Set up `build.gradle` with all dependencies
- [ ] Create `application.yml` configuration
- [ ] Port `DirichletGate` → `DirichletKernel` (util)
- [ ] Port `SnapKernel` (util, no changes)
- [ ] Refactor `GeometricResonanceFactorizer` → `GeometricResonanceService`
  - [ ] Extract configuration to `@ConfigurationProperties`
  - [ ] Replace `System.out` with `Logger`
  - [ ] Extract file I/O to `ResultExporter`
  - [ ] Return structured `FactorizationResult`
- [ ] Create domain models (`FactorizationRequest`, `FactorizationResult`)
- [ ] Implement Spring Shell commands
- [ ] Add logging configuration
- [ ] Write unit tests
- [ ] Write integration test (for the official challenge number)

### 6.2 Validation

- [ ] Run test suite: `./gradlew test`
- [ ] Start interactive shell: `./gradlew bootRun`
- [ ] Factor the official challenge number via shell
- [ ] Verify output artifacts in `results/` directory
- [ ] Compare results with z-sandbox Java version (should match exactly)

---

## Phase 7: Future Enhancements (Post-Port)

### 7.1 Ready for Extension
- Add multiple factorization strategies (GVA, Z5D, etc.)
- Implement progress tracking with Spring Events
- Add REST API layer (Spring Web MVC)
- Database persistence (Spring Data JPA) for results
- Distributed computation (Spring Cloud)

### 7.2 Integration with z-sandbox Research
- Import other factorization methods from z-sandbox
- Bridge to Python implementations via JNI or process execution
- Unified configuration between Java and Python components

---

## Phase 8: Deliverables

### 8.1 Working Application
- Fully functional Spring Boot terminal app
- Interactive shell with `factor` command
- Configuration via `application.yml`
- Logging to console and file
- Test suite with 100% coverage of ported code

### 8.2 Documentation
- `README.md`: Quick start guide
- `PORTING_NOTES.md`: Differences from z-sandbox version
- Javadoc for all public APIs
- Sample shell session transcript

### 8.3 Build Artifacts
- Executable JAR: `build/libs/geofac-1.0.0-SNAPSHOT.jar`
- Run standalone: `java -jar geofac-1.0.0-SNAPSHOT.jar`

---

## Execution Timeline

**Estimated effort: 4-6 hours**

1. **Phase 1 (30 min)**: Project setup, Gradle, dependencies
2. **Phase 2 (45 min)**: Package structure, domain models, config
3. **Phase 3 (90 min)**: Port utility classes + refactor main service
4. **Phase 4 (60 min)**: Spring Shell commands
5. **Phase 5 (60 min)**: Test suite
6. **Phase 6 (30 min)**: Integration testing and validation
7. **Phase 7/8 (30 min)**: Documentation and final cleanup

---

## Source Files to Port

### From z-sandbox (`/Users/velocityworks/IdeaProjects/z-sandbox/src/main/java/org/zfifteen/sandbox`)

1. **GeometricResonanceFactorizer.java** (main class, ~328 lines)
   - Refactor to: `com.geofac.service.GeometricResonanceService`
   - Extract: Configuration, file I/O, logging

2. **resonance/DirichletGate.java** (~71 lines)
   - Port to: `com.geofac.util.DirichletKernel`
   - Changes: Package name only

3. **resonance/SnapKernel.java** (~61 lines)
   - Port to: `com.geofac.util.SnapKernel`
   - Changes: Package name only

**Total LOC to port:** ~460 lines of production code

---

## Success Criteria

### Functional Requirements
✅ Factor the official 127-bit challenge semiprime.
✅ Produce identical results to z-sandbox Java implementation.
✅ Interactive shell with help, factor, config, export commands.
✅ Configuration via YAML (no hardcoded values).
✅ Structured logging (no System.out in production code).

### Technical Requirements
✅ Spring Boot 3.2+ with Spring Shell
✅ Java 17+ compatibility
✅ Gradle build system
✅ Unit + integration test coverage ≥ 80%
✅ Executable JAR artifact

### Quality Requirements
✅ Clean separation of concerns (service, util, shell, config)
✅ No regressions from z-sandbox version
✅ Platform-independent (works on x86_64, ARM64)
✅ Deterministic results (same inputs → same outputs)

---

## Notes

### Platform Compatibility
- Java BigDecimal ensures platform independence (unlike Python mpmath)
- No IEEE 754 float conversions (all operations in BigDecimal)
- Tested on macOS M1 Max (ARM64) - should work identically on x86_64

### Alignment with z-sandbox Mission Charter
- Research focus: Understanding and refining existing techniques
- No breakthrough claims: Validated on the Gate 1 challenge number.
- Honest limitations: Parameters may be overfit to single test case.
- Reproducibility: Java implementation for cross-platform determinism.

### Future Research Integration
This Spring Boot application can serve as the foundation for:
- Multi-algorithm comparison framework
- Batch processing of factorization experiments
- Integration with Python research code (z-sandbox)
- REST API for distributed experimentation
