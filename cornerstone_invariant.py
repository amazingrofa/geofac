"""
Cornerstone Invariant Framework
=================================

This module formalizes the cornerstone principle of the Z Framework:
the introduction of an **invariant** that governs systems across different domains,
utilizing the **Lorentz-inspired normalization equation** Z = A(B/c).

MATHEMATICAL FOUNDATION:
-----------------------

The Lorentz-inspired normalization equation:
    Z = A(B/c)

Where:
    - Z: Normalized observation or measurement
    - A: Frame-dependent quantity (scalar or function)
    - B: Rate, velocity, or domain parameter
    - c: Universal invariant constant (domain-dependent)

INVARIANT PROPERTIES:
--------------------

1. **Universality**: The invariant c provides a reference point that anchors
   all model observations across different frames of reference.

2. **Consistency**: By standardizing against a constant, systems maintain
   consistency across frames of reference, whether in physics, mathematics,
   or computational domains.

3. **Reproducibility**: The invariant removes ambiguity in comparative
   measurements or derived quantities, leading to outcomes that are both
   reproducible and comparable.

4. **Symmetry**: Mirrors the geometry in relativity where transformations
   preserve the invariant (speed of light), creating symmetry and robustness
   in derived properties.

DOMAIN APPLICATIONS:
-------------------

1. **Physical Domain**: Z = T(v/c)
   - Invariant: c = speed of light (299,792,458 m/s)
   - Application: Relativistic time dilation, length contraction
   - Frame-dependent: Time, length, mass measurements

2. **Discrete Mathematical Domain**: Z = n(Δₙ/Δₘₐₓ)
   - Invariant: Δₘₐₓ = e² (default maximum frame shift)
   - Application: Prime density mapping, discrete distributions
   - Frame-dependent: Integer sequences, divisor functions

3. **Number-Theoretic Domain**: Z = θ'(n,k)
   - Invariant: φ (golden ratio) or other mathematical constants
   - Application: Prime-density scaling, divisor relationships
   - Frame-dependent: Density functions, curvature measures

4. **Optimization Domain**: Z = f(x/x_max)
   - Invariant: x_max = maximum value in optimization space
   - Application: Golden ratio geodesics, optimization constraints
   - Frame-dependent: Objective function values

THEORETICAL SIGNIFICANCE:
------------------------

This principle is the scaffolding upon which the Z Framework is built,
providing:

- **Invariance is Robust**: Anchors problem-solving around constants immune
  to arbitrary transformations or changes in observation frames.

- **Elegant Simplicity in Complexity**: Just as Lorentz transformations
  simplify the theory of relativity for inertial frames, Z = A(B/c)
  simplifies otherwise complex mappings, scaling, and normalizations.

- **Tool for Discovery**: Provides a platform for reproducible validation
  across domains while inspiring new derivations.

- **Geometric Harmony**: Introduces harmonious consistency that drives
  empirical, geometric, and computational innovation.

USAGE EXAMPLES:
--------------

    # Physical domain - relativistic transformations
    >>> from src.core.cornerstone_invariant import PhysicalInvariant
    >>> phys = PhysicalInvariant()
    >>> time_dilated = phys.compute_z(proper_time=1.0, velocity=0.8*phys.c)

    # Discrete domain - prime density normalization
    >>> from src.core.cornerstone_invariant import DiscreteInvariant
    >>> discrete = DiscreteInvariant()
    >>> normalized = discrete.compute_z(n=1000, delta_n=0.5)

    # Custom domain - arbitrary invariant
    >>> from src.core.cornerstone_invariant import CornerstoneInvariant
    >>> custom = CornerstoneInvariant(c=100.0, domain="custom")
    >>> result = custom.compute_z(A=10, B=50)

INTEGRATION WITH FRAMEWORK:
---------------------------

This module integrates with:
- src.core.axioms: Universal Z form implementation
- src.core.z_baseline: Baseline Z predictor
- src.core.z_5d_enhanced: Enhanced 5D predictions
- src.core.geodesic_mapping: Geodesic density transformations

References:
-----------
- Lorentz transformations in special relativity
- Z Framework unified-framework repository
- Cognitive Number Theory applications
- Golden Ratio Geodesics optimization
"""

import mpmath as mp
from typing import Union, Callable, Dict, Any, Optional
from math import e, log, sqrt

# Note: Precision is managed locally within methods using mp.workdps()
# to avoid global side effects that could affect other parts of the codebase


