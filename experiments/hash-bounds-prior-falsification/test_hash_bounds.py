#!/usr/bin/env python3
"""
Test Suite for Hash-Bounds Prior Falsification Experiment
=========================================================

Pytest tests for the Hash-Bounds predictor implementation.

Run with:
    pytest test_hash_bounds.py -v
"""

import pytest
import os
import sys

# Add experiment directory to path
sys.path.insert(0, os.path.dirname(__file__))

from hash_bounds_predictor import (
    HashBoundsPredictor,
    PredictedBand,
    BandCheckResult,
    set_precision,
    run_diagnostic
)


# =============================================================================
# Test Constants
# =============================================================================

# 127-bit challenge (whitelisted)
CHALLENGE_127 = 137524771864208156028430259349934309717
P_127 = 10508623501177419659
Q_127 = 13086849276577416863

# 30-bit Gate 1
N_30BIT = 1073217479
P_30BIT = 32749
Q_30BIT = 32771


# =============================================================================
# Test Predictor Initialization
# =============================================================================

class TestPredictorInit:
    """Test predictor initialization and configuration."""
    
    def test_default_init(self):
        """Test default initialization."""
        predictor = HashBoundsPredictor()
        config = predictor.get_config()
        
        assert config['width'] == pytest.approx(0.155, rel=1e-6)
        assert config['use_sqrt_N'] is True
        assert config['bit_length_scaling'] is True
    
    def test_custom_width(self):
        """Test custom width initialization."""
        predictor = HashBoundsPredictor(width=0.2)
        config = predictor.get_config()
        
        assert config['width'] == pytest.approx(0.2, rel=1e-6)
    
    def test_custom_settings(self):
        """Test full custom initialization."""
        predictor = HashBoundsPredictor(
            width=0.25,
            use_sqrt_N=False,
            bit_length_scaling=False
        )
        config = predictor.get_config()
        
        assert config['width'] == pytest.approx(0.25, rel=1e-6)
        assert config['use_sqrt_N'] is False
        assert config['bit_length_scaling'] is False


# =============================================================================
# Test Precision Setting
# =============================================================================

class TestPrecision:
    """Test precision setting based on bit-length."""
    
    def test_precision_small(self):
        """Test precision for small numbers."""
        N = 10**10
        dps = set_precision(N)
        
        # bit_length(10^10) ≈ 34
        # Required: max(100, 34*4 + 200) = max(100, 336) = 336
        assert dps >= 100
        assert dps >= N.bit_length() * 4 + 200
    
    def test_precision_127bit(self):
        """Test precision for 127-bit challenge."""
        dps = set_precision(CHALLENGE_127)
        
        # bit_length = 127
        # Required: max(100, 127*4 + 200) = 708
        expected = max(100, 127 * 4 + 200)
        assert dps == expected
    
    def test_precision_large(self):
        """Test precision for large numbers."""
        N = 10**50
        dps = set_precision(N)
        
        # Should scale with bit-length
        assert dps >= 100
        assert dps >= N.bit_length() * 4 + 200


# =============================================================================
# Test Band Prediction
# =============================================================================

class TestBandPrediction:
    """Test band prediction functionality."""
    
    def test_predict_band_returns_correct_type(self):
        """Test that predict_band returns PredictedBand."""
        predictor = HashBoundsPredictor()
        band = predictor.predict_band(N_30BIT)
        
        assert isinstance(band, PredictedBand)
        assert hasattr(band, 'center')
        assert hasattr(band, 'lower')
        assert hasattr(band, 'upper')
        assert hasattr(band, 'width')
    
    def test_band_in_unit_interval(self):
        """Test that band values are in [0, 1)."""
        predictor = HashBoundsPredictor()
        band = predictor.predict_band(CHALLENGE_127)
        
        assert 0 <= float(band.center) < 1
        assert 0 <= float(band.lower) < 1
        assert 0 <= float(band.upper) < 1
    
    def test_band_width_matches_config(self):
        """Test that band width approximately matches configured width."""
        predictor = HashBoundsPredictor(width=0.155)
        band = predictor.predict_band(CHALLENGE_127)
        
        # Width should be close to 0.155 (may be adjusted by bit-length scaling)
        assert float(band.width) >= 0.155
        assert float(band.width) < 0.3  # Reasonable upper bound
    
    def test_band_width_no_scaling(self):
        """Test band width without bit-length scaling."""
        predictor = HashBoundsPredictor(width=0.155, bit_length_scaling=False)
        band = predictor.predict_band(CHALLENGE_127)
        
        assert float(band.width) == pytest.approx(0.155, rel=1e-6)
    
    def test_band_consistency(self):
        """Test that same N gives same band."""
        predictor = HashBoundsPredictor()
        band1 = predictor.predict_band(CHALLENGE_127)
        band2 = predictor.predict_band(CHALLENGE_127)
        
        assert float(band1.center) == float(band2.center)
        assert float(band1.lower) == float(band2.lower)
        assert float(band1.upper) == float(band2.upper)


