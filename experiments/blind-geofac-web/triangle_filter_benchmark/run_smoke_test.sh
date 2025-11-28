#!/usr/bin/env bash
# Quick Triangle Filter Smoke Test
# Runs a single factorization with filter enabled vs disabled for comparison.
# Use this for quick validation; use run_triangle_filter_benchmark.sh for full benchmark.
#
# Reference: https://github.com/zfifteen/geofac/pull/171

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$WEB_ROOT/../.." && pwd)"

# Create secure temp directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "=== Triangle Filter Smoke Test ==="
echo "Reference: https://github.com/zfifteen/geofac/pull/171"
echo ""

# Parse triangle filter stats from log file
parse_triangle_stats() {
    local log_file="$1"
    local checked rejected rate
    
    # Extract stats: "Triangle filter stats: checked=N, rejected=M (X.X%)"
    checked=$(grep -oE 'checked=[0-9]+' "$log_file" 2>/dev/null | tail -1 | cut -d= -f2 || echo "0")
    rejected=$(grep -oE 'rejected=[0-9]+' "$log_file" 2>/dev/null | tail -1 | cut -d= -f2 || echo "0")
    rate=$(grep -oE '\([0-9.]+%\)' "$log_file" 2>/dev/null | tail -1 | tr -d '()%' || echo "N/A")
    
    echo "$checked $rejected $rate"
}

run_quick_test() {
    local filter_enabled="$1"
    local label
    
    if [ "$filter_enabled" = "true" ]; then
        label="ENABLED"
    else
        label="DISABLED"
    fi
    
    local log_file="$TEMP_DIR/smoke_test_${filter_enabled}.log"
    
    echo "Running with triangle filter $label..."
    
    local start_time
    start_time=$(date +%s)
    
    # Run quick test (not the long challenge)
    "$REPO_ROOT/gradlew" -p "$WEB_ROOT" test \
        -Dgeofac.triangle-filter-enabled="$filter_enabled" \
        --tests "com.geofac.blind.service.FactorServiceTest" \
        2>&1 | tee "$log_file"
    
    local end_time
    end_time=$(date +%s)
    local elapsed=$((end_time - start_time))
    
    # Extract stats
    read -r checked rejected rate < <(parse_triangle_stats "$log_file")
    
    echo ""
    echo "Filter $label:"
    echo "  Wall-clock: ${elapsed}s"
    echo "  Triangle filter: checked=$checked, rejected=$rejected, rate=${rate}%"
    echo ""
}

echo "--- Baseline (Filter Disabled) ---"
run_quick_test "false"

echo "--- Test (Filter Enabled) ---"
run_quick_test "true"

echo "=== Smoke Test Complete ==="
