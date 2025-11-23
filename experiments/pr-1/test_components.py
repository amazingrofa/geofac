"""
Unit tests for PR-1 experiment components.

Tests individual modules: torus_construction, gva_embedding, qmc_probe
"""

import sys
import unittest
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from torus_construction import IsospectraLatticeGenerator
from gva_embedding import GVAEmbedding
from qmc_probe import QMCProbe


class TestTorusConstruction(unittest.TestCase):
    """Test torus construction and isospectral lattice generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator_4d = IsospectraLatticeGenerator(dimension=4)
        self.generator_6d = IsospectraLatticeGenerator(dimension=6)
        self.generator_8d = IsospectraLatticeGenerator(dimension=8)
    
    def test_even_quadratic_form_4d(self):
        """Test 4D even quadratic form generation."""
        basis = self.generator_4d.generate_even_quadratic_form()
        
        self.assertEqual(basis.shape, (4, 4))
        self.assertIsInstance(basis, np.ndarray)
        
        # Check that basis is not just identity
        self.assertFalse(np.allclose(basis, np.eye(4)))
    
    def test_even_quadratic_form_6d(self):
        """Test 6D even quadratic form generation."""
        basis = self.generator_6d.generate_even_quadratic_form()
        
        self.assertEqual(basis.shape, (6, 6))
        self.assertIsInstance(basis, np.ndarray)
    
    def test_even_quadratic_form_8d(self):
        """Test 8D even quadratic form generation."""
        basis = self.generator_8d.generate_even_quadratic_form()
        
        self.assertEqual(basis.shape, (8, 8))
        self.assertIsInstance(basis, np.ndarray)
    
    def test_deform_basis(self):
        """Test basis deformation."""
        original = self.generator_4d.generate_even_quadratic_form()
        deformed = self.generator_4d.deform_basis(original)
        
        self.assertEqual(deformed.shape, original.shape)
        # Deformed should be different
        self.assertFalse(np.allclose(deformed, original))
    
    def test_compute_laplace_eigenvalues(self):
        """Test Laplace eigenvalue computation."""
        basis = np.eye(4)
        eigs = self.generator_4d.compute_laplace_eigenvalues(basis, n_eigenvalues=10)
        
        self.assertEqual(len(eigs), 10)
        # Eigenvalues should be positive
        self.assertTrue(np.all(eigs > 0))
        # Should be sorted
        self.assertTrue(np.all(eigs[:-1] <= eigs[1:]))
    
    def test_verify_isospectrality(self):
        """Test isospectrality verification."""
        basis1 = np.eye(4)
        basis2 = np.eye(4) * 1.0  # Same basis, should be isospectral
        
        is_iso, max_diff = self.generator_4d.verify_isospectrality(basis1, basis2)
        
        self.assertTrue(is_iso)
        self.assertLess(max_diff, 1e-10)
    
    def test_generate_isospectral_choir_4d(self):
        """Test choir generation for 4D."""
        choir = self.generator_4d.generate_isospectral_choir(choir_size=2)
        
        self.assertEqual(len(choir), 2)
        for basis in choir:
            self.assertEqual(basis.shape, (4, 4))
    
    def test_generate_isospectral_choir_6d(self):
        """Test choir generation for 6D."""
        choir = self.generator_6d.generate_isospectral_choir(choir_size=3)
        
        self.assertEqual(len(choir), 3)
        for basis in choir:
            self.assertEqual(basis.shape, (6, 6))


class TestGVAEmbedding(unittest.TestCase):
    """Test GVA embedding and curvature computation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gva = GVAEmbedding(precision=50)
    
    def test_compute_divisor_count_small(self):
        """Test divisor count for small numbers."""
        # Prime number
        self.assertEqual(self.gva.compute_divisor_count(7), 2)
        # Composite
        self.assertEqual(self.gva.compute_divisor_count(12), 6)
    
    def test_compute_divisor_count_semiprime(self):
        """Test divisor count for semiprimes with known factors."""
        p, q = 13, 17
        n = p * q
        
        # With factors
        count = self.gva.compute_divisor_count(n, p, q)
        self.assertEqual(count, 4)
        
        # Without factors (small enough to compute)
        count_no_factors = self.gva.compute_divisor_count(n)
        self.assertEqual(count_no_factors, 4)
    
    def test_compute_curvature(self):
        """Test curvature computation."""
        n = 1073217479  # 30-bit semiprime
        p = 32749
        q = 32771
        
        kappa = self.gva.compute_curvature(n, p, q)
        
        # Should be a positive value
        self.assertGreater(float(kappa), 0)
    
    def test_embed_in_torus(self):
        """Test toroidal embedding."""
        n = 100
        lattice = np.eye(4)
        
        coords = self.gva.embed_in_torus(n, lattice)
        
        self.assertEqual(len(coords), 4)
        self.assertIsInstance(coords, np.ndarray)
    
    def test_compute_geodesic_distance(self):
        """Test geodesic distance computation."""
        coords1 = np.array([0.1, 0.2, 0.3, 0.4])
        coords2 = np.array([0.5, 0.6, 0.7, 0.8])
        lattice = np.eye(4)
        
        dist = self.gva.compute_geodesic_distance(coords1, coords2, lattice)
        
        self.assertGreater(dist, 0)
        self.assertIsInstance(dist, float)


