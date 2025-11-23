#!/usr/bin/env bash
set -euo pipefail

# Verbose Gate 3 (127-bit) geometric resonance run with full diagnostics.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
LOG_DIR="$ROOT/results/gate3-$STAMP"
LOG_FILE="$LOG_DIR/gate3.log"

mkdir -p "$LOG_DIR"

# Pick a Gradle runner that actually exists, favoring the wrapper.
if [[ -x "$ROOT/gradlew" ]]; then
  GRADLE_RUNNER="$ROOT/gradlew"
  GRADLE_SOURCE="gradlew (repo wrapper)"
else
  GRADLE_RUNNER="$(command -v gradle || true)"
  GRADLE_SOURCE="$( [[ -n "$GRADLE_RUNNER" ]] && echo "gradle (system)" || echo "gradle-not-found" )"
fi

CPU_BRAND="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || true)"
CPU_PHYS="$(sysctl -n hw.physicalcpu 2>/dev/null || true)"
CPU_LOG="$(sysctl -n hw.logicalcpu 2>/dev/null || true)"
MEM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || true)"

{
  echo "=== geofac Gate 3 diagnostic run ==="
  echo "timestamp_utc: $STAMP"
  echo "script: $0"
  echo "cwd: $(pwd)"
  echo "root: $ROOT"
  echo "uname: $(uname -a)"
  echo "cpu: ${CPU_BRAND:-unknown} (physical=${CPU_PHYS:-?} logical=${CPU_LOG:-?})"
  echo "mem_bytes: ${MEM_BYTES:-unknown}"
  echo "git_head: $(git -C "$ROOT" rev-parse HEAD)"
  echo "git_status: $(git -C "$ROOT" status --short --branch)"
  echo "java_version: $(java -version 2>&1 | tr '\n' ' ')"
  if [[ -n "$GRADLE_RUNNER" ]]; then
    echo "gradle_runner: $GRADLE_SOURCE -> $GRADLE_RUNNER"
    echo "gradle_version: $($GRADLE_RUNNER -v | sed -n '1,3p' | tr '\n' ' ')"
  else
    echo "gradle_runner: NOT FOUND"
  fi
  echo "ulimit_core: $(ulimit -c)"
  echo "ulimit_fsize: $(ulimit -f)"
  echo "disk_free_root: $(df -h "$ROOT" | tail -1)"
  echo "env_java_home: ${JAVA_HOME:-unset}"
  echo "env_gradle_opts: ${GRADLE_OPTS:-unset}"
  echo "log_file: $LOG_FILE"
  echo "----------------------------------------"
} | tee "$LOG_FILE"

cd "$ROOT"

SECONDS=0
echo "[INFO] starting Gate 3 test at $(date -u +"%Y-%m-%dT%H:%M:%SZ")" | tee -a "$LOG_FILE"

if [[ -z "$GRADLE_RUNNER" ]]; then
  echo "[ERROR] No gradle runner available; aborting." | tee -a "$LOG_FILE"
  exit 1
fi

# Run the Gate 3 test with verbose logging and gate override enabled.
"$GRADLE_RUNNER" test \
  --tests "com.geofac.FactorizerServiceTest.testGate3_127BitChallenge" \
  --info --stacktrace --console plain \
  -Dgeofac.allow-127bit-benchmark=true \
  -Dlogging.level.com.geofac=DEBUG \
  -Dspring.main.banner-mode=off \
  -Dspring.shell.interactive.enabled=false \
  2>&1 | tee -a "$LOG_FILE"

ELAPSED=$SECONDS
echo "[INFO] finished at $(date -u +"%Y-%m-%dT%H:%M:%SZ"), elapsed_seconds=$ELAPSED" | tee -a "$LOG_FILE"
echo "logs_saved_to: $LOG_FILE"
