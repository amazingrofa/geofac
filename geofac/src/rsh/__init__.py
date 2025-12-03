"""
Resonant Slope Hunter (RSH) package.

Exports the main factorization entry point and helper utilities.
"""

from .core import factorize_rsh  # noqa: F401
from .signal import generate_error_signal  # noqa: F401
from .frequency import detect_local_frequency, estimate_chirp  # noqa: F401
from .slope import derive_candidates  # noqa: F401

__all__ = [
    "factorize_rsh",
    "generate_error_signal",
    "detect_local_frequency",
    "estimate_chirp",
    "derive_candidates",
]
