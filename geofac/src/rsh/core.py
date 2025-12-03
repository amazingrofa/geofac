"""
Main loop for the Resonant Slope Hunter (RSH) factorization prototype.
"""

from __future__ import annotations

import math
from typing import Callable, Iterable, List, Tuple

import numpy as np

from .signal import generate_error_signal
from .frequency import detect_local_frequency, estimate_chirp
from .slope import derive_candidates

# Type alias for custom detectors (useful in tests or experimentation).
DetectorFn = Callable[[np.ndarray], Tuple[float, float]]


def _ceil_sqrt(n: int) -> int:
    root = math.isqrt(n)
    return root if root * root == n else root + 1


def factorize_rsh(
    n: int,
    window_size: int = 256,
    target_phases: Iterable[float] | None = None,
    max_period_multiples: int = 10,
    x_start: int | None = None,
    detector: DetectorFn = detect_local_frequency,
    chirp_extrapolate: bool = False,
) -> Tuple[int, int] | None:
    """
    Attempt to factor n using the Resonant Slope Hunter heuristic.

    Steps:
      1) Choose x_start = ceil(sqrt(n)) if not provided.
      2) Generate error signal window of length window_size.
      3) Detect dominant envelope frequency & phase.
      4) Map frequency/phase to candidate k positions and test candidates.

    Args:
        n: Target integer (semiprime expected).
        window_size: Number of samples in the local window (default 256).
        target_phases: Phase alignments to try (defaults to 0, pi/2, pi, 3pi/2).
        max_period_multiples: How many period jumps (m/freq) to attempt.
        x_start: Optional explicit starting x; defaults to ceil(sqrt(n)).
        detector: Function that returns (freq, phase) from the signal window.
        chirp_extrapolate: If True, fit a reciprocal-sqrt chirp to the
            instantaneous frequency and use it for additional candidates.

    Returns:
        (p, q) with p <= q if a factorization is found, else None.
    """
    if n < 4:
        raise ValueError("n must be composite (>= 4).")
    if window_size <= 0:
        raise ValueError("window_size must be positive.")

    a0 = x_start if x_start is not None else _ceil_sqrt(n)

    signal = generate_error_signal(n, a0, window_size)
    freq, phase = detector(signal)

    # Optional chirp fit for highly unbalanced cases.
    chirp_params = None
    if chirp_extrapolate:
        chirp_params = estimate_chirp(signal, k_offset=0.0)

    candidates = derive_candidates(
        n=n,
        a0=a0,
        window_size=window_size,
        freq=freq,
        phase=phase,
        target_phases=target_phases,
        max_period_multiples=max_period_multiples,
        chirp_params=chirp_params,
    )

    if not candidates:
        return None

    # Return the smallest candidate pair for determinism.
    candidates_sorted = sorted(candidates, key=lambda pq: pq[0])
    return candidates_sorted[0]
