import sys
from pathlib import Path

import importlib.util
import pytest

# Add repo root for imports
ROOT = Path(__file__).resolve().parents[1]

MODULE_PATH = ROOT / "experiments" / "final-factorization-127bit" / "run_completion.py"
spec = importlib.util.spec_from_file_location("run_completion_ff", MODULE_PATH)
run_completion = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(run_completion)

generate_candidates_from_spikes = run_completion.generate_candidates_from_spikes
apply_gva_filter = run_completion.apply_gva_filter


def test_candidate_generation_deterministic():
    N = 1125899772623531  # 50-bit gate example
    spikes = [
        {
            "b": 10.0,
            "tau_triple_prime": 0.1,
            "magnitude": 0.1,
            "error": 1e-6,
            "quality": 1e5,
        }
    ]

    first = generate_candidates_from_spikes(N, spikes, search_radius_bits=0.2, max_candidates_per_spike=10, total_max_candidates=20)
    second = generate_candidates_from_spikes(N, spikes, search_radius_bits=0.2, max_candidates_per_spike=10, total_max_candidates=20)

    assert [c["candidate"] for c in first] == [c["candidate"] for c in second]


def test_no_injected_factors():
    N = 1125899772623531
    spikes = [
        {
            "b": 10.0,
            "tau_triple_prime": 0.1,
            "magnitude": 0.1,
            "error": 1e-6,
            "quality": 1e5,
        }
    ]
    candidates = generate_candidates_from_spikes(N, spikes, search_radius_bits=0.1, max_candidates_per_spike=5, total_max_candidates=10)
    # The search window is near 2^10 (~1024), far from the true 50-bit factors, so they shouldn't appear.
    assert all(c["candidate"] < 10_000 for c in candidates)


def test_gva_filter_prefers_true_divisor():
    N = 15
    candidates = [
        {"candidate": 3, "tau_score": 1.0},
        {"candidate": 4, "tau_score": 1.0},
    ]
    ranked = apply_gva_filter(N, candidates, k_values=[0.35])
    assert ranked[0]["candidate"] == 3
    assert ranked[0]["gva_is_divisor"] is True
