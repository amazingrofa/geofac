# Geometric Resonance Factorization - Python Implementation

This directory contains a complete Python/mpmath implementation of geometric resonance factorization for the 127-bit challenge.

## Quick Start

### Installation

```bash
pip install mpmath pytest
```

### Run Tests

```bash
# Fast tests (skip slow 127-bit factorization)
pytest test_geometric_resonance.py -v

# All tests including full factorization
pytest test_geometric_resonance.py -v -m slow
```

### Run Demo

```bash
python experiments/demo_geometric_resonance.py
```

### Run Full Factorization

```bash
python experiments/geometric_resonance_factorization.py
```

## Files

- **geometric_resonance_factorization.py** - Main factorization module
- **test_geometric_resonance.py** - Comprehensive test suite (20 tests)
- **demo_geometric_resonance.py** - Quick demonstration
- **docs/GEOMETRIC_RESONANCE_IMPLEMENTATION.md** - Complete documentation

## Features

- ✓ Z-framework forms (Z = A(B/c), discrete, number-theoretic)
- ✓ Dirichlet kernel resonance detection
- ✓ Golden-ratio QMC sampling (deterministic)
- ✓ Scale-adaptive parameter tuning (Z5D insights)
- ✓ Explicit precision: 704 decimal digits for 127-bit
- ✓ No classical fallbacks (pure geometric resonance)
- ✓ Complete reproducibility (pinned seeds, logged parameters)

## Documentation

See [docs/GEOMETRIC_RESONANCE_IMPLEMENTATION.md](docs/GEOMETRIC_RESONANCE_IMPLEMENTATION.md) for:
- Mathematical foundation
- Scale-adaptive parameter formulas
- Algorithm walkthrough
- Usage examples
- Expected output

## Target

**127-bit Challenge**: N = 137524771864208156028430259349934309717
- Expected factors: p = 10508623501177419659, q = 13086849276577416863
- Precision: 704 decimal digits
- Timeout: 10800 seconds (3 hours with scale-adaptive parameters)
