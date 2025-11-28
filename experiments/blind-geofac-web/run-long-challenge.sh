#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"

JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@21}"
export JAVA_HOME

CMD=("$REPO_ROOT/gradlew" -p "$ROOT" clean test -Dgeofac.runLongChallengeIT=true --tests "com.geofac.blind.service.FactorServiceChallengeIT")

echo "JAVA_HOME=$JAVA_HOME"
echo "Running: ${CMD[*]}"
"${CMD[@]}"