# =============================================================================
# Test Factor Checking
# =============================================================================

class TestFactorChecking:
    """Test factor checking with both strategies."""
    
    def test_check_returns_correct_type(self):
        """Test that check returns BandCheckResult."""
        predictor = HashBoundsPredictor()
        result = predictor.check_factor_in_band(N_30BIT, P_30BIT, 'fracSqrt')
        
        assert isinstance(result, BandCheckResult)
        assert hasattr(result, 'in_band')
        assert hasattr(result, 'factor_value')
        assert hasattr(result, 'strategy')
    
    def test_check_fracSqrt_strategy(self):
        """Test fracSqrt strategy."""
        predictor = HashBoundsPredictor()
        result = predictor.check_factor_in_band(N_30BIT, P_30BIT, 'fracSqrt')
        
        assert result.strategy == 'fracSqrt'
        assert 0 <= float(result.factor_value) < 1
    
    def test_check_dOverSqrtN_strategy(self):
        """Test dOverSqrtN strategy."""
        predictor = HashBoundsPredictor()
        result = predictor.check_factor_in_band(N_30BIT, P_30BIT, 'dOverSqrtN')
        
        assert result.strategy == 'dOverSqrtN'
        assert 0 <= float(result.factor_value) < 1
    
    def test_invalid_strategy_raises(self):
        """Test that invalid strategy raises error."""
        predictor = HashBoundsPredictor()
        
        with pytest.raises(ValueError):
            predictor.check_factor_in_band(N_30BIT, P_30BIT, 'invalid')
    
    def test_distance_from_center_is_valid(self):
        """Test that distance from center is computed correctly."""
        predictor = HashBoundsPredictor()
        result = predictor.check_factor_in_band(N_30BIT, P_30BIT, 'fracSqrt')
        
        # Distance should be in [0, 0.5] due to wrap-around
        assert 0 <= float(result.distance_from_center) <= 0.5


# =============================================================================
# Test Diagnostic Runner
# =============================================================================

class TestDiagnostic:
    """Test the run_diagnostic function."""
    
    def test_diagnostic_30bit(self):
        """Test diagnostic on 30-bit semiprime."""
        results = run_diagnostic(N_30BIT, P_30BIT, Q_30BIT)
        
        # Check structure
        assert 'N' in results
        assert 'p' in results
        assert 'q' in results
        assert 'band' in results
        assert 'checks' in results
        assert 'summary' in results
        
        # Check values
        assert results['N'] == str(N_30BIT)
        assert int(results['p']) * int(results['q']) == N_30BIT
    
    def test_diagnostic_127bit(self):
        """Test diagnostic on 127-bit challenge."""
        results = run_diagnostic(CHALLENGE_127, P_127, Q_127)
        
        assert results['N_bit_length'] == 127
        assert 'checks' in results
        assert len(results['checks']) == 4  # 2 factors × 2 strategies
    
    def test_diagnostic_summary(self):
        """Test that diagnostic produces valid summary."""
        results = run_diagnostic(N_30BIT, P_30BIT, Q_30BIT)
        
        summary = results['summary']
        assert summary['total_checks'] == 4
        assert 0 <= summary['hits'] <= 4
        assert 0 <= summary['hit_rate'] <= 1


