"""
Test suite for adaptive windowing falsification experiment.

Tests the hypothesis against all validation gates:
- Gate 1: 30-bit (1073217479 = 32749 × 32771)
- Gate 2: 60-bit (1152921470247108503 = 1073741789 × 1073741827)  
- Gate 3: 127-bit CHALLENGE (137524771864208156028430259349934309717)
"""

import pytest
import time
from adversarial_test_adaptive import AdaptiveFactorization, WindowResult


# Validation gate test numbers from docs/validation/VALIDATION_GATES.md
GATE_1_30BIT = {
    'N': 1073217479,
    'p': 32749,
    'q': 32771,
    'bits': 30
}

GATE_2_60BIT = {
    'N': 1152921470247108503,
    'p': 1073741789,
    'q': 1073741827,
    'bits': 60
}

GATE_3_127BIT = {
    'N': 137524771864208156028430259349934309717,
    'p': 10508623501177419659,
    'q': 13086849276577416863,
    'bits': 127
}


class TestAdaptiveWindowing:
    """Test adaptive windowing strategy on validation gates."""
    
    def test_gate1_30bit_instantiation(self):
        """Test that solver can be instantiated with 30-bit number."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        assert solver.N == GATE_1_30BIT['N']
        assert solver.sqrt_N > 0
        assert len(solver.windows) == 9
    
    def test_gate2_60bit_instantiation(self):
        """Test that solver can be instantiated with 60-bit number."""
        solver = AdaptiveFactorization(GATE_2_60BIT['N'])
        assert solver.N == GATE_2_60BIT['N']
        assert solver.sqrt_N > 0
    
    def test_gate3_127bit_instantiation(self):
        """Test that solver can be instantiated with 127-bit number."""
        solver = AdaptiveFactorization(GATE_3_127BIT['N'])
        assert solver.N == GATE_3_127BIT['N']
        assert solver.sqrt_N > 0
    
    def test_candidate_generation_deterministic(self):
        """Test that candidate generation is deterministic with same seed."""
        solver1 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=42)
        solver2 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=42)
        
        candidates1 = solver1.generate_candidates(0.13, count=100)
        candidates2 = solver2.generate_candidates(0.13, count=100)
        
        assert candidates1 == candidates2, "Candidate generation must be deterministic"
    
    def test_candidate_generation_different_seeds(self):
        """Test that different seeds produce different candidates."""
        solver1 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=42)
        solver2 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=99)
        
        candidates1 = solver1.generate_candidates(0.13, count=100)
        candidates2 = solver2.generate_candidates(0.13, count=100)
        
        assert candidates1 != candidates2, "Different seeds should produce different candidates"
    
    def test_candidate_range_bounds(self):
        """Test that candidates are within expected range."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        window = 0.13
        candidates = solver.generate_candidates(window, count=1000)
        
        range_val = int(solver.sqrt_N * window)
        lower = max(2, solver.sqrt_N - range_val)
        upper = solver.sqrt_N + range_val
        
        for candidate in candidates:
            assert lower <= candidate <= upper, f"Candidate {candidate} outside range [{lower}, {upper}]"
    
    def test_enrichment_calculation_zero_high_signal(self):
        """Test enrichment when no high-signal scores."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        scores = [-1.0] * 100  # All above baseline
        enrichment = solver.compute_enrichment(scores, baseline=-5.0)
        assert enrichment == 0.0
    
    def test_enrichment_calculation_all_high_signal(self):
        """Test enrichment when all scores are high-signal."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        scores = [-10.0] * 100  # All below baseline
        enrichment = solver.compute_enrichment(scores, baseline=-5.0)
        # 100/100 = 1.0, 1.0 / 0.001 = 1000x enrichment
        assert enrichment == 1000.0
    
    def test_window_scan_returns_result(self):
        """Test that window scan returns valid result."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        result = solver.scan_window(0.13, sample_count=1000)
        
        assert isinstance(result, WindowResult)
        assert result.window_size == 0.13
        assert result.candidates_checked == 1000
        assert result.duration >= 0
        assert len(result.top_candidates) == 10
    
    def test_check_true_factors_found(self):
        """Test detection when true factor is in candidates."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        p, q = GATE_1_30BIT['p'], GATE_1_30BIT['q']
        
        # Create candidate list with true factor
        candidates = [(p, -8.0), (12345, -7.0), (67890, -6.0)]
        found, rank = solver.check_true_factors(candidates, p, q)
        
        assert found is True
        assert rank == 1
    
    def test_check_true_factors_not_found(self):
        """Test detection when true factor is not in candidates."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        p, q = GATE_1_30BIT['p'], GATE_1_30BIT['q']
        
        # Create candidate list without true factors
        candidates = [(12345, -8.0), (67890, -7.0), (11111, -6.0)]
        found, rank = solver.check_true_factors(candidates, p, q)
        
        assert found is False
        assert rank == -1
    
    @pytest.mark.slow
    def test_gate1_30bit_full_run(self):
        """Test full adaptive windowing run on 30-bit gate."""
        solver = AdaptiveFactorization(
            GATE_1_30BIT['N'],
            seed=42
        )
        
        start = time.time()
        result = solver.run(
            p=GATE_1_30BIT['p'],
            q=GATE_1_30BIT['q'],
            verbose=False
        )
        duration = time.time() - start
        
        # Document the result
        print(f"\nGate 1 (30-bit) result:")
        print(f"  Signal lock: {result is not None}")
        print(f"  Duration: {duration:.2f}s")
        if result:
            print(f"  Top 3 candidates: {result[:3]}")
    
    @pytest.mark.slow
    def test_gate2_60bit_full_run(self):
        """Test full adaptive windowing run on 60-bit gate."""
        solver = AdaptiveFactorization(
            GATE_2_60BIT['N'],
            seed=42
        )
        
        start = time.time()
        result = solver.run(
            p=GATE_2_60BIT['p'],
            q=GATE_2_60BIT['q'],
            verbose=False
        )
        duration = time.time() - start
        
        # Document the result
        print(f"\nGate 2 (60-bit) result:")
        print(f"  Signal lock: {result is not None}")
        print(f"  Duration: {duration:.2f}s")
        if result:
            print(f"  Top 3 candidates: {result[:3]}")
    
    @pytest.mark.slow
    def test_gate3_127bit_full_run(self):
        """Test full adaptive windowing run on 127-bit CHALLENGE."""
        solver = AdaptiveFactorization(
            GATE_3_127BIT['N'],
            seed=42
        )
        
        start = time.time()
        result = solver.run(
            p=GATE_3_127BIT['p'],
            q=GATE_3_127BIT['q'],
            verbose=False
        )
        duration = time.time() - start
        
        # Document the result
        print(f"\nGate 3 (127-bit CHALLENGE) result:")
        print(f"  Signal lock: {result is not None}")
        print(f"  Duration: {duration:.2f}s")
        if result:
            print(f"  Top 3 candidates: {result[:3]}")
    
    def test_reproducibility_across_runs(self):
        """Test that runs with same seed produce identical results."""
        solver1 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=42)
        solver2 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=42)
        
        result1 = solver1.scan_window(0.13, sample_count=100)
        result2 = solver2.scan_window(0.13, sample_count=100)
        
        assert result1.enrichment == result2.enrichment
        assert result1.top_candidates == result2.top_candidates
    
    def test_window_progression(self):
        """Test that windows are scanned in correct order."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        expected_windows = [0.13, 0.20, 0.30, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0]
        assert solver.windows == expected_windows


