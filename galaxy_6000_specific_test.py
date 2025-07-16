#!/usr/bin/env python3
"""
Galaxy 6000 Specific Test
Test why Galaxy 6000 products are not being found
"""

import duckdb

def test_galaxy_6000_specific():
    """Test Galaxy 6000 specific filtering"""
    print("🔍 Testing Galaxy 6000 Specific Filtering")
    print("=" * 50)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Test 1: Check Galaxy 6000 products with obsolescence filter
            print("📊 Test 1: Galaxy 6000 with obsolescence filter")
            query1 = """
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE RANGE_LABEL ILIKE '%Galaxy%' 
              AND SUBRANGE_LABEL ILIKE '%6000%'
              AND (COMMERCIAL_STATUS = '19-end of commercialization block' 
                   OR COMMERCIAL_STATUS = '18-End of commercialisation' 
                   OR COMMERCIAL_STATUS = '14-End of commerc. announced' 
                   OR COMMERCIAL_STATUS = '16-Post commercialisation')
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
            """
            
            results1 = conn.execute(query1).fetchall()
            print(f"📊 Found {len(results1)} Galaxy 6000 obsolete products")
            
            for row in results1:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Test 2: Check Galaxy 6000 products with SPIBS filter
            print(f"\n📊 Test 2: Galaxy 6000 with SPIBS filter")
            query2 = """
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE RANGE_LABEL ILIKE '%Galaxy%' 
              AND SUBRANGE_LABEL ILIKE '%6000%'
              AND PL_SERVICES = 'SPIBS'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
            """
            
            results2 = conn.execute(query2).fetchall()
            print(f"📊 Found {len(results2)} Galaxy 6000 SPIBS products")
            
            for row in results2:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Test 3: Check Galaxy 6000 products with UPS filter
            print(f"\n📊 Test 3: Galaxy 6000 with UPS filter")
            query3 = """
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE RANGE_LABEL ILIKE '%Galaxy%' 
              AND SUBRANGE_LABEL ILIKE '%6000%'
              AND DEVICETYPE_LABEL ILIKE '%ups%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
            """
            
            results3 = conn.execute(query3).fetchall()
            print(f"📊 Found {len(results3)} Galaxy 6000 UPS products")
            
            for row in results3:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Test 4: Check Galaxy 6000 products with ALL filters
            print(f"\n📊 Test 4: Galaxy 6000 with ALL filters (our service query)")
            query4 = """
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
              AND (RANGE_LABEL = 'Galaxy' 
                   OR RANGE_LABEL ILIKE 'Galaxy %' 
                   OR RANGE_LABEL ILIKE '% Galaxy' 
                   OR RANGE_LABEL ILIKE '% Galaxy %' 
                   OR RANGE_LABEL ILIKE 'MGE Galaxy%' 
                   OR RANGE_LABEL ILIKE 'APC Galaxy%')
              AND PL_SERVICES = 'SPIBS' 
              AND (SUBRANGE_LABEL = '6000' 
                   OR SUBRANGE_LABEL ILIKE '6000 %' 
                   OR SUBRANGE_LABEL ILIKE '% 6000' 
                   OR SUBRANGE_LABEL ILIKE '% 6000 %') 
              AND DEVICETYPE_LABEL ILIKE '%ups%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
            """
            
            results4 = conn.execute(query4).fetchall()
            print(f"📊 Found {len(results4)} Galaxy 6000 products with ALL filters")
            
            for row in results4:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Test 5: Check what Galaxy 6000 products exist without any filters
            print(f"\n📊 Test 5: All Galaxy 6000 products (no filters)")
            query5 = """
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE RANGE_LABEL ILIKE '%Galaxy%' 
              AND SUBRANGE_LABEL ILIKE '%6000%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL, COMMERCIAL_STATUS
            """
            
            results5 = conn.execute(query5).fetchall()
            print(f"📊 Found {len(results5)} total Galaxy 6000 products")
            
            # Group by status
            status_groups = {}
            for row in results5:
                range_label, subrange, product_id, status, pl, device_type = row
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append((range_label, subrange, product_id, pl))
            
            for status, products in status_groups.items():
                print(f"\n📋 Status: {status} ({len(products)} products)")
                for range_label, subrange, product_id, pl in products[:5]:  # Show first 5
                    print(f"  • {range_label} {subrange} - {product_id} - {pl}")
                if len(products) > 5:
                    print(f"  ... and {len(products) - 5} more")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_galaxy_6000_specific() 