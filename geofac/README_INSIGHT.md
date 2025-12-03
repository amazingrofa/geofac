# Zeta-Guided Geofac (The Insight)

This module `geofac_zeta_guided.py` implements the **"Equidistributed Periodic Tori with Twisted Ruelle Zetas"** insight.

It replaces the standard "blind" geometric search with a structured, arithmetically tuned search based on three advanced mathematical principles:

## 1. Equidistribution (The "Donut" Shape)
*   **Concept:** Random points clump together. "Perfect" points spread out evenly (equidistribution).
*   **Implementation:** We use **Sobol Sequences** (Quasi-Monte Carlo) instead of Python's `random.randint`.
*   **Effect:** Coverage of the search window converges at rate $O(1/N)$ instead of $O(1/\sqrt{N})$.

## 2. Torsion (The "Twisted Zeta")
*   **Concept:** The Ruelle Zeta function evaluates to an "exact torsion number" at zero, counting special signed loops.
*   **Implementation:** We modulate the standard Dirichlet kernel with a `zeta_modulation` factor.
    *   We derive "torsion phases" from the bits of $N$.
    *   We sum cosine waves with these phases to create "arithmetic interference."
*   **Effect:** The search prioritizes regions where the "arithmetic resonance" is high, effectively guessing where the factors *should* be based on the number's topology.

## 3. Fractal Scaling (The "Power Law")
*   **Concept:** Errors in these systems follow "fractal power laws" in the strong coupling limit.
*   **Implementation:** We apply a power-law transformation ($x \to x^\gamma$, with $\gamma=1.5$) to the search window.
*   **Effect:** This clusters sampling density near the "resonance valley" (the center of the window) while still allowing long-tail searches, matching the predicted error distribution.

## Usage

```bash
python3 geofac_zeta_guided.py <N> --window 10000000 --samples 65536
```

*Note: Use a power of 2 for `samples` (e.g., 65536) to maximize Sobol sequence balance.

```