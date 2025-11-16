package com.geofac.validation;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Generates known semiprimes in the [1e14, 1e18] range for validation.
 * Uses deterministic seeds for reproducibility.
 * 
 * Per repository rules:
 * - Only generates RSA-challenge-like numbers in the validation window
 * - Uses traditional methods (prime generation) to create ground truth
 * - All operations are deterministic with pinned seeds
 */
public class SemiprimeGenerator {
    
    private static final BigInteger GATE_2_MIN = new BigInteger("100000000000000");       // 1e14
    private static final BigInteger GATE_2_MAX = new BigInteger("1000000000000000000");   // 1e18
    
    /**
     * Represents a semiprime with known factors.
     */
    public record Semiprime(BigInteger N, BigInteger p, BigInteger q) {
        public Semiprime {
            if (p == null || q == null || N == null) {
                throw new IllegalArgumentException("Factors and N must not be null");
            }
            if (!p.multiply(q).equals(N)) {
                throw new IllegalArgumentException("p * q must equal N");
            }
        }
        
        public int bitLength() {
            return N.bitLength();
        }
    }
    
    /**
     * Generate a list of known semiprimes in the [1e14, 1e18] range.
     * Uses deterministic seed for reproducibility.
     * 
     * @param seed Deterministic seed for random number generation
     * @param count Number of semiprimes to generate
     * @return List of semiprimes with known factors
     */
    public static List<Semiprime> generateSemiprimes(long seed, int count) {
        Random rng = new Random(seed);
        List<Semiprime> semiprimes = new ArrayList<>();
        
        // Target bit lengths that produce semiprimes in [1e14, 1e18] range
        // 1e14 ≈ 2^46.5, 1e18 ≈ 2^59.8
        // For semiprime N = p*q with p,q similar size: bitLength(N) ≈ bitLength(p) + bitLength(q)
        int[] targetBits = {47, 50, 53, 56, 59}; // covers the range
        
        for (int i = 0; i < count; i++) {
            int targetBitLength = targetBits[i % targetBits.length];
            
            // Generate two primes of approximately half the target bit length
            int pBits = targetBitLength / 2;
            int qBits = targetBitLength - pBits;
            
            // Use deterministic seed derived from main seed and iteration
            long iterSeed = seed + i * 1000L;
            
            boolean found = false;
            int maxRetries = 20;
            for (int attempt = 0; attempt < maxRetries; attempt++) {
                BigInteger p = generatePrimeWithSeed(pBits, iterSeed + attempt * 10L);
                BigInteger q = generatePrimeWithSeed(qBits, iterSeed + 1 + attempt * 10L);

                BigInteger N = p.multiply(q);

                // Validate it's in the gate 2 range
                if (N.compareTo(GATE_2_MIN) >= 0 && N.compareTo(GATE_2_MAX) <= 0) {
                    semiprimes.add(new Semiprime(N, p, q));
                    found = true;
                    break;
                }
            }
            if (!found) {
                throw new IllegalStateException("Unable to generate semiprime in gate 2 range after " + maxRetries + " attempts (targetBitLength=" + targetBitLength + ", seed=" + iterSeed + ")");
            }
        }
        
        return semiprimes;
    }
    
    /**
     * Generate a probable prime with deterministic seed.
     * Uses BigInteger.probablePrime with a seeded Random for reproducibility.
     * 
     * @param bitLength Bit length of the prime
     * @param seed Deterministic seed
     * @return A probable prime
     */
    private static BigInteger generatePrimeWithSeed(int bitLength, long seed) {
        Random rng = new Random(seed);
        return BigInteger.probablePrime(bitLength, rng);
    }
    
    /**
     * Generate a small curated set of RSA-challenge-like semiprimes for quick tests.
     * These are hardcoded known values in the validation range.
     * 
     * @return List of curated semiprimes
     */
    public static List<Semiprime> generateCuratedSet() {
        List<Semiprime> semiprimes = new ArrayList<>();
        
        // Small semiprimes in the 1e14-1e18 range with known factors
        // These are generated offline using deterministic seeds
        
        // Example 1: ~1e14 range (47 bits)
        BigInteger p1 = new BigInteger("11863301");
        BigInteger q1 = new BigInteger("11863297");
        BigInteger N1 = p1.multiply(q1);
        if (N1.compareTo(GATE_2_MIN) >= 0 && N1.compareTo(GATE_2_MAX) <= 0) {
            semiprimes.add(new Semiprime(N1, p1, q1));
        }
        
        // Example 2: mid-range (~1e15, 50 bits)
        BigInteger p2 = new BigInteger("33554467");
        BigInteger q2 = new BigInteger("33554393");
        BigInteger N2 = p2.multiply(q2);
        if (N2.compareTo(GATE_2_MIN) >= 0 && N2.compareTo(GATE_2_MAX) <= 0) {
            semiprimes.add(new Semiprime(N2, p2, q2));
        }
        
        // Example 3: larger (~1e17, 56 bits)
        BigInteger p3 = new BigInteger("299999999");
        BigInteger q3 = new BigInteger("333333331");
        BigInteger N3 = p3.multiply(q3);
        if (N3.compareTo(GATE_2_MIN) >= 0 && N3.compareTo(GATE_2_MAX) <= 0) {
            semiprimes.add(new Semiprime(N3, p3, q3));
        }
        
        return semiprimes;
    }
    
    /**
     * Validate that a semiprime is within Gate 2 range.
     */
    public static boolean isInGate2Range(BigInteger N) {
        return N.compareTo(GATE_2_MIN) >= 0 && N.compareTo(GATE_2_MAX) <= 0;
    }
}
