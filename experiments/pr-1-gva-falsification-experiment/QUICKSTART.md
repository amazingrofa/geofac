# GVA 5D Falsification Experiment - Quick Start

## Prerequisites

```bash
pip install mpmath scipy numpy
```

## Quick Test (5 minutes)

Test on CHALLENGE_127 with 100K samples:

```bash
python3 gva_5d_falsification.py --target CHALLENGE_127 --samples 100000
```

## Full Falsification Tests

### RSA-100 Test (Several hours)

```bash
python3 gva_5d_falsification.py --target RSA-100 --samples 1000000
```

### RSA-129 Test (Very long)

```bash
python3 gva_5d_falsification.py --target RSA-129 --samples 1000000
```

## Understanding Results

The experiment outputs:
- Console summary with verdict
- JSON file with complete metrics: `results_<target>_<timestamp>.json`

### Key Metrics

- **Success**: Did we factor N?
- **Density Enhancement**: Change in candidate density from Jacobian weighting
- **Min Distance**: Smallest geodesic distance found (lower = closer to factor)
- **Candidates Tested**: Total candidates evaluated
- **Time**: Execution time per k-value

### Expected Outcomes

**CHALLENGE_127 (127-bit)**: Should NOT factor (validates operational baseline)
**RSA-100 (330-bit)**: Should NOT factor → **FALSIFIES** GVA hypothesis
**RSA-129 (427-bit)**: Should NOT factor → **FALSIFIES** GVA hypothesis

## Interpreting Falsification

The GVA hypothesis is **falsified** if:

1. ❌ Cannot factor RSA-100 within 10^6 samples
2. ❌ Density enhancement < 15% (claimed 15-20%)
3. ❌ No correlation between min distance and actual factors
4. ❌ No 100x speedup vs baseline

## Files Generated

- `results_*.json` - Complete experiment data
- Console output - Human-readable summary

## Troubleshooting

**ModuleNotFoundError: mpmath**
```bash
pip install mpmath
```

**scipy.stats.qmc not available**
- Falls back to golden ratio QMC (still functional)
- Install scipy for Sobol sequences: `pip install scipy`

**numpy not available**
- Bootstrap CIs disabled (still functional)
- Install numpy for confidence intervals: `pip install numpy`
