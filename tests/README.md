# Tests Directory

Organized test suite for GVA factorization across the operational range [10^14, 10^18].

## Test Structure

### Scale-Based Tests
- `test_gva_80bit.py` - 80-bit semiprime tests (below operational range, for baseline)
- `test_gva_90bit.py` - 90-bit semiprime tests (below operational range, for baseline)
- `test_gva_95bit.py` - 95-bit semiprime tests (approaching operational range)
- `test_gva_100bit.py` - 100-bit semiprime tests (10^14 lower boundary)
- `test_gva_105bit.py` - 105-bit semiprime tests (mid 10^14)
- `test_gva_110bit.py` - 110-bit semiprime tests (upper 10^14)
- `test_gva_115bit.py` - 115-bit semiprime tests (10^15-10^16)
- `test_gva_120bit.py` - 120-bit semiprime tests (mid 10^16)
- `test_gva_125bit.py` - 125-bit semiprime tests (10^17)
- `test_gva_130bit.py` - 130-bit semiprime tests (approaching 10^18)
- `test_gva_140bit.py` - 140-bit semiprime tests (above operational range)
- `test_gva_150bit.py` - 150-bit semiprime tests (above operational range)

### Method-Specific Tests
- `test_geometric_resonance.py` - Geometric resonance factorization method tests

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific bit-width tests
pytest tests/test_gva_100bit.py

# Run with verbose output
pytest tests/ -v

# Run tests for operational range only
pytest tests/test_gva_{100,105,110,115,120,125,130}bit.py
```

## Test Invariants

Per CODING_STYLE.md:
- All tests use RSA challenge numbers (no synthetic semiprimes)
- Operational range: [10^14, 10^18] (47-60 bits approximately)
- 127-bit whitelist: CHALLENGE_127 = 137524771864208156028430259349934309717
- No classical fallbacks (Pollard's Rho, trial division, ECM, sieves)
- Deterministic/quasi-deterministic methods only
- Explicit precision: max(configured, N.bitLength() × 4 + 200)

## Success Criteria

Tests must log:
- Exact parameters (precision, thresholds, sample counts, timeouts)
- Timestamps
- Measured outcomes (factorization time, candidates tested)
- Success/failure with reproducible seeds

