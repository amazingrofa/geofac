# Codex CLI Network Configuration Guide for Goose/geofac

## Overview
This document captures the process of configuring the Codex CLI (`codex`) for network access (e.g., enabling `--search` for web_search tool to fetch external resources like GitHub PRs). This is essential for tasks in the geofac project, such as analyzing external repos without manual intervention.

**Context**: 
- Operating System: macOS
- Current Directory: `/Users/velocityworks/IdeaProjects/geofac`
- Codex Version: v0.58.0 (research preview)
- Goal: Enable outbound HTTP (web_search) while maintaining safety (no full bypasses).
- Date Captured: 2025-11-19

Codex runs in a sandboxed environment by default (`network_access=restricted`, `approval_policy=never`), blocking external fetches. Fixes involve editing `~/.codex/config.toml` and enabling features.

## Initial Diagnosis
Run these commands to inspect:

1. **Check Directory**:
   ```bash
   ls -la /Users/velocityworks/.codex
   ```
   - Expected: Contains `config.toml`, `auth.json`, `history.jsonl`, etc.
   - If missing: Run `codex login` to initialize.

2. **View Current Config**:
   ```bash
   cat /Users/velocityworks/.codex/config.toml
   ```
   - Default: Basic model/settings, trusted projects (e.g., geofac), no network/features sections.
   - Issues: MCP timeouts (default 10s), `web_search_request=false`.

3. **List Features**:
   ```bash
   codex features list
   ```
   - Key: `web_search_request` (stable, default: false)—gates `--search`.
   - Others: `shell_command_tool` (local shell, false); `view_image_tool` (true).

Common Errors:
- `MCP client for opencode timed out after 10 seconds`: Internal tool server slow.
- `--search` misplaced: Use top-level before subcommand (e.g., `codex --search exec ...`).
- Parse errors in config: TOML syntax (no literal `\n`; use proper sections).

## Config Changes
Backup first: `cp /Users/velocityworks/.codex/config.toml /Users/velocityworks/.codex/config.toml.bak`.

Use a text editor (e.g., VSCode) or Goose's `developer__text_editor` tool to overwrite `~/.codex/config.toml` with the following (preserve your existing trusted projects/notices):

```toml
model = "gpt-5.1"
model_reasoning_effort = "high"

# Trusted projects (add yours if needed; geofac already included)
[projects."/Users/velocityworks/IdeaProjects/geofac"]
trust_level = "trusted"

# ... (other projects like unified-framework, etc.)

[notice]
hide_gpt5_1_migration_prompt = true
hide_full_access_warning = true

# MCP server config: Increase timeout to fix opencode errors
[mcp_servers.opencode]
command = "opencode"
startup_timeout_sec = 30  # Or 60+ if still timing out

# Enable network/web search feature (stable)
[features]
web_search_request = true
```

- **Key Additions Explained**:
  - `startup_timeout_sec = 30`: Extends MCP (`opencode`) startup from 10s (prevents tool failures).
  - `web_search_request = true`: Permanently enables `--search` (outbound HTTP, no approval needed).
  - Trusted projects: Relaxes local sandbox for geofac (allows file edits).

Alternative: Use CLI overrides without editing (one-shot):
```bash
codex -c 'features.web_search_request=true' -c 'mcp_servers.opencode.startup_timeout_sec=30' --search exec "Your prompt"
```

Verify: `cat ~/.codex/config.toml` (no parse errors); `codex features list` (web_search_request=true).

## Testing Network Access
Run this to confirm:

```bash
codex --search exec "Test network: Fetch and summarize https://example.com. Confirm if working."
```

- **Expected Output**:
  - Success: "Yes, network access via my browsing tool is working." + Page summary (e.g., "Example Domain: Reserved for docs...").
  - Tokens: ~2,500 (high reasoning).
  - Session ID: e.g., 019a99d5-... (use for `codex resume <id>`).

If Fails:
- Timeout: Increase `startup_timeout_sec` to 60; restart session (`codex logout; codex login`).
- Auth: Run `codex login` (uses OpenAI API; check `auth.json`).
- Sandbox: For local writes, ensure project is "trusted"; avoid `--danger-full-access` unless externally secured.

## Usage Tips for Goose/geofac
- **One-Shot Mode** (Non-Interactive):
  ```bash
  cd /Users/velocityworks/IdeaProjects/geofac
  codex --search -c model_reasoning_effort=high exec "Analyze PR: https://github.com/zfifteen/unified-framework/pull/930 for geofac QMC relevance."
  ```
  - Maintain Session: Use `codex resume --last` or session_id from output.
  - Parallel: Not native; chain commands.

- **In Goose (This Agent)**:
  - Invoke via `developer__shell`: e.g., `codex --search exec "Prompt"`.
  - For PRs: Fetch with `gh pr view` (if CLI installed) as fallback (network works via shell).
  - Extensions: If Goose's Extension Manager is enabled, search/enable codex-related ones.

- **Advanced**:
  - Models: `-c model="o3"` (faster) or `--oss` (local Ollama, no network).
  - Sandbox: `--sandbox workspace-write` (default safe); `danger-full-access` only if needed (risky!).
  - Approvals: `-a on-request` for flexibility (model asks for risky commands).
  - Features: Enable others via config (e.g., `shell_command_tool=true` for advanced shell).

- **Geofac-Specific**:
  - Use for external analysis (e.g., unified-framework PRs on θ′-bias/QMC).
  - Integrate with todo: Add "Run codex analysis on PR #930" to TODO.
  - Reproducibility: Pin seeds in prompts; log session_ids.

## Reversion/Undo
- Restore: `cp /Users/velocityworks/.codex/config.toml.bak /Users/velocityworks/.codex/config.toml`.
- Disable Feature: Edit config to `web_search_request = false`; or CLI: `-c features.web_search_request=false`.
- Clear Sessions: Delete `~/.codex/sessions/*` or `history.jsonl` (resets history).

## References
- Codex Help: `codex --help` (full options).
- Config Docs: Check Codex GitHub (if accessible) or `codex features help`.
- Goose Tools: Use `developer__shell` for codex invokes; `developer__text_editor` for config edits.
- Timestamp: Captured 2025-11-19 during geofac session on PR analysis.

For updates, re-run diagnosis and append changes here.
