"""
Test GVA factorization on 120+ bit semiprimes.

This test extends GVA capability from 115-bit to 120+ bit semiprimes,
demonstrating continued scaling of the geodesic-guided approach.
"""

from gva_factorization import gva_factor_search
import time

# Test cases: 120-bit semiprimes
# Generated using primes near 1.153 × 10^18 (≈ sqrt(2^120))
# p = 1150000000000000027 (prime near 1.15 × 10^18)
# q = 1150000000000000057 (next prime after p)
TEST_CASES_120BIT = [
    {
        'name': '120-bit balanced semiprime',
        'N': 1322500000000000096600000000000001539,
        'p': 1150000000000000027,
        'q': 1150000000000000057,
    },
]


def test_120bit_gva():
    """
    Test GVA factorization on 120+ bit semiprimes.
    """
    print("=" * 70)
    print("GVA Factorization: 120+ Bit Semiprime Test")
    print("=" * 70)
    print()
    
    results = []
    
    for test_case in TEST_CASES_120BIT:
        N = test_case['N']
        expected_p = test_case['p']
        expected_q = test_case['q']
        name = test_case['name']
        
        print(f"Test: {name}")
        print(f"N = {N}")
        print(f"Bit length: {N.bit_length()}")
        print(f"Expected factors: {expected_p} × {expected_q}")
        print()
        
        # Test with multiple k values and increased candidates for 120+ bits
        start_time = time.time()
        factors = gva_factor_search(
            N,
            k_values=[0.30, 0.35, 0.40],
            max_candidates=500000,  # Increased for 120+ bits
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
    success = test_120bit_gva()
    exit(0 if success else 1)
