"""
Pytest configuration for geofac tests.
Ensures tests can import modules from root and experiments directories.
"""
import sys
from pathlib import Path

# Add root directory to path (for gva_factorization, geofac, etc.)
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Add experiments directory to path (for experimental modules)
experiments_dir = root_dir / "experiments"
sys.path.insert(0, str(experiments_dir))

