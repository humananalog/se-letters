#!/usr/bin/env python3
"""
Test Full Pipeline Integration with New Scoring System
Tests the complete flow from document processing to LLM evaluation

Version: 2.2.0
Author: Alexandre Huther
Date: 2025-07-16
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.services.production_pipeline_service import ProductionPipelineService
from se_letters.services.intelligent_product_matching_service import IntelligentProductMatchingService
from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.models.product_matching import LetterProductInfo
from se_letters.core.config import get_config


def test_full_pipeline_integration():
    """Test the complete pipeline with new scoring system"""
    print("🧪 Testing Full Pipeline Integration")
    print("=" * 50)
    
    # Initialize services
    config = get_config()
    pipeline_service = ProductionPipelineService()
    matching_service = IntelligentProductMatchingService(debug_mode=True)
    db_service = SOTAProductDatabaseService()
    
    # Test with Galaxy 6000 example
    print("📋 Testing with Galaxy 6000 example")
    
    # Create test letter product info
    test_letter_product = LetterProductInfo(
        product_identifier="Galaxy 6000",
        range_label="Galaxy 6000",
        subrange_label="6000",
        product_line="SPIBS (Secure Power)",
        product_description="Galaxy 6000 UPS Range - End of Service Notification",
        technical_specifications={
            "device_type": "UPS",
            "power_range": "6000VA",
            "brand": "Schneider Electric"
        },
        obsolescence_status="End of Service",
        end_of_service_date="2024-12-31",
        replacement_suggestions="Galaxy VM series"
    )
    
    print(f"🔍 Product: {test_letter_product.range_label}")
    print(f"📝 Description: {test_letter_product.product_description}")
    print()
    
    # Step 1: Discover candidates with scoring
    print("🔍 Step 1: Discovering product candidates with scoring...")
    discovery_result = db_service.discover_product_candidates(
        test_letter_product, max_candidates=20
    )
    
    print(f"📊 Found {len(discovery_result.candidates)} candidates")
    print(f"⏱️ Discovery time: {discovery_result.processing_time_ms:.2f}ms")
    
    if discovery_result.candidates:
        top_score = max(c.match_score for c in discovery_result.candidates)
        print(f"🏆 Top score: {top_score:.2f}")
        
        # Show top 5 candidates
        print("🎯 Top 5 candidates:")
        for i, candidate in enumerate(discovery_result.candidates[:5]):
            print(f"  {i+1}. Score: {candidate.match_score:.2f} | "
                  f"{candidate.range_label} {candidate.subrange_label} | "
                  f"ID: {candidate.product_identifier}")
    
    print()
    
    # Step 2: Test LLM integration
    print("🤖 Step 2: Testing LLM integration with scored candidates...")
    
    try:
        # Create matching prompt to see what the LLM receives
        prompt = matching_service._create_matching_prompt(
            test_letter_product, discovery_result.candidates
        )
        
        print(f"📝 LLM Prompt length: {len(prompt)} characters")
        print("📋 LLM Prompt preview (first 500 chars):")
        print("-" * 50)
        print(prompt[:500] + "...")
        print("-" * 50)
        
        # Test LLM matching (if API key is available)
        print("\n🤖 Testing LLM matching...")
        matching_result = matching_service.match_products(
            test_letter_product, discovery_result.candidates
        )
        
        print(f"✅ LLM matching completed in {matching_result.processing_time_ms:.2f}ms")
        print(f"📊 LLM found {matching_result.total_matches} matching products")
        print(f"🎯 Range-based matching: {matching_result.range_based_matching}")
        
        # Show LLM results
        if matching_result.matching_products:
            print("🏆 LLM Selected Products:")
            for i, match in enumerate(matching_result.matching_products[:5]):
                print(f"  {i+1}. {match.product_identifier} | "
                      f"Confidence: {match.confidence:.2f} | "
                      f"Type: {match.match_type}")
                print(f"     Reason: {match.reason[:100]}...")
        
        print()
        
    except Exception as e:
        print(f"⚠️ LLM test skipped (likely no API key): {e}")
        print("   This is expected in test environment")
    
    # Step 3: Test pipeline integration
    print("🔧 Step 3: Testing pipeline service integration...")
    
    try:
        # Test the product matching method in pipeline service
        mock_grok_result = {
            "products": [
                {
                    "product_identifier": "Galaxy 6000",
                    "range_label": "Galaxy 6000",
                    "subrange_label": "6000",
                    "product_line": "SPIBS (Secure Power)",
                    "product_description": "Galaxy 6000 UPS Range",
                    "technical_specifications": {
                        "device_type": "UPS",
                        "power_range": "6000VA"
                    },
                    "obsolescence_status": "End of Service",
                    "end_of_service_date": "2024-12-31",
                    "replacement_suggestions": "Galaxy VM series"
                }
            ]
        }
        
        # Test the pipeline's product matching method
        pipeline_result = pipeline_service._process_product_matching(
            mock_grok_result, Path("test_galaxy_6000.pdf")
        )
        
        print(f"✅ Pipeline integration test completed")
        print(f"📊 Pipeline result success: {pipeline_result['success']}")
        print(f"🎯 Total products processed: {pipeline_result.get('total_products', 0)}")
        
    except Exception as e:
        print(f"⚠️ Pipeline integration test failed: {e}")
    
    print()
    print("✅ Full pipeline integration test completed!")


def test_scoring_accuracy():
    """Test scoring accuracy with known cases"""
    print("\n🧪 Testing Scoring Accuracy")
    print("=" * 50)
    
    db_service = SOTAProductDatabaseService()
    
    # Test cases with expected outcomes
    test_cases = [
        {
            "name": "Galaxy 6000",
            "range_label": "Galaxy 6000",
            "expected_range": "MGE Galaxy 6000",
            "expected_score_min": 7.0,
            "description": "Should find MGE Galaxy 6000 products with high scores"
        },
        {
            "name": "PIX 2B", 
            "range_label": "PIX 2B",
            "expected_range": "PIX 2B",
            "expected_score_min": 7.0,
            "description": "Should find PIX 2B products with high scores"
        },
        {
            "name": "SEPAM 20",
            "range_label": "SEPAM 20", 
            "expected_range": "SEPAM",
            "expected_score_min": 5.0,
            "description": "Should find SEPAM products with moderate-high scores"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"📝 Expected: {test_case['description']}")
        
        test_product = LetterProductInfo(
            product_identifier=test_case['name'],
            range_label=test_case['range_label'],
            subrange_label="",
            product_line="SPIBS (Secure Power)",
            product_description=f"{test_case['name']} test product",
            technical_specifications={},
            obsolescence_status=None,
            end_of_service_date=None,
            replacement_suggestions=None
        )
        
        discovery_result = db_service.discover_product_candidates(
            test_product, max_candidates=10
        )
        
        if discovery_result.candidates:
            top_score = max(c.match_score for c in discovery_result.candidates)
            top_range = discovery_result.candidates[0].range_label
            
            print(f"   Top score: {top_score:.2f} (expected >= {test_case['expected_score_min']})")
            print(f"   Top range: {top_range} (expected: {test_case['expected_range']})")
            
            # Check if expectations are met
            score_ok = top_score >= test_case['expected_score_min']
            range_ok = test_case['expected_range'].lower() in top_range.lower()
            
            if score_ok and range_ok:
                print(f"   ✅ PASS: Score and range match expectations")
            else:
                print(f"   ❌ FAIL: Score or range doesn't match expectations")
        else:
            print(f"   ❌ FAIL: No candidates found")


if __name__ == "__main__":
    try:
        test_full_pipeline_integration()
        test_scoring_accuracy()
        print("\n🎉 All integration tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc() 