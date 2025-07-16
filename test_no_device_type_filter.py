#!/usr/bin/env python3
"""
Test No Device Type Filter
Test Galaxy 6000 search without device type filtering
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.models.product_matching import LetterProductInfo

def test_galaxy_6000_no_device_filter():
    """Test Galaxy 6000 search without device type filtering"""
    print("🔍 Testing Galaxy 6000 Search WITHOUT Device Type Filter")
    print("=" * 60)
    
    # Initialize service
    service = SOTAProductDatabaseService()
    
    # Test with current parameters (MGE Galaxy 6000, empty subrange)
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
    
    # Test WITHOUT device type filtering (empty description)
    print("📋 Testing WITHOUT device type filtering (empty description):")
    try:
        result_no_device = service.discover_product_candidates(
            LetterProductInfo(
                product_identifier='MGE Galaxy 6000',
                range_label='MGE Galaxy 6000',
                subrange_label='',
                product_line='SPIBS',
                product_description='',  # Empty description = no device type filter
                technical_specifications={}
            ),
            max_candidates=1000  # Increase limit
        )
        
        print(f"📊 Service found (no device filter): {len(result_no_device.candidates)} products")
        
        # Show first 10 results
        print(f"🎯 First 10 results:")
        for i, candidate in enumerate(result_no_device.candidates[:10]):
            print(f"  {i+1}. {candidate.range_label} {candidate.subrange_label}")
            print(f"     Product ID: {candidate.product_identifier}")
            print(f"     PL Services: {candidate.pl_services}")
            print(f"     Device Type: {candidate.devicetype_label}")
            print(f"     Score: {candidate.match_score:.2f}")
            print()
            
        # Count by device type
        device_counts = {}
        for candidate in result_no_device.candidates:
            device_type = candidate.devicetype_label
            device_counts[device_type] = device_counts.get(device_type, 0) + 1
        
        print(f"📊 Results by device type:")
        for device_type, count in sorted(device_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {device_type}: {count} products")
            
    except Exception as e:
        print(f"❌ Service error: {e}")

def test_direct_database_query_no_device_filter():
    """Test direct database query without device type filter"""
    print(f"\n🔍 Testing Direct Database Query WITHOUT Device Type Filter")
    print("=" * 60)
    
    import duckdb
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Check Galaxy 6000 with obsolescence filter but NO device type filter
            print("📊 Galaxy 6000 - Obsolete products only (no device type filter):")
            galaxy_obsolete_no_device = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL,
                    COUNT(*) as count
                FROM products 
                WHERE RANGE_LABEL = 'MGE Galaxy 6000'
                  AND (COMMERCIAL_STATUS = '19-end of commercialization block' 
                       OR COMMERCIAL_STATUS = '18-End of commercialisation' 
                       OR COMMERCIAL_STATUS = '14-End of commerc. announced' 
                       OR COMMERCIAL_STATUS = '16-Post commercialisation')
                  AND PL_SERVICES = 'SPIBS'
                GROUP BY RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER, COMMERCIAL_STATUS, PL_SERVICES, DEVICETYPE_LABEL
                ORDER BY DEVICETYPE_LABEL, PRODUCT_IDENTIFIER
            """).fetchall()
            
            print(f"📊 Found {len(galaxy_obsolete_no_device)} unique Galaxy 6000 obsolete products (no device filter):")
            
            # Count by device type
            device_counts = {}
            for row in galaxy_obsolete_no_device:
                range_label, subrange, product_id, status, pl, device_type, count = row
                device_counts[device_type] = device_counts.get(device_type, 0) + 1
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl} - {device_type}")
            
            print(f"\n📊 Results by device type:")
            for device_type, count in sorted(device_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {device_type}: {count} products")
                
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_galaxy_6000_no_device_filter()
    test_direct_database_query_no_device_filter()
    print("\n✅ Testing complete!") 