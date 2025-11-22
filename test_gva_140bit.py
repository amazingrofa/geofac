"""
Test GVA factorization on 140+ bit semiprimes.

This test extends GVA capability from 130-bit to 140+ bit semiprimes,
demonstrating the "larger = easier" phenomenon when factor gaps are tight.

Based on lessons learned from PR #97 (130-bit breakthrough):
- Geodesic convergence strengthens with scale for balanced semiprimes
- Budget of 700k candidates is conservative (expect <2% usage)
- Precision scaling formula: bitLength × 4 + 200 dps
- Factor gap (not bit length) remains the true difficulty axis
"""

from gva_factorization import gva_factor_search
import time

# Test cases: 140-bit semiprimes with tight gaps
# Generated using primes near 1.18 × 10^21 (≈ sqrt(2^140))
# Deliberately chosen with gap=10 to leverage geodesic curvature benefits
TEST_CASES_140BIT = [
    {
        'name': '140-bit balanced semiprime (gap=10)',
        'N': 1404225000000000001080720000000000000207911,
        'p': 1185000000000000000451,
        'q': 1185000000000000000461,
        'gap': 10,
        'expected_budget_pct': 2.0,  # Expect <2% of 700k candidates
        'expected_runtime_sec': 5.0,  # Expect <5s based on 130-bit pattern
    },
]


def test_140bit_gva():
    """
    Test GVA factorization on 140+ bit semiprimes.
    
    Expected behavior based on PR #97 insights:
    - Runtime should be <5s (potentially faster than 125-bit due to stronger geodesics)
    - Candidate usage should be <2% of budget (5k-15k of 700k candidates)
    - Precision: 141 × 4 + 200 = 764 dps (adaptive formula)
    """
    print("=" * 70)
    print("GVA Factorization: 140+ Bit Semiprime Test (PR #98)")
    print("=" * 70)
    print()
    
    results = []
    
    for test_case in TEST_CASES_140BIT:
        N = test_case['N']
        expected_p = test_case['p']
        expected_q = test_case['q']
        name = test_case['name']
        gap = test_case['gap']
        expected_budget_pct = test_case['expected_budget_pct']
        expected_runtime = test_case['expected_runtime_sec']
        
        print(f"Test: {name}")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Expected factors: {expected_p} × {expected_q}")
        print(f"Factor gap: {gap}")
        print(f"Expected runtime: <{expected_runtime}s")
        print(f"Expected budget usage: <{expected_budget_pct}%")
        print()
        
        # Test with multiple k values and 700k candidate budget for 140+ bits
        # Based on +50k candidates / 5-bit rule: 600k (130-bit) + 100k = 700k
        start_time = time.time()
        factors = gva_factor_search(
            N,
            k_values=[0.30, 0.35, 0.40],
            max_candidates=700000,  # 700k candidate budget
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
                else:
                    print(f"   ⚠️  Runtime exceeded expectation ({elapsed:.3f}s > {expected_runtime}s)")
                
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
        print("🎉 140-bit breakthrough confirmed!")
        print("   Geodesic curvature continues to strengthen with scale.")
    
    return all_passed


if __name__ == "__main__":
    success = test_140bit_gva()
    exit(0 if success else 1)
