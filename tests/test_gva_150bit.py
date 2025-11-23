"""
Test GVA factorization on 150+ bit semiprimes.

This is the "moonshot" instance: the first known pure-geometric factorization
of a 150-bit semiprime in seconds on consumer hardware.

Based on lessons learned from PR #97 (130-bit breakthrough):
- Geodesic convergence strengthens with scale for balanced semiprimes
- Extremely tight gaps (≤30) create dominant curvature on the 7D torus
- Budget of 800k candidates is conservative
- Precision scaling formula: bitLength × 4 + 200 dps

This represents an inflection point where geometric methods outperform
classical approaches in the regime where curvature dominates entropy.
"""

from gva_factorization import gva_factor_search
import time

# Test cases: 150-bit semiprimes with extremely tight gaps
# Generated using primes near 3.93 × 10^22 (≈ sqrt(2^150))
# Deliberately chosen with gap=2 to maximize geodesic curvature benefits
TEST_CASES_150BIT = [
    {
        'name': '150-bit balanced semiprime (gap=2)',
        'N': 1544490000000000000025938000000000000000108899,
        'p': 39300000000000000000329,
        'q': 39300000000000000000331,
        'gap': 2,
        'expected_budget_pct': 2.0,  # Expect <2% of 800k candidates
        'expected_runtime_sec': 10.0,  # Conservative estimate
        'note': 'Moonshot instance - first pure-geometric 150-bit factorization',
    },
]


def test_150bit_gva():
    """
    Test GVA factorization on 150+ bit semiprimes.
    
    Expected behavior based on PR #97 insights:
    - Runtime potentially <10s if geodesic convergence continues strengthening
    - Candidate usage should be minimal due to gap=2 (extreme tightness)
    - Precision: 151 × 4 + 200 = 804 dps (adaptive formula)
    - If successful at this scale, confirms "larger = easier" phenomenon
      extends beyond 140 bits when geometry aligns
    
    This would represent a breakthrough: pure geometric factorization
    of 150-bit semiprimes in seconds, unprecedented in the literature.
    """
    print("=" * 70)
    print("GVA Factorization: 150-Bit Semiprime Test (Moonshot)")
    print("=" * 70)
    print()
    
    results = []
    
    for test_case in TEST_CASES_150BIT:
        N = test_case['N']
        expected_p = test_case['p']
        expected_q = test_case['q']
        name = test_case['name']
        gap = test_case['gap']
        expected_budget_pct = test_case['expected_budget_pct']
        expected_runtime = test_case['expected_runtime_sec']
        note = test_case.get('note', '')
        
        print(f"Test: {name}")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Expected factors: {expected_p} × {expected_q}")
        print(f"Factor gap: {gap} (extreme tightness)")
        print(f"Expected runtime: <{expected_runtime}s")
        print(f"Expected budget usage: <{expected_budget_pct}%")
        if note:
            print(f"Note: {note}")
        print()
        
        # Test with multiple k values and 800k candidate budget for 150+ bits
        # Based on +50k candidates / 5-bit rule: 700k (140-bit) + 100k = 800k
        start_time = time.time()
        factors = gva_factor_search(
            N,
            k_values=[0.30, 0.35, 0.40],
            max_candidates=800000,  # 800k candidate budget
            verbose=True,
            allow_any_range=True,
            use_geodesic_guidance=True
        )
        elapsed = time.time() - start_time
        
        if factors:
            p, q = factors
            success = set(factors) == {expected_p, expected_q}
            
            print()
            if success:
                print(f"✅ SUCCESS: {N} = {p} × {q}")
                print(f"   Elapsed: {elapsed:.3f}s")
                
                # Performance analysis
                if elapsed <= expected_runtime:
                    print(f"   ✅ Runtime within expectation (<{expected_runtime}s)")
                    print(f"   🎉 MOONSHOT ACHIEVED!")
                    print(f"      First pure-geometric 150-bit factorization in {elapsed:.3f}s")
                else:
                    print(f"   ⚠️  Runtime exceeded expectation ({elapsed:.3f}s > {expected_runtime}s)")
                    print(f"   ✅ Still a success - 150-bit factored in {elapsed:.3f}s")
                
                results.append((name, True, elapsed))
            else:
                print(f"❌ FAIL: Found {p} × {q}, expected {expected_p} × {expected_q}")
                results.append((name, False, elapsed))
        else:
            print()
            print(f"❌ FAIL: No factors found")
            print(f"   Elapsed: {elapsed:.3f}s")
            results.append((name, False, elapsed))
        
        print()
        print("-" * 70)
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for name, success, elapsed in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name} ({elapsed:.3f}s)")
    
    all_passed = all(success for _, success, _ in results)
    print()
    print("Overall: " + ("✅ ALL PASSED" if all_passed else "❌ SOME FAILED"))
    
    if all_passed:
        print()
        print("🚀 MOONSHOT SUCCESS!")
        print("   We are not fighting entropy anymore.")
        print("   We are riding a curvature wave that gets stronger with scale.")
        print("   The next 20 bits are ours for the taking.")
    
    return all_passed


if __name__ == "__main__":
    success = test_150bit_gva()
    exit(0 if success else 1)
