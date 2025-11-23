"""
Quasi-Monte Carlo Probing with Sobol Sequences and Owen Scrambling

Implements parallel QMC probing across isospectral tori for resonance
cross-validation.

References:
- QMC methods: Sobol sequences, Owen scrambling
"""

import numpy as np
from scipy.stats import qmc
from typing import List, Tuple, Optional
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class QMCProbe:
    """
    Quasi-Monte Carlo probe using Sobol sequences with Owen scrambling.
    
    Implements parallel probing across multiple isospectral tori for
    resonance cross-validation.
    """
    
    def __init__(self, dimension: int, n_samples: int = 10000, 
                 scramble: bool = True, seed: int = 42):
        """
        Initialize QMC probe.
        
        Args:
            dimension: Dimension of the search space
            n_samples: Number of QMC samples
            scramble: Use Owen scrambling
            seed: Random seed for scrambling
        """
        self.dimension = dimension
        self.n_samples = n_samples
        self.scramble = scramble
        self.seed = seed
        
        # Initialize Sobol sequence generator
        self.sampler = qmc.Sobol(d=dimension, scramble=scramble, seed=seed)
        
        logger.info(f"Initialized QMC probe: dim={dimension}, samples={n_samples}, "
                   f"scramble={scramble}")
    
    def generate_samples(self, n_samples: Optional[int] = None) -> np.ndarray:
        """
        Generate Sobol sequence samples.
        
        Args:
            n_samples: Number of samples (uses default if None)
        
        Returns:
            Array of shape (n_samples, dimension) in [0, 1]^d
        """
        if n_samples is None:
            n_samples = self.n_samples
        
        samples = self.sampler.random(n_samples)
        
        logger.debug(f"Generated {n_samples} Sobol samples")
        return samples
    
    def scale_to_search_space(self, samples: np.ndarray, 
                              bounds: List[Tuple[float, float]]) -> np.ndarray:
        """
        Scale unit hypercube samples to search space bounds.
        
        Args:
            samples: Samples in [0, 1]^d
            bounds: List of (lower, upper) bounds for each dimension
        
        Returns:
            Scaled samples
        """
        if len(bounds) != self.dimension:
            raise ValueError(f"Bounds must have {self.dimension} dimensions")
        
        scaled = np.zeros_like(samples)
        for i, (lower, upper) in enumerate(bounds):
            scaled[:, i] = lower + samples[:, i] * (upper - lower)
        
        return scaled
    
    def compute_resonance_amplitude(self, sample: np.ndarray, n: int, 
                                   lattice_basis: np.ndarray) -> float:
        """
        Compute resonance amplitude at a sample point.
        
        PHASE 1 PLACEHOLDER: This is a simplified resonance computation.
        Phase 2 will integrate the full GVA Dirichlet kernel gating and
        phase-corrected snap mechanisms from the main geofac implementation.
        
        Args:
            sample: Sample point in search space
            n: Target semiprime
            lattice_basis: Lattice basis for the torus
        
        Returns:
            Resonance amplitude (0 to 1)
        """
        # Simplified resonance: depends on distance from factor manifold
        # In reality, this would use Dirichlet kernel gating, etc.
        
        # Compute a pseudo-resonance based on sample properties
        # Higher values near sqrt(n)
        sqrt_n = float(n) ** 0.5
        
        # Sample represents a potential factor candidate
        candidate = sample[0] if len(sample) > 0 else sqrt_n
        
        # Resonance decays with distance from sqrt(n)
        distance_factor = np.exp(-np.abs(candidate - sqrt_n) / sqrt_n)
        
        # Add geometric contribution from lattice
        lattice_contribution = 1.0 / (1.0 + np.linalg.norm(lattice_basis @ sample[:self.dimension]))
        
        amplitude = distance_factor * lattice_contribution
        
        return float(amplitude)
    
    def probe_torus(self, n: int, lattice_basis: np.ndarray, 
                   n_samples: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Probe a single torus with QMC samples.
        
        Args:
            n: Target semiprime
            lattice_basis: Lattice basis for the torus
            n_samples: Number of samples (uses default if None)
        
        Returns:
            (samples, amplitudes) tuple
        """
        if n_samples is None:
            n_samples = self.n_samples
        
        # Generate samples
        samples = self.generate_samples(n_samples)
        
        # Scale to search space around sqrt(n)
        sqrt_n = float(n) ** 0.5
        search_width = 0.1 * sqrt_n  # 10% window
        
        bounds = [(sqrt_n - search_width, sqrt_n + search_width)] + \
                 [(-1, 1)] * (self.dimension - 1)
        scaled_samples = self.scale_to_search_space(samples, bounds)
        
        # Compute resonance amplitudes
        amplitudes = np.array([
            self.compute_resonance_amplitude(sample, n, lattice_basis)
            for sample in scaled_samples
        ])
        
        logger.debug(f"Probed torus: mean amplitude={np.mean(amplitudes):.4f}, "
                    f"max amplitude={np.max(amplitudes):.4f}")
        
        return scaled_samples, amplitudes
    
    def parallel_probe_choir(self, n: int, choir: List[np.ndarray], 
                            n_samples: Optional[int] = None,
                            max_workers: int = 4) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Probe multiple tori in parallel.
        
        PHASE 1 NOTE: Currently runs sequentially. Phase 3 will add true
        parallelism using ProcessPoolExecutor with proper QMC state handling.
        Structure is ready for parallelization.
        
        Args:
            n: Target semiprime
            choir: List of lattice bases (isospectral choir)
            n_samples: Number of samples per torus
            max_workers: Number of parallel workers (reserved for Phase 3)
        
        Returns:
            List of (samples, amplitudes) tuples for each torus
        """
        logger.info(f"Parallel probing {len(choir)} tori with {max_workers} workers")
        
        results = []
        
        # Note: For true parallelism, would need to handle QMC state carefully
        # For now, probe sequentially but structure for parallelization
        for i, lattice_basis in enumerate(choir):
            logger.debug(f"Probing torus {i+1}/{len(choir)}")
            result = self.probe_torus(n, lattice_basis, n_samples)
            results.append(result)
        
        logger.info(f"Completed parallel probing of {len(results)} tori")
        return results
    
    def cross_validate_resonances(self, probe_results: List[Tuple[np.ndarray, np.ndarray]],
                                  threshold: float = 0.95) -> Tuple[float, int]:
        """
        Cross-validate resonances across multiple tori.
        
        Checks for spectral overlap - high resonances that appear
        consistently across isospectral tori indicate preserved metrics.
        
        Args:
            probe_results: List of (samples, amplitudes) from each torus
            threshold: Minimum amplitude to consider as resonance
        
        Returns:
            (overlap_ratio, n_consistent_resonances)
        """
        if not probe_results:
            return 0.0, 0
        
        # Find high-amplitude samples in each torus
        resonance_sets = []
        for samples, amplitudes in probe_results:
            high_amp_indices = np.where(amplitudes > threshold)[0]
            # Use first coordinate rounded to reasonable precision for set operations
            # Round to 6 decimal places to avoid floating-point precision issues
            resonances = set(np.round(samples[high_amp_indices, 0], decimals=6))
            resonance_sets.append(resonances)
        
        # Compute overlap
        if len(resonance_sets) > 1:
            # Intersection of all sets
            common_resonances = set.intersection(*resonance_sets)
            # Union of all sets
            all_resonances = set.union(*resonance_sets)
            
            overlap_ratio = len(common_resonances) / len(all_resonances) if all_resonances else 0.0
            n_consistent = len(common_resonances)
        else:
            overlap_ratio = 1.0
            n_consistent = len(resonance_sets[0]) if resonance_sets else 0
        
        logger.info(f"Cross-validation: overlap={overlap_ratio:.4f}, "
                   f"consistent_resonances={n_consistent}")
        
        return overlap_ratio, n_consistent
    
    def estimate_convergence_error(self, amplitudes: np.ndarray, 
                                   window_size: int = 100) -> float:
        """
        Estimate QMC convergence error.
        
        Computes running mean stability to estimate convergence.
        
        Args:
            amplitudes: Array of amplitude values
            window_size: Window size for running mean
        
        Returns:
            Estimated relative error
        """
        if len(amplitudes) < 2 * window_size:
            return 1.0  # Insufficient samples
        
        # Compute running means
        running_means = np.convolve(amplitudes, 
                                   np.ones(window_size) / window_size, 
                                   mode='valid')
        
        # Estimate error from variance of running means
        if len(running_means) > 0:
            error = np.std(running_means) / (np.mean(running_means) + 1e-10)
        else:
            error = 1.0
        
        logger.debug(f"Estimated convergence error: {error:.4e}")
        return float(error)


def demonstrate_qmc_probing():
    """Demonstrate QMC probing."""
    logger.info("=== Demonstrating QMC Probing ===")
    
    # Create QMC probe
    probe = QMCProbe(dimension=4, n_samples=1000, scramble=True, seed=42)
    
    # Generate samples
    samples = probe.generate_samples(100)
    print(f"Generated {len(samples)} Sobol samples")
    print(f"Sample shape: {samples.shape}")
    print(f"First 5 samples:\n{samples[:5]}")
    
    # Test probing
    n = 1073217479  # Gate 1 semiprime
    lattice = np.eye(4)
    
    scaled_samples, amplitudes = probe.probe_torus(n, lattice, n_samples=100)
    
    print(f"\nProbing results:")
    print(f"Mean amplitude: {np.mean(amplitudes):.4f}")
    print(f"Max amplitude: {np.max(amplitudes):.4f}")
    print(f"Samples above 0.5: {np.sum(amplitudes > 0.5)}")
    
    # Test convergence
    error = probe.estimate_convergence_error(amplitudes)
    print(f"Estimated convergence error: {error:.4e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demonstrate_qmc_probing()
