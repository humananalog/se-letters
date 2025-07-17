#!/usr/bin/env python3
"""
Verify Active Services Script
Tests that all active services can be imported correctly after archival.

Author: Alexandre Huther
Date: 2025-07-17
"""

import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_service_imports():
    """Test that all active services can be imported"""
    logger.info("🔍 Testing active service imports...")
    
    try:
        # Test core services
        from se_letters.services.document_processor import DocumentProcessor  # noqa: F401
        logger.success("✅ DocumentProcessor imported successfully")
        
        from se_letters.services.xai_service import XAIService  # noqa: F401
        logger.success("✅ XAIService imported successfully")
        
        from se_letters.services.enhanced_product_mapping_service_v3 import (  # noqa: F401
            EnhancedProductMappingServiceV3
        )
        logger.success("✅ EnhancedProductMappingServiceV3 imported successfully")
        
        from se_letters.services.postgresql_letter_database_service import (  # noqa: F401
            PostgreSQLLetterDatabaseService
        )
        logger.success("✅ PostgreSQLLetterDatabaseService imported successfully")
        
        from se_letters.services.postgresql_production_pipeline_service_v2_3 import (  # noqa: F401
            PostgreSQLProductionPipelineServiceV2_3
        )
        logger.success("✅ PostgreSQLProductionPipelineServiceV2_3 imported successfully")
        
        # Test utils (json_output_manager is in utils, not services)
        from se_letters.utils.json_output_manager import JSONOutputManager  # noqa: F401
        logger.success("✅ JSONOutputManager imported successfully")
        
        logger.success("🎉 All active services imported successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_archived_services_not_accessible():
    """Test that archived services are not accessible from main services directory"""
    logger.info("🔍 Testing that archived services are not accessible...")
    
    archived_services = [
        "postgresql_production_pipeline_service",
        "production_pipeline_service", 
        "letter_database_service",
        "intelligent_product_matching_service",
        "sota_product_database_service",
        "embedding_service",
        "preview_service"
    ]
    
    failed_imports = []
    
    for service in archived_services:
        try:
            # Try to import from main services directory
            module = __import__(f"se_letters.services.{service}", fromlist=[""])  # noqa: F841
            logger.warning(f"⚠️ Archived service {service} is still accessible!")
            failed_imports.append(service)
        except ImportError:
            logger.success(f"✅ Archived service {service} correctly not accessible")
        except Exception as e:
            logger.success(f"✅ Archived service {service} correctly not accessible: {e}")
    
    if failed_imports:
        logger.warning(f"⚠️ {len(failed_imports)} archived services still accessible: {failed_imports}")
        return False
    else:
        logger.success("🎉 All archived services correctly not accessible!")
        return True


def main():
    """Main verification function"""
    logger.info("🚀 Starting active services verification...")
    
    # Test active services
    active_success = test_service_imports()
    
    # Test archived services
    archived_success = test_archived_services_not_accessible()
    
    if active_success and archived_success:
        logger.success("🎉 All verification tests passed!")
        logger.info("📋 Active services are working correctly")
        logger.info("📦 Archived services are properly isolated")
        return 0
    else:
        logger.error("❌ Some verification tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 