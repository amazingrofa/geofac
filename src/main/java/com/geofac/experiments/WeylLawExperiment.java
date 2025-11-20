package com.geofac.experiments;

import com.geofac.util.PrecisionUtil;
import ch.obermuhlner.math.big.BigDecimalMath;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.io.PrintWriter;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.*;

/**
 * Weyl Law Remainder Oscillations Experiment
 * 
 * Tests the hypothesis that Weyl law remainders R(λ) from spectral counting N(λ)
 * can calibrate QMC variance in geodesic distance probes for geometric factorization.
 */
public class WeylLawExperiment {
    
    private static final String EXPERIMENT_DIR = "experiments/weyl-law-remainder-oscillations/results";
    private static final String TIMESTAMP = Instant.now().toString().replace(':', '-');
    
    // Test numbers from validation gates
    private static final BigInteger GATE_3_N = new BigInteger("137524771864208156028430259349934309717");
    private static final BigInteger GATE_3_P = new BigInteger("10508623501177419659");
    private static final BigInteger GATE_3_Q = new BigInteger("13086849276577416863");
    
    // Representative numbers in operational range [10^14, 10^18]
    private static final BigInteger[] TEST_NUMBERS = {
        new BigInteger("100000000000000001"),
        new BigInteger("1000000000000000003"),
    };
    
    private final PrintWriter log;
    private final String resultsDir;
    
    public WeylLawExperiment() throws Exception {
        resultsDir = EXPERIMENT_DIR + "/" + TIMESTAMP;
        Files.createDirectories(Paths.get(resultsDir));
        log = new PrintWriter(new File(resultsDir + "/experiment.log"));
    }
    
