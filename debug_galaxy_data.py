#!/usr/bin/env python3
"""
Debug Galaxy Data
Check what Galaxy data actually exists in the database
"""

import duckdb

def debug_galaxy_data():
    """Debug Galaxy data in database"""
    print("🔍 Debugging Galaxy Data in Database")
    print("=" * 50)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Check if we can connect and query
            print("✅ Database connected successfully")
            
            # Check total products
            total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            print(f"📊 Total products in database: {total:,}")
            
            # Check all products with 'Galaxy' in range label
            print(f"\n📊 All products with 'Galaxy' in RANGE_LABEL:")
            galaxy_products = conn.execute("""
                SELECT DISTINCT RANGE_LABEL, COUNT(*) as count
                FROM products 
                WHERE RANGE_LABEL ILIKE '%Galaxy%'
                GROUP BY RANGE_LABEL
                ORDER BY count DESC
            """).fetchall()
            
            print(f"📊 Found {len(galaxy_products)} distinct Galaxy ranges:")
            for range_label, count in galaxy_products:
                print(f"  • {range_label}: {count} products")
            
            # Check all products with 'Galaxy' in subrange label
            print(f"\n📊 All products with 'Galaxy' in SUBRANGE_LABEL:")
            galaxy_subrange = conn.execute("""
                SELECT DISTINCT SUBRANGE_LABEL, COUNT(*) as count
                FROM products 
                WHERE SUBRANGE_LABEL ILIKE '%Galaxy%'
                GROUP BY SUBRANGE_LABEL
                ORDER BY count DESC
            """).fetchall()
            
            print(f"📊 Found {len(galaxy_subrange)} distinct Galaxy subranges:")
            for subrange_label, count in galaxy_subrange:
                print(f"  • {subrange_label}: {count} products")
            
            # Check all products with '6000' in subrange label
            print(f"\n📊 All products with '6000' in SUBRANGE_LABEL:")
            products_6000 = conn.execute("""
                SELECT DISTINCT SUBRANGE_LABEL, RANGE_LABEL, COUNT(*) as count
                FROM products 
                WHERE SUBRANGE_LABEL ILIKE '%6000%'
                GROUP BY SUBRANGE_LABEL, RANGE_LABEL
                ORDER BY count DESC
            """).fetchall()
            
            print(f"📊 Found {len(products_6000)} distinct 6000 subranges:")
            for subrange_label, range_label, count in products_6000:
                print(f"  • {range_label} {subrange_label}: {count} products")
            
            # Check MGE Galaxy 6000 specifically
            print(f"\n📊 MGE Galaxy 6000 products:")
            mge_galaxy_6000 = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL
                FROM products 
                WHERE RANGE_LABEL ILIKE '%MGE Galaxy%' 
                  AND SUBRANGE_LABEL ILIKE '%6000%'
                ORDER BY RANGE_LABEL, SUBRANGE_LABEL
                LIMIT 10
            """).fetchall()
            
            print(f"📊 Found {len(mge_galaxy_6000)} MGE Galaxy 6000 products:")
            for row in mge_galaxy_6000:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Check what the actual range labels look like
            print(f"\n📊 Sample range labels containing 'Galaxy':")
            sample_ranges = conn.execute("""
                SELECT DISTINCT RANGE_LABEL
                FROM products 
                WHERE RANGE_LABEL ILIKE '%Galaxy%'
                ORDER BY RANGE_LABEL
                LIMIT 20
            """).fetchall()
            
            for (range_label,) in sample_ranges:
                print(f"  • '{range_label}'")
            
            # Check what the actual subrange labels look like
            print(f"\n📊 Sample subrange labels containing '6000':")
            sample_subranges = conn.execute("""
                SELECT DISTINCT SUBRANGE_LABEL
                FROM products 
                WHERE SUBRANGE_LABEL ILIKE '%6000%'
                ORDER BY SUBRANGE_LABEL
                LIMIT 20
            """).fetchall()
            
            for (subrange_label,) in sample_subranges:
                print(f"  • '{subrange_label}'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_galaxy_data() 