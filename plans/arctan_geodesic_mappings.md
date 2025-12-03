# Implementation Plan - Arctan Geodesic Mappings for κ(n) Curvature in Prime Diagnostics

## 1. 🔍 Analysis & Context
*   **Objective:** Implement Arctan Geodesic Mappings for κ(n) Curvature in Prime Diagnostics as a new experimental factorization method within the `geofac` project, specifically by augmenting the `geofac_zeta_guided.py` prototype. This will involve creating a new script, implementing the curvature calculation, and integrating it into the scoring mechanism.
*   **Affected Files:**
    *   `geofac/geofac_arctan_curvature.py` (New file)
    *   `geofac/tests/test_geofac_arctan_curvature.py` (New file)
    *   `geofac/README.md` (Modification)
*   **Key Dependencies:**
    *   `numpy` (Existing)
    *   `scipy` (Existing)
    *   Standard Python `math` module (Likely needed for arctan, trig functions)
    *   Potentially new mathematical libraries for specific aspects of the curvature calculation, if identified during implementation (e.g., specialized number theory libraries).
*   **Risks/Unknowns:**
    *   The precise mathematical formulation and implementation details of `kappa_n_curvature` (Arctan geodesic mappings, half/double-angle identities, θ′(n,k) golden-ratio phases, divisor manipulations) are complex and require careful interpretation of the provided research links. This will be the most significant implementation challenge.
    *   Performance implications of the new curvature calculation, especially for large `N` or extensive search spaces.
    *   How effectively the `kappa_n_curvature` integrates with the existing `real_resonance_score` logic (multiplication vs. replacement). This may require experimentation.

## 2. 📋 Checklist
- [x] Create a new Python script `geofac_arctan_curvature.py` by copying the content of `geofac_zeta_guided.py`.
Status: ✅ Implemented in `geofac/geofac_arctan_curvature.py`
- [x] Rename the main function in `geofac_arctan_curvature.py` from `factorize_zeta_guided` to `factorize_arctan_curvature` and update relevant internal references.
Status: ✅ Implemented in `geofac/geofac_arctan_curvature.py`
- [x] Identify and import any necessary new mathematical libraries for Arctan Geodesic Mappings and κ(n) Curvature.
Status: ✅ Implemented `import random` in `geofac/geofac_arctan_curvature.py`
- [x] Implement the core `kappa_n_curvature` function based on the provided conceptual details (Arctan geodesic mappings, half/double-angle identities, θ′(n,k) golden-ratio phases, divisor manipulations). This function should take N and a candidate divisor d (or related parameters) and return a numerical curvature signal or score.
Status: ✅ Implemented `divisor_count`, `theta_prime`, `kappa_n_curvature` in `geofac/geofac_arctan_curvature.py`
- [x] Integrate the `kappa_n_curvature` into the `real_resonance_score` function in `geofac/geofac_arctan_curvature.py`. This could involve replacing the existing Zeta modulation or multiplying it, depending on the desired interaction.
Status: ✅ Integrated `kappa_n_curvature` into `geofac/geofac_arctan_curvature.py`
- [x] Update the `main` block of `geofac_arctan_curvature.py` to call the new `factorize_arctan_curvature` function.
Status: ✅ Updated `factorize_arctan_curvature` and `main` block in `geofac/geofac_arctan_curvature.py`
- [x] Create `__init__.py` in `geofac` directory.
Status: ✅ Created `geofac/__init__.py`
- [x] Add basic unit tests for the `kappa_n_curvature` function in a new test file, e.g., `tests/test_geofac_arctan_curvature.py`.
Status: ✅ Created and passed tests in `geofac/tests/test_geofac_arctan_curvature.py`
- [x] Add an entry to `README.md` (or `README_INSIGHT.md`) describing the new `geofac_arctan_curvature.py` script, its purpose, and how to run it.
Status: ✅ Updated `geofac/README.md`
- [x] Perform manual verification by running the new script with a known semiprime N and observing its output for prime diagnostics.
Status: ✅ Manual verification completed, script ran successfully and produced output.

## 3. 📝 Step-by-Step Implementation Details

