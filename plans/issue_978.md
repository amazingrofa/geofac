# Implementation Plan - Resonant Slope Hunter (RSH) Algorithm

## 1. 🔍 Analysis & Context
*   **Objective:** Implement the Resonant Slope Hunter algorithm for semiprime factorization, utilizing the Lattice Resonance Conjecture to achieve >10x speedup over naive Fermat factorization.
*   **Affected Files:**
    *   New Directory: `src/rsh/`
    *   New File: `src/rsh/__init__.py`
    *   New File: `src/rsh/signal.py` (Sawtooth signal generation)
    *   New File: `src/rsh/frequency.py` (Frequency detection logic)
    *   New File: `src/rsh/slope.py` (Slope decoding and candidate derivation)
    *   New File: `src/rsh/core.py` (Main algorithm and heuristic loop)
    *   New File: `tests/test_rsh.py`
*   **Key Dependencies:** `numpy` (for numerical operations/signal processing), `pytest` (for testing).
*   **Risks/Unknowns:**
    *   Specifics of the "local frequency detection" on the Fermat curve need precise implementation from the theoretical description.
    *   Performance overhead of Python for heavy arithmetic; vectorization with NumPy is crucial.
    *   Algorithm convergence for highly unbalanced semiprimes.

## 2. 📋 Checklist
- [ ] Step 1: Initialize Module Structure & Environment
- [ ] Step 2: Implement Sawtooth Signal Generator
- [ ] Step 3: Implement Frequency Detection Logic
- [ ] Step 4: Implement Slope Decoding & Candidate Derivation
- [ ] Step 5: Implement Main RSH Loop (Adaptive Jumping)
- [ ] Step 6: Verification & Benchmarking

## 3. 📝 Step-by-Step Implementation Details

### Step 1: Initialize Module Structure & Environment
*   **Goal:** Set up the Python package structure and dependencies.
*   **Action:**
    *   Create directory `src/rsh`.
    *   Create `src/rsh/__init__.py` to expose key functions.
    *   Ensure `numpy` is available (create/update `requirements.txt` if needed, though we will assume standard env for this plan).
*   **Verification:** `import rsh` succeeds in a python shell.

### Step 2: Implement Sawtooth Signal Generator
*   **Goal:** Generate the quantization error signal from the Fermat curve.
*   **Action:**
    *   Create `src/rsh/signal.py`.
    *   Implement class/function `generate_error_signal(n, x_start, window_size)`:
        *   Calculate `y = sqrt(x^2 - n)`.
        *   Compute error `e(x) = y - floor(y)`.
        *   Return signal array (using NumPy).
*   **Verification:** Test with small `n` (e.g., `n=15`, `n=127`) and verify output values against manual calculation.

### Step 3: Implement Frequency Detection Logic
*   **Goal:** Detect local periodicity in the error signal.
*   **Action:**
    *   Create `src/rsh/frequency.py`.
    *   Implement `detect_local_frequency(signal_segment)`:
        *   Apply windowing (if necessary).
        *   Use FFT (`numpy.fft.rfft`) or autocorrelation to find dominant peaks.
        *   Return dominant frequency `f` and phase.
*   **Verification:** Pass a synthetic sawtooth wave and verify the detected frequency matches the input.

### Step 4: Implement Slope Decoding & Candidate Derivation
*   **Goal:** Translate frequency into a factorization candidate.
*   **Action:**
    *   Create `src/rsh/slope.py`.
    *   Implement `frequency_to_slope(f, x_current)`:
        *   Map frequency `f` to the slope of the divisor `p` on the Fermat curve.
    *   Implement `derive_candidate(slope, n)`:
        *   Convert slope back to a potential factor `p`.
*   **Verification:** Unit test with known `p, q` pairs. Reverse engineer `f` from `p`, pass it to the function, and verify `p` is recovered.

### Step 5: Implement Main RSH Loop (Adaptive Jumping)
*   **Goal:** Orchestrate the search using adaptive jumps.
*   **Action:**
    *   Create `src/rsh/core.py`.
    *   Implement `factorize_rsh(n, max_iter=1000)`:
        *   Initialize `x` at `ceil(sqrt(n))`.
        *   Loop:
            *   Generate signal window at `x`.
            *   Detect frequency `f`.
            *   Decode slope -> candidate `p`.
            *   Check if `n % p == 0`. If yes, return `(p, n//p)`.
            *   Calculate jump size `delta_x` based on resonance intensity or slope gradient.
            *   Update `x += delta_x`.
*   **Verification:** Run `factorize_rsh` on `Gate-127` (or smaller test semiprimes first) and verify it finds factors.

### Step 6: Verification & Benchmarking
*   **Goal:** Ensure performance meets the >10x speedup target.
*   **Action:**
    *   Create `tests/test_rsh.py`.
    *   Add `test_small_semiprimes` (e.g., n=8051).
    *   Add `test_gate_127` (if feasible for unit tests, otherwise separate script).
    *   Create a benchmark script `scripts/benchmark.py` comparing `rsh` vs naive Fermat.
*   **Verification:** Run `pytest` and `python scripts/benchmark.py`.

## 4. 🧪 Testing Strategy
*   **Unit Tests:**
    *   `test_signal_generation`: Correct error values.
    *   `test_frequency_detection`: Accurate peak finding.
    *   `test_conversion`: Slope <-> Frequency mathematics.
*   **Integration Tests:**
    *   Full factorization of random 20-bit, 40-bit semiprimes.
*   **Manual Verification:**
    *   Compare step count of RSH vs Naive Fermat for the same `n`.

## 5. ✅ Success Criteria
*   Module `rsh` is importable and functional.
*   `factorize_rsh` correctly factors valid semiprimes.
*   Benchmark shows significantly fewer iterations or time than naive Fermat implementation for unbalanced inputs.
*   Code passes `flake8` / linting standards.
