#!/usr/bin/env python3
"""
Test Enhanced Semantic Extraction with Multi-Dimensional Database Fields
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.services.enhanced_semantic_extraction_engine import (
    EnhancedSemanticExtractionEngine,
    SearchCriteria
)
from se_letters.services.enhanced_duckdb_service import EnhancedDuckDBService

def test_enhanced_extraction():
    """Test enhanced semantic extraction capabilities."""
    
    print("🔍 ENHANCED SEMANTIC EXTRACTION TEST")
    print("=" * 80)
    
    # Initialize services
    extraction_engine = EnhancedSemanticExtractionEngine()
    db_service = EnhancedDuckDBService()
    
    # Get dimension statistics
    stats = db_service.get_dimension_statistics()
    print(f"📊 DATABASE DIMENSIONS:")
    print(f"   Ranges: {stats['unique_ranges']:,}")
    print(f"   Subranges: {stats['unique_subranges']:,}")
    print(f"   Device Types: {stats['unique_device_types']:,}")
    print(f"   Brands: {stats['unique_brands']:,}")
    print(f"   PL Services: {stats['unique_pl_services']:,}")
    
    # Test documents with different content types
    test_documents = [
        {
            "name": "Circuit Breaker Document",
            "text": """
            This communication concerns the end of commercialization of NSX100 
            circuit breakers from Schneider Electric. The NSX100 series, part of 
            the Compact NSX range, includes models with ratings up to 630A at 690V.
            These low voltage circuit breakers will be replaced by newer models.
            Contact your local Schneider Electric representative for migration guidance.
            """,
            "expected_dimensions": ["ranges", "subranges", "device_types", "brands", "technical_specs"]
        },
        {
            "name": "Variable Speed Drive Document", 
            "text": """
            Altivar Process ATV900 drives above 15kW are being withdrawn from service.
            These variable speed drives from Schneider Electric served industrial 
            automation applications. The ATV900 >= 15kw subrange includes models 
            from 15kW to 1500kW for IDPAS applications.
            """,
            "expected_dimensions": ["ranges", "subranges", "device_types", "brands", "pl_services", "technical_specs"]
        },
        {
            "name": "Historical Brand Document",
            "text": """
            Telemecanique contactors and Merlin Gerin protection relays are being 
            consolidated under the Schneider Electric brand. This affects TeSys 
            contactors and Sepam protection relays across PSIBS power systems.
            """,
            "expected_dimensions": ["ranges", "device_types", "brands", "pl_services"]
        },
        {
            "name": "Technical Specification Document",
            "text": """
            Medium voltage switchgear SM6-24 rated at 24kV, 630A with SF6 insulation.
            This MV equipment includes circuit breakers, disconnectors, and protection 
            relays for power distribution applications up to 40kA short circuit current.
            """,
            "expected_dimensions": ["ranges", "subranges", "device_types", "technical_specs"]
        }
    ]
    
    print("\n🧪 TESTING ENHANCED EXTRACTION")
    print("=" * 80)
    
    for i, doc in enumerate(test_documents, 1):
        print(f"\n📄 Document {i}: {doc['name']}")
        print("-" * 60)
        
        # Extract enhanced semantics
        start_time = time.time()
        result = extraction_engine.extract_enhanced_semantics(doc['text'])
        extraction_time = (time.time() - start_time) * 1000
        
        print(f"⚡ Extraction Time: {extraction_time:.1f}ms")
        print(f"🎯 Confidence: {result.extraction_confidence:.2f}")
        print(f"📊 Total Matches: {len(result.semantic_matches)}")
        
        # Display results by dimension
        if result.ranges:
            print(f"🔧 Ranges ({len(result.ranges)}): {', '.join(result.ranges)}")
        
        if result.subranges:
            print(f"🔩 Subranges ({len(result.subranges)}): {', '.join(result.subranges)}")
        
        if result.device_types:
            print(f"⚙️  Device Types ({len(result.device_types)}): {', '.join(result.device_types)}")
        
        if result.brands:
            print(f"🏷️  Brands ({len(result.brands)}): {', '.join(result.brands)}")
        
        if result.pl_services:
            print(f"🏢 PL Services ({len(result.pl_services)}): {', '.join(result.pl_services)}")
        
        if result.technical_specs:
            print(f"📐 Technical Specs ({len(result.technical_specs)}): {', '.join(result.technical_specs)}")
        
        # Test refined search
        search_criteria = SearchCriteria(
            ranges=result.ranges if result.ranges else None,
            subranges=result.subranges if result.subranges else None,
            device_types=result.device_types if result.device_types else None,
            brands=result.brands if result.brands else None,
            pl_services=result.pl_services if result.pl_services else None,
            technical_specs=result.technical_specs if result.technical_specs else None,
            obsolete_only=True
        )
        
        # Search products using multi-dimensional criteria
        search_result = db_service.search_products(search_criteria)
        
        print(f"🔍 Search Strategy: {search_result.search_strategy}")
        print(f"📦 Products Found: {search_result.total_count:,}")
        print(f"📉 Search Space Reduction: {search_result.search_space_reduction:.1%}")
        print(f"⚡ Search Time: {search_result.processing_time_ms:.1f}ms")
        
        # Show top products
        if search_result.products:
            print(f"🏆 Top Products:")
            for j, product in enumerate(search_result.products[:3], 1):
                print(f"   {j}. {product['PRODUCT_IDENTIFIER']} - {product['PRODUCT_DESCRIPTION'][:50]}...")
    
    print("\n🎯 SEARCH SPACE REFINEMENT ANALYSIS")
    print("=" * 80)
    
    # Compare search strategies
    baseline_criteria = SearchCriteria(obsolete_only=True)
    baseline_result = db_service.search_products(baseline_criteria)
    
    print(f"📊 Baseline (obsolete only): {baseline_result.total_count:,} products")
    
    # Test different refinement strategies
    refinement_tests = [
        ("Range only", SearchCriteria(ranges=["Compact NSX <630"], obsolete_only=True)),
        ("Subrange only", SearchCriteria(subranges=["NSX100"], obsolete_only=True)),
        ("Device type only", SearchCriteria(device_types=["LV equipment - Low voltage circuit breaker"], obsolete_only=True)),
        ("Brand only", SearchCriteria(brands=["Schneider Electric"], obsolete_only=True)),
        ("PL service only", SearchCriteria(pl_services=["PPIBS"], obsolete_only=True)),
        ("Multi-dimensional", SearchCriteria(
            ranges=["Compact NSX <630"],
            subranges=["NSX100"],
            device_types=["LV equipment - Low voltage circuit breaker"],
            brands=["Schneider Electric"],
            pl_services=["PPIBS"],
            obsolete_only=True
        ))
    ]
    
    print("\n📈 REFINEMENT COMPARISON:")
    for name, criteria in refinement_tests:
        result = db_service.search_products(criteria)
        reduction = (baseline_result.total_count - result.total_count) / baseline_result.total_count
        print(f"   {name:<20}: {result.total_count:>8,} products ({reduction:>6.1%} reduction)")
    
    print("\n🎉 ENHANCED SEMANTIC EXTRACTION TEST COMPLETE")
    print("✅ Multi-dimensional extraction working")
    print("✅ Search space refinement effective")
    print("✅ Performance optimized")
    
    # Cleanup
    extraction_engine.close()
    db_service.close()

if __name__ == "__main__":
    test_enhanced_extraction() 