class TestEnrichmentMetrics:
    """Test enrichment calculation edge cases."""
    
    def test_empty_scores(self):
        """Test enrichment with empty score list."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        enrichment = solver.compute_enrichment([])
        assert enrichment == 0.0
    
    def test_all_baseline_scores(self):
        """Test enrichment when all scores equal baseline."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        scores = [-5.0] * 100
        enrichment = solver.compute_enrichment(scores, baseline=-5.0)
        assert enrichment == 0.0  # None below baseline
    
    def test_mixed_scores(self):
        """Test enrichment with mixed scores."""
        solver = AdaptiveFactorization(GATE_1_30BIT['N'])
        # 10 high-signal out of 100
        scores = [-10.0] * 10 + [-1.0] * 90
        enrichment = solver.compute_enrichment(scores, baseline=-5.0)
        # 10/100 = 0.1, 0.1 / 0.001 = 100x
        assert enrichment == 100.0


class TestValidationCompliance:
    """Test compliance with validation gates and coding style."""
    
    def test_precision_formula_documented(self):
        """Test that precision formula is documented (from CODING_STYLE.md)."""
        # Precision should be: max(configured, N.bitLength() * 4 + 200)
        # This test just verifies the formula is known
        N = GATE_3_127BIT['N']
        min_precision = N.bit_length() * 4 + 200
        # For 127-bit number: 127 * 4 + 200 = 708
        assert min_precision == 708
    
    def test_no_stochastic_methods(self):
        """Verify no truly stochastic methods (deterministic with seed)."""
        # With same seed, results must be identical
        solver1 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=42)
        solver2 = AdaptiveFactorization(GATE_1_30BIT['N'], seed=42)
        
        # Run multiple windows
        results1 = [solver1.scan_window(w, sample_count=100) for w in [0.13, 0.20]]
        results2 = [solver2.scan_window(w, sample_count=100) for w in [0.13, 0.20]]
        
        for r1, r2 in zip(results1, results2):
            assert r1.enrichment == r2.enrichment
            assert r1.top_candidates == r2.top_candidates
    
    def test_validation_gate_numbers_correct(self):
        """Verify validation gate numbers match docs/validation/VALIDATION_GATES.md."""
        # Gate 1: 30-bit
        assert GATE_1_30BIT['N'] == 1073217479
        assert GATE_1_30BIT['p'] * GATE_1_30BIT['q'] == GATE_1_30BIT['N']
        
        # Gate 2: 60-bit
        assert GATE_2_60BIT['N'] == 1152921470247108503
        assert GATE_2_60BIT['p'] * GATE_2_60BIT['q'] == GATE_2_60BIT['N']
        
        # Gate 3: 127-bit CHALLENGE
        assert GATE_3_127BIT['N'] == 137524771864208156028430259349934309717
        assert GATE_3_127BIT['p'] * GATE_3_127BIT['q'] == GATE_3_127BIT['N']
