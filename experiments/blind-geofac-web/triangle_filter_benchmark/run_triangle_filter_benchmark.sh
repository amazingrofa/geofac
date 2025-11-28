#!/usr/bin/env bash
# Triangle Filter Benchmark Script
# Compares 127-bit challenge factorization with triangle filter enabled vs disabled.
#
# Reference: https://github.com/zfifteen/geofac/pull/171
#
# Usage: ./run_triangle_filter_benchmark.sh [num_runs]
#   num_runs: Number of runs per configuration (default: 3)
#
# Output:
#   - Logs for each run in triangle_filter_benchmark/results/
#   - Summary stats printed to stdout

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$WEB_ROOT/../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"

NUM_RUNS="${1:-3}"

# Test class for 127-bit challenge (configurable via env var)
TEST_CLASS="${BENCHMARK_TEST_CLASS:-com.geofac.blind.service.FactorServiceChallengeIT}"

mkdir -p "$RESULTS_DIR"

echo "=== Triangle Filter Benchmark ==="
echo "Reference: https://github.com/zfifteen/geofac/pull/171"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Runs per configuration: $NUM_RUNS"
echo "Test class: $TEST_CLASS"
echo "Results directory: $RESULTS_DIR"
echo ""

# Parse triangle filter stats from log file
# Format: "Triangle filter stats: checked=N, rejected=M (X.X%)"
parse_triangle_stats() {
    local log_file="$1"
    local checked rejected rate
    
    checked=$(grep -oE 'checked=[0-9]+' "$log_file" 2>/dev/null | tail -1 | cut -d= -f2 || echo "0")
    rejected=$(grep -oE 'rejected=[0-9]+' "$log_file" 2>/dev/null | tail -1 | cut -d= -f2 || echo "0")
    rate=$(grep -oE '\([0-9.]+%\)' "$log_file" 2>/dev/null | tail -1 | tr -d '()%' || echo "N/A")
    
    echo "$checked $rejected $rate"
}

# Function to run a single benchmark
run_benchmark() {
    local filter_enabled="$1"
    local run_num="$2"
    local label
    
    if [ "$filter_enabled" = "true" ]; then
        label="enabled"
    else
        label="disabled"
    fi
    
    local log_file="$RESULTS_DIR/run_${label}_${run_num}.log"
    
    echo "  Run $run_num (filter $label)..."
    
    # Capture start time (integer seconds for portability)
    local start_time
    start_time=$(date +%s)
    
    # Run the test with triangle filter setting
    "$REPO_ROOT/gradlew" -p "$WEB_ROOT" test \
        -Dgeofac.runLongChallengeIT=true \
        -Dgeofac.triangle-filter-enabled="$filter_enabled" \
        --tests "$TEST_CLASS" \
        --info \
        2>&1 | tee "$log_file" || {
            echo "  FAILED (see $log_file)"
            return 1
        }
    
    local end_time
    end_time=$(date +%s)
    
    # Calculate elapsed time (integer arithmetic, no bc dependency)
    local elapsed=$((end_time - start_time))
    
    # Extract triangle filter stats from log
    read -r checked rejected reject_rate < <(parse_triangle_stats "$log_file")
    
    # Check for success
    local success="false"
    if grep -q "Factorization should succeed" "$log_file" && grep -q "BUILD SUCCESSFUL" "$log_file"; then
        success="true"
    fi
    
    # Extract duration from test output if available
    local duration_ms
    duration_ms=$(grep -oE 'durationMs=[0-9]+' "$log_file" 2>/dev/null | tail -1 | cut -d= -f2 || echo "N/A")
    
    echo "    Wall-clock: ${elapsed}s | Duration: ${duration_ms}ms | Success: $success"
    echo "    Triangle filter: checked=$checked, rejected=$rejected, rate=${reject_rate}%"
    
    # Append to summary CSV
    echo "$label,$run_num,$elapsed,$duration_ms,$success,$checked,$rejected,$reject_rate" >> "$RESULTS_DIR/summary.csv"
}

# Initialize summary CSV
echo "mode,run,wall_clock_s,duration_ms,success,checked,rejected,reject_rate_pct" > "$RESULTS_DIR/summary.csv"

echo ""
echo "--- Baseline (Filter Disabled) ---"
for i in $(seq 1 "$NUM_RUNS"); do
    run_benchmark "false" "$i"
done

echo ""
echo "--- Test (Filter Enabled) ---"
for i in $(seq 1 "$NUM_RUNS"); do
    run_benchmark "true" "$i"
done

echo ""
echo "=== Benchmark Complete ==="
echo "Results saved to: $RESULTS_DIR/summary.csv"
echo ""
echo "Summary:"
cat "$RESULTS_DIR/summary.csv"
