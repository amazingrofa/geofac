"""
Quick validation of the experiment framework.

This script demonstrates the core components without requiring dependencies
to be installed, using minimal synthetic examples.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def validate_structure():
    """Validate directory structure."""
    print("=== Validating Directory Structure ===")
    
    base = Path(__file__).parent
    
    required_files = [
        'README.md',
        'config.yaml',
        'requirements.txt',
        'data/test_cases.json',
        'src/__init__.py',
        'src/torus_construction.py',
        'src/gva_embedding.py',
        'src/qmc_probe.py',
        'src/falsification_test.py',
    ]
    
    all_present = True
    for file_path in required_files:
        full_path = base / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} MISSING")
            all_present = False
    
    return all_present


def check_imports():
    """Check that all modules can be imported."""
    print("\n=== Checking Python Imports ===")
    
    try:
        import torus_construction
        print("✓ torus_construction module")
    except ImportError as e:
        print(f"✗ torus_construction: {e}")
        return False
    
    try:
        import gva_embedding
        print("✓ gva_embedding module")
    except ImportError as e:
        print(f"✗ gva_embedding: {e}")
        return False
    
    try:
        import qmc_probe
        print("✓ qmc_probe module")
    except ImportError as e:
        print(f"✗ qmc_probe: {e}")
        return False
    
    try:
        import falsification_test
        print("✓ falsification_test module")
    except ImportError as e:
        print(f"✗ falsification_test: {e}")
        return False
    
    return True


def validate_config():
    """Validate configuration files."""
    print("\n=== Validating Configuration ===")
    
    import json
    import yaml
    
    base = Path(__file__).parent
    
    # Check config.yaml
    try:
        with open(base / 'config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        required_keys = ['experiment', 'dimensions', 'thresholds', 'qmc', 'gva']
        for key in required_keys:
            if key in config:
                print(f"✓ config.yaml has '{key}'")
            else:
                print(f"✗ config.yaml missing '{key}'")
                return False
    except Exception as e:
        print(f"✗ Error loading config.yaml: {e}")
        return False
    
    # Check test_cases.json
    try:
        with open(base / 'data' / 'test_cases.json', 'r') as f:
            test_cases = json.load(f)
        
        if 'test_cases' in test_cases:
            n_cases = len(test_cases['test_cases'])
            print(f"✓ test_cases.json has {n_cases} test cases")
        else:
            print("✗ test_cases.json missing 'test_cases'")
            return False
    except Exception as e:
        print(f"✗ Error loading test_cases.json: {e}")
        return False
    
    return True


def main():
    """Run all validations."""
    print("\n" + "="*60)
    print("PR-1 Falsification Experiment Framework Validation")
    print("="*60 + "\n")
    
    structure_ok = validate_structure()
    
    if not structure_ok:
        print("\n✗ VALIDATION FAILED: Missing required files")
        return 1
    
    imports_ok = check_imports()
    
    if not imports_ok:
        print("\n✗ VALIDATION FAILED: Import errors")
        print("\nNote: Run 'pip install -r requirements.txt' to install dependencies")
        return 1
    
    config_ok = validate_config()
    
    if not config_ok:
        print("\n✗ VALIDATION FAILED: Configuration errors")
        return 1
    
    print("\n" + "="*60)
    print("✓ ALL VALIDATIONS PASSED")
    print("="*60)
    print("\nFramework is ready for execution.")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run experiment: python src/falsification_test.py")
    print("3. Check results in: data/results/")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
