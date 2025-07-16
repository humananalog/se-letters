#!/usr/bin/env python3
"""
Check MiCOM P120 Obsolete
Check if there are any obsolete products in MiCOM Px20 Series P120
"""

import duckdb

def check_micom_p120_obsolete():
    """Check MiCOM P120 obsolete products"""
    print("🔍 Checking MiCOM P120 Obsolete Products")
    print("=" * 50)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Check all P120 products
            print("📊 All MiCOM Px20 Series P120 products:")
            p120_all = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL
                FROM products 
                WHERE RANGE_LABEL = 'MiCOM Px20 Series' 
                  AND SUBRANGE_LABEL = 'P120'
                ORDER BY PRODUCT_IDENTIFIER
            """).fetchall()
            
            print(f"📊 Found {len(p120_all)} MiCOM Px20 Series P120 products:")
            for row in p120_all:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Check P120 with obsolescence filter
            print(f"\n📊 MiCOM Px20 Series P120 obsolete products:")
            p120_obsolete = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL
                FROM products 
                WHERE RANGE_LABEL = 'MiCOM Px20 Series' 
                  AND SUBRANGE_LABEL = 'P120'
                  AND (COMMERCIAL_STATUS = '19-end of commercialization block' 
                       OR COMMERCIAL_STATUS = '18-End of commercialisation' 
                       OR COMMERCIAL_STATUS = '14-End of commerc. announced' 
                       OR COMMERCIAL_STATUS = '16-Post commercialisation')
                ORDER BY PRODUCT_IDENTIFIER
            """).fetchall()
            
            print(f"📊 Found {len(p120_obsolete)} MiCOM Px20 Series P120 obsolete products:")
            for row in p120_obsolete:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Check what commercial statuses exist for P120
            print(f"\n📊 MiCOM Px20 Series P120 commercial statuses:")
            statuses = conn.execute("""
                SELECT DISTINCT COMMERCIAL_STATUS, COUNT(*) as count
                FROM products 
                WHERE RANGE_LABEL = 'MiCOM Px20 Series' 
                  AND SUBRANGE_LABEL = 'P120'
                GROUP BY COMMERCIAL_STATUS
                ORDER BY count DESC
            """).fetchall()
            
            for status, count in statuses:
                print(f"  • {status}: {count} products")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_micom_p120_obsolete() 