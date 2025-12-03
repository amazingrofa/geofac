"""
Frequency/phase to factor candidate mapping for Resonant Slope Hunter.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Tuple

import numpy as np


def _candidate_from_k(n: int, a0: int, k_estimate: float) -> Tuple[int, int] | None:
    """
    Convert a k-position estimate into a factor candidate using Fermat form.

    Args:
        n: Target integer.
        a0: ceil(sqrt(n)) reference.
        k_estimate: Estimated position offset (1-indexed within the window).

    Returns:
        (p, q) if a perfect square is found, else None.
    """
    a = a0 + int(round(k_estimate)) - 1
    if a <= 1:
        return None
    delta = a * a - n
    if delta < 0:
        return None
    b = int(round(math.isqrt(delta)))
    if b * b != delta:
        return None
    p = a - b
    q = a + b
    if p <= 1 or q <= 1:
        return None
    if n % p != 0:
        return None
    return (p, q) if p <= q else (q, p)


def derive_candidates(
    n: int,
    a0: int,
    window_size: int,
    freq: float,
    phase: float,
    target_phases: Iterable[float] | None = None,
    max_period_multiples: int = 10,
    chirp_params: Tuple[float, float] | None = None,
) -> List[Tuple[int, int]]:
    """
    Derive factor candidates from detected frequency/phase.

    Formula (per provided research notes):
        dk = (target_phase - phase) / (2*pi*freq)
        k = current_k + dk, current_k = window_size
        a = a0 + k - 1
        delta = a^2 - n
        if delta is square: p = a - b
        Additionally explore dk + m*(1/freq) for m=1..max_period_multiples

    Args:
        n: Target integer to factor.
        a0: ceil(sqrt(n)).
        window_size: Length of the error-signal window (current_k).
        freq: Dominant frequency (cycles/step).
        phase: Phase (radians) at the dominant frequency bin.
        target_phases: Iterable of target phase alignments to try; defaults
            to [0, pi/2, pi, 3pi/2].
        max_period_multiples: How many additional period jumps to try.
        chirp_params: Optional tuple (c, k0) for the reciprocal-sqrt model of
            instantaneous frequency; enables extrapolation via phase
            integration beyond the local window.

    Returns:
        List of unique (p, q) pairs (p <= q) that divide n.
    """
    found: List[Tuple[int, int]] = []
    seen = set()

    targets = (
        list(target_phases)
        if target_phases is not None
        else [0.0, math.pi / 2, math.pi, 3 * math.pi / 2]
    )
    current_k = float(window_size)

    if freq > 0:
        period = 1.0 / freq

        for tgt in targets:
            dk_base = (tgt - phase) / (2.0 * math.pi * freq)
            for m in range(max_period_multiples + 1):
                dk = dk_base + m * period
                k_est = current_k + dk
                candidate = _candidate_from_k(n, a0, k_est)
                if candidate is None:
                    continue
                if candidate in seen:
                    continue
                seen.add(candidate)
                found.append(candidate)

    if chirp_params is not None:
        c, k0 = chirp_params
        if c > 0 and k0 > 0:
            sqrt_current = math.sqrt(current_k + k0)
            for tgt in targets:
                for m in range(max_period_multiples + 1):
                    delta_phase = tgt + 2.0 * math.pi * m - phase
                    step = delta_phase / (4.0 * math.pi * c)
                    sqrt_target = sqrt_current + step
                    if sqrt_target <= 0:
                        continue
                    k_est = (sqrt_target * sqrt_target) - k0
                    candidate = _candidate_from_k(n, a0, k_est)
                    if candidate is None or candidate in seen:
                        continue
                    seen.add(candidate)
                    found.append(candidate)
    return found
