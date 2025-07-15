#!/usr/bin/env python3
"""
Multiple Matches Demo - Intelligent Product Matching
Demonstrates the new intelligent product matching service that finds ALL
matching products instead of just the single best match.

Version: 2.0.0
Author: SE Letters Team
"""

import sys
from pathlib import Path
from typing import List

# Add paths
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(current_dir.parent / "services"))

from intelligent_product_matching_service import (
    IntelligentProductMatchingService,
    LetterProductInfo,
    ProductCandidate
)
from loguru import logger


def create_mock_letter_product() -> LetterProductInfo:
    """Create mock letter product info for testing"""
    return LetterProductInfo(
        product_identifier="PIX 2B",
        range_label="PIX Double Bus Bar",
        subrange_label="PIX 2B",
        product_line="PSIBS (Power Systems)",
        product_description=(
            "Medium Voltage equipment with double bus bar configuration, "
            "launched in 2014."
        ),
        technical_specifications={
            "voltage_levels": ["12 – 17.5kV"],
            "current_ratings": ["up to 3150A"],
            "frequencies": ["50/60Hz"]
        },
        obsolescence_status="Withdrawn",
        end_of_service_date="November 2023 (Belgium frame contract only)",
        replacement_suggestions="No substitution available for this range."
    )


def create_mock_candidates() -> List[ProductCandidate]:
    """Create mock discovered candidates for testing"""
    return [
        ProductCandidate(
            product_identifier="PIX2B-HV-3150-50HZ",
            product_type="Switchgear",
            product_description=(
                "High Voltage Double Bus Bar Switchgear 50Hz"
            ),
            brand_code="SE",
            brand_label="Schneider Electric",
            range_code="PIX2B",
            range_label="PIX Double Bus Bar",
            subrange_code="PIX2B",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="PIX2B-MV-2500-50HZ",
            product_type="Switchgear",
            product_description="Medium Voltage Double Bus Bar Switchgear 50Hz",
            brand_code="SE",
            brand_label="Schneider Electric",
            range_code="PIX2B",
            range_label="PIX Double Bus Bar",
            subrange_code="PIX2B",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="PIX2B-LV-1600-50HZ",
            product_type="Switchgear",
            product_description="Low Voltage Double Bus Bar Switchgear 50Hz",
            brand_code="SE",
            brand_label="Schneider Electric",
            range_code="PIX2B",
            range_label="PIX Double Bus Bar",
            subrange_code="PIX2B",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="PIX2B-HV-3150-60HZ",
            product_type="Switchgear",
            product_description="High Voltage Double Bus Bar Switchgear 60Hz",
            brand_code="SE",
            brand_label="Schneider Electric",
            range_code="PIX2B",
            range_label="PIX Double Bus Bar",
            subrange_code="PIX2B",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="PIX2B-MV-2500-60HZ",
            product_type="Switchgear",
            product_description="Medium Voltage Double Bus Bar Switchgear 60Hz",
            brand_code="SE",
            brand_label="Schneider Electric",
            range_code="PIX2B",
            range_label="PIX Double Bus Bar",
            subrange_code="PIX2B",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="PIX1A-HV-2500",
            product_type="Switchgear",
            product_description="Single Bus Bar Switchgear",
            brand_code="SE",
            brand_label="Schneider Electric",
            range_code="PIX1A",
            range_label="PIX Single Bus Bar",
            subrange_code="PIX1A",
            subrange_label="PIX 1A",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="GALAXY-UPS-500",
            product_type="UPS",
            product_description="Galaxy UPS System",
            brand_code="SE",
            brand_label="Schneider Electric",
            range_code="GALAXY",
            range_label="Galaxy UPS",
            subrange_code="GALAXY",
            subrange_label="Galaxy",
            devicetype_label="UPS System",
            pl_services="SPIBS"
        )
    ]


def print_results(result):
    """Print results in a nice format"""
    print(f"\n{'='*60}")
    print("INTELLIGENT PRODUCT MATCHING RESULTS (MULTIPLE MATCHES)")
    print(f"{'='*60}")
    
    print(f"Letter Product: {result.letter_product_info.product_identifier}")
    print(f"Range: {result.letter_product_info.range_label}")
    print(f"Product Line: {result.letter_product_info.product_line}")
    print(f"Technical Specs: {result.letter_product_info.technical_specifications}")
    
    print(f"\n{'='*60}")
    print("MATCHING RESULTS")
    print(f"{'='*60}")
    
    print(f"Total Matches Found: {result.total_matches}")
    print(f"Range-based Matching: {result.range_based_matching}")
    print(f"Excluded Low Confidence: {result.excluded_low_confidence}")
    print(f"Processing Time: {result.processing_time_ms:.2f}ms")
    
    if result.matching_products:
        print(f"\n{'='*60}")
        print("INDIVIDUAL MATCHES")
        print(f"{'='*60}")
        
        for i, match in enumerate(result.matching_products, 1):
            print(f"\nMatch {i}:")
            print(f"  Product: {match.product_identifier}")
            print(f"  Confidence: {match.confidence:.2f}")
            print(f"  Match Type: {match.match_type}")
            print(f"  Technical Score: {match.technical_match_score:.2f}")
            print(f"  Nomenclature Score: {match.nomenclature_match_score:.2f}")
            print(f"  Product Line Score: {match.product_line_match_score:.2f}")
            print(f"  Reason: {match.reason}")
    else:
        print("\n⚠️  No matches found!")
    
    print(f"\n{'='*60}")


def run_demo():
    """Run the multiple matches demo"""
    try:
        logger.info("🚀 Starting Multiple Matches Demo")
        
        # Initialize service with debug mode
        service = IntelligentProductMatchingService(debug_mode=True)
        
        # Create test data
        letter_product = create_mock_letter_product()
        candidates = create_mock_candidates()
        
        logger.info(f"📋 Testing with {len(candidates)} candidates")
        
        # Process matching
        result = service.match_products(letter_product, candidates)
        
        # Print results
        print_results(result)
        
        # Save results
        output_dir = Path("scripts/sandbox/intelligent_product_matching/results")
        output_path = service.save_results(result, output_dir)
        
        if output_path:
            print(f"\n💾 Results saved to: {output_path}")
        
        logger.info("✅ Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    run_demo() 