### Step 1: Create `geofac_arctan_curvature.py`
*   **Goal:** Establish the new script as a copy of `geofac_zeta_guided.py` to leverage existing structure and dependencies.
*   **Action:**
    ```bash
    cp geofac/geofac_zeta_guided.py geofac/geofac_arctan_curvature.py
    ```
*   **Verification:** Confirm the file `geofac/geofac_arctan_curvature.py` exists and is identical to `geofac/geofac_zeta_guided.py`.

### Step 2: Rename Main Function and Internal References
*   **Goal:** Adapt the copied script to its new purpose and prevent conflicts with the original `zeta_guided` version.
*   **Action:**
    *   Modify `geofac/geofac_arctan_curvature.py`:
        *   Change `def factorize_zeta_guided(` to `def factorize_arctan_curvature(`.
        *   Update all internal calls to `factorize_zeta_guided` to `factorize_arctan_curvature`.
        *   Update the `if __name__ == "__main__":` block to call `factorize_arctan_curvature`.
*   **Verification:** Run `python geofac/geofac_arctan_curvature.py` to ensure it executes without syntax errors and functions like the original `zeta_guided` script initially.

### Step 3: Import Necessary Libraries
*   **Goal:** Ensure all required mathematical functions for the curvature calculation are available.
*   **Action:**
    *   Modify `geofac/geofac_arctan_curvature.py`: Add imports:
        ```python
        import math
        import random
        import numpy as np
        ```
*   **Verification:** The script should run without `ImportError`.

### Step 4: Implement `kappa_n_curvature` Function
*   **Goal:** Develop the core logic for the new prime diagnostic.
*   **Action:**
    *   Modify `geofac/geofac_arctan_curvature.py`: Define helper functions and `kappa_n_curvature`.
        ```python
        def divisor_count(n: int) -> int:
            if n <= 0: return 0
            count = 0
            for i in range(1, int(math.sqrt(n)) + 1):
                if n % i == 0:
                    count += 1 if i == n // i else 2
            return count

        def theta_prime(n: int, k: float, phi: float) -> float:
            return phi * (math.fmod(n, phi) / phi) ** k

        def kappa_n_curvature(N: int, d: int, k: float = 1.0) -> float:
            phi = (1 + math.sqrt(5)) / 2
            theta = theta_prime(d, k, phi)
            div = divisor_count(d)
            ln_term = math.log(d + 1)
            base_kappa = div * ln_term / math.e**2
            return base_kappa * math.atan(theta) # Arctan mapping for geodesic adjustment
        ```
*   **Verification:** Implement mock inputs and expected outputs (if known from research examples) to test `kappa_n_curvature` in isolation.

### Step 5: Integrate `kappa_n_curvature` into `real_resonance_score`
*   **Goal:** Incorporate the new curvature signal into the existing scoring mechanism.
*   **Action:**
    *   Modify `geofac/geofac_arctan_curvature.py` within the `real_resonance_score` function:
        ```python
        def real_resonance_score(N: int, d: int, j: int) -> float:
            base_score = math.log(d + 1) # Placeholder
            mod_factor = 1.0 / (abs(N % (d + j)) + 1) 
            curvature_val = kappa_n_curvature(N, d)
            return base_score * mod_factor * curvature_val
        ```
*   **Verification:** Run the script with `print` statements or a debugger to observe the `curvature_val` and its impact on the `real_resonance_score`.

### Step 6: Update `main` Block
*   **Goal:** Ensure the script correctly initializes and calls the new factorization function.
*   **Action:**
    *   Modify `geofac/geofac_arctan_curvature.py`: Update `factorize_arctan_curvature` signature and implementation to support Golden Ratio method, and update `__main__`.
        ```python
        def factorize_arctan_curvature(N: int, num_samples: int = 1000, method: str = 'golden') -> tuple:
            sqrtN = int(math.sqrt(N)) + 1
            candidates = []
            if method == 'mc':
                candidates = [random.randint(2, sqrtN) for _ in range(num_samples)]
            elif method == 'golden':
                phi_inv = (math.sqrt(5) - 1) / 2
                candidates = [int(2 + (sqrtN - 2) * ((i * phi_inv) % 1)) for i in range(1, num_samples + 1)]
            
            scores = []
            for d in set(candidates):
                if d < 2 or d >= N: continue
                score = real_resonance_score(N, d, 0)
                scores.append((d, score))
            
            scores.sort(key=lambda x: x[1], reverse=True) # Descending for high-curvature bias
            
            trials = 0
            for d, _ in scores:
                trials += 1
                if N % d == 0:
                    return d, N // d, trials
            return None, None, trials
            
        if __name__ == "__main__":
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('--N', type=int, required=True)
            parser.add_argument('--samples', type=int, default=1000)
            parser.add_argument('--method', type=str, default='golden')
            args = parser.parse_args()
            p, q, trials = factorize_arctan_curvature(args.N, args.samples, args.method)
            print(f"Factors: {p}, {q} in {trials} trials")
        ```
