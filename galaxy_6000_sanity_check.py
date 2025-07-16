#!/usr/bin/env python3
"""
Galaxy 6000 Multi-Dimensional Sanity Check
Comprehensive analysis of Galaxy 6000 data in IBcatalogue database
"""

import duckdb
import sys
import os

def connect_to_database():
    """Connect to IBcatalogue database"""
    db_path = "data/IBcatalogue.duckdb"
    try:
        conn = duckdb.connect(db_path)
        print(f"✅ Connected to database: {db_path}")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def check_total_products(conn):
    """Check total number of products in database"""
    print("\n🔍 CHECK 1: Total Products in Database")
    print("=" * 50)
    
    try:
        result = conn.execute("SELECT COUNT(*) FROM products").fetchone()
        total_products = result[0]
        print(f"📊 Total products in IBcatalogue: {total_products:,}")
        return total_products
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

def check_galaxy_products(conn):
    """Check all Galaxy-related products"""
    print("\n🔍 CHECK 2: All Galaxy Products")
    print("=" * 50)
    
    try:
        # Check all products with 'Galaxy' in range label
        galaxy_products = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                BRAND_LABEL,
                DEVICETYPE_LABEL
            FROM products 
            WHERE RANGE_LABEL ILIKE '%Galaxy%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER
        """).fetchall()
        
        print(f"📊 Total Galaxy products found: {len(galaxy_products)}")
        
        if galaxy_products:
            print("\n🎯 Galaxy Products Breakdown:")
            current_range = ""
            for row in galaxy_products:
                range_label, subrange, product_id, status, pl, brand, device_type = row
                
                if range_label != current_range:
                    current_range = range_label
                    print(f"\n📋 Range: {range_label}")
                
                print(f"  • {subrange} - {product_id} - {status} - {pl} - {brand} - {device_type}")
        
        return galaxy_products
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def check_galaxy_6000_specific(conn):
    """Check specifically for Galaxy 6000 products"""
    print("\n🔍 CHECK 3: Galaxy 6000 Specific Products")
    print("=" * 50)
    
    try:
        # Check for Galaxy 6000 specifically
        galaxy_6000_products = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                BRAND_LABEL,
                DEVICETYPE_LABEL,
                PRODUCT_DESCRIPTION
            FROM products 
            WHERE (RANGE_LABEL ILIKE '%Galaxy%' AND SUBRANGE_LABEL ILIKE '%6000%')
               OR (RANGE_LABEL ILIKE '%Galaxy%' AND PRODUCT_IDENTIFIER ILIKE '%6000%')
               OR (RANGE_LABEL ILIKE '%Galaxy%' AND PRODUCT_DESCRIPTION ILIKE '%6000%')
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER
        """).fetchall()
        
        print(f"📊 Galaxy 6000 specific products found: {len(galaxy_6000_products)}")
        
        if galaxy_6000_products:
            print("\n🎯 Galaxy 6000 Products:")
            for row in galaxy_6000_products:
                range_label, subrange, product_id, status, pl, brand, device_type, description = row
                print(f"  • {range_label} {subrange} - {product_id}")
                print(f"    Status: {status}")
                print(f"    PL: {pl} | Brand: {brand} | Type: {device_type}")
                print(f"    Description: {description[:100]}...")
                print()
        else:
            print("❌ No Galaxy 6000 specific products found!")
        
        return galaxy_6000_products
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def check_obsolescence_status_distribution(conn):
    """Check distribution of obsolescence statuses"""
    print("\n🔍 CHECK 4: Obsolescence Status Distribution")
    print("=" * 50)
    
    try:
        # Check all commercial statuses
        status_distribution = conn.execute("""
            SELECT 
                COMMERCIAL_STATUS,
                COUNT(*) as count
            FROM products
            GROUP BY COMMERCIAL_STATUS
            ORDER BY count DESC
        """).fetchall()
        
        print("📊 Commercial Status Distribution:")
        for status, count in status_distribution:
            print(f"  • {status}: {count:,}")
        
        # Check obsolescence-related statuses
        obsolescence_products = conn.execute("""
            SELECT COUNT(*) 
            FROM products
            WHERE COMMERCIAL_STATUS ILIKE '%end of commercialisation%'
               OR COMMERCIAL_STATUS ILIKE '%end of commercialization%'
               OR COMMERCIAL_STATUS ILIKE '%end of commerc. announced%'
               OR COMMERCIAL_STATUS ILIKE '%obsolescence%'
               OR COMMERCIAL_STATUS ILIKE '%discontinued%'
        """).fetchone()
        
        print(f"\n📊 Total obsolete products: {obsolescence_products[0]:,}")
        
        return status_distribution
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def check_spibs_products(conn):
    """Check SPIBS product line distribution"""
    print("\n🔍 CHECK 5: SPIBS Product Line Analysis")
    print("=" * 50)
    
    try:
        # Check all SPIBS products
        spibs_products = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                BRAND_LABEL,
                DEVICETYPE_LABEL
            FROM products 
            WHERE PL_SERVICES = 'SPIBS'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
        """).fetchall()
        
        print(f"📊 Total SPIBS products: {len(spibs_products)}")
        
        # Check SPIBS Galaxy products
        spibs_galaxy = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                BRAND_LABEL,
                DEVICETYPE_LABEL
            FROM products 
            WHERE PL_SERVICES = 'SPIBS' AND RANGE_LABEL ILIKE '%Galaxy%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
        """).fetchall()
        
        print(f"📊 SPIBS Galaxy products: {len(spibs_galaxy)}")
        
        if spibs_galaxy:
            print("\n🎯 SPIBS Galaxy Products:")
            for row in spibs_galaxy:
                range_label, subrange, product_id, status, brand, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {brand}")
        
        return spibs_products, spibs_galaxy
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

