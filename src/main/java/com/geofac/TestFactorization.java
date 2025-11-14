package com.geofac;

import com.geofac.util.DirichletKernel;
import com.geofac.util.SnapKernel;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import ch.obermuhlner.math.big.BigDecimalMath;

public class TestFactorization {

    public static void main(String[] args) {
        // The official Gate 1 challenge number. See docs/VALIDATION_GATES.md for details.
        BigInteger N = new BigInteger("137524771864208156028430259349934309717");
        
        // Test parameters
        int precision = 240;
        long samples = 3000;
        int mSpan = 180;
        double threshold = 0.92;
        double kLo = 0.25;
        double kHi = 0.45;

        System.out.println("Testing factorization of N = " + N);
        System.out.println("Bit length: " + N.bitLength());

        // Adaptive precision
        int adaptivePrecision = Math.max(precision, N.bitLength() * 2 + 100);
        MathContext mc = new MathContext(adaptivePrecision, RoundingMode.HALF_EVEN);

        System.out.println("Adaptive precision: " + adaptivePrecision);

        // Initialize constants
        BigDecimal bdN = new BigDecimal(N, mc);
        BigDecimal lnN = BigDecimalMath.log(bdN, mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        BigDecimal phiInv = computePhiInv(mc);

        System.out.println("Starting search...");

        // Simple search - just check if we can find factors
        BigInteger[] result = search(N, mc, lnN, twoPi, phiInv, samples, mSpan, threshold, kLo, kHi);

        if (result != null) {
            System.out.println("SUCCESS: Found factors");
            System.out.println("p = " + result[0]);
            System.out.println("q = " + result[1]);
            System.out.println("Verification: " + result[0].multiply(result[1]).equals(N));
        } else {
            System.out.println("FAILED: No factors found");
        }
    }

    private static BigDecimal computePhiInv(MathContext mc) {
        BigDecimal sqrt5 = BigDecimalMath.sqrt(BigDecimal.valueOf(5), mc);
        return sqrt5.subtract(BigDecimal.ONE, mc).divide(BigDecimal.valueOf(2), mc);
    }

    private static BigInteger[] search(BigInteger N, MathContext mc, BigDecimal lnN,
                                       BigDecimal twoPi, BigDecimal phiInv,
                                       long samples, int mSpan, double threshold,
                                       double kLo, double kHi) {
        BigDecimal u = BigDecimal.ZERO;
        BigDecimal kWidth = BigDecimal.valueOf(kHi - kLo);
        BigDecimal thresholdBd = BigDecimal.valueOf(threshold);

        for (long n = 0; n < samples; n++) {
            // Update golden ratio sequence
            u = u.add(phiInv, mc);
            if (u.compareTo(BigDecimal.ONE) >= 0) {
                u = u.subtract(BigDecimal.ONE, mc);
            }

            BigDecimal k = BigDecimal.valueOf(kLo).add(kWidth.multiply(u, mc), mc);
            BigInteger m0 = BigInteger.ZERO;

            for (int dm = -mSpan; dm <= mSpan; dm++) {
                BigInteger m = m0.add(BigInteger.valueOf(dm));
                BigDecimal theta = twoPi.multiply(new BigDecimal(m), mc).divide(k, mc);

                // Dirichlet kernel filtering
                BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, 6, mc);
                if (amplitude.compareTo(thresholdBd) > 0) {
                    BigInteger p0 = SnapKernel.phaseCorrectedSnap(lnN, theta, mc);

                    // Test candidate and neighbors
                    BigInteger[] hit = testNeighbors(N, p0);
                    if (hit != null) {
                        return hit;
                    }
                }
            }
        }

        return null;
    }

    private static BigInteger[] testNeighbors(BigInteger N, BigInteger pCenter) {
        BigInteger[] offsets = { BigInteger.ZERO, BigInteger.valueOf(-1), BigInteger.ONE };
        for (BigInteger off : offsets) {
            BigInteger p = pCenter.add(off);
            if (p.compareTo(BigInteger.ONE) <= 0 || p.compareTo(N) >= 0) {
                continue;
            }
            if (N.mod(p).equals(BigInteger.ZERO)) {
                BigInteger q = N.divide(p);
                return ordered(p, q);
            }
        }
        return null;
    }

    private static BigInteger[] ordered(BigInteger a, BigInteger b) {
        return (a.compareTo(b) <= 0) ? new BigInteger[]{a, b} : new BigInteger[]{b, a};
    }
}