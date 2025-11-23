"""
GVA Embedding and Curvature Computation

Implements GVA (Geometric Value Analysis) embedding for integers into
toroidal coordinates and computes discrete curvature κ(n).

References:
- GVA Implementation: https://github.com/zfifteen/z-sandbox
"""

import numpy as np
import mpmath as mp
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class GVAEmbedding:
    """
    GVA embedding for integers into high-dimensional tori.
    
    Computes discrete curvature κ(n) = d(n) * ln(n+1) / e²
    where d(n) is the divisor function.
    """
    
    def __init__(self, precision: int = 200):
        """
        Initialize GVA embedding with specified precision.
        
        Args:
            precision: Decimal precision for mpmath (adaptive: max(precision, bitLength*4+200))
        """
        self.precision = precision
        mp.mp.dps = precision
        logger.info(f"Initialized GVA embedding with precision={precision}")
    
    def compute_divisor_count(self, n: int, p: Optional[int] = None, q: Optional[int] = None) -> int:
        """
        Compute the number of divisors d(n).
        
        Args:
            n: Integer to compute divisors for
            p: Optional first prime factor (for semiprimes)
            q: Optional second prime factor (for semiprimes)
        
        Returns:
            Number of divisors
            
        Note:
            PHASE 1 LIMITATION: For large numbers without known factors (n > 1M),
            assumes primality and returns d(n) = 2. This is a placeholder for
            Phase 2 integration with proper factorization methods. In production,
            this should use the GVA factorization engine or proper primality testing.
            For the current experiment scope (testing semiprimes with known factors),
            this limitation does not affect correctness.
        """
        if n <= 0:
            return 0
        
        # Fast path for semiprimes with known factors
        if p is not None and q is not None:
            if p == q:
                # n = p^2 has divisors: 1, p, p^2
                return 3
            else:
                # n = p*q has divisors: 1, p, q, p*q
                return 4
        
        # For primes, d(p) = 2
        # Check small range for primality test optimization
        if n < 1000000:
            # Only do trial division for smaller numbers
            count = 0
            sqrt_n = int(float(n) ** 0.5)
            
            for i in range(1, sqrt_n + 1):
                if n % i == 0:
                    count += 1 if i * i == n else 2
            
            return count
        
        # For large numbers without factors, assume it's prime (d(n) = 2)
        # This is a placeholder - in Phase 2, this should use proper factorization
        logger.warning(f"Using placeholder divisor count for large n={n} without known factors")
        return 2
    
    def compute_curvature(self, n: int, p: Optional[int] = None, q: Optional[int] = None) -> mp.mpf:
        """
        Compute GVA discrete curvature κ(n) = d(n) * ln(n+1) / e².
        
        Args:
            n: Integer to compute curvature for
            p: Optional first prime factor (for semiprimes)
            q: Optional second prime factor (for semiprimes)
        
        Returns:
            Curvature value as mpmath high-precision float
        """
        # Adaptive precision: max(configured, bitLength * 4 + 200)
        bit_length = n.bit_length()
        adaptive_precision = max(self.precision, bit_length * 4 + 200)
        
        if adaptive_precision != mp.mp.dps:
            mp.mp.dps = adaptive_precision
            logger.debug(f"Adjusted precision to {adaptive_precision} for {bit_length}-bit number")
        
        d_n = self.compute_divisor_count(n, p, q)
        
        # κ(n) = d(n) * ln(n+1) / e²
        n_mp = mp.mpf(n)
        e_squared = mp.e ** 2
        curvature = mp.mpf(d_n) * mp.log(n_mp + 1) / e_squared
        
        logger.debug(f"κ({n}) = {d_n} * ln({n}+1) / e² = {curvature}")
        
        return curvature
    
    def embed_in_torus(self, n: int, lattice_basis: np.ndarray) -> np.ndarray:
        """
        Embed integer n into toroidal coordinates using lattice basis.
        
        The embedding scales n by the curvature and maps it onto the
        fundamental domain of the torus defined by the lattice.
        
        PHASE 1 PLACEHOLDER: Simple quasi-random distribution using golden ratio.
        Phase 2 will integrate full GVA embedding from gva_factorization.py
        with proper factor-manifold projection.
        
        Args:
            n: Integer to embed
            lattice_basis: Lattice basis matrix (dim x dim)
        
        Returns:
            Toroidal coordinates (dim-dimensional vector)
        """
        dimension = lattice_basis.shape[0]
        
        # Compute curvature scaling
        kappa = float(self.compute_curvature(n))
        
        # Project n onto lattice coordinates
        # Simple projection: distribute n across dimensions with curvature weighting
        n_float = float(n)
        
        # Use golden ratio for quasi-uniform distribution
        phi = (1 + np.sqrt(5)) / 2
        
        coords = np.zeros(dimension)
        for i in range(dimension):
            # Quasi-random distribution using golden ratio
            coords[i] = (n_float * (phi ** (i + 1))) % 1.0
        
        # Scale by curvature
        coords = coords * kappa
        
        # Map to fundamental domain using lattice basis
        # Reduce modulo the lattice
        try:
            lattice_coords = np.linalg.solve(lattice_basis, coords)
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse for singular matrices
            logger.warning("Singular lattice basis, using pseudo-inverse")
            lattice_coords = np.linalg.lstsq(lattice_basis, coords, rcond=None)[0]
        
        lattice_coords = lattice_coords % 1.0  # Periodic boundary
        
        # Back to Euclidean coordinates
        embedded_coords = lattice_basis @ lattice_coords
        
        logger.debug(f"Embedded n={n} into torus: {embedded_coords}")
        
        return embedded_coords
    
    def compute_geodesic_distance(self, coords1: np.ndarray, coords2: np.ndarray,
                                  lattice_basis: np.ndarray) -> float:
        """
        Compute geodesic distance between two points on the torus.
        
        On a flat torus, this is the minimum distance considering
        periodic boundary conditions.
        
        Args:
            coords1: First point coordinates
            coords2: Second point coordinates
            lattice_basis: Lattice basis defining the torus
        
        Returns:
            Geodesic distance
        """
        # Convert to lattice coordinates
        try:
            lat_coords1 = np.linalg.solve(lattice_basis, coords1)
            lat_coords2 = np.linalg.solve(lattice_basis, coords2)
        except np.linalg.LinAlgError:
            # Fallback for singular matrices
            lat_coords1 = np.linalg.lstsq(lattice_basis, coords1, rcond=None)[0]
            lat_coords2 = np.linalg.lstsq(lattice_basis, coords2, rcond=None)[0]
        
        # Compute difference with periodic boundary
        diff = lat_coords1 - lat_coords2
        diff = diff - np.round(diff)  # Shortest distance on torus
        
        # Back to Euclidean and compute norm
        euclidean_diff = lattice_basis @ diff
        distance = np.linalg.norm(euclidean_diff)
        
        return distance
    
    def map_factor_to_isospectral_class(self, factor: int, choir: list) -> int:
        """
        Map a factor to an isospectral class (lattice in the choir).
        
        This is a heuristic mapping based on factor properties.
        
        Args:
            factor: Prime factor to map
            choir: List of lattice bases (isospectral choir)
        
        Returns:
            Index of the lattice in the choir
        """
        # Simple heuristic: use factor modulo choir size
        choir_size = len(choir)
        index = factor % choir_size
        
        logger.debug(f"Mapped factor {factor} to lattice {index} in choir")
        
        return index
    
    def compute_metric_preservation_ratio(self, n: int, p: int, q: int,
                                          choir: list) -> float:
        """
        Compute metric preservation ratio for factor detection.
        
        Embeds n, p, q into isospectral choir and checks if geodesic
        distances are preserved according to the arithmetic relationship.
        
        PHASE 1 PLACEHOLDER: Simplified ratio for framework testing.
        Phase 2 will implement rigorous preservation metric based on
        Riemannian geometry and spectral theory from the literature.
        
        Args:
            n: Semiprime (n = p * q)
            p: First prime factor
            q: Second prime factor
            choir: List of isospectral lattice bases
        
        Returns:
            Preservation ratio (1.0 = perfect preservation)
        """
        # Embed in different lattices
        lattice_n = choir[0]  # Base lattice for n
        lattice_p = choir[self.map_factor_to_isospectral_class(p, choir)]
        lattice_q = choir[self.map_factor_to_isospectral_class(q, choir)]
        
        # Compute embeddings
        coords_n = self.embed_in_torus(n, lattice_n)
        coords_p = self.embed_in_torus(p, lattice_p)
        coords_q = self.embed_in_torus(q, lattice_q)
        
        # Expected relationship: κ(n) should relate to κ(p) and κ(q)
        kappa_n = float(self.compute_curvature(n, p, q))
        kappa_p = float(self.compute_curvature(p))
        kappa_q = float(self.compute_curvature(q))
        
        # Theoretical expectation (simplified)
        expected_ratio = kappa_n / (kappa_p + kappa_q)
        
        # Compute actual geometric distances
        dist_pq = self.compute_geodesic_distance(coords_p, coords_q, lattice_n)
        dist_n_origin = np.linalg.norm(coords_n)
        
        # Preservation ratio (how well geometry matches arithmetic)
        if dist_pq > 0:
            actual_ratio = dist_n_origin / dist_pq
            preservation = min(expected_ratio / actual_ratio, actual_ratio / expected_ratio)
        else:
            preservation = 0.0
        
        logger.info(f"Metric preservation ratio for n={n}: {preservation:.4f}")
        
        return preservation


