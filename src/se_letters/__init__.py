"""
SE Letters - Schneider Electric Obsolescence Letter Processing Pipeline

A comprehensive automated pipeline for processing Schneider Electric obsolescence letters
and matching them to the IBcatalogue product database using advanced AI/ML techniques.

Author: Alexandre Huther
Version: 2.2.0
"""

__version__ = "2.2.0"
__author__ = "Alexandre Huther"
__description__ = "Schneider Electric Obsolescence Letter Processing Pipeline"

from .core.config import get_config
from .services.production_pipeline_service import ProductionPipelineService

__all__ = [
    "get_config",
    "ProductionPipelineService",
    "__version__",
    "__author__",
    "__description__",
] 