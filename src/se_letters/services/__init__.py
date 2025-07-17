"""External service integrations for the SE Letters project.

ACTIVE PRODUCTION SERVICES (v2.3):
- postgresql_production_pipeline_service_v2_3: Main production pipeline
- document_processor: Core document processing service
- xai_service: Official xAI SDK integration for Grok-3
- enhanced_product_mapping_service_v3: Advanced product matching
- postgresql_letter_database_service: PostgreSQL database operations

ARCHIVED SERVICES:
- See src/se_letters/services/archive/ARCHIVAL_SUMMARY.md for details
"""

from .document_processor import DocumentProcessor
from .xai_service import XAIService
from .enhanced_product_mapping_service_v3 import (
    EnhancedProductMappingServiceV3
)
from .postgresql_letter_database_service import (
    PostgreSQLLetterDatabaseService
)
from .postgresql_production_pipeline_service_v2_3 import (
    PostgreSQLProductionPipelineServiceV2_3
)

__all__ = [
    "DocumentProcessor",
    "XAIService", 
    "EnhancedProductMappingServiceV3",
    "PostgreSQLLetterDatabaseService",
    "PostgreSQLProductionPipelineServiceV2_3",
] 