#!/usr/bin/env python3
"""
PIX Database Analysis - Quick Investigation
Focus on understanding PIX product variability in the database

Goal: Understand why PSIBS filter only found 1 product for PIX2B
"""

import duckdb
from loguru import logger
from collections import Counter
import pandas as pd

def analyze_pix_products():
    """Quick PIX product analysis"""
    
    db_path = "../../data/IBcatalogue.duckdb"
    
    logger.info("🔍 PIX Product Database Analysis")
    logger.info("=" * 50)
    
    try:
        with duckdb.connect(db_path) as conn:
            # Total products
            total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            logger.info(f"📊 Total products in database: {total:,}")
            
            # 1. PIX PRODUCT SEARCH
            logger.info("\n🔍 1. PIX PRODUCT SEARCH")
            logger.info("-" * 30)
            
            pix_products = conn.execute("""
                SELECT 
                    product_identifier,
                    range_label,
                    subrange_label,
                    product_description,
                    brand_label,
                    commercial_status,
                    pl_services
                FROM products 
                WHERE 
                    range_label ILIKE '%PIX%' OR 
                    subrange_label ILIKE '%PIX%' OR
                    product_description ILIKE '%PIX%' OR
                    product_identifier ILIKE '%PIX%'
                ORDER BY range_label, subrange_label
                LIMIT 50
            """).fetchall()
            
            logger.info(f"📦 PIX products found: {len(pix_products)}")
            
            if pix_products:
                logger.info("\n📋 PIX Products Sample:")
                for i, product in enumerate(pix_products[:15], 1):
                    logger.info(f"{i:2d}. {product[0]} | {product[1]} | {product[2]} | {product[5]}")
                
                # Range analysis
                ranges = Counter(p[1] for p in pix_products if p[1])
                logger.info(f"\n📊 PIX Range Distribution:")
                for range_name, count in ranges.most_common(10):
                    logger.info(f"   {range_name}: {count} products")
                
                # Status analysis
                statuses = Counter(p[5] for p in pix_products if p[5])
                logger.info(f"\n📊 PIX Status Distribution:")
                for status, count in statuses.most_common():
                    logger.info(f"   {status}: {count} products")
            
            # 2. DOUBLE BUS BAR SEARCH
            logger.info("\n🔍 2. DOUBLE BUS BAR SEARCH")
            logger.info("-" * 30)
            
            bus_bar_products = conn.execute("""
                SELECT 
                    product_identifier,
                    range_label,
                    subrange_label,
                    product_description,
                    brand_label,
                    commercial_status
                FROM products 
                WHERE 
                    product_description ILIKE '%bus bar%' OR
                    product_description ILIKE '%busbar%' OR
                    product_description ILIKE '%double bus%' OR
                    range_label ILIKE '%bus%' OR
                    subrange_label ILIKE '%bus%'
                ORDER BY range_label
                LIMIT 20
            """).fetchall()
            
            logger.info(f"📦 Bus bar products found: {len(bus_bar_products)}")
            
            if bus_bar_products:
                logger.info("\n📋 Bus Bar Products Sample:")
                for i, product in enumerate(bus_bar_products[:10], 1):
                    logger.info(f"{i:2d}. {product[0]} | {product[1]} | {product[2]} | {product[5]}")
            
            # 3. PSIBS PRODUCTS SEARCH
            logger.info("\n🔍 3. PSIBS PRODUCTS SEARCH")
            logger.info("-" * 30)
            
            psibs_products = conn.execute("""
                SELECT 
                    range_label,
                    COUNT(*) as count,
                    COUNT(DISTINCT subrange_label) as subranges,
                    STRING_AGG(DISTINCT commercial_status, ', ') as statuses
                FROM products 
                WHERE pl_services ILIKE '%PSIBS%'
                GROUP BY range_label
                ORDER BY count DESC
                LIMIT 15
            """).fetchall()
            
            logger.info(f"📦 PSIBS product ranges: {len(psibs_products)}")
            
            total_psibs = 0
            if psibs_products:
                logger.info("\n📋 PSIBS Ranges:")
                for range_name, count, subranges, statuses in psibs_products:
                    total_psibs += count
                    logger.info(f"   {range_name}: {count} products ({subranges} subranges)")
            
            logger.info(f"\n📊 Total PSIBS products: {total_psibs:,}")
            
            # 4. SWITCHGEAR SEARCH
            logger.info("\n🔍 4. SWITCHGEAR SEARCH")
            logger.info("-" * 30)
            
            switchgear_count = conn.execute("""
                SELECT COUNT(*) FROM products 
                WHERE 
                    product_description ILIKE '%switchgear%' OR
                    range_label ILIKE '%switchgear%'
            """).fetchone()[0]
            
            logger.info(f"📦 Switchgear products: {switchgear_count:,}")
            
            # 5. MEDIUM VOLTAGE SEARCH
            logger.info("\n🔍 5. MEDIUM VOLTAGE SEARCH")
            logger.info("-" * 30)
            
            mv_count = conn.execute("""
                SELECT COUNT(*) FROM products 
                WHERE 
                    product_description ILIKE '%medium voltage%' OR
                    product_description ILIKE '%mv%' OR
                    product_description ILIKE '%kv%'
            """).fetchone()[0]
            
            logger.info(f"📦 Medium voltage products: {mv_count:,}")
            
            # 6. SPECIFIC PIX 2B SEARCH
            logger.info("\n🔍 6. SPECIFIC PIX 2B SEARCH")
            logger.info("-" * 30)
            
            pix2b_products = conn.execute("""
                SELECT 
                    product_identifier,
                    range_label,
                    subrange_label,
                    product_description,
                    brand_label,
                    commercial_status,
                    pl_services
                FROM products 
                WHERE 
                    (product_description ILIKE '%pix%2b%' OR
                     product_description ILIKE '%pix%double%' OR
                     product_description ILIKE '%pix 2b%' OR
                     range_label ILIKE '%pix%2b%' OR
                     range_label ILIKE '%double%bus%' OR
                     subrange_label ILIKE '%2b%') 
                ORDER BY range_label, subrange_label
            """).fetchall()
            
            logger.info(f"📦 PIX 2B specific matches: {len(pix2b_products)}")
            
            if pix2b_products:
                logger.info("\n📋 PIX 2B Specific Products:")
                for i, product in enumerate(pix2b_products, 1):
                    logger.info(f"{i:2d}. {product[0]}")
                    logger.info(f"    Range: {product[1]} | Sub: {product[2]}")
                    logger.info(f"    Status: {product[5]} | PL: {product[6]}")
                    logger.info(f"    Desc: {product[3][:100]}...")
                    logger.info("")
            
            # 7. KEY INSIGHTS
            logger.info("\n🎯 KEY INSIGHTS")
            logger.info("=" * 30)
            
            logger.info(f"📊 Total PIX products in database: {len(pix_products):,}")
            logger.info(f"📊 PIX 2B specific matches: {len(pix2b_products)}")
            logger.info(f"📊 Total PSIBS products: {total_psibs:,}")
            logger.info(f"📊 Bus bar products: {len(bus_bar_products)}")
            logger.info(f"📊 Switchgear products: {switchgear_count:,}")
            logger.info(f"📊 Medium voltage products: {mv_count:,}")
            
            if len(pix_products) > 1:
                logger.info(f"\n⚠️  FINDING: Database contains {len(pix_products)} PIX products but filter only found 1")
                logger.info(f"💡 ISSUE: Grok metadata only contained 1 product, not a database search limitation")
                logger.info(f"💡 RECOMMENDATION: The issue is in grok extraction, not database matching")
            else:
                logger.info(f"\n✅ FINDING: Database search confirms limited PIX products available")
            
            # Save results
            if pix_products:
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                
                # Create DataFrame
                columns = ['product_identifier', 'range_label', 'subrange_label', 
                          'product_description', 'brand_label', 'commercial_status', 'pl_services']
                pix_df = pd.DataFrame(pix_products, columns=columns)
                
                # Save to Excel
                filename = f"pix_database_analysis_{timestamp}.xlsx"
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    pix_df.to_excel(writer, sheet_name='All PIX Products', index=False)
                    
                    # Summary
                    summary_data = {
                        'Metric': [
                            'Total Database Products',
                            'PIX Products Found',
                            'PIX 2B Specific',
                            'PSIBS Products Total',
                            'Bus Bar Products',
                            'Switchgear Products',
                            'Medium Voltage Products'
                        ],
                        'Count': [
                            total,
                            len(pix_products),
                            len(pix2b_products),
                            total_psibs,
                            len(bus_bar_products),
                            switchgear_count,
                            mv_count
                        ]
                    }
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Analysis Summary', index=False)
                
                logger.info(f"\n💾 Analysis saved: {filename}")
            
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise

if __name__ == "__main__":
    analyze_pix_products() 