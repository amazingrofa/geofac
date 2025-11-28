package com.geofac.blind.util;

import ch.obermuhlner.math.big.BigDecimalMath;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.util.ArrayList;
import java.util.List;

/**
 * Shell-based exclusion filter for pruning dead zones in the search space.
 * Copied from the main repo to keep the web app aligned with the geometric engine.
 */
public class ShellExclusionFilter {

    private static final Logger log = LoggerFactory.getLogger(ShellExclusionFilter.class);

    public record ShellDefinition(int index, BigDecimal rMin, BigDecimal rMax) {}

    public record ShellExclusionConfig(
            BigDecimal delta,
            int shellCount,
            double tau,
            double tauSpike,
            double overlapPercent,
            int kSamples
    ) {}

    public static List<ShellDefinition> generateShells(BigInteger N, ShellExclusionConfig config, MathContext mc) {
        List<ShellDefinition> shells = new ArrayList<>();

        BigDecimal sqrtN = BigDecimalMath.sqrt(new BigDecimal(N, mc), mc);
        BigDecimal delta = config.delta();
        BigDecimal overlap = delta.multiply(BigDecimal.valueOf(config.overlapPercent()), mc);

        for (int i = 1; i <= config.shellCount(); i++) {
            BigDecimal outer = sqrtN.subtract(delta.multiply(BigDecimal.valueOf(i - 1), mc), mc).add(overlap, mc);
            BigDecimal inner = sqrtN.subtract(delta.multiply(BigDecimal.valueOf(i), mc), mc);

            if (inner.compareTo(BigDecimal.ZERO) <= 0 || inner.compareTo(outer) >= 0) {
                continue;
            }

            shells.add(new ShellDefinition(-i, inner, outer));
        }

        for (int i = 1; i <= config.shellCount(); i++) {
            BigDecimal inner = sqrtN.add(delta.multiply(BigDecimal.valueOf(i - 1), mc), mc).subtract(overlap, mc);
            BigDecimal outer = sqrtN.add(delta.multiply(BigDecimal.valueOf(i), mc), mc);
            shells.add(new ShellDefinition(i, inner, outer));
        }

        log.info("Generated {} shells: delta={}, overlap={}", shells.size(), delta, overlap);
        return shells;
    }

    public static boolean shouldExcludeShell(
            ShellDefinition shell,
            double kLo,
            double kHi,
            ShellExclusionConfig config,
            int J,
            BigDecimal twoPi,
            MathContext mc) {

        List<BigDecimal> amplitudes = new ArrayList<>();
        BigDecimal kWidth = BigDecimal.valueOf(kHi - kLo);

        BigDecimal rWidth = shell.rMax().subtract(shell.rMin(), mc);
        BigDecimal rCenter = shell.rMin().add(rWidth.divide(BigDecimal.valueOf(2), mc), mc);

        for (int i = 0; i < config.kSamples(); i++) {
            double uk = (double) i / (config.kSamples() - 1); // Uniform sampling [0, 1]
            BigDecimal k = BigDecimal.valueOf(kLo).add(kWidth.multiply(BigDecimal.valueOf(uk), mc), mc);

            BigDecimal theta = BigDecimal.ZERO;
            BigDecimal amplitude = DirichletKernel.normalizedAmplitude(theta, J, mc);
            amplitudes.add(amplitude);
        }

        BigDecimal maxAmplitude = amplitudes.stream()
                .max(BigDecimal::compareTo)
                .orElse(BigDecimal.ZERO);

        boolean hasSpike = hasSpike(amplitudes, config.tauSpike());
        boolean shouldExclude = maxAmplitude.doubleValue() < config.tau() && !hasSpike;

        if (shouldExclude) {
            log.info("Excluding shell {}: rMin={}, rMax={}, maxAmp={}, tau={}, tauSpike={}, hasSpike={}",
                    shell.index(), shell.rMin(), shell.rMax(),
                    String.format("%.6f", maxAmplitude.doubleValue()),
                    config.tau(), config.tauSpike(), hasSpike);
        }

        return shouldExclude;
    }

    private static boolean hasSpike(List<BigDecimal> amplitudes, double tauSpike) {
        if (amplitudes.size() < 3) {
            return amplitudes.stream().anyMatch(a -> a.doubleValue() >= tauSpike);
        }

        for (int i = 1; i < amplitudes.size() - 1; i++) {
            double prev = amplitudes.get(i - 1).doubleValue();
            double curr = amplitudes.get(i).doubleValue();
            double next = amplitudes.get(i + 1).doubleValue();

            if (curr >= tauSpike && curr >= prev && curr >= next) {
                return true;
            }
        }

        if (amplitudes.get(0).doubleValue() >= tauSpike) {
            return true;
        }
        return amplitudes.get(amplitudes.size() - 1).doubleValue() >= tauSpike;
    }

    public static List<BigDecimal> filterKSamples(
            List<BigDecimal> kSamples,
            List<ShellDefinition> excludedShells,
            BigDecimal lnN,
            BigDecimal twoPi,
            MathContext mc) {

        if (excludedShells.isEmpty()) {
            return kSamples;
        }

        List<BigDecimal> filtered = new ArrayList<>();
        for (BigDecimal k : kSamples) {
            boolean excluded = false;

            // Approximate a candidate radius p0 for this k using m=1; then test which shell it falls into.
            BigDecimal theta = twoPi.divide(k, mc);
            BigInteger p0 = SnapKernel.phaseCorrectedSnap(lnN, theta, mc);
            if (p0.compareTo(BigInteger.TWO) <= 0) {
                filtered.add(k);
                continue;
            }

            for (ShellDefinition shell : excludedShells) {
                BigDecimal lnRMin = BigDecimalMath.log(shell.rMin(), mc);
                BigDecimal lnRMax = BigDecimalMath.log(shell.rMax(), mc);
                BigDecimal lnP0 = BigDecimalMath.log(new BigDecimal(p0, mc), mc);

                if (lnP0.compareTo(lnRMin) >= 0 && lnP0.compareTo(lnRMax) <= 0) {
                    excluded = true;
                    break;
                }
            }
            if (!excluded) {
                filtered.add(k);
            }
        }

        return filtered;
    }
}
