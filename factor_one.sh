#!/bin/bash
set -euo pipefail

set -euo pipefail

# One-shot factorization of the target N using geometric resonance
# Produces per-run diagnostics and plaintext factors if successful
#
# Project: geofac - Geometric Resonance Factorization
# Repo: https://github.com/zfifteen/geofac
# README: https://github.com/zfifteen/geofac/blob/main/README.md
# Coding Style: https://github.com/zfifteen/geofac/blob/main/CODING_STYLE.md
# Validation Gates: https://github.com/zfifteen/geofac/blob/main/docs/VALIDATION_GATES.md
# Agents/Operating Rules: https://github.com/zfifteen/geofac/blob/main/AGENTS.md
#
# This script implements a diagnostic-first workflow to factor the Gate 1 challenge number.
# Fixed: Double-2π bug in SnapKernel that caused invalid p0 values.
#
# IMPORTANT: Fast-path is disabled. Real success means the geometric resonance algorithm
# discovers the factors without being given them.

# The official Gate 1 challenge number. See docs/VALIDATION_GATES.md for details.
TARGET_N="137524771864208156028430259349934309717"

# Generate unique run ID
RUN_ID="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="results/single_run_${RUN_ID}"
mkdir -p "$OUT_DIR"

echo "=== Geometric Resonance Factorization ==="
echo "N = $TARGET_N"
echo "Run ID = $RUN_ID"
echo "Output directory = $OUT_DIR"
echo ""

# Run the factorization with diagnostics enabled
# Parameters: Extended search with higher sample count and longer timeout
# Based on user feedback that original timeouts were insufficient
# Adaptive precision = max(configured, N.bitLength()*4 + 200) = 708
java \
  -Dgeofac.allow-127bit-benchmark=true \
  -Dgeofac.enable-fast-path=false \
  -Dgeofac.enable-diagnostics=true \
  -Dgeofac.precision=400 \
  -Dgeofac.samples=10000 \
  -Dgeofac.m-span=100 \
  -Dgeofac.j=6 \
  -Dgeofac.threshold=0.50 \
  -Dgeofac.k-lo=0.25 \
  -Dgeofac.k-hi=0.65 \
  -Dgeofac.search-timeout-ms=300000 \
  -jar build/libs/geofac-0.1.0-SNAPSHOT.jar factor "$TARGET_N" 2>&1 | tee "$OUT_DIR/run.log"

# Check for success in the log
if grep -q "SUCCESS" "$OUT_DIR/run.log"; then
    echo ""
    echo "=== Factorization Successful ==="
    
    # Extract p and q from the output
    p=$(grep -Eo 'p = [0-9]+' "$OUT_DIR/run.log" | grep -Eo '[0-9]+')
    q=$(grep -Eo 'q = [0-9]+' "$OUT_DIR/run.log" | grep -Eo '[0-9]+')

    # Validate extraction
    if [ -z "$p" ] || [ -z "$q" ]; then
        echo "Error: Could not extract factors from output"
        exit 1
    fi
    
    # Save factors to plaintext files
    echo "$p" > "$OUT_DIR/p.txt"
    echo "$q" > "$OUT_DIR/q.txt"
    
    echo "p = $p"
    echo "q = $q"
    echo "Factors saved to $OUT_DIR/p.txt and $OUT_DIR/q.txt"
    echo ""
    echo "All artifacts saved to $OUT_DIR/"
    exit 0
else
    echo ""
    echo "=== Factorization Failed ==="
    echo "Check logs in $OUT_DIR/run.log for details"
    exit 1
fi