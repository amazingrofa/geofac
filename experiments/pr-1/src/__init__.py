"""
Isospectral Tori Falsification Experiment

This package implements a falsification experiment testing whether
non-isometric isospectral flat tori preserve curvature-divisor metrics
under GVA embeddings.
"""

__version__ = "1.0.0"
__author__ = "Grok (Computational Investigation Mode)"
__date__ = "2025-11-23"

from .torus_construction import IsospectraLatticeGenerator
from .gva_embedding import GVAEmbedding
from .qmc_probe import QMCProbe
from .falsification_test import FalsificationTest

__all__ = [
    'IsospectraLatticeGenerator',
    'GVAEmbedding',
    'QMCProbe',
    'FalsificationTest',
]
