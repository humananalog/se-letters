"""SE Letters - Schneider Electric Obsolescence Letter Matching Pipeline.

This package provides tools for processing obsolescence letters and matching
them to product records using AI/ML techniques.
"""

__version__ = "1.0.0"
__author__ = "SE Letters Team"
__email__ = "team@se-letters.com"

from .core.pipeline import Pipeline
from .core.config import get_config
from .models.document import Document, DocumentResult
from .models.letter import Letter, LetterMetadata

__all__ = [
    "Pipeline",
    "get_config",
    "Document",
    "DocumentResult",
    "Letter",
    "LetterMetadata",
] 