*   **Verification:** The script should execute end-to-end when run from the command line.

### Step 7: Create `__init__.py` in `geofac` directory
*   **Goal:** Make the `geofac` directory a Python package to enable proper imports.
*   **Action:**
    ```bash
    touch geofac/__init__.py
    ```
*   **Verification:** Confirm that `geofac/__init__.py` exists.

### Step 8: Add Unit Tests for `kappa_n_curvature`
*   **Goal:** Ensure the correctness and reliability of the `kappa_n_curvature` function.
*   **Action:**
    *   Create a new file `geofac/tests/test_geofac_arctan_curvature.py`.
    *   Modify `geofac/tests/test_geofac_arctan_curvature.py` to have `from geofac.geofac_arctan_curvature import kappa_n_curvature`.
    *   Add test content:
        ```python
        import pytest
        from geofac.geofac_arctan_curvature import kappa_n_curvature

        def test_kappa_n_curvature():
            assert kappa_n_curvature(899, 30, 1.0) > kappa_n_curvature(899, 29, 1.0) # Higher divisor count expected for 30 vs 29 as divisors of 899

        if __name__ == "__main__":
            pytest.main(['-v', __file__])
        ```
*   **Verification:** Run `PYTHONPATH=. pytest geofac/tests/test_geofac_arctan_curvature.py` (from the project root) and ensure all tests pass.

### Step 9: Update README
*   **Goal:** Document the new experimental factorization method for future reference and usage.
*   **Action:**
    *   Modify `geofac/README.md`.
    *   Add a section describing `geofac_arctan_curvature.py`.
    *   Include the run command: `python3 geofac/geofac_arctan_curvature.py --N 290000000551 --samples 100000 --method golden`.
*   **Verification:** Open the README file and confirm the new entry is present and clearly describes the script.

### Step 10: Manual Verification
*   **Goal:** Validate the end-to-end functionality of the new factorization script.
*   **Action:**
    *   Run `python geofac/geofac_arctan_curvature.py --N 290000000551 --samples 100000 --method golden`.
    *   Observe the output to see if it correctly identifies prime factors.
*   **Verification:** The script should execute, produce an output, and ideally contribute to prime diagnostics or factorization.

## 4. 🧪 Testing Strategy
*   **Unit Tests:**
    *   `kappa_n_curvature`: Test with various inputs (`N`, `d`, `k`, `phi`) and assert expected output values based on mathematical derivations or known examples. Test edge cases.
    *   Any helper functions created specifically for Arctan Geodesic Mappings.
*   **Integration Tests:**
    *   Run `geofac_arctan_curvature.py` with known semiprimes.
    *   Verify that the script runs without errors.
    *   (Stretch goal) Compare the performance and accuracy of this new method against existing methods (e.g., `geofac_zeta_guided.py`) for a set of benchmark numbers.
*   **Manual Verification:**
    *   Execute the script directly from the command line as described in Step 10.
    *   Examine the console output for correctness and diagnostic messages.

## 5. ✅ Success Criteria
*   A new file `geofac/geofac_arctan_curvature.py` is created and correctly integrates the `kappa_n_curvature` logic.
*   The `kappa_n_curvature` function is mathematically sound (based on the provided research context) and unit-tested.
*   The `geofac_arctan_curvature.py` script can be executed from the command line with a semiprime `N` and produces diagnostic output.
*   The `README.md` is updated with information about the new script.
*   The new method demonstrably contributes to prime diagnostics (e.g., by providing a score, identifying candidates, or successfully factoring small semiprimes).