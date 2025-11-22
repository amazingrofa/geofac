"""
Test GVA factorization on 105+ bit semiprimes.

This test extends GVA capability from 100-bit to 105+ bit semiprimes,
demonstrating continued scaling of the geodesic-guided approach.
"""

from gva_factorization import gva_factor_search
import time

# Test cases: 105-bit semiprimes
# Generated using primes near 5 × 10^15 (≈ sqrt(2^105))
# p = 5000000000000023 (prime near 5 × 10^15)
# q = 5000000000000111 (next prime after p)
TEST_CASES_105BIT = [
    {
        'name': '105-bit balanced semiprime',
        'N': 25000000000000670000000000002553,
        'p': 5000000000000023,
        'q': 5000000000000111,
    },
]


def test_105bit_gva():
    """
    Test GVA factorization on 105+ bit semiprimes.
    """
    print("=" * 70)
    print("GVA Factorization: 105+ Bit Semiprime Test")
    print("=" * 70)
    print()
    
    results = []
    
    for test_case in TEST_CASES_105BIT:
        N = test_case['N']
        expected_p = test_case['p']
        expected_q = test_case['q']
        name = test_case['name']
        
        print(f"Test: {name}")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Expected factors: {expected_p} × {expected_q}")
        print()
        
        # Test with multiple k values and increased candidates for 105+ bits
        start_time = time.time()
        factors = gva_factor_search(
            N,
            k_values=[0.30, 0.35, 0.40],
            max_candidates=350000,  # Increased for 105+ bits
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
    success = test_105bit_gva()
    exit(0 if success else 1)