def check_ups_device_types(conn):
    """Check UPS device type distribution"""
    print("\n🔍 CHECK 6: UPS Device Type Analysis")
    print("=" * 50)
    
    try:
        # Check all UPS products
        ups_products = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                BRAND_LABEL
            FROM products 
            WHERE DEVICETYPE_LABEL ILIKE '%ups%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
        """).fetchall()
        
        print(f"📊 Total UPS products: {len(ups_products)}")
        
        # Check UPS Galaxy products
        ups_galaxy = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                BRAND_LABEL
            FROM products 
            WHERE DEVICETYPE_LABEL ILIKE '%ups%' AND RANGE_LABEL ILIKE '%Galaxy%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
        """).fetchall()
        
        print(f"📊 UPS Galaxy products: {len(ups_galaxy)}")
        
        if ups_galaxy:
            print("\n🎯 UPS Galaxy Products:")
            for row in ups_galaxy:
                range_label, subrange, product_id, status, pl, brand = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl} - {brand}")
        
        return ups_products, ups_galaxy
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

def check_apc_brand_products(conn):
    """Check APC brand products"""
    print("\n🔍 CHECK 7: APC Brand Analysis")
    print("=" * 50)
    
    try:
        # Check all APC products
        apc_products = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE BRAND_LABEL ILIKE '%APC%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
        """).fetchall()
        
        print(f"📊 Total APC products: {len(apc_products)}")
        
        # Check APC Galaxy products
        apc_galaxy = conn.execute("""
            SELECT 
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_IDENTIFIER,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                DEVICETYPE_LABEL
            FROM products 
            WHERE BRAND_LABEL ILIKE '%APC%' AND RANGE_LABEL ILIKE '%Galaxy%'
            ORDER BY RANGE_LABEL, SUBRANGE_LABEL
        """).fetchall()
        
        print(f"📊 APC Galaxy products: {len(apc_galaxy)}")
        
        if apc_galaxy:
            print("\n🎯 APC Galaxy Products:")
            for row in apc_galaxy:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl} - {device_type}")
        
        return apc_products, apc_galaxy
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

def run_comprehensive_test_query(conn):
    """Run the exact query that our service would generate"""
    print("\n🔍 CHECK 8: Service Query Simulation")
    print("=" * 50)
    
    try:
        # Simulate the exact query our service would generate for Galaxy 6000 SPIBS
        service_query = """
        SELECT 
            PRODUCT_IDENTIFIER,
            PRODUCT_TYPE,
            PRODUCT_DESCRIPTION,
            BRAND_CODE,
            BRAND_LABEL,
            RANGE_CODE,
            RANGE_LABEL,
            SUBRANGE_CODE,
            SUBRANGE_LABEL,
            DEVICETYPE_LABEL,
            PL_SERVICES,
            COMMERCIAL_STATUS
        FROM products
        WHERE 1=1
         AND (COMMERCIAL_STATUS ILIKE '%end of commercialisation%' 
              OR COMMERCIAL_STATUS ILIKE '%end of commercialization%' 
              OR COMMERCIAL_STATUS ILIKE '%end of commerc. announced%' 
              OR COMMERCIAL_STATUS ILIKE '%obsolescence%' 
              OR COMMERCIAL_STATUS ILIKE '%discontinued%')
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
        LIMIT 50
        """
        
        results = conn.execute(service_query).fetchall()
        
        print(f"📊 Service query results: {len(results)} products")
        
        if results:
            print("\n🎯 Service Query Results:")
            for row in results:
                product_id, product_type, description, brand_code, brand_label, range_code, range_label, subrange_code, subrange_label, device_type, pl_services, commercial_status = row
                print(f"  • {range_label} {subrange_label} - {product_id}")
                print(f"    Status: {commercial_status}")
                print(f"    PL: {pl_services} | Brand: {brand_label} | Type: {device_type}")
                print(f"    Description: {description[:80]}...")
                print()
        else:
            print("❌ No results from service query!")
        
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    """Run comprehensive Galaxy 6000 sanity check"""
    print("🚀 Galaxy 6000 Multi-Dimensional Sanity Check")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Run all checks
        total_products = check_total_products(conn)
        galaxy_products = check_galaxy_products(conn)
        galaxy_6000_products = check_galaxy_6000_specific(conn)
        status_distribution = check_obsolescence_status_distribution(conn)
        spibs_products, spibs_galaxy = check_spibs_products(conn)
        ups_products, ups_galaxy = check_ups_device_types(conn)
        apc_products, apc_galaxy = check_apc_brand_products(conn)
        service_results = run_comprehensive_test_query(conn)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"• Total products in database: {total_products:,}")
        print(f"• Total Galaxy products: {len(galaxy_products)}")
        print(f"• Galaxy 6000 specific: {len(galaxy_6000_products)}")
        print(f"• Total SPIBS products: {len(spibs_products)}")
        print(f"• SPIBS Galaxy products: {len(spibs_galaxy)}")
        print(f"• Total UPS products: {len(ups_products)}")
        print(f"• UPS Galaxy products: {len(ups_galaxy)}")
        print(f"• Total APC products: {len(apc_products)}")
        print(f"• APC Galaxy products: {len(apc_galaxy)}")
        print(f"• Service query results: {len(service_results)}")
        
        if len(service_results) == 0:
            print("\n⚠️  WARNING: Service query returned 0 results!")
            print("This suggests the filtering might be too restrictive.")
        
    finally:
        conn.close()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    main() 