# P-adic Topology of Geofac

Purpose: normalize geofac's terminology to standard p-adic / adelic language without changing behavior.

## Canonical definitions (p-adic)
- Valuation `v_p(n)`: largest `e` such that `p^e` divides `n`.
- Absolute value `|x|_p = p^{-v_p(x)}` with `|0|_p = 0`.
- Metric `d_p(a,b) = |a-b|_p`; balls are `B_p(a, r) = {x : d_p(a,x) <= r}`.
- Truncated expansion: `x = a_0 + a_1 p + ... + a_k p^k (mod p^{k+1})` with `a_i in {0,...,p-1}`.
- Hensel lifting / p-adic Newton: refine a root `x_0 (mod p)` of `f` to `x_k (mod p^k)` using the usual Newton step with derivative invertible mod `p`.
- Adeles (truncated): product space `R x prod_p Q_p` restricted here to the finite set of primes geofac samples per run.

## Legacy -> standard mapping
| Legacy geofac term | Standard term | One-line meaning |
| --- | --- | --- |
| prime-power spine | truncated `Z_p` expansion / valuation tree | ordered digits of `x (mod p^k)`; depth = how many powers of `p` are resolved |
| residue tunneling / infinite descent | Hensel lifting / p-adic Newton chain | successive lifts of a residue through `mod p, p^2, ...` |
| cluster island / ultrametric stratum | closed ball in `(Z_p, d_p)` | set of numbers sharing the same `p`-adic prefix / valuation radius |
| ghost / negative index state | element with `v_p(x) < 0` in `Q_p \ Z_p` | requires at least one negative power of `p` (denominator present) |
| global state (Z + geofac layers) | truncated adelic space `R x prod_p Q_p` | real snapshot paired with finite `p`-adic coordinates per prime |

## How this maps to geofac
- Per-prime layers that previously stored "spines" are `Z_p` prefixes; depth corresponds to the highest resolved `p`-power.
- "Residue tunnels" / "infinite descent chains" are Hensel lifts: iterating a residue through `p^k` to sharpen it.
- "Cluster islands" are exactly `p`-adic balls; amplitude/threshold gating chooses which balls to explore.
- "Negative index" bookkeeping refers to states outside `Z_p` (valuation < 0), i.e., rationals with a `p` in the denominator.
- The combined real + per-prime view is an (intentionally) truncated adele; behavior is unchanged, only the vocabulary is now standard.

## Worked example (deterministic experiment)
Run the included demo to see the mapping in action:

```bash
python docs/experiments/padic_spine_demo.py
```

What it shows (and logs):
- Adaptive precision is set to `max(configured, bit_length * 4 + 200)` and printed.
- "Spine" = first six `Z_p` digits of `n=123456789` for `p in {3,5,7}` with `v_p(n)` alongside.
- Ultrametric distance examples (`d_p`) that collapse when valuations grow.
- A Hensel lifting chain for `x^2 == 2 (mod 7^k)` up to `k=4`, illustrating "residue tunneling."

Outputs are deterministic (no sampling, no seeds needed) and serve only as empirical evidence for the terminology correspondence; the factorization algorithm itself is unchanged.

Artifact: results/padic_demo_20251120T212521Z/run.log (cmd: `python docs/experiments/padic_spine_demo.py`).
