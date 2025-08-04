"""
Lease Population Module
Handles all lease population functionality including document processing,
placeholder replacement, image embedding, and signature block generation.
"""

from .core import LeasePopulationProcessor
from .routes import register_lease_population_routes
from .utils import normalize_placeholder_key, strip_brackets
from .image_handler import ImageEmbeddingHandler

__all__ = [
    'LeasePopulationProcessor',
    'register_lease_population_routes',
    'normalize_placeholder_key',
    'strip_brackets',
    'ImageEmbeddingHandler'
] 