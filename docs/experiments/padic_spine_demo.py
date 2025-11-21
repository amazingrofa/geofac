#!/usr/bin/env python3
"""
Deterministic p-adic correspondence demo for geofac terminology.
- Shows how a legacy "spine" is just a truncated Z_p expansion.
- Demonstrates residue tunneling via a short Hensel lifting chain.

Run:
  python docs/experiments/padic_spine_demo.py

Outputs are deterministic and log the precision used (adaptive: max(configured, bit_length * 4 + 200)).
"""
from __future__ import annotations

import datetime
import mpmath as mp
from typing import List, Tuple

CONFIGURED_PRECISION = 80  # decimal digits (unused if adaptive is higher)


def v_p(n: int, p: int) -> int:
    """p-adic valuation: highest exponent e with p**e | n."""
    if p <= 1:
        raise ValueError("p must be prime and >=2")
    if n == 0:
        return 0
    e = 0
    m = abs(n)
    while m % p == 0:
        m //= p
        e += 1
    return e


def truncated_p_adic_digits(n: int, p: int, depth: int) -> List[int]:
    """Return first `depth` digits of the Z_p expansion of n."""
    digits = []
    m = n
    for _ in range(depth):
        digits.append(m % p)
        m //= p
    return digits


def p_adic_abs(n: int, p: int) -> mp.mpf:
    return mp.power(p, -v_p(n, p))


def p_adic_distance(a: int, b: int, p: int) -> mp.mpf:
    return p_adic_abs(a - b, p)


def hensel_lift_sqrt2(p: int, levels: int) -> List[Tuple[int, int]]:
    """Lift root of x^2 - 2 = 0 from mod p to mod p**levels."""
    if p == 2:
        raise ValueError("choose odd prime for square root of 2")
    # Find a root mod p (exists for p=7: 3^2=9==2 mod 7)
    x = 3 % p
    lifts = [(1, x)]
    modulus = p
    for k in range(2, levels + 1):
        modulus *= p
        f_x = (x * x - 2) % modulus
        f_prime = (2 * x) % p
        inv = pow(f_prime, -1, p)
        x = (x - inv * f_x) % modulus
        lifts.append((k, x))
    return lifts


def main() -> None:
    n = 123456789
    primes = [3, 5, 7]
    depth = 6
    adaptive_precision = max(CONFIGURED_PRECISION, n.bit_length() * 4 + 200)
    mp.mp.dps = adaptive_precision

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"timestamp={now}")
    print(f"n={n}, bitlength={n.bit_length()}, mp.mp.dps={mp.mp.dps}")
    print(f"primes={primes}, depth={depth}\n")

    print("spine -> truncated Z_p digits (low-order first)")
    for p in primes:
        digits = truncated_p_adic_digits(n, p, depth)
        print(f"p={p}: v_p(n)={v_p(n, p)}, digits={digits}")
    print()

    a, b = 123450, 123456
    for p in primes:
        print(
            f"d_p({a},{b}) = {p_adic_distance(a, b, p)} (balls shrink fast when valuations grow)"
        )
    print()

    print("hensel lifting chain for x^2 == 2 (mod 7^k)")
    for level, root in hensel_lift_sqrt2(7, 4):
        print(f"k={level}: root={root} mod 7^{level}")


if __name__ == "__main__":
    main()