class TestQMCProbe(unittest.TestCase):
    """Test QMC probing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.qmc = QMCProbe(dimension=4, n_samples=100, scramble=True)
    
    def test_generate_samples(self):
        """Test Sobol sequence generation."""
        samples = self.qmc.generate_samples(50)
        
        self.assertEqual(samples.shape, (50, 4))
        # Should be in [0, 1] range
        self.assertTrue(np.all(samples >= 0))
        self.assertTrue(np.all(samples <= 1))
    
    def test_scale_to_search_space(self):
        """Test sample scaling."""
        samples = np.random.rand(10, 4)
        bounds = [(0, 10), (-1, 1), (-1, 1), (-1, 1)]
        
        scaled = self.qmc.scale_to_search_space(samples, bounds)
        
        self.assertEqual(scaled.shape, samples.shape)
        # Check bounds
        self.assertTrue(np.all(scaled[:, 0] >= 0))
        self.assertTrue(np.all(scaled[:, 0] <= 10))
    
    def test_compute_resonance_amplitude(self):
        """Test resonance amplitude computation."""
        sample = np.array([1e9, 0.1, 0.2, 0.3])
        n = 1000000000019  # Prime
        lattice = np.eye(4)
        
        amp = self.qmc.compute_resonance_amplitude(sample, n, lattice)
        
        self.assertIsInstance(amp, (float, np.floating))
        self.assertGreaterEqual(amp, 0)
    
    def test_probe_torus(self):
        """Test full torus probing."""
        n = 1073217479
        lattice = np.eye(4)
        
        samples, amplitudes = self.qmc.probe_torus(n, lattice)
        
        self.assertEqual(len(samples), 100)
        self.assertEqual(len(amplitudes), 100)
        self.assertTrue(np.all(amplitudes >= 0))


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""
    
    def test_end_to_end_4d(self):
        """Test complete workflow for 4D."""
        # Generate lattices
        generator = IsospectraLatticeGenerator(dimension=4)
        choir = generator.generate_isospectral_choir(choir_size=2)
        
        # Set up GVA
        gva = GVAEmbedding(precision=50)
        
        # Use a small semiprime
        n = 1073217479
        p = 32749
        q = 32771
        
        # Test metric preservation
        preservation = gva.compute_metric_preservation_ratio(n, p, q, choir)
        
        self.assertIsInstance(preservation, float)
        self.assertGreaterEqual(preservation, 0)
        self.assertLessEqual(preservation, 1)
    
    def test_qmc_with_choir(self):
        """Test QMC probing with multiple tori."""
        generator = IsospectraLatticeGenerator(dimension=4)
        choir = generator.generate_isospectral_choir(choir_size=2)
        
        qmc = QMCProbe(dimension=4, n_samples=50)
        n = 1073217479
        
        # Probe each lattice
        for lattice in choir:
            samples, amplitudes = qmc.probe_torus(n, lattice)
            self.assertEqual(len(samples), 50)
            self.assertEqual(len(amplitudes), 50)


if __name__ == '__main__':
    unittest.main()