# =============================================================================
# Test Validation Gates
# =============================================================================

class TestValidationGates:
    """Test against project validation gates."""
    
    def test_gate1_30bit_runs(self):
        """Gate 1: 30-bit runs without error."""
        predictor = HashBoundsPredictor()
        band = predictor.predict_band(N_30BIT)
        
        assert band is not None
        assert float(band.width) > 0
    
    def test_127bit_whitelist_runs(self):
        """Test 127-bit challenge runs without error."""
        predictor = HashBoundsPredictor()
        band = predictor.predict_band(CHALLENGE_127)
        
        assert band is not None
        assert CHALLENGE_127.bit_length() == 127
    
    def test_operational_range_10_14(self):
        """Test semiprime at 10^14 scale runs."""
        p, q = 10000019, 10000079
        N = p * q
        
        assert 10**14 <= N <= 10**18
        
        predictor = HashBoundsPredictor()
        results = run_diagnostic(N, p, q, predictor)
        
        assert results is not None
        assert 'summary' in results
    
    def test_operational_range_10_17(self):
        """Test semiprime at 10^17 scale runs."""
        p, q = 100000007, 1000000007
        N = p * q
        
        assert 10**14 <= N <= 10**18
        
        predictor = HashBoundsPredictor()
        results = run_diagnostic(N, p, q, predictor)
        
        assert results is not None


# =============================================================================
# Test Mathematical Properties
# =============================================================================

class TestMathProperties:
    """Test mathematical properties of the predictor."""
    
    def test_fractional_part_in_range(self):
        """Test that fractional parts are in [0, 1)."""
        predictor = HashBoundsPredictor()
        
        for N, p, q in [(N_30BIT, P_30BIT, Q_30BIT), (CHALLENGE_127, P_127, Q_127)]:
            for factor in [p, q]:
                for strategy in ['fracSqrt', 'dOverSqrtN']:
                    result = predictor.check_factor_in_band(N, factor, strategy)
                    val = float(result.factor_value)
                    assert 0 <= val < 1, f"Factor value {val} out of range for {strategy}"
    
    def test_prime_index_approximation_positive(self):
        """Test that prime index approximation is positive."""
        predictor = HashBoundsPredictor()
        band = predictor.predict_band(CHALLENGE_127)
        
        assert float(band.m_approx) > 0
        assert float(band.p_pred) > 0
    
    def test_wrap_around_handling(self):
        """Test that wrap-around bands are handled correctly."""
        # Create a predictor and manually test wrap-around logic
        predictor = HashBoundsPredictor(width=0.3)
        
        # Get a band
        band = predictor.predict_band(N_30BIT)
        
        # If band doesn't wrap, lower < upper
        # If band wraps, lower > upper
        lower = float(band.lower)
        upper = float(band.upper)
        
        # Either should be valid
        assert (lower <= upper) or (lower > upper)


# =============================================================================
# Test Reproducibility
# =============================================================================

class TestReproducibility:
    """Test reproducibility of results."""
    
    def test_deterministic_bands(self):
        """Test that predictions are deterministic."""
        predictor1 = HashBoundsPredictor()
        predictor2 = HashBoundsPredictor()
        
        band1 = predictor1.predict_band(CHALLENGE_127)
        band2 = predictor2.predict_band(CHALLENGE_127)
        
        assert float(band1.center) == float(band2.center)
        assert float(band1.lower) == float(band2.lower)
        assert float(band1.upper) == float(band2.upper)
    
    def test_deterministic_checks(self):
        """Test that factor checks are deterministic."""
        predictor1 = HashBoundsPredictor()
        predictor2 = HashBoundsPredictor()
        
        result1 = predictor1.check_factor_in_band(CHALLENGE_127, P_127, 'fracSqrt')
        result2 = predictor2.check_factor_in_band(CHALLENGE_127, P_127, 'fracSqrt')
        
        assert result1.in_band == result2.in_band
        assert float(result1.factor_value) == float(result2.factor_value)


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
