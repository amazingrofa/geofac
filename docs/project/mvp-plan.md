## Goal
Get a working Spring Boot terminal application that can factor the official 127-bit test case (see `docs/VALIDATION_GATES.md`) using Spring Shell - **minimal complexity, maximum speed**.

## Functional Requirements (MVP Scope)
✅ Factor the official 127-bit semiprime challenge number.
✅ Produce identical results to z-sandbox Java implementation.
✅ Interactive shell with `factor` command.
✅ Basic configuration via YAML.
✅ Structured logging (no System.out).

## Out of Scope (Future Enhancements)
- ❌ Complex domain models
- ❌ Export commands (just log results)
- ❌ Config commands (just use application.yml)
- ❌ Comprehensive test suite (manual verification only)
- ❌ REST API
- ❌ Database persistence

---

## Simplified Package Structure

```
com.geofac/
├── GeofacApplication.java           # Spring Boot main (minimal)
├── FactorizerService.java           # Core logic (ported from GeometricResonanceFactorizer)
├── FactorizerShell.java             # Spring Shell commands (single file)
└── util/
    ├── DirichletKernel.java         # Copy from z-sandbox DirichletGate
    └── SnapKernel.java              # Copy from z-sandbox SnapKernel
```

**Total files to create: 5**

---

## Step-by-Step Implementation

### Step 1: Project Setup (5 minutes)

**1.1 Create `build.gradle`**
```gradle
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
}

group = 'com.geofac'
version = '0.1.0-SNAPSHOT'
java.sourceCompatibility = JavaVersion.VERSION_17

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter'
    implementation 'org.springframework.shell:spring-shell-starter:3.2.0'
    implementation 'ch.obermuhlner:big-math:2.3.2'
}
```

**1.2 Create `settings.gradle`**
```gradle
rootProject.name = 'geofac'
```

**1.3 Create `src/main/resources/application.yml`**
```yaml
spring:
  application:
    name: geofac

geofac:
  precision: 240
  samples: 3000
  m-span: 180
  j: 6
  threshold: 0.92
  k-lo: 0.25
  k-hi: 0.45

logging:
  level:
    com.geofac: INFO
```

---

### Step 2: Copy Utility Classes (10 minutes)

**2.1 Create `src/main/java/com/geofac/util/DirichletKernel.java`**
- Copy from: `z-sandbox/src/main/java/org/zfifteen/sandbox/resonance/DirichletGate.java`
- Change package: `package com.geofac.util;`
- Rename class: `DirichletGate` → `DirichletKernel`

**2.2 Create `src/main/java/com/geofac/util/SnapKernel.java`**
- Copy from: `z-sandbox/src/main/java/org/zfifteen/sandbox/resonance/SnapKernel.java`
- Change package: `package com.geofac.util;`
- No other changes needed

---

### Step 3: Create Service (30 minutes)

**3.1 Create `src/main/java/com/geofac/FactorizerService.java`**

Extract core logic from `GeometricResonanceFactorizer.java`:

