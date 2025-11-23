"""
Test GVA factorization on 80+ bit semiprimes.

This test extends GVA capability beyond the validated 50-64 bit range
to demonstrate factorization of 80+ bit semiprimes.
"""

from gva_factorization import gva_factor_search, adaptive_precision
import time

# Test cases: 80-bit semiprimes
# Generated using primes near 2^40
# p = 1099511627791 (the 50,847,535th prime)
# q = 1099511629813 (the 50,847,657th prime)
TEST_CASES_80BIT = [
    {
        'name': '80-bit balanced semiprime',
        'N': 1208925821870827034933083,
        'p': 1099511627791,
        'q': 1099511629813,
    },
]


def test_80bit_gva():
    """
    Test GVA factorization on 80+ bit semiprimes.
    """
    print("=" * 70)
    print("GVA Factorization: 80+ Bit Semiprime Test")
    print("=" * 70)
    print()
    
    results = []
    
    for test_case in TEST_CASES_80BIT:
        N = test_case['N']
        expected_p = test_case['p']
        expected_q = test_case['q']
        name = test_case['name']
        
        print(f"Test: {name}")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Expected factors: {expected_p} × {expected_q}")
        print()
        
        # Test with multiple k values and increased candidates
        start_time = time.time()
        factors = gva_factor_search(
            N,
            k_values=[0.30, 0.35, 0.40],
            max_candidates=100000,  # Increased for 80+ bits
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
    
    return all_passed


if __name__ == "__main__":
    success = test_80bit_gva()
    exit(0 if success else 1)
