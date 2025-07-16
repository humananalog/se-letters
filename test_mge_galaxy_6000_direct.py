#!/usr/bin/env python3
"""
Direct Test for MGE Galaxy 6000
Test the exact query that should find MGE Galaxy 6000 products
"""

import duckdb

def test_mge_galaxy_6000_direct():
    """Test MGE Galaxy 6000 products directly"""
    print("🔍 Direct Test for MGE Galaxy 6000")
    print("=" * 50)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Test 1: MGE Galaxy 6000 with obsolescence filter
            print("📊 Test 1: MGE Galaxy 6000 with obsolescence filter")
            query1 = """
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE RANGE_LABEL = 'MGE Galaxy 6000'
              AND (COMMERCIAL_STATUS = '19-end of commercialization block' 
                   OR COMMERCIAL_STATUS = '18-End of commercialisation' 
                   OR COMMERCIAL_STATUS = '14-End of commerc. announced' 
                   OR COMMERCIAL_STATUS = '16-Post commercialisation')
            ORDER BY COMMERCIAL_STATUS, PRODUCT_IDENTIFIER
            LIMIT 10
            """
            
            results1 = conn.execute(query1).fetchall()
            print(f"📊 Found {len(results1)} MGE Galaxy 6000 obsolete products")
            
            for row in results1:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Test 2: MGE Galaxy 6000 with SPIBS filter
            print(f"\n📊 Test 2: MGE Galaxy 6000 with SPIBS filter")
            query2 = """
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE RANGE_LABEL = 'MGE Galaxy 6000'
              AND PL_SERVICES = 'SPIBS'
            ORDER BY COMMERCIAL_STATUS, PRODUCT_IDENTIFIER
            LIMIT 10
            """
            
            results2 = conn.execute(query2).fetchall()
            print(f"📊 Found {len(results2)} MGE Galaxy 6000 SPIBS products")
            
            for row in results2:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Test 3: MGE Galaxy 6000 with ALL filters (our service query)
            print(f"\n📊 Test 3: MGE Galaxy 6000 with ALL filters (our service query)")
            query3 = """
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE (COMMERCIAL_STATUS = '19-end of commercialization block' 
                   OR COMMERCIAL_STATUS = '18-End of commercialisation' 
                   OR COMMERCIAL_STATUS = '14-End of commerc. announced' 
                   OR COMMERCIAL_STATUS = '16-Post commercialisation')
              AND RANGE_LABEL = 'MGE Galaxy 6000'
              AND PL_SERVICES = 'SPIBS' 
              AND DEVICETYPE_LABEL ILIKE '%ups%'
            ORDER BY COMMERCIAL_STATUS, PRODUCT_IDENTIFIER
            LIMIT 10
            """
            
            results3 = conn.execute(query3).fetchall()
            print(f"📊 Found {len(results3)} MGE Galaxy 6000 products with ALL filters")
            
            for row in results3:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Test 4: Check what statuses MGE Galaxy 6000 products actually have
            print(f"\n📊 Test 4: MGE Galaxy 6000 status distribution")
            query4 = """
            SELECT 
                COMMERCIAL_STATUS,
                COUNT(*) as count
            FROM products 
            WHERE RANGE_LABEL = 'MGE Galaxy 6000'
            GROUP BY COMMERCIAL_STATUS
            ORDER BY count DESC
            """
            
            results4 = conn.execute(query4).fetchall()
            print(f"📊 MGE Galaxy 6000 status distribution:")
            for status, count in results4:
                print(f"  • {status}: {count} products")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_mge_galaxy_6000_direct() 