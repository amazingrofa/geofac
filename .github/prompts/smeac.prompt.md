---
name: "/smeac"
description: "Generate a SMEAC brief markdown in .orders and print a <=500-char summary."
arguments:
  - name: details
    description: Optional additional details to include and derive short description from
    required: false
---

You are the GitHub Copilot CLI inside this repository.
When the user invokes /smeac [details]:
- Derive short-description from the first 5 words of {details}, lowercased and hyphenated; default to "session-context" if empty.
- Write a SMEAC markdown file to .orders/smeac-yyyymmdd-<short-description>.md containing sections: Situation, Mission, Execution, Administration & Logistics, Command & Signal, plus metadata (timestamp UTC, branch, commit, Java).
- Also print a summary of the operation to stdout, truncated to 500 characters.
- Prefer running the local ./smeac script if present; otherwise emit equivalent content directly.
- Keep outputs deterministic and minimal; respect project invariants in CODING_STYLE.md and README.md (no classical factoring fallbacks; deterministic methods; log precision).

Only show the 500-character summary to the user; do not print the entire markdown in chat.
