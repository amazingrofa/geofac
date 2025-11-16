#!/usr/bin/env bash
#
# run-tpm-standup.sh
# Executes the Technical Program Manager (TPM) stand-up workflow autonomously.
#
# Usage: .pm/run-tpm-standup.sh
# Can be run from anywhere within the repository.
#
# This script pre-approves all necessary tools to avoid permission prompts:
# - gh operations (viewing/creating issues, posting comments)
# - File operations (reading task files, writing reports)
# - Code search operations (grep, glob for analysis)

set -euo pipefail

# Find the repository root (works from anywhere in the repo)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [[ -z "$REPO_ROOT" ]]; then
    echo "Error: Not in a git repository" >&2
    exit 1
fi

# Change to repository root
cd "$REPO_ROOT"

# Verify task files exist
if [[ ! -f ".pm/pm_mvp_task_00_PROJECT_MANAGER_JOB_DESCRIPTION.md" ]]; then
    echo "Error: TPM task files not found in .pm/" >&2
    exit 1
fi

# Show what we're doing
echo "========================================="
echo "Starting TPM Stand-Up Workflow"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Repo: $REPO_ROOT"
echo "========================================="
echo ""

# Execute the TPM workflow with pre-approved tools
# --verbose shows real-time progress
# Pre-approved tools prevent permission prompts
claude --verbose \
  --allowedTools "Bash(gh:*)" "Bash(git:*)" "Write" "Read" "Edit" "Grep" "Glob" "WebFetch" \
  "Execute the full TPM stand-up workflow: read .pm/pm_mvp_task_00_PROJECT_MANAGER_JOB_DESCRIPTION.md and follow the task chain through tasks 01, 02, and 03 to completion. Work autonomously without asking for permission."

echo ""
echo "========================================="
echo "TPM Stand-Up Workflow Complete"
echo "========================================="
