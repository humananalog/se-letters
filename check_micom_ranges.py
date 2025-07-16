#!/usr/bin/env python3
"""
Check MiCOM Ranges
Check what MiCOM ranges actually exist in the database
"""

import duckdb

def check_micom_ranges():
    """Check MiCOM ranges in database"""
    print("🔍 Checking MiCOM Ranges in Database")
    print("=" * 50)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Check all MiCOM ranges
            print("📊 All MiCOM ranges:")
            micom_ranges = conn.execute("""
                SELECT DISTINCT RANGE_LABEL, COUNT(*) as count
                FROM products 
                WHERE RANGE_LABEL ILIKE '%MiCOM%'
                GROUP BY RANGE_LABEL
                ORDER BY count DESC
            """).fetchall()
            
            for range_label, count in micom_ranges:
                print(f"  • {range_label}: {count} products")
            
            # Check MiCOM P20 specifically
            print(f"\n📊 MiCOM P20 products:")
            micom_p20 = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL
                FROM products 
                WHERE RANGE_LABEL ILIKE '%MiCOM%' 
                  AND (SUBRANGE_LABEL ILIKE '%P20%' OR RANGE_LABEL ILIKE '%P20%')
                ORDER BY RANGE_LABEL, SUBRANGE_LABEL
                LIMIT 10
            """).fetchall()
            
            print(f"📊 Found {len(micom_p20)} MiCOM P20 products:")
            for row in micom_p20:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Check MiCOM P20 with obsolescence filter
            print(f"\n📊 MiCOM P20 obsolete products:")
            micom_p20_obsolete = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL
                FROM products 
                WHERE RANGE_LABEL ILIKE '%MiCOM%' 
                  AND (SUBRANGE_LABEL ILIKE '%P20%' OR RANGE_LABEL ILIKE '%P20%')
                  AND (COMMERCIAL_STATUS = '19-end of commercialization block' 
                       OR COMMERCIAL_STATUS = '18-End of commercialisation' 
                       OR COMMERCIAL_STATUS = '14-End of commerc. announced' 
                       OR COMMERCIAL_STATUS = '16-Post commercialisation')
                ORDER BY RANGE_LABEL, SUBRANGE_LABEL
                LIMIT 10
            """).fetchall()
            
            print(f"📊 Found {len(micom_p20_obsolete)} MiCOM P20 obsolete products:")
            for row in micom_p20_obsolete:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_micom_ranges() 