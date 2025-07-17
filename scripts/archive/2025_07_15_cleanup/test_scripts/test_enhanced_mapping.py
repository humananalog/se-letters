#!/usr/bin/env python3
"""
Test Enhanced Product Mapping Service
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from se_letters.services.enhanced_product_mapping_service_v3 import EnhancedProductMappingServiceV3
from loguru import logger

def test_enhanced_mapping():
    """Test the enhanced product mapping service"""
    
    # Initialize the service
    mapping_service = EnhancedProductMappingServiceV3()
    
    # Test product mapping for PIX 2B
    logger.info("🔍 Testing enhanced product mapping for PIX 2B")
    
    result = mapping_service.process_product_mapping(
        product_identifier="PIX 2B",
        range_label="PIX",
        subrange_label="2B",
        product_line="PSIBS",  # Power Systems
        max_candidates=10
    )
    
    logger.info(f"✅ Mapping completed")
    logger.info(f"📊 Confidence: {result.confidence_score:.3f}")
    logger.info(f"🎯 Search strategy: {result.search_strategy}")
    logger.info(f"📦 Modernization candidates: {len(result.modernization_candidates)}")
    
    # Show top matches
    for i, candidate in enumerate(result.modernization_candidates[:5]):
        logger.info(f"  {i+1}. {candidate.product_identifier} (confidence: {candidate.confidence_score:.3f})")
        logger.info(f"      Range: {candidate.range_label}")
        logger.info(f"      Description: {candidate.product_description[:100]}...")
    
    return result

if __name__ == "__main__":
    test_enhanced_mapping() 