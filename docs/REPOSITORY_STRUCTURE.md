# Repository Structure

Clean, organized structure following minimal surface area principle.

## Root Directory

**Core Files (Keep in Root)**
- `README.md` - Project overview and boundaries
- `geofac.py` - Main GVA factorization implementation
- `gva_factorization.py` - Core GVA algorithm
- `pytest.ini` - Test configuration

**Build & Configuration**
- `build.gradle`, `settings.gradle`, `gradle.properties` - Gradle build system
- `gradlew`, `gradlew.bat` - Gradle wrapper scripts
- `geofac.iml` - IntelliJ module file

## Organized Directories

### `/docs` - All Documentation
Moved from root:
- `AGENTS.md` - Agent instructions and workflow
- `CHANGELOG.md` - Version history
- `CLAUDE.md`, `GEMINI.md` - AI assistant configurations
- `CODING_STYLE.md` - Canonical style and invariants (**authoritative**)
- `GEOMETRIC_RESONANCE_FACTORIZATION.md` - Method documentation
- `GVA_README.md` - GVA implementation guide
- `PROOF_PACK_DEMO.md`, `PROOF_PACK_README.md` - Proof pack documentation
- `PYTHON_IMPLEMENTATION_README.md` - Python implementation notes
- `RISKS.md` - Risk analysis
- `SUMMARY.md` - Project summary
- `TECHNICAL_BRIEF.md` - Technical overview
- `harden-factor_one.sh-diagnostics-first-workflow-SMEAC.md` - Workflow docs
- `hot_or_not_pr_894.md` - PR analysis

### `/scripts` - Shell Scripts
Moved from root:
- `factor_one.sh` - Factorization script
- `proof_pack.sh` - Proof pack generation
- `run_gate3_verbose.sh` - Gate 3 testing
- `geofac.py` - Main Python runner (symlink or reference)

### `/tests` - Test Suite
Moved from root (all `test_*.py` files):
- `test_gva_80bit.py` through `test_gva_150bit.py` - Scale-based tests
- `test_geometric_resonance.py` - Method-specific tests
- `README.md` - Test documentation

### `/experiments` - Experimental Code
Moved from root:
- `benchmark_gva.py` - Performance benchmarking
- `cornerstone_invariant.py`, `cornerstone_invariant_demo.py` - Invariant exploration
- `demo_geometric_resonance.py` - Resonance method demo
- `experiment_geodesic.py` - Geodesic experiments
- `geometric_resonance_factorization.py` - Resonance implementation

Existing experiment subdirectories:
- `fractal-recursive-gva-falsification/` - FR-GVA testing
- `127bit-challenge-router-attack/`, `8d-imbalance-tuned-gva/`, etc.

### `/build` - Build Artifacts
- `build/artifacts/` - Logs and build outputs
  - `gradle_stack.txt` - Gradle error logs
  - `geofac.log` - Application logs
  - `results.json` - Result artifacts

### `/src` - Source Code
- Java source tree (Gradle project structure)

### Other Directories
- `/results` - Test results and proof packs
- `/specs` - Specifications
- `/smeac` - SMEAC workflow artifacts
- `/downloads` - Downloaded resources
- `/gradle` - Gradle wrapper files

## Cleanup Actions Performed

1. **Moved 15 documentation files** from root → `/docs`
2. **Moved 2 shell scripts** from root → `/scripts`
3. **Moved 13 test files** from root → `/tests` (new directory)
4. **Moved 6 experimental scripts** from root → `/experiments`
5. **Moved 3 build artifacts** from root → `/build/artifacts`
6. **Removed 1 temp file** (`temp_test.java`)

## Benefits

- **Cleaner root**: Only essential project files (README, main implementations, build config)
- **Better discoverability**: Related files grouped by purpose
- **Follows conventions**: Tests in `/tests`, docs in `/docs`, scripts in `/scripts`
- **Easier navigation**: Reduced visual clutter, clear boundaries
- **Minimal surface area**: Aligns with CODING_STYLE.md principles

## Authoritative Sources

Per Copilot instructions:
- **CODING_STYLE.md** (in `/docs`) - Canonical style and invariants
- **README.md** (in root) - Project overview and boundaries

