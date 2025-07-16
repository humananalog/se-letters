#!/usr/bin/env python3
"""
Test Improved Search Space Filtering
Test the fixed search space filtering for Galaxy 6000 and MiCOM P20
"""

import duckdb
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.models.product_matching import LetterProductInfo

def test_galaxy_6000_search():
    """Test Galaxy 6000 search space filtering"""
    print("🔍 Testing Galaxy 6000 Search Space Filtering")
    print("=" * 60)
    
    # Initialize service
    service = SOTAProductDatabaseService()
    
    # Create test filters
    filters = {
        'range_label': 'Galaxy',
        'subrange_label': '6000',
        'product_line': 'SPIBS',
        'product_identifier': 'Galaxy 6000',
        'product_description': 'Uninterruptible Power Supply (UPS) system'
    }
    
    print(f"📋 Search Filters: {filters}")
    
    # Test the query building
    query = service._build_discovery_query(filters, 50)
    print(f"\n🔍 Generated Query:")
    print(query)
    
    # Test execution
    try:
        result = service.discover_product_candidates(
            LetterProductInfo(
                product_identifier='MGE Galaxy 6000',  # Use full range name
                range_label='MGE Galaxy 6000',         # Use full range name
                subrange_label='',                     # Empty since it's part of range
                product_line='SPIBS',
                product_description='Uninterruptible Power Supply (UPS) system',
                technical_specifications={}  # Add missing parameter
            ),
            max_candidates=50
        )
        
        print(f"\n✅ Results:")
        print(f"📊 Total candidates found: {len(result.candidates)}")
        
        if result.candidates:
            print(f"🎯 Top 5 candidates:")
            for i, candidate in enumerate(result.candidates[:5]):
                print(f"  {i+1}. {candidate.range_label} {candidate.subrange_label}")
                print(f"     Product ID: {candidate.product_identifier}")
                print(f"     PL Services: {candidate.pl_services}")
                print(f"     Commercial Status: {getattr(candidate, 'commercial_status', 'N/A')}")
                print(f"     Score: {candidate.match_score:.2f}")
                print()
        else:
            print("❌ No candidates found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_micom_p20_search():
    """Test MiCOM P20 search space filtering"""
    print("\n🔍 Testing MiCOM P20 Search Space Filtering")
    print("=" * 60)
    
    # Initialize service
    service = SOTAProductDatabaseService()
    
    # Create test filters
    filters = {
        'range_label': 'MiCOM',
        'subrange_label': 'P20',
        'product_line': 'DPIBS',
        'product_identifier': 'MiCOM P20',
        'product_description': 'Protection relay system'
    }
    
    print(f"📋 Search Filters: {filters}")
    
    # Test the query building
    query = service._build_discovery_query(filters, 50)
    print(f"\n🔍 Generated Query:")
    print(query)
    
    # Test execution
    try:
        result = service.discover_product_candidates(
            LetterProductInfo(
                product_identifier='MiCOM P120',
                range_label='MiCOM Px20 Series',  # Use correct range from database
                subrange_label='P120',             # Use valid subrange from database
                product_line='DPIBS',
                product_description='Protection relay system',
                technical_specifications={}  # Add missing parameter
            ),
            max_candidates=50
        )
        
        print(f"\n✅ Results:")
        print(f"📊 Total candidates found: {len(result.candidates)}")
        
        if result.candidates:
            print(f"🎯 Top 5 candidates:")
            for i, candidate in enumerate(result.candidates[:5]):
                print(f"  {i+1}. {candidate.range_label} {candidate.subrange_label}")
                print(f"     Product ID: {candidate.product_identifier}")
                print(f"     PL Services: {candidate.pl_services}")
                print(f"     Commercial Status: {getattr(candidate, 'commercial_status', 'N/A')}")
                print(f"     Score: {candidate.match_score:.2f}")
                print()
        else:
            print("❌ No candidates found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_direct_database_query():
    """Test direct database queries to verify obsolescence filtering"""
    print("\n🔍 Testing Direct Database Queries")
    print("=" * 60)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Test Galaxy 6000 obsolescence filtering
            print("📊 Galaxy 6000 - All products:")
            galaxy_all = conn.execute("""
                SELECT RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER, COMMERCIAL_STATUS, PL_SERVICES
                FROM products 
                WHERE RANGE_LABEL ILIKE '%Galaxy%' AND SUBRANGE_LABEL ILIKE '%6000%'
                LIMIT 10
            """).fetchall()
            
            for row in galaxy_all:
                print(f"  {row[0]} {row[1]} - {row[2]} - {row[3]} - {row[4]}")
            
            print(f"\n📊 Galaxy 6000 - Obsolete products only:")
            galaxy_obsolete = conn.execute("""
                SELECT RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER, COMMERCIAL_STATUS, PL_SERVICES
                FROM products 
                WHERE RANGE_LABEL ILIKE '%Galaxy%' AND SUBRANGE_LABEL ILIKE '%6000%'
                AND (COMMERCIAL_STATUS ILIKE '%end of commercialisation%' 
                     OR COMMERCIAL_STATUS ILIKE '%end of commercialization%'
                     OR COMMERCIAL_STATUS ILIKE '%end of commerc. announced%'
                     OR COMMERCIAL_STATUS ILIKE '%obsolescence%'
                     OR COMMERCIAL_STATUS ILIKE '%discontinued%')
                LIMIT 10
            """).fetchall()
            
            for row in galaxy_obsolete:
                print(f"  {row[0]} {row[1]} - {row[2]} - {row[3]} - {row[4]}")
            
            # Test MiCOM P20 obsolescence filtering
            print(f"\n📊 MiCOM P20 - All products:")
            micom_all = conn.execute("""
                SELECT RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER, COMMERCIAL_STATUS, PL_SERVICES
                FROM products 
                WHERE RANGE_LABEL ILIKE '%MiCOM%' AND SUBRANGE_LABEL ILIKE '%P20%'
                LIMIT 10
            """).fetchall()
            
            for row in micom_all:
                print(f"  {row[0]} {row[1]} - {row[2]} - {row[3]} - {row[4]}")
            
            print(f"\n📊 MiCOM P20 - Obsolete products only:")
            micom_obsolete = conn.execute("""
                SELECT RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER, COMMERCIAL_STATUS, PL_SERVICES
                FROM products 
                WHERE RANGE_LABEL ILIKE '%MiCOM%' AND SUBRANGE_LABEL ILIKE '%P20%'
                AND (COMMERCIAL_STATUS ILIKE '%end of commercialisation%' 
                     OR COMMERCIAL_STATUS ILIKE '%end of commercialization%'
                     OR COMMERCIAL_STATUS ILIKE '%end of commerc. announced%'
                     OR COMMERCIAL_STATUS ILIKE '%obsolescence%'
                     OR COMMERCIAL_STATUS ILIKE '%discontinued%')
                LIMIT 10
            """).fetchall()
            
            for row in micom_obsolete:
                print(f"  {row[0]} {row[1]} - {row[2]} - {row[3]} - {row[4]}")
                
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Improved Search Space Filtering")
    print("=" * 60)
    
    # Test direct database queries first
    test_direct_database_query()
    
    # Test service queries
    test_galaxy_6000_search()
    test_micom_p20_search()
    
    print("\n✅ Testing complete!") 