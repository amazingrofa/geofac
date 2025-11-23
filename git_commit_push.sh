#!/bin/bash
set -e

cd /Users/velocityworks/IdeaProjects/geofac

echo "=== Git Commit and Push Script ==="
echo ""

echo "Step 1: Staging all changes..."
git add -A
echo "✓ Changes staged"

echo ""
echo "Step 2: Committing changes..."
git commit -m "chore: organize repository structure

Root cause: Repository root cluttered with ~35 files (docs, tests, scripts, experiments, artifacts) reducing discoverability and violating minimal surface area principle.

Fix: Organize files into standard directories
- Move 15 documentation files → docs/
- Move 13 test files → tests/ (new directory)
- Move 2 shell scripts → scripts/
- Move 6 experimental scripts → experiments/
- Move 3 build artifacts → build/artifacts/
- Remove 1 temp file (temp_test.java)
- Create tests/README.md, tests/conftest.py, docs/CLEANUP_SUMMARY.md, docs/REPOSITORY_STRUCTURE.md
- Update pytest.ini with testpaths configuration
- Update 5 doc files with corrected script/module paths

Impact: Root reduced to 12 essential files; clear boundaries between docs, tests, scripts, experiments; all 33 tests discoverable; maintains backward compatibility.

Tested: pytest --collect-only tests/ → 33 tests collected; all imports working via conftest.py

Artifact: docs/CLEANUP_SUMMARY.md, docs/REPOSITORY_STRUCTURE.md, tests/README.md"
echo "✓ Changes committed"

echo ""
echo "Step 3: Pushing to remote..."
git push
echo "✓ Changes pushed"

echo ""
echo "=== Complete ==="
echo ""
echo "Recent commit:"
git log -1 --oneline

echo ""
echo "Repository status:"
git status --short