def demonstrate_gva_embedding():
    """Demonstrate GVA embedding and curvature computation."""
    logger.info("=== Demonstrating GVA Embedding ===")
    
    gva = GVAEmbedding(precision=200)
    
    # Test with small semiprime
    n = 1073217479  # Gate 1: 30-bit
    p = 32749
    q = 32771
    
    print(f"\nTesting GVA embedding for n={n} (p={p}, q={q})")
    
    # Compute curvatures
    kappa_n = gva.compute_curvature(n, p, q)
    kappa_p = gva.compute_curvature(p)
    kappa_q = gva.compute_curvature(q)
    
    print(f"κ({n}) = {kappa_n}")
    print(f"κ({p}) = {kappa_p}")
    print(f"κ({q}) = {kappa_q}")
    
    # Create simple 4D lattice for demonstration
    lattice = np.eye(4)
    
    # Embed in torus
    coords_n = gva.embed_in_torus(n, lattice)
    coords_p = gva.embed_in_torus(p, lattice)
    coords_q = gva.embed_in_torus(q, lattice)
    
    print(f"\nEmbedded coordinates:")
    print(f"n: {coords_n}")
    print(f"p: {coords_p}")
    print(f"q: {coords_q}")
    
    # Compute geodesic distances
    dist_np = gva.compute_geodesic_distance(coords_n, coords_p, lattice)
    dist_nq = gva.compute_geodesic_distance(coords_n, coords_q, lattice)
    dist_pq = gva.compute_geodesic_distance(coords_p, coords_q, lattice)
    
    print(f"\nGeodesic distances:")
    print(f"d(n, p) = {dist_np:.4f}")
    print(f"d(n, q) = {dist_nq:.4f}")
    print(f"d(p, q) = {dist_pq:.4f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demonstrate_gva_embedding()
