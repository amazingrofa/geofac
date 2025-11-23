"""
Cornerstone Invariant Framework - Cross-Domain Demonstration

This script demonstrates the universality and power of the cornerstone invariant
principle Z = A(B/c) across different domains:
1. Physical domain (relativity)
2. Discrete mathematical domain (prime densities)
3. Number-theoretic domain (geodesic transformations)

The demonstration shows how the same fundamental principle applies across
vastly different contexts, providing consistency, reproducibility, and
computational elegance.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.cornerstone_invariant import (
    PhysicalInvariant,
    DiscreteInvariant,
    NumberTheoreticInvariant,
    CornerstoneInvariant,
    validate_cornerstone_principle,
)


def print_section(title, width=80):
    """Print a formatted section header."""
    print()
    print("=" * width)
    print(f" {title}")
    print("=" * width)
    print()


def demo_physical_domain():
    """Demonstrate physical domain with relativistic transformations."""
    print_section("1. PHYSICAL DOMAIN - Relativistic Transformations")

    phys = PhysicalInvariant()

    print(f"Invariant: c = {float(phys.c):.0f} m/s (speed of light)")
    print(f"Domain: {phys.domain}")
    print()

    # Time dilation examples
    print("Time Dilation Examples:")
    print("-" * 80)
    velocities = [0.1, 0.5, 0.8, 0.9, 0.99]

    for v_factor in velocities:
        velocity = v_factor * phys.c
        proper_time = 1.0  # 1 second in rest frame

        try:
            dilated_time = phys.time_dilation(proper_time, velocity)
            print(f"  v = {v_factor:.2f}c → τ = {float(dilated_time):.6f} seconds")
        except ValueError as e:
            print(f"  v = {v_factor:.2f}c → Error: {e}")

    print()

    # Length contraction examples
    print("Length Contraction Examples:")
    print("-" * 80)

    for v_factor in velocities:
        velocity = v_factor * phys.c
        rest_length = 10.0  # 10 meters in rest frame

        try:
            contracted = phys.length_contraction(rest_length, velocity)
            print(f"  v = {v_factor:.2f}c → L = {float(contracted):.6f} meters")
        except ValueError as e:
            print(f"  v = {v_factor:.2f}c → Error: {e}")

    print()
    print("Observation: As velocity approaches c, time dilates significantly")
    print("             and length contracts toward zero, consistent with")
    print("             special relativity predictions.")


def demo_discrete_domain():
    """Demonstrate discrete mathematical domain with prime densities."""
    print_section("2. DISCRETE MATHEMATICAL DOMAIN - Prime Density Normalization")

    discrete = DiscreteInvariant()

    print(f"Invariant: Δₘₐₓ = e² ≈ {float(discrete.c):.6f}")
    print(f"Domain: {discrete.domain}")
    print()

    # Prime density normalization
    print("Prime Density Normalization Examples:")
    print("-" * 80)

    test_values = [100, 500, 1000, 5000, 10000]

    for n in test_values:
        delta_n = 0.5  # Example frame shift
        normalized = discrete.compute_normalized_density(n, delta_n)
        print(f"  n = {n:5d}, Δₙ = {delta_n:.2f} → Z = {float(normalized):.4f}")

    print()

    # Divisor scaling
    print("Divisor-Based Frame Shift Examples:")
    print("-" * 80)

    for n in test_values:
        scaled = discrete.compute_divisor_scaling(n)
        print(f"  n = {n:5d} → Δₙ = d(n)·ln(n+1)/e² → Z = {float(scaled):.4f}")

    print()
    print("Observation: Discrete normalization provides consistent scaling")
    print("             for prime density analysis across different integer ranges.")


def demo_number_theoretic_domain():
    """Demonstrate number-theoretic domain with geodesic transformations."""
    print_section("3. NUMBER-THEORETIC DOMAIN - Geodesic Transformations")

    nt = NumberTheoreticInvariant()

    print(f"Invariant: φ = {float(nt.c):.6f} (golden ratio)")
    print(f"Domain: {nt.domain}")
    print()

    # Geodesic transformations
    print("Geodesic Transformation Examples (θ'(n,k) = φ·{n/φ}^k):")
    print("-" * 80)

    n_values = [10, 50, 100, 500, 1000]
    k_values = [0.1, 0.3, 0.5, 0.7]

    print(f"{'n':<8}", end="")
    for k in k_values:
        print(f"k={k:<12.1f}", end="")
    print()
    print("-" * 80)

    for n in n_values:
        print(f"{n:<8}", end="")
        for k in k_values:
            geodesic = nt.compute_geodesic_transform(n, k)
            print(f"{float(geodesic):12.4f}", end="  ")
        print()

    print()
    print("Observation: Geodesic transformations scale smoothly with n and k,")
    print("             enabling optimization and density enhancement analysis.")


def demo_cross_domain_consistency():
    """Demonstrate consistency of the invariant principle across domains."""
    print_section("4. CROSS-DOMAIN CONSISTENCY - Universal Application")

    print("Testing the same fundamental equation Z = A(B/c) across domains:")
    print("-" * 80)
    print()

    # Create instances for each domain
    phys = PhysicalInvariant()
    discrete = DiscreteInvariant()
    nt = NumberTheoreticInvariant()
    custom = CornerstoneInvariant(c=100.0, domain="custom")

    # Test with normalized parameters
    A_value = 10.0
    B_value = 50.0

    print(f"Input: A = {A_value}, B = {B_value}")
    print()

    domains = [
        ("Physical", phys, f"c = {float(phys.c):.0f}"),
        ("Discrete", discrete, f"c = {float(discrete.c):.4f}"),
        ("Number-Theoretic", nt, f"c = {float(nt.c):.6f}"),
        ("Custom", custom, f"c = {float(custom.c):.1f}"),
    ]

    for name, invariant, c_str in domains:
        result = invariant.compute_z(A=A_value, B=B_value)
        ratio = B_value / float(invariant.c)
        print(f"{name:20s}: {c_str:20s} → Z = {float(result):.10f}")

    print()
    print("Observation: The equation Z = A(B/c) consistently computes across")
    print("             all domains, adjusting only for domain-specific invariants.")


def demo_validation_checks():
    """Run and display validation checks for cornerstone principle."""
    print_section("5. CORNERSTONE PRINCIPLE VALIDATION")

    print("Running comprehensive validation checks...")
    print("-" * 80)
    print()

    validation = validate_cornerstone_principle()

    checks = [
        ("Universality", "Same equation works across domains"),
        ("Consistency", "Results are frame-invariant"),
        ("Reproducibility", "Same inputs give same outputs"),
        ("Symmetry", "Transformations preserve properties"),
        ("Precision", "High-precision computation maintained"),
    ]

    for i, (check_name, description) in enumerate(checks):
        passed = validation[check_name.lower() + "_check"]
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:20s}: {status}")
        print(f"{'':20s}  {description}")

        if not passed:
            error_key = check_name.lower() + "_error"
            if error_key in validation:
                print(f"{'':20s}  Error: {validation[error_key]}")
        print()

    overall_status = (
        "✅ ALL CHECKS PASSED"
        if validation["overall_pass"]
        else "❌ SOME CHECKS FAILED"
    )
    print("-" * 80)
    print(f"Overall Result: {overall_status}")


def demo_practical_applications():
    """Show practical applications of the cornerstone principle."""
    print_section("6. PRACTICAL APPLICATIONS")

    print("Real-world applications of the cornerstone invariant principle:")
    print("-" * 80)
    print()

    applications = [
        {
            "domain": "Unified Framework",
            "application": "Unifying relativistic and discrete formulations",
            "invariant": "c (speed of light)",
            "benefit": "Consistent theoretical foundation across physics and mathematics",
        },
        {
            "domain": "Cognitive Number Theory",
            "application": "Prime density and divisor-scaling analysis",
            "invariant": "e² or Δₘₐₓ",
            "benefit": "Normalized study of complex patterns in integer sequences",
        },
        {
            "domain": "Golden Ratio Geodesics",
            "application": "Optimization with geodesic constraints",
            "invariant": "φ (golden ratio)",
            "benefit": "Elegant optimization leveraging mathematical harmony",
        },
        {
            "domain": "RSA Cryptography",
            "application": "Semiprime factorization via Z5D",
            "invariant": "Domain-specific scaling constants",
            "benefit": "Novel approaches to computational number theory",
        },
    ]

    for i, app in enumerate(applications, 1):
        print(f"{i}. {app['domain']}")
        print(f"   Application: {app['application']}")
        print(f"   Invariant: {app['invariant']}")
        print(f"   Benefit: {app['benefit']}")
        print()


def demo_theoretical_significance():
    """Explain theoretical significance of the cornerstone principle."""
    print_section("7. THEORETICAL SIGNIFICANCE")

    print("Why the cornerstone invariant principle matters:")
    print("-" * 80)
    print()

    principles = [
        {
            "title": "Invariance is Robust",
            "description": "Anchors problem-solving around constants immune to "
            "arbitrary transformations or changes in observation frames. "
            "Results grounded in invariance generalize across disciplines.",
        },
        {
            "title": "Elegant Simplicity in Complexity",
            "description": "Just as Lorentz transformations simplify relativity for "
            "inertial frames, Z = A(B/c) simplifies complex mappings, "
            "scaling, and normalizations.",
        },
        {
            "title": "Tool for Discovery",
            "description": "Provides platform for reproducible validation across domains "
            "while inspiring new derivations. Applications include mutation "
            "analysis, curvature theories, and prime prediction.",
        },
        {
            "title": "Geometric Harmony",
            "description": "Introduces harmonious consistency that drives empirical, "
            "geometric, and computational innovation in both physical "
            "and abstract representations.",
        },
    ]

    for i, principle in enumerate(principles, 1):
        print(f"{i}. {principle['title']}")
        print(f"   {principle['description']}")
        print()


def main():
    """Run the complete cornerstone invariant demonstration."""
    print()
    print("=" * 80)
    print(" CORNERSTONE INVARIANT FRAMEWORK")
    print(" Cross-Domain Demonstration")
    print("=" * 80)
    print()
    print("This demonstration shows how the Lorentz-inspired normalization")
    print("equation Z = A(B/c) provides a universal foundation for the Z Framework,")
    print("enabling consistent, reproducible, and elegant solutions across")
    print("physical, mathematical, and computational domains.")

    # Run all demonstrations
    demo_physical_domain()
    demo_discrete_domain()
    demo_number_theoretic_domain()
    demo_cross_domain_consistency()
    demo_validation_checks()
    demo_practical_applications()
    demo_theoretical_significance()

    # Final summary
    print_section("CONCLUSION")
    print("The cornerstone invariant principle Z = A(B/c) is:")
    print()
    print("  • The FOUNDATION of the Z Framework")
    print("  • The BIG PICTURE governing overarching structure")
    print("  • The CRITICAL MECHANISM for immediate impact")
    print()
    print("It represents both:")
    print("  1. Theoretical profundity - deep mathematical insights")
    print("  2. Practical impact - efficient computational implementations")
    print()
    print("This is the scaffolding upon which all experimental and theoretical")
    print("work in the Z Framework is built.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
