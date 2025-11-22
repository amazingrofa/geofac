#!/usr/bin/env python3
"""
Run Complete Z5D Comprehensive Challenge Experiment
====================================================

Executes all 6 steps in sequence with proper error handling.

Usage:
    python3 run_experiment.py [--quick]

Options:
    --quick: Run quick validation only (tests + API check)
"""

import sys
import subprocess
import time
from pathlib import Path


def run_command(cmd, description, timeout=None):
    """Run a command with nice output."""
    print(f"\n{'='*70}")
    print(f"Step: {description}")
    print('='*70)
    print(f"Command: {' '.join(cmd)}")
    print()
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=False,
            text=True
        )
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"\n✓ {description} completed in {elapsed:.2f}s")
            return True
        else:
            print(f"\n✗ {description} failed with exit code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print(f"\n⏱ {description} timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"\n✗ {description} failed with error: {e}")
        return False


def main():
    """Run full experiment."""
    quick_mode = '--quick' in sys.argv
    
    print("="*70)
    print("Z5D Comprehensive Challenge Experiment")
    print("="*70)
    print()
    
    if quick_mode:
        print("Running in QUICK mode (validation only)")
        print()
        
        # Run tests
        if not run_command(
            ['python3', '-m', 'pytest', 'test_z5d_comprehensive.py', '-v'],
            "Run test suite"
        ):
            print("\n✗ Tests failed. Fix errors before proceeding.")
            return 1
        
        # Test Z5D API
        if not run_command(
            ['python3', 'z5d_api.py'],
            "Test Z5D API",
            timeout=30
        ):
            print("\n✗ Z5D API test failed.")
            return 1
        
        print("\n" + "="*70)
        print("✓ Quick validation passed!")
        print("="*70)
        print("\nTo run full experiment: python3 run_experiment.py")
        return 0
    
    # Full experiment
    steps = [
        (['python3', '-m', 'pytest', 'test_z5d_comprehensive.py', '-v'],
         "Step 0: Run tests", 60),
        
        (['python3', 'calibrate_bands.py'],
         "Step 1: Calibration", 300),
        
        (['python3', 'rehearsal_60_96bit.py'],
         "Step 3: Rehearsal (60-96 bit)", 1800),
        
        (['python3', 'parameterize_127bit.py'],
         "Step 4: Parameterize 127-bit", 60),
        
        (['python3', 'production_run.py'],
         "Step 5: Production run", 3900),
        
        (['python3', 'analyze_results.py'],
         "Step 6: Analyze results", 60),
    ]
    
    start_time = time.time()
    
    for cmd, desc, timeout in steps:
        if not run_command(cmd, desc, timeout):
            print(f"\n✗ Experiment stopped at: {desc}")
            return 1
    
    total_time = time.time() - start_time
    
    print("\n" + "="*70)
    print("✓ Full experiment completed!")
    print("="*70)
    print(f"Total time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
    print()
    print("Generated artifacts:")
    artifacts = [
        'calibration_results.json',
        'rehearsal_results.json',
        'challenge_params.json',
        'run_log.jsonl',
        'production_summary.json',
        'ANALYSIS_SUMMARY.md'
    ]
    
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {artifact} ({size:,} bytes)")
        else:
            print(f"  ✗ {artifact} (missing)")
    
    print()
    print("Review ANALYSIS_SUMMARY.md for results.")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