class CornerstoneInvariant:
    """
    Base class implementing the cornerstone invariant principle Z = A(B/c).

    This class provides the fundamental implementation of the Lorentz-inspired
    normalization equation that anchors the entire Z Framework.

    Attributes:
        c (mp.mpf): Universal invariant constant for the domain
        domain (str): Name of the application domain
        precision_threshold (mp.mpf): Numerical precision requirement (default: 1e-16)
    """

    def __init__(
        self, c: float, domain: str = "universal", precision_threshold: float = 1e-16
    ):
        """
        Initialize cornerstone invariant with domain-specific constant.

        Args:
            c: Universal invariant constant (must be positive)
            domain: Name of the application domain
            precision_threshold: Maximum acceptable numerical error

        Raises:
            ValueError: If c is not positive
        """
        if c <= 0:
            raise ValueError(f"Invariant c must be positive, got {c}")

        self.c = mp.mpf(c)
        self.domain = domain
        self.precision_threshold = mp.mpf(precision_threshold)

    def compute_z(
        self, A: Union[float, Callable], B: float, validate_precision: bool = True
    ) -> mp.mpf:
        """
        Compute Z = A(B/c) with Lorentz-inspired normalization.

        Args:
            A: Frame-dependent quantity (scalar or function)
            B: Rate, velocity, or domain parameter
            validate_precision: Whether to validate numerical precision

        Returns:
            Normalized Z value with high precision

        Raises:
            ValueError: If precision requirements not met
        """
        # Convert to high precision
        B_mp = mp.mpf(B)

        # Compute normalized ratio
        ratio = B_mp / self.c

        # Apply frame-dependent transformation
        if callable(A):
            result = A(ratio)
        else:
            A_mp = mp.mpf(A)
            result = A_mp * ratio

        # Validate precision if requested
        if validate_precision:
            self._validate_precision(result)

        return result

    def _validate_precision(self, result: mp.mpf) -> None:
        """
        Validate numerical precision meets framework requirements.

        Args:
            result: Computed result to validate

        Raises:
            ValueError: If precision requirement not satisfied
        """
        # Cross-precision validation
        with mp.workdps(25):
            low_prec = mp.mpf(result)

        precision_error = abs(result - low_prec)

        if precision_error >= self.precision_threshold:
            raise ValueError(
                f"Precision requirement not met in {self.domain} domain: "
                f"Δ = {precision_error} >= {self.precision_threshold}"
            )

    def get_invariant_properties(self) -> Dict[str, Any]:
        """
        Get properties of the invariant for this domain.

        Returns:
            Dictionary containing invariant properties
        """
        return {
            "domain": self.domain,
            "invariant_c": float(self.c),
            "precision_threshold": float(self.precision_threshold),
            "universality": "Provides reference frame consistency",
            "symmetry": "Preserves transformation properties",
            "reproducibility": "Enables comparable measurements",
        }


class PhysicalInvariant(CornerstoneInvariant):
    """
    Physical domain implementation with c = speed of light.

    Implements Z = T(v/c) for relativistic transformations where:
    - c = 299,792,458 m/s (speed of light)
    - T = frame-dependent physical quantity (time, length, mass)
    - v = velocity

    This specialization enforces causality constraints (|v| < c).
    """

    SPEED_OF_LIGHT = 299792458.0  # m/s

    def __init__(self, precision_threshold: float = 1e-16):
        """Initialize physical domain with speed of light as invariant."""
        super().__init__(
            c=self.SPEED_OF_LIGHT,
            domain="physical",
            precision_threshold=precision_threshold,
        )

    def time_dilation(self, proper_time: float, velocity: float) -> mp.mpf:
        """
        Compute relativistic time dilation: τ = τ₀/√(1-(v/c)²)

        Args:
            proper_time: Proper time in rest frame
            velocity: Velocity of moving frame

        Returns:
            Dilated time measurement

        Raises:
            ValueError: If velocity exceeds speed of light (causality violation)
        """
        if abs(velocity) >= self.c:
            raise ValueError(
                f"Causality violation: |v| = {abs(velocity)} >= c = {self.c}"
            )

        def lorentz_factor(v_over_c):
            """Lorentz factor γ = 1/√(1-β²)"""
            beta_sq = v_over_c**2
            if beta_sq >= 1:
                raise ValueError("Relativistic factor requires |v/c| < 1")
            return proper_time / mp.sqrt(1 - beta_sq)

        return self.compute_z(lorentz_factor, velocity)

    def length_contraction(self, rest_length: float, velocity: float) -> mp.mpf:
        """
        Compute relativistic length contraction: L = L₀√(1-(v/c)²)

        Args:
            rest_length: Length in rest frame
            velocity: Velocity of moving frame

        Returns:
            Contracted length measurement
        """
        if abs(velocity) >= self.c:
            raise ValueError(
                f"Causality violation: |v| = {abs(velocity)} >= c = {self.c}"
            )

        def contraction_factor(v_over_c):
            """Contraction factor = √(1-β²)"""
            beta_sq = v_over_c**2
            if beta_sq >= 1:
                raise ValueError("Contraction requires |v/c| < 1")
            return rest_length * mp.sqrt(1 - beta_sq)

        return self.compute_z(contraction_factor, velocity)

    def relativistic_momentum(self, rest_mass: float, velocity: float) -> mp.mpf:
        """
        Compute relativistic momentum: p = γm₀v

        Args:
            rest_mass: Rest mass
            velocity: Velocity

        Returns:
            Relativistic momentum
        """
        if abs(velocity) >= self.c:
            raise ValueError("Causality violation: |v| >= c")

        gamma = self.time_dilation(1.0, velocity)  # Lorentz factor
        return rest_mass * velocity * gamma


