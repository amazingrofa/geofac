package com.geofac;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

import java.math.BigInteger;

/**
 * Spring Shell Commands for Geometric Factorization
 */
@ShellComponent
public class FactorizerShell {

    private static final Logger log = LoggerFactory.getLogger(FactorizerShell.class);

    private final FactorizerService service;

    public FactorizerShell(FactorizerService service) {
        this.service = service;
    }

    @ShellMethod(value = "Factor a semiprime using geometric resonance", key = "factor")
    public String factor(@ShellOption(help = "The number to factor (decimal integer)") String n) {
        try {
            // Parse input
            BigInteger N = parseBigInteger(n);

            // Validate
            if (N.bitLength() < 10) {
                return formatError("Number too small (must be at least 10 bits)");
            }

            if (N.bitLength() > 1024) {
                return formatWarning(
                    "WARNING: Very large number (" + N.bitLength() + " bits)\n" +
                    "This may take a very long time or fail.\n" +
                    "Validated range: 64-bit to 192-bit\n" +
                    "Proceed? Use 'factor " + n + "' again to confirm"
                );
            }

            // Factor
            log.info("Shell command: factor {}", N);
            long startTime = System.currentTimeMillis();
            FactorizationResult result = service.factor(N);
            long duration = System.currentTimeMillis() - startTime;

            // Format result
            if (result.success()) {
                return formatSuccess(result.p(), result.q(), duration);
            } else {
                return formatFailure(result.config().samples(), duration);
            }

        } catch (NumberFormatException e) {
            return formatError(
                "Invalid number format. Expected a decimal integer.\n" +
                "See docs/VALIDATION_GATES.md for the official challenge number."
            );
        } catch (IllegalArgumentException e) {
            return formatError(e.getMessage());
        } catch (OutOfMemoryError e) {
            return formatError(
                "Out of memory\n" +
                "Number may be too large for available RAM\n" +
                "Try smaller number or increase JVM heap size"
            );
        } catch (Exception e) {
            log.error("Unexpected error during factorization", e);
            return formatError(
                "Unexpected error: " + e.getClass().getSimpleName() + "\n" +
                "Message: " + e.getMessage() + "\n" +
                "Check logs for details"
            );
        }
    }

    @ShellMethod(value = "Show example usage", key = {"example", "demo"})
    public String example() {
        return """
            === Geometric Factorizer - Example Usage ===

            This project follows a two-gate validation policy. See docs/VALIDATION_GATES.md for details.

            1. Run Gate 1 Validation (127-bit challenge):
               > factor 137524771864208156028430259349934309717

            2. Run a number within the Gate 2 Operational Range [1e14, 1e18] (after Gate 1 is passed):
               > factor 214748364799999999

            3. View this help:
               > help factor

            Note: This method is experimental. Success is only guaranteed for the Gate 1 challenge.
            """;
    }

    // Helper methods for formatted output

    private BigInteger parseBigInteger(String s) throws NumberFormatException {
        String trimmed = s.trim().replaceAll("_", ""); // Allow underscores for readability
        if (trimmed.isEmpty()) {
            throw new NumberFormatException("Empty string");
        }
        return new BigInteger(trimmed);
    }

    private String formatSuccess(BigInteger p, BigInteger q, long durationMs) {
        return String.format(
            """
            ╔═══════════════════════════════════════════════════════════════╗
            ║                        ✓ SUCCESS                              ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ p = %-57s ║
            ║ q = %-57s ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ Time: %5.2f seconds                                         ║
            ╚═══════════════════════════════════════════════════════════════╝
            """,
            p.toString(),
            q.toString(),
            durationMs / 1000.0
        );
    }

    private String formatFailure(long samples, long durationMs) {
        return String.format(
            """
            ╔═══════════════════════════════════════════════════════════════╗
            ║                        ✗ NO FACTORS FOUND                     ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ Samples tested: %-45d ║
            ║ Time elapsed:   %5.2f seconds                              ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ Suggestions:                                                  ║
            ║ • This number may require different parameters                ║
            ║ • Try adjusting configuration in application.yml              ║
            ║ • Some semiprimes cannot be factored by this method           ║
            ╚═══════════════════════════════════════════════════════════════╝
            """,
            samples,
            durationMs / 1000.0
        );
    }

    private String formatError(String message) {
        return String.format(
            """
            ╔═══════════════════════════════════════════════════════════════╗
            ║                          ERROR                                ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ %s
            ╚═══════════════════════════════════════════════════════════════╝
            """,
            wrapText(message, 61)
        );
    }

    private String formatWarning(String message) {
        return String.format(
            """
            ╔═══════════════════════════════════════════════════════════════╗
            ║                         WARNING                               ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ %s
            ╚═══════════════════════════════════════════════════════════════╝
            """,
            wrapText(message, 61)
        );
    }

    private String wrapText(String text, int width) {
        StringBuilder sb = new StringBuilder();
        String[] lines = text.split("\n");
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i];
            if (line.length() <= width) {
                sb.append(String.format("║ %-" + width + "s ║\n", line));
            } else {
                // Wrap long lines
                String[] words = line.split(" ");
                StringBuilder currentLine = new StringBuilder();
                for (String word : words) {
                    if (currentLine.length() + word.length() + 1 <= width) {
                        if (currentLine.length() > 0) currentLine.append(" ");
                        currentLine.append(word);
                    } else {
                        sb.append(String.format("║ %-" + width + "s ║\n", currentLine.toString()));
                        currentLine = new StringBuilder(word);
                    }
                }
                if (currentLine.length() > 0) {
                    sb.append(String.format("║ %-" + width + "s ║\n", currentLine.toString()));
                }
            }
        }
        return sb.toString().trim();
    }
}