    public static void main(String[] args) {
        try {
            WeylLawExperiment exp = new WeylLawExperiment();
            exp.runExperiment();
            exp.close();
        } catch (Exception e) {
            System.err.println("Experiment failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    public void runExperiment() throws Exception {
        logSection("WEYL LAW REMAINDER OSCILLATIONS EXPERIMENT");
        log("Timestamp: " + TIMESTAMP);
        log("Results directory: " + resultsDir);
        log("");
        
        logSection("HYPOTHESIS");
        log("Weyl law remainders R(λ) from oscillatory terms in spectral counting N(λ)");
        log("arising from lattice-point deviations in thin annuli on flat tori can");
        log("calibrate QMC variance in geodesic distance probes for geometric factorization.");
        log("");
        
        logSection("EXPERIMENT DESIGN");
        log("1. Compute spectral counting N(λ) for toroidal embeddings");
        log("2. Extract remainder R(λ) = N(λ) - WeylMainTerm(λ)");
        log("3. Count lattice points in thin annuli of width δ");
        log("4. Measure QMC variance baseline (golden-ratio sampling)");
        log("5. Measure QMC variance with remainder-calibrated sampling");
        log("6. Compare convergence rates and factorization efficiency");
        log("");
        
        // Test on Gate 3 (127-bit challenge)
        testNumber(GATE_3_N, GATE_3_P, GATE_3_Q, "Gate 3 (127-bit challenge)");
        
        // Test on operational range numbers
        for (int i = 0; i < TEST_NUMBERS.length; i++) {
            testNumber(TEST_NUMBERS[i], null, null, "Operational range test " + (i+1));
        }
        
        logSection("CONCLUSION");
        analyzeResults();
    }
    
    private void testNumber(BigInteger N, BigInteger knownP, BigInteger knownQ, String label) throws Exception {
        logSection("Testing: " + label);
        log("N = " + N);
        log("N bitLength = " + N.bitLength());
        
        if (knownP != null && knownQ != null) {
            log("Known factors: p = " + knownP + ", q = " + knownQ);
        }
        log("");
        
        // Compute adaptive precision
        int precision = Math.max(240, N.bitLength() * 4 + 200);
        MathContext mc = new MathContext(precision, java.math.RoundingMode.HALF_EVEN);
        log("Precision: " + precision + " decimal digits");
        
        // Dimension of toroidal embedding (heuristic: log2(N) gives dimension)
        int dimension = N.bitLength();
        log("Toroidal embedding dimension: " + dimension);
        
        // Spectral parameter λ derived from N
        BigDecimal lambda = computeSpectralParameter(N, mc);
        log("Spectral parameter λ: " + lambda.toString());
        
        // Compute Weyl main term
        BigDecimal weylMainTerm = computeWeylMainTerm(lambda, dimension, mc);
        log("Weyl main term: " + weylMainTerm.toPlainString());
        
        // Compute spectral counting function N(λ) via lattice point counting
        long spectralCount = countLatticePoints(lambda, dimension, mc);
        log("Spectral count N(λ): " + spectralCount);
        
        // Extract remainder R(λ)
        BigDecimal remainder = BigDecimal.valueOf(spectralCount).subtract(weylMainTerm, mc);
        log("Remainder R(λ): " + remainder.toPlainString());
        
        if (spectralCount > 0) {
            log("Remainder ratio |R(λ)|/N(λ): " + 
                remainder.abs(mc).divide(BigDecimal.valueOf(spectralCount), mc).toPlainString());
        }
        
        // Compute annulus width δ
        BigDecimal delta = computeAnnulusWidth(N, mc);
        log("Annulus width δ: " + delta.toPlainString());
        
        // Count lattice points in thin annulus
        long annulusCount = countLatticePointsInAnnulus(lambda, delta, dimension, mc);
        log("Lattice points in annulus [λ, λ+δ]: " + annulusCount);
        
        // Measure baseline QMC variance (without remainder calibration)
        double baselineVariance = measureQMCVariance(N, 3000, false, remainder, mc);
        log("QMC variance (baseline, golden-ratio): " + baselineVariance);
        
        // Measure remainder-calibrated QMC variance
        double calibratedVariance = measureQMCVariance(N, 3000, true, remainder, mc);
        log("QMC variance (remainder-calibrated): " + calibratedVariance);
        
        // Compute variance reduction factor
        double reductionFactor = baselineVariance / calibratedVariance;
        log("Variance reduction factor: " + reductionFactor);
        
        // Analysis
        log("");
        log("ANALYSIS:");
        if (reductionFactor > 1.1) {
            log("✓ Remainder calibration shows variance reduction (" + 
                String.format("%.2f%%", (reductionFactor - 1) * 100) + ")");
        } else if (reductionFactor < 0.9) {
            log("✗ Remainder calibration increases variance (" +
                String.format("%.2f%%", (1 - reductionFactor) * 100) + " worse)");
        } else {
            log("~ Remainder calibration has negligible effect (within 10%)");
        }
        
        // Check if remainder oscillations are significant
        if (spectralCount > 0) {
            BigDecimal remainderRatio = remainder.abs(mc).divide(
                BigDecimal.valueOf(spectralCount), mc);
            if (remainderRatio.compareTo(BigDecimal.valueOf(0.01)) > 0) {
                log("Remainder oscillations are significant (>1% of main term)");
            } else {
                log("Remainder oscillations are negligible (<1% of main term)");
            }
        }
        
        log("");
    }
    
    private BigDecimal computeSpectralParameter(BigInteger N, MathContext mc) {
        BigDecimal bdN = new BigDecimal(N, mc);
        BigDecimal sqrt = BigDecimalMath.sqrt(bdN, mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        return sqrt.divide(twoPi, mc);
    }
    
    private BigDecimal computeWeylMainTerm(BigDecimal lambda, int d, MathContext mc) {
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        BigDecimal twoPiPowD = BigDecimalMath.pow(twoPi, d, mc);
        
        BigDecimal dHalf = BigDecimal.valueOf(d).divide(BigDecimal.valueOf(2), mc);
        BigDecimal lambdaPowDHalf = BigDecimalMath.pow(lambda, dHalf, mc);
        
        return lambdaPowDHalf.divide(twoPiPowD, mc);
    }
    
    private long countLatticePoints(BigDecimal lambda, int d, MathContext mc) {
        if (d > 20) {
            BigDecimal sqrtD = BigDecimalMath.sqrt(BigDecimal.valueOf(d), mc);
            BigDecimal scaled = lambda.multiply(sqrtD, mc);
            BigDecimal count = BigDecimalMath.pow(scaled, d, mc);
            return count.toBigInteger().longValue();
        }
        
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal dHalf = BigDecimal.valueOf(d).divide(BigDecimal.valueOf(2), mc);
        BigDecimal piPowDHalf = BigDecimalMath.pow(pi, dHalf, mc);
        BigDecimal lambdaPowD = BigDecimalMath.pow(lambda, d, mc);
        double gammaArg = d / 2.0 + 1;
        BigDecimal gamma = computeGamma(gammaArg, mc);
        
        BigDecimal volume = piPowDHalf.multiply(lambdaPowD, mc).divide(gamma, mc);
        return volume.toBigInteger().longValue();
    }
    
    private long countLatticePointsInAnnulus(BigDecimal lambda, BigDecimal delta, int d, MathContext mc) {
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal dHalf = BigDecimal.valueOf(d).divide(BigDecimal.valueOf(2), mc);
        BigDecimal piPowDHalf = BigDecimalMath.pow(pi, dHalf, mc);
        BigDecimal two = BigDecimal.valueOf(2);
        BigDecimal lambdaPowDMinus1 = BigDecimalMath.pow(lambda, d - 1, mc);
        double gammaArg = d / 2.0;
        BigDecimal gamma = computeGamma(gammaArg, mc);
        
        BigDecimal surfaceArea = two.multiply(piPowDHalf, mc)
            .multiply(lambdaPowDMinus1, mc)
            .divide(gamma, mc);
        
        BigDecimal annulusVolume = surfaceArea.multiply(delta, mc);
        return Math.max(1, annulusVolume.toBigInteger().longValue());
    }
    
    private BigDecimal computeAnnulusWidth(BigInteger N, MathContext mc) {
        BigDecimal bdN = new BigDecimal(N, mc);
        BigDecimal sqrtN = BigDecimalMath.sqrt(bdN, mc);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal twoPi = pi.multiply(BigDecimal.valueOf(2), mc);
        return twoPi.divide(sqrtN, mc);
    }
    
    private BigDecimal computeGamma(double z, MathContext mc) {
        if (z <= 0) return BigDecimal.ONE;
        
        BigDecimal bdZ = BigDecimal.valueOf(z);
        BigDecimal pi = BigDecimalMath.pi(mc);
        BigDecimal e = BigDecimalMath.e(mc);
        BigDecimal two = BigDecimal.valueOf(2);
        
        BigDecimal twoPiOverZ = two.multiply(pi, mc).divide(bdZ, mc);
        BigDecimal sqrtTerm = BigDecimalMath.sqrt(twoPiOverZ, mc);
        
        BigDecimal zOverE = bdZ.divide(e, mc);
        BigDecimal powerTerm = BigDecimalMath.pow(zOverE, bdZ, mc);
        
        return sqrtTerm.multiply(powerTerm, mc);
    }
    
    private double measureQMCVariance(BigInteger N, int samples, 
                                     boolean useRemainderCalibration,
                                     BigDecimal remainder, MathContext mc) {
        BigDecimal phi = BigDecimal.ONE.add(BigDecimalMath.sqrt(BigDecimal.valueOf(5), mc), mc)
            .divide(BigDecimal.valueOf(2), mc);
        BigDecimal phiInv = BigDecimal.ONE.divide(phi, mc);
        
        List<BigDecimal> samplePoints = new ArrayList<>();
        
        for (int i = 0; i < samples; i++) {
            BigDecimal t = BigDecimal.valueOf(i).multiply(phiInv, mc);
            
            if (useRemainderCalibration) {
                BigDecimal remainderFactor = BigDecimal.ONE.add(
                    remainder.divide(BigDecimal.valueOf(1000), mc), mc);
                t = t.multiply(remainderFactor, mc);
            }
            
            t = t.subtract(new BigDecimal(t.toBigInteger()), mc);
            samplePoints.add(t);
        }
        
        BigDecimal mean = BigDecimal.ZERO;
        for (BigDecimal point : samplePoints) {
            mean = mean.add(point, mc);
        }
        mean = mean.divide(BigDecimal.valueOf(samples), mc);
        
        BigDecimal variance = BigDecimal.ZERO;
        for (BigDecimal point : samplePoints) {
            BigDecimal diff = point.subtract(mean, mc);
            variance = variance.add(diff.multiply(diff, mc), mc);
        }
        variance = variance.divide(BigDecimal.valueOf(samples - 1), mc);
        
        return variance.doubleValue();
    }
    
    private void analyzeResults() {
        log("FALSIFICATION ANALYSIS:");
        log("");
        log("The experiment tests whether Weyl law remainder oscillations R(λ)");
        log("can improve QMC variance in the geometric resonance factorization method.");
        log("");
        log("KEY FINDINGS:");
        log("");
        log("1. Remainder Magnitude:");
        log("   The Weyl law remainder R(λ) is computed as the difference between");
        log("   the lattice-point count and the asymptotic main term. For the test");
        log("   numbers in the validation gates, the remainder-to-main-term ratio");
        log("   indicates the relative importance of oscillatory effects.");
        log("");
        log("2. QMC Variance Comparison:");
        log("   Golden-ratio QMC sampling (baseline) is compared against remainder-");
        log("   calibrated sampling. A variance reduction factor > 1.1 would suggest");
        log("   the remainder provides useful calibration information. A factor near");
        log("   1.0 indicates negligible effect.");
        log("");
        log("3. Operational Feasibility:");
        log("   Even if remainder calibration shows theoretical benefit, practical");
        log("   application requires:");
        log("   - Computing R(λ) must be faster than the factorization itself");
        log("   - The calibration must not introduce additional error");
        log("   - The method must remain deterministic/quasi-deterministic");
        log("");
        log("4. Hypothesis Verdict:");
        log("   If variance reduction factors are consistently near 1.0 or less,");
        log("   the hypothesis is FALSIFIED: Weyl law remainders do not provide");
        log("   actionable calibration information for this geometric method.");
        log("");
        log("   If reduction factors exceed 1.5 consistently, further investigation");
        log("   may be warranted, but implementation complexity must be justified.");
        log("");
    }
    
    private void logSection(String title) {
        log("=".repeat(70));
        log(title);
        log("=".repeat(70));
    }
    
    private void log(String message) {
        System.out.println(message);
        log.println(message);
        log.flush();
    }
    
    private void close() {
        log.close();
        System.out.println("\nResults written to: " + resultsDir);
    }
}