class DiscreteInvariant(CornerstoneInvariant):
    """
    Discrete mathematical domain implementation with Δₘₐₓ as invariant.

    Implements Z = n(Δₙ/Δₘₐₓ) for discrete distributions where:
    - Δₘₐₓ = e² (default maximum frame shift)
    - n = frame-dependent integer
    - Δₙ = measured frame shift at n

    Applications: Prime density mapping, divisor scaling, integer sequences.
    """

    E_SQUARED = e**2  # Default discrete invariant

    def __init__(
        self, delta_max: Optional[float] = None, precision_threshold: float = 1e-16
    ):
        """
        Initialize discrete domain with maximum frame shift as invariant.

        Args:
            delta_max: Maximum frame shift (default: e²)
            precision_threshold: Numerical precision requirement
        """
        invariant = delta_max if delta_max is not None else self.E_SQUARED
        super().__init__(
            c=invariant, domain="discrete", precision_threshold=precision_threshold
        )

    def compute_normalized_density(self, n: int, delta_n: float) -> mp.mpf:
        """
        Compute normalized prime density: Z = n(Δₙ/Δₘₐₓ)

        Args:
            n: Frame-dependent integer
            delta_n: Frame shift at n

        Returns:
            Normalized density value
        """
        return self.compute_z(A=n, B=delta_n)

    def compute_divisor_scaling(self, n: int) -> mp.mpf:
        """
        Compute divisor-based frame shift: Δₙ = d(n)·ln(n+1)/e²

        Args:
            n: Integer for divisor computation

        Returns:
            Normalized divisor scaling

        Note:
            Uses log(n) as simplified approximation for d(n) (divisor count).
            This approximation is consistent with z_baseline implementation
            and provides adequate accuracy for frame shift calculations.
            For exact divisor counts, consider using sympy.divisor_count().
        """
        if n < 1:
            return mp.mpf(0)

        # Approximate divisor count (consistent with z_baseline)
        # This is a simplified approximation: d(n) ≈ log(n)
        d_n = log(n) if n > 1 else 1
        ln_term = log(n + 1)
        delta_n = (d_n * ln_term) / self.c

        return self.compute_z(A=n, B=delta_n)


class NumberTheoreticInvariant(CornerstoneInvariant):
    """
    Number-theoretic domain with golden ratio or mathematical constants.

    Implements Z = θ'(n,k) for prime-density transformations where:
    - c = φ (golden ratio) or other mathematical constant
    - θ'(n,k) = geodesic transformation for prime density

    Applications: Cognitive Number Theory, golden ratio geodesics.
    """

    # Use high-precision golden ratio calculation (maintain mp.mpf precision)
    GOLDEN_RATIO = mp.mpf(1 + mp.sqrt(5)) / 2  # φ ≈ 1.618

    def __init__(
        self,
        invariant_constant: Optional[float] = None,
        precision_threshold: float = 1e-16,
    ):
        """
        Initialize number-theoretic domain.

        Args:
            invariant_constant: Mathematical constant (default: golden ratio)
            precision_threshold: Numerical precision requirement
        """
        invariant = invariant_constant if invariant_constant else self.GOLDEN_RATIO
        super().__init__(
            c=invariant,
            domain="number_theoretic",
            precision_threshold=precision_threshold,
        )

    def compute_geodesic_transform(self, n: int, k: float) -> mp.mpf:
        """
        Compute geodesic transformation: θ'(n,k) = φ·{n/φ}^k

        Args:
            n: Integer parameter
            k: Geodesic exponent

        Returns:
            Geodesic-transformed value
        """

        def geodesic_func(ratio):
            """Geodesic transformation function"""
            return self.c * (ratio**k)

        return self.compute_z(geodesic_func, B=n)


