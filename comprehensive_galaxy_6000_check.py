#!/usr/bin/env python3
"""
Comprehensive Galaxy 6000 Check
Check ALL Galaxy 6000 products in database and compare with search results
"""

import duckdb
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.models.product_matching import LetterProductInfo

def check_all_galaxy_6000_products():
    """Check ALL Galaxy 6000 products in database"""
    print("🔍 COMPREHENSIVE Galaxy 6000 Database Check")
    print("=" * 60)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Check ALL Galaxy 6000 products (no filters)
            print("📊 ALL Galaxy 6000 products (no filters):")
            all_galaxy_6000 = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL,
                    COUNT(*) as count
                FROM products 
                WHERE (RANGE_LABEL ILIKE '%Galaxy%' AND SUBRANGE_LABEL ILIKE '%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%' AND SUBRANGE_LABEL ILIKE '%Galaxy%')
                   OR (RANGE_LABEL ILIKE '%Galaxy%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%Galaxy%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%Galaxy%6000%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%6000%Galaxy%')
                GROUP BY RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER, COMMERCIAL_STATUS, PL_SERVICES, DEVICETYPE_LABEL
                ORDER BY RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER
            """).fetchall()
            
            print(f"📊 Found {len(all_galaxy_6000)} unique Galaxy 6000 products:")
            for row in all_galaxy_6000:
                range_label, subrange, product_id, status, pl, device_type, count = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl} - {device_type}")
            
            # Check by commercial status
            print(f"\n📊 Galaxy 6000 products by commercial status:")
            status_counts = conn.execute("""
                SELECT 
                    COMMERCIAL_STATUS,
                    COUNT(*) as count
                FROM products 
                WHERE (RANGE_LABEL ILIKE '%Galaxy%' AND SUBRANGE_LABEL ILIKE '%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%' AND SUBRANGE_LABEL ILIKE '%Galaxy%')
                   OR (RANGE_LABEL ILIKE '%Galaxy%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%Galaxy%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%Galaxy%6000%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%6000%Galaxy%')
                GROUP BY COMMERCIAL_STATUS
                ORDER BY count DESC
            """).fetchall()
            
            for status, count in status_counts:
                print(f"  • {status}: {count} products")
            
            # Check by product line
            print(f"\n📊 Galaxy 6000 products by product line:")
            pl_counts = conn.execute("""
                SELECT 
                    PL_SERVICES,
                    COUNT(*) as count
                FROM products 
                WHERE (RANGE_LABEL ILIKE '%Galaxy%' AND SUBRANGE_LABEL ILIKE '%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%' AND SUBRANGE_LABEL ILIKE '%Galaxy%')
                   OR (RANGE_LABEL ILIKE '%Galaxy%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%Galaxy%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%Galaxy%6000%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%6000%Galaxy%')
                GROUP BY PL_SERVICES
                ORDER BY count DESC
            """).fetchall()
            
            for pl, count in pl_counts:
                print(f"  • {pl}: {count} products")
            
            # Check by device type
            print(f"\n📊 Galaxy 6000 products by device type:")
            device_counts = conn.execute("""
                SELECT 
                    DEVICETYPE_LABEL,
                    COUNT(*) as count
                FROM products 
                WHERE (RANGE_LABEL ILIKE '%Galaxy%' AND SUBRANGE_LABEL ILIKE '%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%' AND SUBRANGE_LABEL ILIKE '%Galaxy%')
                   OR (RANGE_LABEL ILIKE '%Galaxy%6000%')
                   OR (RANGE_LABEL ILIKE '%6000%Galaxy%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%Galaxy%6000%')
                   OR (PRODUCT_IDENTIFIER ILIKE '%6000%Galaxy%')
                GROUP BY DEVICETYPE_LABEL
                ORDER BY count DESC
            """).fetchall()
            
            for device, count in device_counts:
                print(f"  • {device}: {count} products")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_service_search():
    """Test the service search and compare results"""
    print(f"\n🔍 Testing Service Search")
    print("=" * 60)
    
    # Initialize service
    service = SOTAProductDatabaseService()
    
    # Test with current parameters
    print("📋 Testing with current parameters (MGE Galaxy 6000, empty subrange):")
    try:
        result = service.discover_product_candidates(
            LetterProductInfo(
                product_identifier='MGE Galaxy 6000',
                range_label='MGE Galaxy 6000',
                subrange_label='',
                product_line='SPIBS',
                product_description='Uninterruptible Power Supply (UPS) system',
                technical_specifications={}
            ),
            max_candidates=1000  # Increase limit
        )
        
        print(f"📊 Service found: {len(result.candidates)} products")
        
        # Show first 10 results
        print(f"🎯 First 10 results:")
        for i, candidate in enumerate(result.candidates[:10]):
            print(f"  {i+1}. {candidate.range_label} {candidate.subrange_label}")
            print(f"     Product ID: {candidate.product_identifier}")
            print(f"     PL Services: {candidate.pl_services}")
            print(f"     Device Type: {candidate.devicetype_label}")
            print(f"     Score: {candidate.match_score:.2f}")
            print()
            
    except Exception as e:
        print(f"❌ Service error: {e}")
    
    # Test with broader search (just 'Galaxy')
    print("📋 Testing with broader search (just 'Galaxy'):")
    try:
        result_broad = service.discover_product_candidates(
            LetterProductInfo(
                product_identifier='Galaxy 6000',
                range_label='Galaxy',
                subrange_label='6000',
                product_line='SPIBS',
                product_description='Uninterruptible Power Supply (UPS) system',
                technical_specifications={}
            ),
            max_candidates=1000  # Increase limit
        )
        
        print(f"📊 Broad search found: {len(result_broad.candidates)} products")
        
        # Show first 10 results
        print(f"🎯 First 10 results:")
        for i, candidate in enumerate(result_broad.candidates[:10]):
            print(f"  {i+1}. {candidate.range_label} {candidate.subrange_label}")
            print(f"     Product ID: {candidate.product_identifier}")
            print(f"     PL Services: {candidate.pl_services}")
            print(f"     Device Type: {candidate.devicetype_label}")
            print(f"     Score: {candidate.match_score:.2f}")
            print()
            
    except Exception as e:
        print(f"❌ Broad search error: {e}")

if __name__ == "__main__":
    check_all_galaxy_6000_products()
    test_service_search()
    print("\n✅ Comprehensive check complete!") 