```java
package com.geofac;

import com.geofac.util.DirichletKernel;
import com.geofac.util.SnapKernel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.IntStream;

import ch.obermuhlner.math.big.BigDecimalMath;

@Service
public class FactorizerService {

    private static final Logger log = LoggerFactory.getLogger(FactorizerService.class);

    @Value("${geofac.precision}")
    private int precision;

    @Value("${geofac.samples}")
    private long samples;

    @Value("${geofac.m-span}")
    private int mSpan;

    @Value("${geofac.j}")
    private int J;

    @Value("${geofac.threshold}")
    private double threshold;

    @Value("${geofac.k-lo}")
    private double kLo;

    @Value("${geofac.k-hi}")
    private double kHi;

    public BigInteger[] factor(BigInteger N) {
        log.info("Starting factorization of {}-bit number", N.bitLength());
        log.info("N = {}", N);

        // Initialize precision and constants
        MathContext mc = new MathContext(precision, RoundingMode.HALF_EVEN);
        BigDecimal bdN = new BigDecimal(N, mc);
        BigDecimal lnN = BigDecimalMath.log(bdN, mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        BigDecimal phiInv = computePhiInv(mc);

        log.info("Configuration: precision={}, samples={}, m-span={}, J={}, threshold={}",
                 precision, samples, mSpan, J, threshold);

        // Search
        BigInteger[] result = search(N, mc, lnN, twoPi, phiInv);

        if (result != null) {
            log.info("SUCCESS: Found factors");
            log.info("p = {}", result[0]);
            log.info("q = {}", result[1]);

            // Verify
            if (!result[0].multiply(result[1]).equals(N)) {
                throw new IllegalStateException("Product check failed!");
            }
        } else {
            log.warn("No factors found");
        }

        return result;
    }

    private BigInteger[] search(BigInteger N, MathContext mc, BigDecimal lnN,
                                BigDecimal twoPi, BigDecimal phiInv) {
        BigDecimal u = BigDecimal.ZERO;
        BigDecimal kWidth = BigDecimal.valueOf(kHi - kLo);
        BigDecimal thresholdBd = BigDecimal.valueOf(threshold);

        for (long n = 0; n < samples; n++) {
            if (n % 500 == 0) {
                log.debug("Progress: {}/{} samples", n, samples);
            }

            // Update golden ratio sequence
            u = u.add(phiInv, mc);
            if (u.compareTo(BigDecimal.ONE) >= 0) {
                u = u.subtract(BigDecimal.ONE, mc);
            }

            BigDecimal k = BigDecimal.valueOf(kLo).add(kWidth.multiply(u, mc), mc);
            BigInteger m0 = BigInteger.ZERO; // Balanced semiprime

            AtomicReference<BigInteger[]> result = new AtomicReference<>();

            // Parallel m-scan
            IntStream.rangeClosed(-mSpan, mSpan).parallel().forEach(dm -> {
                if (result.get() != null) return;

                BigInteger m = m0.add(BigInteger.valueOf(dm));
                BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);

                BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, J, mc);
                if (amplitude.compareTo(thresholdBd) > 0) {
                    BigInteger p0 = SnapKernel.phaseCorrectedSnap(lnN, theta, mc);
                    BigInteger[] hit = testNeighbors(N, p0);
                    if (hit != null) {
                        result.compareAndSet(null, hit);
                    }
                }
            });

            if (result.get() != null) {
                return result.get();
            }
        }

        return null;
    }

    private BigInteger[] testNeighbors(BigInteger N, BigInteger pCenter) {
        BigInteger[] offsets = { BigInteger.ZERO, BigInteger.valueOf(-1), BigInteger.ONE };
        for (BigInteger off : offsets) {
            BigInteger p = pCenter.add(off);
            if (p.compareTo(BigInteger.ONE) <= 0 || p.compareTo(N) >= 0) continue;
            if (N.mod(p).equals(BigInteger.ZERO)) {
                BigInteger q = N.divide(p);
                return ordered(p, q);
            }
        }
        return null;
    }

    private static BigInteger[] ordered(BigInteger a, BigInteger b) {
        return (a.compareTo(b) <= 0) ? new BigInteger[]{a, b} : new BigInteger[]{b, a};
    }

    private BigDecimal computePhiInv(MathContext mc) {
        BigDecimal sqrt5 = BigDecimalMath.sqrt(BigDecimal.valueOf(5), mc);
        return sqrt5.subtract(BigDecimal.ONE, mc).divide(BigDecimal.valueOf(2), mc);
    }
}
```

---

### Step 4: Create Shell Interface (15 minutes)

**4.1 Create `src/main/java/com/geofac/FactorizerShell.java`**