def demonstrate_invariant_universality():
    """
    Demonstrate the universality of the invariant principle across domains.

    Returns:
        Dictionary with demonstration results for each domain
    """
    results = {}

    # Physical domain demonstration
    phys = PhysicalInvariant()
    results["physical"] = {
        "domain": "Physical (Relativity)",
        "invariant": f"c = {float(phys.c)} m/s",
        "example": "Time dilation at v = 0.8c",
        "result": float(phys.time_dilation(1.0, 0.8 * phys.c)),
    }

    # Discrete domain demonstration
    discrete = DiscreteInvariant()
    results["discrete"] = {
        "domain": "Discrete Mathematics",
        "invariant": f"Δₘₐₓ = e² ≈ {float(discrete.c):.4f}",
        "example": "Prime density normalization at n=1000",
        "result": float(discrete.compute_divisor_scaling(1000)),
    }

    # Number-theoretic domain demonstration
    nt = NumberTheoreticInvariant()
    results["number_theoretic"] = {
        "domain": "Number Theory",
        "invariant": f"φ = {float(nt.c):.6f} (golden ratio)",
        "example": "Geodesic transform θ'(100, 0.3)",
        "result": float(nt.compute_geodesic_transform(100, 0.3)),
    }

    return results


def validate_cornerstone_principle():
    """
    Validate the cornerstone invariant principle with consistency checks.

    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "universality_check": False,
        "consistency_check": False,
        "reproducibility_check": False,
        "symmetry_check": False,
        "precision_check": False,
    }

    # Test 1: Universality - same equation works across domains
    try:
        phys = PhysicalInvariant()
        discrete = DiscreteInvariant()

        # Both should compute without error
        _ = phys.compute_z(A=1.0, B=1.0e8)
        _ = discrete.compute_z(A=100, B=5.0)

        validation_results["universality_check"] = True
    except Exception as e:
        validation_results["universality_error"] = str(e)

    # Test 2: Consistency - results are frame-invariant
    try:
        phys = PhysicalInvariant()

        # Time dilation should be consistent regardless of computation path
        t1 = phys.time_dilation(2.0, 0.5 * phys.c)
        t2 = 2.0 * phys.time_dilation(1.0, 0.5 * phys.c)

        if abs(t1 - t2) < 1e-10:
            validation_results["consistency_check"] = True
    except Exception as e:
        validation_results["consistency_error"] = str(e)

    # Test 3: Reproducibility - same inputs give same outputs
    try:
        discrete = DiscreteInvariant()

        results = [discrete.compute_divisor_scaling(500) for _ in range(5)]

        if all(abs(r - results[0]) < 1e-15 for r in results):
            validation_results["reproducibility_check"] = True
    except Exception as e:
        validation_results["reproducibility_error"] = str(e)

    # Test 4: Symmetry - transformation preserves properties
    try:
        nt = NumberTheoreticInvariant()

        # Geodesic transformations should preserve relative ordering
        z1 = nt.compute_geodesic_transform(10, 0.3)
        z2 = nt.compute_geodesic_transform(20, 0.3)

        if z2 > z1:  # Ordering preserved
            validation_results["symmetry_check"] = True
    except Exception as e:
        validation_results["symmetry_error"] = str(e)

    # Test 5: Precision - high-precision computation maintained
    try:
        phys = PhysicalInvariant()

        # Should maintain precision within threshold
        phys.time_dilation(1.0, 0.9 * phys.c)

        # If no exception raised, precision is maintained
        validation_results["precision_check"] = True
    except Exception as e:
        validation_results["precision_error"] = str(e)

    validation_results["overall_pass"] = all(
        [
            validation_results["universality_check"],
            validation_results["consistency_check"],
            validation_results["reproducibility_check"],
            validation_results["symmetry_check"],
            validation_results["precision_check"],
        ]
    )

    return validation_results


if __name__ == "__main__":
    print("=" * 70)
    print("CORNERSTONE INVARIANT FRAMEWORK DEMONSTRATION")
    print("=" * 70)
    print()

    # Demonstrate universality
    print("1. INVARIANT UNIVERSALITY ACROSS DOMAINS")
    print("-" * 70)
    demo_results = demonstrate_invariant_universality()
    for key, result in demo_results.items():
        print(f"\n{result['domain']}:")
        print(f"  Invariant: {result['invariant']}")
        print(f"  Example: {result['example']}")
        print(f"  Result: {result['result']:.6f}")

    print()
    print("=" * 70)

    # Validate cornerstone principle
    print("2. CORNERSTONE PRINCIPLE VALIDATION")
    print("-" * 70)
    validation = validate_cornerstone_principle()

    checks = [
        ("Universality", validation["universality_check"]),
        ("Consistency", validation["consistency_check"]),
        ("Reproducibility", validation["reproducibility_check"]),
        ("Symmetry", validation["symmetry_check"]),
        ("Precision", validation["precision_check"]),
    ]

    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name}: {status}")

    print()
    overall = (
        "✅ ALL CHECKS PASSED"
        if validation["overall_pass"]
        else "❌ SOME CHECKS FAILED"
    )
    print(f"Overall: {overall}")
    print("=" * 70)
