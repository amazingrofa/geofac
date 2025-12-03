import math
import sys
from pathlib import Path

import numpy as np

# Ensure src/ is on path for imports.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.append(str(SRC))

from rsh.signal import generate_error_signal  # noqa: E402
from rsh.frequency import detect_local_frequency, estimate_chirp  # noqa: E402
from rsh.slope import derive_candidates  # noqa: E402
from rsh.core import factorize_rsh  # noqa: E402


def test_generate_error_signal_simple():
    n = 15  # factors 3 and 5
    a0 = math.isqrt(n)
    if a0 * a0 < n:
        a0 += 1
    sig = generate_error_signal(n, a0, 3)
    # First sample at x = ceil(sqrt(15)) = 4 => sqrt(1) = 1, error = 0
    assert np.isclose(sig[0], 0.0)
    assert len(sig) == 3


def test_detect_local_frequency_amplitude_modulation():
    length = 256
    k = np.arange(length)
    f_env = 0.125  # cycles/step (period 8)
    f_carrier = 0.4
    signal = (1.0 + 0.6 * np.sin(2 * np.pi * f_env * k)) * np.sin(
        2 * np.pi * f_carrier * k
    )
    freq, _phase = detect_local_frequency(signal)
    assert abs(freq - f_env) < 0.02  # allow small spectral leakage tolerance


def test_derive_candidates_matches_constructed_phase():
    n = 77  # 7 * 11
    a0 = math.isqrt(n)
    if a0 * a0 < n:
        a0 += 1
    window_size = 256

    # Engineer a phase so that dk steers k to the known solution (k ~ 1).
    freq = 0.25
    target_phase = 0.0
    k_target = 1.0
    dk_needed = k_target - window_size
    phase = target_phase - dk_needed * 2 * np.pi * freq  # large positive phase

    candidates = derive_candidates(
        n=n,
        a0=a0,
        window_size=window_size,
        freq=freq,
        phase=phase,
        target_phases=[target_phase],
        max_period_multiples=0,
    )
    assert (7, 11) in candidates or (11, 7) in candidates


def test_factorize_rsh_with_stub_detector():
    n = 77
    window_size = 256

    # Stub detector that reuses the engineered freq/phase from the previous test.
    freq = 0.25
    target_phase = 0.0
    dk_needed = 1.0 - window_size
    phase = target_phase - dk_needed * 2 * np.pi * freq

    def stub_detector(_signal):
        return freq, phase

    result = factorize_rsh(
        n=n,
        window_size=window_size,
        target_phases=[target_phase],
        max_period_multiples=0,
        detector=stub_detector,
    )
    assert result == (7, 11)


def test_estimate_chirp_recovers_model_parameters():
    c_true = 0.3
    k0_true = 5.0
    length = 256
    k = np.arange(length)
    freq = c_true / np.sqrt(k + k0_true)
    phase = np.cumsum(2 * np.pi * freq)
    signal = np.sin(phase)

    est = estimate_chirp(signal)
    assert est is not None
    c_est, k0_est = est
    assert abs(c_est - c_true) / c_true < 0.15
    assert 1.0 < k0_est < 50.0


def test_chirp_candidates_with_empty_targets():
    n = 77
    a0 = math.isqrt(n)
    if a0 * a0 < n:
        a0 += 1

    candidates = derive_candidates(
        n=n,
        a0=a0,
        window_size=1,
        freq=0.0,  # skip base freq branch; rely on chirp extrapolation only
        phase=0.0,
        target_phases=None,
        max_period_multiples=0,
        chirp_params=(0.5, 1.0),
    )
    assert (7, 11) in candidates or (11, 7) in candidates