```java
package com.geofac;

import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

import java.math.BigInteger;

@ShellComponent
public class FactorizerShell {

    private final FactorizerService service;

    public FactorizerShell(FactorizerService service) {
        this.service = service;
    }

    @ShellMethod(value = "Factor a semiprime using geometric resonance", key = "factor")
    public String factor(@ShellOption String n) {
        try {
            BigInteger N = new BigInteger(n);

            if (N.bitLength() < 10) {
                return "Error: Number too small (must be at least 10 bits)";
            }

            long startTime = System.currentTimeMillis();
            BigInteger[] factors = service.factor(N);
            long duration = System.currentTimeMillis() - startTime;

            if (factors != null) {
                return String.format(
                    "✓ SUCCESS\n" +
                    "p = %s\n" +
                    "q = %s\n" +
                    "Time: %.2f seconds",
                    factors[0], factors[1], duration / 1000.0
                );
            } else {
                return String.format(
                    "✗ FAILED\n" +
                    "No factors found after %d samples\n" +
                    "Time: %.2f seconds",
                    service.samples, duration / 1000.0
                );
            }

        } catch (NumberFormatException e) {
            return "Error: Invalid number format. Provide a decimal integer.";
        } catch (Exception e) {
            return "Error: " + e.getMessage();
        }
    }
}
```

---

### Step 5: Create Application (5 minutes)

**5.1 Create `src/main/java/com/geofac/GeofacApplication.java`**

```java
package com.geofac;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class GeofacApplication {

    public static void main(String[] args) {
        SpringApplication.run(GeofacApplication.class, args);
    }
}
```

---

### Step 6: Test (10 minutes)

**6.1 Build**
```bash
cd /Users/velocityworks/IdeaProjects/geofac
./gradlew build
```

**6.2 Run**
```bash
./gradlew bootRun
```

**6.3 Test in Shell**
Get the official challenge number from `docs/VALIDATION_GATES.md`.
```
shell> factor <the-challenge-number>
```

**Expected Output:**
A success message with the correct factors `p` and `q`.

---

## File Creation Order

1. ✅ `settings.gradle`
2. ✅ `build.gradle`
3. ✅ `src/main/resources/application.yml`
4. ✅ `src/main/java/com/geofac/util/DirichletKernel.java` (copy from z-sandbox)
5. ✅ `src/main/java/com/geofac/util/SnapKernel.java` (copy from z-sandbox)
6. ✅ `src/main/java/com/geofac/FactorizerService.java` (refactor from z-sandbox)
7. ✅ `src/main/java/com/geofac/FactorizerShell.java` (new)
8. ✅ `src/main/java/com/geofac/GeofacApplication.java` (minimal)

---

## Success Criteria

- [ ] Application starts without errors
- [ ] Shell prompt appears: `shell>`
- [ ] `help` command shows available commands
- [ ] `factor <the-challenge-number>` succeeds
- [ ] Results match the factors defined in `docs/VALIDATION_GATES.md`
- [ ] Logs show INFO level messages (no System.out)

---

## Estimated Time: 1.5 hours

- Setup: 5 min
- Copy utils: 10 min
- Create service: 30 min
- Create shell: 15 min
- Create app: 5 min
- Test & debug: 25 min

---

## What's Different from Full Plan

**Simplified:**
- No complex domain models (just BigInteger[] return values)
- No ResultExporter (just log to console)
- No config commands (edit application.yml)
- No export command (future)
- No comprehensive tests (manual verification)
- Single service file instead of multiple

**Kept:**
- Spring Boot + Spring Shell
- Configuration via YAML
- Structured logging (SLF4J)
- Platform-independent BigDecimal
- Parallel m-scan

---

## Next Steps After MVP

Once this works:
1. Add export command (save to results/ directory)
2. Add config commands (view/set parameters)
3. Add proper test suite
4. Refactor into cleaner domain models
5. Add more factorization strategies
6. Follow full spring-boot-build-plan.md
