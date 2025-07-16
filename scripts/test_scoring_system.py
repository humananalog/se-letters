#!/usr/bin/env python3
"""
Test Script for Multi-Factor Scoring System
Tests the new scoring logic with Galaxy 6000 example

Version: 2.2.0
Author: Alexandre Huther
Date: 2025-07-16
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.models.product_matching import LetterProductInfo
from se_letters.core.config import get_config


def test_galaxy_6000_scoring():
    """Test the scoring system with Galaxy 6000 example"""
    print("🧪 Testing Multi-Factor Scoring System")
    print("=" * 50)
    
    # Initialize service
    config = get_config()
    db_service = SOTAProductDatabaseService()
    
    # Create test letter product info (Galaxy 6000)
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
    
    print(f"📋 Test Product: {test_letter_product.range_label}")
    print(f"🔍 Product Line: {test_letter_product.product_line}")
    print(f"📝 Description: {test_letter_product.product_description}")
    print()
    
    # Test discovery with scoring
    print("🔍 Discovering product candidates with scoring...")
    discovery_result = db_service.discover_product_candidates(
        test_letter_product, max_candidates=20
    )
    
    print(f"📊 Found {len(discovery_result.candidates)} candidates")
    print(f"⏱️ Processing time: {discovery_result.processing_time_ms:.2f}ms")
    print(f"🎯 Search strategy: {discovery_result.search_strategy}")
    print()
    
    # Display top candidates with scores
    print("🏆 TOP 10 CANDIDATES (Ranked by Score):")
    print("-" * 80)
    
    for i, candidate in enumerate(discovery_result.candidates[:10]):
        print(f"{i+1:2d}. Score: {candidate.match_score:5.2f} | "
              f"ID: {candidate.product_identifier:<20} | "
              f"Range: {candidate.range_label:<15} | "
              f"Subrange: {candidate.subrange_label or 'N/A':<10} | "
              f"PL: {candidate.pl_services}")
    
    print()
    
    # Analyze scoring distribution
    scores = [c.match_score for c in discovery_result.candidates]
    if scores:
        print("📈 SCORING ANALYSIS:")
        print(f"   Highest Score: {max(scores):.2f}")
        print(f"   Average Score: {sum(scores)/len(scores):.2f}")
        print(f"   Lowest Score: {min(scores):.2f}")
        
        # Count by score ranges
        excellent = len([s for s in scores if s >= 8.0])
        good = len([s for s in scores if 5.0 <= s < 8.0])
        moderate = len([s for s in scores if 3.0 <= s < 5.0])
        weak = len([s for s in scores if s < 3.0])
        
        print(f"   Excellent (8.0+): {excellent}")
        print(f"   Good (5.0-7.9): {good}")
        print(f"   Moderate (3.0-4.9): {moderate}")
        print(f"   Weak (<3.0): {weak}")
    
    print()
    
    # Check for Galaxy 6000 specific matches
    print("🎯 GALAXY 6000 SPECIFIC ANALYSIS:")
    galaxy_6000_matches = [
        c for c in discovery_result.candidates 
        if "6000" in (c.range_label or "") or "6000" in (c.subrange_label or "")
    ]
    
    if galaxy_6000_matches:
        print(f"✅ Found {len(galaxy_6000_matches)} products with '6000' in range/subrange:")
        for i, candidate in enumerate(galaxy_6000_matches[:5]):
            print(f"   {i+1}. Score: {candidate.match_score:.2f} | "
                  f"{candidate.range_label} {candidate.subrange_label}")
    else:
        print("❌ No products found with '6000' in range/subrange")
    
    # Check for other Galaxy products (potential false positives)
    other_galaxy = [
        c for c in discovery_result.candidates 
        if "Galaxy" in (c.range_label or "") and "6000" not in (c.range_label or "") and "6000" not in (c.subrange_label or "")
    ]
    
    if other_galaxy:
        print(f"⚠️ Found {len(other_galaxy)} other Galaxy products (potential false positives):")
        for i, candidate in enumerate(other_galaxy[:3]):
            print(f"   {i+1}. Score: {candidate.match_score:.2f} | "
                  f"{candidate.range_label} {candidate.subrange_label}")
    
    print()
    print("✅ Scoring system test completed!")


def test_other_examples():
    """Test with other product examples"""
    print("\n🧪 Testing Other Product Examples")
    print("=" * 50)
    
    db_service = SOTAProductDatabaseService()
    
    # Test cases
    test_cases = [
        {
            "name": "PIX 2B",
            "range_label": "PIX 2B",
            "subrange_label": "2B",
            "product_line": "PPIBS (Power Products)",
            "description": "PIX Double Bus Bar"
        },
        {
            "name": "SEPAM 20",
            "range_label": "SEPAM 20",
            "subrange_label": "20",
            "product_line": "DPIBS (Digital Power)",
            "description": "SEPAM Protection Relay"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        test_product = LetterProductInfo(
            product_identifier=test_case['name'],
            range_label=test_case['range_label'],
            subrange_label=test_case['subrange_label'],
            product_line=test_case['product_line'],
            product_description=test_case['description'],
            technical_specifications={},
            obsolescence_status=None,
            end_of_service_date=None,
            replacement_suggestions=None
        )
        
        discovery_result = db_service.discover_product_candidates(
            test_product, max_candidates=10
        )
        
        print(f"   Found {len(discovery_result.candidates)} candidates")
        if discovery_result.candidates:
            top_score = max(c.match_score for c in discovery_result.candidates)
            print(f"   Top score: {top_score:.2f}")
            
            # Show top 3
            for i, candidate in enumerate(discovery_result.candidates[:3]):
                print(f"   {i+1}. Score: {candidate.match_score:.2f} | "
                      f"{candidate.range_label} {candidate.subrange_label}")


if __name__ == "__main__":
    try:
        test_galaxy_6000_scoring()
        test_other_examples()
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 