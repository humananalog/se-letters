#!/usr/bin/env python3
"""
Check MiCOM Px20 Series
Check what products are in the MiCOM Px20 Series range
"""

import duckdb

def check_micom_p20_series():
    """Check MiCOM Px20 Series products"""
    print("🔍 Checking MiCOM Px20 Series Products")
    print("=" * 50)
    
    db_path = "data/IBcatalogue.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Check all products in MiCOM Px20 Series
            print("📊 All MiCOM Px20 Series products:")
            p20_series = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL
                FROM products 
                WHERE RANGE_LABEL = 'MiCOM Px20 Series'
                ORDER BY SUBRANGE_LABEL, PRODUCT_IDENTIFIER
                LIMIT 20
            """).fetchall()
            
            print(f"📊 Found {len(p20_series)} MiCOM Px20 Series products:")
            for row in p20_series:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Check MiCOM Px20 Series with obsolescence filter
            print(f"\n📊 MiCOM Px20 Series obsolete products:")
            p20_series_obsolete = conn.execute("""
                SELECT 
                    RANGE_LABEL,
                    SUBRANGE_LABEL,
                    PRODUCT_IDENTIFIER,
                    COMMERCIAL_STATUS,
                    PL_SERVICES,
                    DEVICETYPE_LABEL
                FROM products 
                WHERE RANGE_LABEL = 'MiCOM Px20 Series'
                  AND (COMMERCIAL_STATUS = '19-end of commercialization block' 
                       OR COMMERCIAL_STATUS = '18-End of commercialisation' 
                       OR COMMERCIAL_STATUS = '14-End of commerc. announced' 
                       OR COMMERCIAL_STATUS = '16-Post commercialisation')
                ORDER BY SUBRANGE_LABEL, PRODUCT_IDENTIFIER
                LIMIT 20
            """).fetchall()
            
            print(f"📊 Found {len(p20_series_obsolete)} MiCOM Px20 Series obsolete products:")
            for row in p20_series_obsolete:
                range_label, subrange, product_id, status, pl, device_type = row
                print(f"  • {range_label} {subrange} - {product_id} - {status} - {pl}")
            
            # Check what subranges exist in MiCOM Px20 Series
            print(f"\n📊 MiCOM Px20 Series subranges:")
            subranges = conn.execute("""
                SELECT DISTINCT SUBRANGE_LABEL, COUNT(*) as count
                FROM products 
                WHERE RANGE_LABEL = 'MiCOM Px20 Series'
                GROUP BY SUBRANGE_LABEL
                ORDER BY count DESC
            """).fetchall()
            
            for subrange, count in subranges:
                print(f"  • {subrange}: {count} products")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_micom_p20_series() 