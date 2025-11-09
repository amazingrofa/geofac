# z-amx — Apple AMX Instruction Set (Z-Framework fork, M1 Max–tuned)

> Reverse-engineered Apple **AMX (Matrix co-processor)** notes, tests, and micro-kernels for Apple Silicon — plus a local-only macOS automation profile (Contacts/iMessage/Mail) to support Z-Framework workflows on **MacBook Pro M1 Max (8P+2E, 32 GB)**.

---

## Why this fork exists

This fork tracks upstream AMX research while adding:
- A Z-Framework–oriented intro and reproducible build/run path on Apple Silicon.
- M1 Max scheduling/concurrency guidance.
- A **local-only macOS Comms Analyst** profile (Contacts → iMessage → Mail) you can invoke from your agent CLI to gather context and generate on-device summaries for research ops and experiment logging. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

> **Note:** Apple AMX here is Apple’s matrix engine, not Intel AMX. Behavior varies by SoC/OS; treat all of this as research material.

---

## Tested hardware / environment (primary)

- **MacBook Pro (M1 Max, 10-core CPU = 8P+2E, 32 GB RAM)**
- macOS Sonoma/Sequoia (arm64 toolchain)
- Xcode CLT / `clang` (arm64), Python 3, GNU make

Keep device identifiers private in logs (serial/UDID redacted in this repo).

---

## AMX quick background (Apple Silicon)

Apple Silicon compute paths you’ll compare in this repo:
1) ARMv8 **NEON** (CPU SIMD)
2) **AMX** matrix engine (this repo)
3) **ANE/NPU**
4) **GPU (Metal)**

Typical sweet spot for AMX: outer-product heavy kernels (small/medium tiles, fp16/bf16→fp32 accumulations). Validate against NEON and Metal for your specific math.

---

## SoC deltas (handy cheat sheet)

- **M1 → M2:** adds **bf16** modes.
- **M2 → M3:** new modes on `ldx`, `ldy`, `matint`.
- **M3 → M4:** some `extrh/extrv/vecfp/vecint` modes ignore low bits of X/Y offset.
- Writemask lineage suggests “v2” style on M1 (7- vs 9-bit families).

(Confirm on your OS; AMX is undocumented and may drift.)

---

## Repo layout (high-value files)

- `aarch64.h` — inline-asm doorway to issue AMX ops from C.
- `*.md` — instruction notes: register file; `matfp/matint`, `vecfp/vecint`, `extr*`, `ldst`, `set/clear`, etc.
- `*.c` — tests/micro-kernels (`test.c`, `perf.c`, e.g., 16×16 tiles).
- `perf_kernels.py`, `perf_table.py` — optional helpers to format & compare results.

---

## Build & run

```bash
# Ensure native arm64:
uname -m                           # expect: arm64
file "$(command -v clang)"         # ensure arm64 toolchain

# Build:
make

# Run examples (names vary with Makefile targets in this fork):
./test                             # basic instruction coverage
./perf                             # microbench selection

# Optional helpers:
python3 perf_kernels.py
python3 perf_table.py
