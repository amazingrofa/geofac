# Kernel Order (J) Impact Study: Experiment Design

## Hypothesis

**Claim:** The Dirichlet kernel order parameter J significantly impacts factorization success. The current default J=6 may not be optimal across all semiprime scales in the operational range [10^14, 10^18].

**Background:** The Dirichlet kernel amplitude function A(θ) = |sin((2J+1)θ/2) / ((2J+1)sin(θ/2))| acts as a resonance gate. The order J controls the "sharpness" of resonance peaks:
- Lower J (e.g., 3): Broader peaks, more candidates pass threshold, less selective
- Higher J (e.g., 15): Sharper peaks, fewer candidates, more selective

The hypothesis suggests there's a "sweet spot" for J that balances selectivity with coverage.

## Experimental Design

### Test Matrix

| J Value | Expected Behavior | Test Purpose |
|---------|-------------------|--------------|
| 3 | Broad filtering, high candidate count | Lower bound |
| 6 | Current default | Baseline |
| 9 | Sharper filtering | Test if sharper helps |
| 12 | Very sharp filtering | Push selectivity |
| 15 | Extremely sharp | Upper bound |

### Test Cases

All tests use official validation gate semiprimes:

1. **Gate 1 (30-bit balanced):**
   - N = 1073217479
   - Factors: p = 32749, q = 32771
   - Expected: Fast success (<1s) for most J values

2. **Gate 2 (60-bit balanced):**
   - N = 1152921470247108503
   - Factors: p = 1073741789, q = 1073741827
   - Expected: Success within reasonable time (<60s)

3. **Operational Range (47-50 bit):**
   - Test semiprimes in [10^14, 10^18]
   - Expected: May show J-dependence

### Parameters

**Fixed Parameters (per config):**
- samples: 3000
- m-span: 180
- threshold: 0.92
- k-lo: 0.25, k-hi: 0.45
- precision: Adaptive (max(240, bitlength × 4 + 200))
- search-timeout-ms: 120000 (2 minutes per attempt)

**Variable Parameter:**
- J ∈ {3, 6, 9, 12, 15}

### Metrics

For each (test case, J) pair, collect:

1. **Success:** Boolean (factors found?)
2. **Runtime:** Seconds to completion or timeout
3. **Samples Evaluated:** Total candidates tested
4. **Amplitude Stats:**
   - Max amplitude observed
   - Mean amplitude of top 100 candidates
   - Amplitude at true factors (if found)

### Falsification Criteria

The hypothesis is **falsified** if:

1. **No Variation:** All J values produce identical results (±5% margin)
2. **No Success:** All J values fail on all test cases
3. **Monotonic Failure:** Performance degrades monotonically with J (suggests J should be minimal)
4. **Random Variation:** Results vary but without consistent pattern (noise, not signal)

The hypothesis is **supported** if:

1. **Clear Optimum:** One J value significantly outperforms others (>20% better success/runtime)
2. **Scale-Dependent:** Optimal J varies by semiprime size (e.g., J=3 for 30-bit, J=9 for 60-bit)
3. **Consistent Pattern:** Higher J improves precision but increases runtime (tradeoff exists)

## Implementation

### Dirichlet Kernel (Python)

```python
import mpmath as mp

def dirichlet_amplitude(theta, J):
    """
    Normalized Dirichlet kernel amplitude.
    A(θ) = |sin((2J+1)θ/2) / ((2J+1)sin(θ/2))|
    """
    t = theta % (2 * mp.pi)  # Reduce to [0, 2π]
    if t > mp.pi:
        t -= 2 * mp.pi  # Reduce to [-π, π]
    
    th2 = t / 2
    sin_th2 = mp.sin(th2)
    
    # Singularity guard
    if abs(sin_th2) < mp.mpf(10) ** (-mp.dps + 10):
        return mp.mpf(1)
    
    two_j_plus_1 = 2 * J + 1
    num = mp.sin(th2 * two_j_plus_1)
    den = sin_th2 * two_j_plus_1
    
    return abs(num / den)
```

### Test Harness

The experiment script (`kernel_order_experiment.py`) implements:

1. **Factorization Engine:** Simplified GVA-style geometric resonance search
2. **Parameter Sweep:** Loop over J values
3. **Metrics Collection:** Capture all specified metrics
4. **Result Export:** JSON format for reproducibility

### Execution

```bash
cd experiments/kernel-order-impact-study
python3 kernel_order_experiment.py
```

Expected runtime: ~10-30 minutes (5 J values × 3 test cases × up to 2 min each)

## Reproducibility

**Environment:**
- Python 3.12+
- mpmath 1.3.0+

**Deterministic Execution:**
- Fixed seeds for QMC sampling
- Explicit precision (mp.dps)
- Logged parameters in results.json

**Parameters Logged:**
- Test case N, p, q
- J value
- All fixed parameters (samples, m-span, threshold, k-range)
- Precision used
- Timestamp

## Expected Outcomes

### If Hypothesis is Supported

Evidence:
- J=9 or J=12 shows higher success rate than J=6 on 60-bit test
- Clear amplitude peak sharpening with higher J
- Tradeoff: higher J = more precision, fewer candidates, potentially higher success

### If Hypothesis is Falsified

Evidence:
- J=6 performs identically to all other values
- All J values fail or succeed equally
- Results are noisy without consistent pattern
- Current default J=6 is as good as any other value

## Alignment with Repository Standards

### CODING_STYLE.md Compliance

✓ **Minimal Scope:** Single parameter (J) tested  
✓ **Clear Criteria:** Success/failure measurable for each test case  
✓ **Reproducible:** Deterministic sampling, pinned parameters, exported artifacts  
✓ **Validation Gates:** Uses official Gate 1 and Gate 2 semiprimes  
✓ **Honest Reporting:** Will report negative results clearly  
✓ **Appropriate Scale:** Tests in operational range [10^14, 10^18]  

### VALIDATION_GATES.md Compliance

✓ **Gate 1 (30-bit):** Included as quick sanity check  
✓ **Gate 2 (60-bit):** Included as scaling validation  
✓ **Precision:** Adaptive formula max(240, bitlength × 4 + 200)  
✓ **Logging:** All parameters and results exported  

## References

- Dirichlet kernel: `src/main/java/com/geofac/util/DirichletKernel.java`
- Default configuration: `src/main/resources/application.yml`
- Validation gates: `docs/VALIDATION_GATES.md`
- Coding standards: `docs/CODING_STYLE.md`
