"""
Frequency detection for Resonant Slope Hunter.

Extracts the dominant envelope frequency and phase from a local window of the
quantization error signal using Hilbert transform + FFT.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy.signal import hilbert, detrend
from scipy.signal.windows import hann
from scipy.optimize import curve_fit


def detect_local_frequency(signal: np.ndarray) -> Tuple[float, float]:
    """
    Detect the dominant envelope frequency and phase.

    Pipeline:
      1) Analytic signal via Hilbert transform.
      2) Envelope magnitude.
      3) Linear detrend + zero-mean.
      4) Hann window taper.
      5) FFT; select dominant non-DC bin.

    Args:
        signal: 1D NumPy array of real values (error signal window).

    Returns:
        (frequency, phase) where frequency is in cycles per sample (step),
        and phase is the angle (radians) of the dominant FFT component.
        Returns (0.0, 0.0) if no meaningful frequency is found.
    """
    if signal.ndim != 1:
        raise ValueError("signal must be 1-D")
    if len(signal) < 2:
        return 0.0, 0.0

    analytic = hilbert(signal)
    envelope = np.abs(analytic)

    envelope_detrended = detrend(envelope, type="linear")
    envelope_zero_mean = envelope_detrended - np.mean(envelope_detrended)

    window = hann(len(envelope_zero_mean))
    tapered = envelope_zero_mean * window

    yf = np.fft.rfft(tapered)
    freqs = np.fft.rfftfreq(len(tapered), d=1.0)

    magnitude = np.abs(yf)
    if len(magnitude) < 2:
        return 0.0, 0.0

    # Ignore DC (index 0) to focus on oscillatory content.
    idx = 1 + int(np.argmax(magnitude[1:]))
    dominant_freq = float(freqs[idx])
    dominant_phase = float(np.angle(yf[idx]))
    return dominant_freq, dominant_phase


def estimate_chirp(signal: np.ndarray, k_offset: float = 0.0) -> Tuple[float, float] | None:
    """
    Estimate reciprocal-sqrt chirp parameters from instantaneous frequency.

    Model: f_inst(k) = c / sqrt(k + k0)

    Args:
        signal: Real 1-D error signal window.
        k_offset: Offset to add to the sample index (useful when the window
            is not starting at k=0 in the global search).

    Returns:
        (c, k0) if a fit succeeds, else None.
    """
    if signal.ndim != 1 or len(signal) < 4:
        return None

    analytic = hilbert(signal)
    phase = np.unwrap(np.angle(analytic))
    inst_freq = np.diff(phase) / (2.0 * np.pi)

    if np.allclose(inst_freq, 0):
        return None

    t = np.arange(len(inst_freq), dtype=float) + float(k_offset)

    valid = inst_freq > 1e-6
    if np.count_nonzero(valid) < 4:
        return None

    inst_freq = inst_freq[valid]
    t = t[valid]

    def model(t_val, c, k0):
        return c / np.sqrt(t_val + k0)

    f0 = float(inst_freq[0])
    c_init = f0 * np.sqrt(t[0] + 1.0)
    k0_init = max(1e-3, (c_init / max(f0, 1e-6)) ** 2 - t[0])

    try:
        popt, _ = curve_fit(
            model,
            t,
            inst_freq,
            p0=(c_init, k0_init),
            bounds=([0.0, 1e-6], [np.inf, np.inf]),
            maxfev=20000,
        )
    except Exception:
        return None

    c_est, k0_est = float(popt[0]), float(popt[1])
    if not np.isfinite(c_est) or not np.isfinite(k0_est) or k0_est <= 0:
        return None
    return c_est, k0_est
