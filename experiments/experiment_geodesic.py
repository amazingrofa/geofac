"""
Experiment: Geodesic Transform vs. Primality
"""
import mpmath as mp
from cornerstone_invariant import NumberTheoreticInvariant

# Using gmpy2 for fast primality testing of large numbers.
# This is a standard, fast library for number theory.
# A fallback to a slower method is included if gmpy2 is not available.
try:
    from gmpy2 import is_prime
except ImportError:
    print("Warning: gmpy2 not found. Using slow fallback for primality testing.")
    def is_prime(n):
        if n < 2: return False
        if n == 2: return True
        if n % 2 == 0: return False
        for i in range(3, int(mp.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True

def run_geodesic_experiment(start_n, count, k_values):
    """
    Computes the geodesic transform for a range of integers and checks primality.

    Args:
        start_n (int): The starting integer for the sequence.
        count (int): The number of integers to test.
        k_values (list): A list of k-exponents to test.
    """
    nt = NumberTheoreticInvariant()
    mp.mp.dps = 50

    print(f"Running experiment from n = {start_n} to {start_n + count - 1}")
    header = f"{'n':<22} | {'is_prime':<10} | " + " | ".join([f"Z (k={k:.2f})" for k in k_values])
    print(header)
    print("-" * len(header))

    for i in range(count):
        n = start_n + i
        primality = is_prime(n)
        
        row = f"{n:<22} | {str(primality):<10} | "
        
        results = []
        for k in k_values:
            z = nt.compute_geodesic_transform(n, k)
            z_str = mp.nstr(z, 18)
            results.append(f"{z_str:<25}")
        
        row += " | ".join(results)
        print(row)

if __name__ == "__main__":
    # Experiment parameters
    # Start at a large, arbitrary integer to avoid trivial cases.
    # A 15-digit number is large enough to be non-trivial but small enough for fast primality tests.
    start_integer = 10**14 + 1
    
    # Number of integers to scan
    scan_count = 100
    
    # Geodesic exponents to test
    exponents = [0.3, 0.5, 0.7]

    run_geodesic_experiment(start_integer, scan_count, exponents)
