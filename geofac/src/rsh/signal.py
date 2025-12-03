"""
Signal utilities for Resonant Slope Hunter.

Generates the quantization error signal along the Fermat curve:
e(x) = sqrt(x^2 - N) - floor(sqrt(x^2 - N))
"""

from __future__ import annotations

import numpy as np


def generate_error_signal(n: int, x_start: int, window_size: int) -> np.ndarray:
    """
    Generate the quantization error signal for x in [x_start, x_start + window_size).

    Args:
        n: Composite integer to factor (assumed >= 4).
        x_start: Starting x value (typically ceil(sqrt(n))).
        window_size: Number of consecutive samples to generate.

    Returns:
        NumPy array of fractional errors e(x).
    """
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if x_start <= 0:
        raise ValueError("x_start must be positive")

    x = x_start + np.arange(window_size, dtype=np.int64)
    y_sq = x.astype(np.float64) ** 2 - float(n)
    # For x >= ceil(sqrt(n)), y_sq should be non-negative; guard numerical jitter.
    y_sq = np.clip(y_sq, a_min=0.0, a_max=None)
    y = np.sqrt(y_sq)
    error = y - np.floor(y)
    return error

