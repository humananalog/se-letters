#!/usr/bin/env python3
"""
Switchgear Families Database Explorer
Comprehensive analysis of switchgear families in the SOTA IBcatalogue database

Investigates:
- PIX product family variations and naming conventions
- PSIBS switchgear product landscape
- Medium voltage equipment categories
- Product identifier patterns and data variability
- Range and subrange classifications

Goal: Understand why PSIBS filter only found 1 product for PIX2B
Version: 1.0.0
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from loguru import logger
import re
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def analyze_switchgear_database():
    """Comprehensive analysis of switchgear families in SOTA database"""
    
    db_path = "../../data/IBcatalogue.duckdb"
    
    if not Path(db_path).exists():
        logger.error(f"❌ SOTA database not found: {db_path}")
        return
    
    logger.info("🔍 Exploring Switchgear Families in SOTA Database")
    logger.info("=" * 60)
    
    try:
        with duckdb.connect(db_path) as conn:
            # Get database overview
            total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            logger.info(f"📊 Total products in database: {total_products:,}")
            
            # 1. EXPLORE PIX PRODUCT FAMILY
            logger.info("\n🔍 1. PIX PRODUCT FAMILY ANALYSIS")
            logger.info("-" * 40)
            
                         pix_products = conn.execute("""
                 SELECT 
                     product_identifier,
                     range_label,
                     subrange_label,
                     product_description,
                     pl_services,
                     bu_label,
                     brand_label,
                     commercial_status
                 FROM products 
                 WHERE 
                     range_label ILIKE '%PIX%' OR 
                     subrange_label ILIKE '%PIX%' OR
                     product_description ILIKE '%PIX%' OR
                     product_identifier ILIKE '%PIX%'
                 ORDER BY range_label, subrange_label
             """).fetchall()
            
            logger.info(f"📦 PIX products found: {len(pix_products)}")
            
            if pix_products:
                pix_ranges = Counter()
                pix_subranges = Counter()
                pix_status = Counter()
                
                for product in pix_products[:10]:  # Show first 10
                    logger.info(f"   🔸 {product[0]} | {product[1]} | {product[2]} | {product[7]}")
                    
                    if product[1]: pix_ranges[product[1]] += 1
                    if product[2]: pix_subranges[product[2]] += 1
                    if product[7]: pix_status[product[7]] += 1
                
                logger.info(f"\n📊 PIX Range Distribution:")
                for range_name, count in pix_ranges.most_common(10):
                    logger.info(f"   {range_name}: {count} products")
                
                logger.info(f"\n📊 PIX Status Distribution:")
                for status, count in pix_status.most_common():
                    logger.info(f"   {status}: {count} products")
            
            # 2. EXPLORE PSIBS PRODUCT LINE
            logger.info("\n🔍 2. PSIBS PRODUCT LINE ANALYSIS")
            logger.info("-" * 40)
            
            psibs_products = conn.execute("""
                SELECT 
                    range_label,
                    COUNT(*) as product_count,
                    COUNT(DISTINCT subrange_label) as subrange_count,
                    STRING_AGG(DISTINCT product_status, ', ') as statuses
                FROM products 
                WHERE pl_services ILIKE '%PSIBS%'
                GROUP BY range_label
                ORDER BY product_count DESC
                LIMIT 20
            """).fetchall()
            
            logger.info(f"📦 PSIBS product ranges: {len(psibs_products)}")
            
            total_psibs = 0
            for range_name, count, subranges, statuses in psibs_products:
                total_psibs += count
                logger.info(f"   🔸 {range_name}: {count} products ({subranges} subranges) - {statuses}")
            
            logger.info(f"\n📊 Total PSIBS products: {total_psibs:,}")
            
            # 3. SWITCHGEAR KEYWORD ANALYSIS
            logger.info("\n🔍 3. SWITCHGEAR KEYWORD ANALYSIS")
            logger.info("-" * 40)
            
            switchgear_keywords = [
                'switchgear', 'switch gear', 'bus bar', 'busbar', 'ring main',
                'circuit breaker', 'load break', 'disconnect', 'isolator',
                'medium voltage', 'mv', 'distribution', 'substation'
            ]
            
            switchgear_analysis = {}
            
            for keyword in switchgear_keywords:
                count = conn.execute(f"""
                    SELECT COUNT(*) FROM products 
                    WHERE 
                        product_description ILIKE '%{keyword}%' OR
                        range_label ILIKE '%{keyword}%' OR
                        subrange_label ILIKE '%{keyword}%'
                """).fetchone()[0]
                
                switchgear_analysis[keyword] = count
                logger.info(f"   🔸 '{keyword}': {count:,} products")
            
            # 4. MEDIUM VOLTAGE ANALYSIS  
            logger.info("\n🔍 4. MEDIUM VOLTAGE ANALYSIS")
            logger.info("-" * 40)
            
            mv_products = conn.execute("""
                SELECT 
                    range_label,
                    COUNT(*) as count,
                    STRING_AGG(DISTINCT brand, ', ') as brands,
                    STRING_AGG(DISTINCT business_unit, ', ') as business_units
                FROM products 
                WHERE 
                    product_description ILIKE '%medium voltage%' OR
                    product_description ILIKE '%mv%' OR
                    product_description ILIKE '%kv%' OR
                    range_label ILIKE '%medium voltage%'
                GROUP BY range_label
                HAVING COUNT(*) > 10
                ORDER BY count DESC
                LIMIT 15
            """).fetchall()
            
            for range_name, count, brands, bus in mv_products:
                logger.info(f"   🔸 {range_name}: {count} products | {brands} | {bus}")
            
            # 5. DOUBLE BUS BAR ANALYSIS
            logger.info("\n🔍 5. DOUBLE BUS BAR ANALYSIS")
            logger.info("-" * 40)
            
            bus_bar_products = conn.execute("""
                SELECT 
                    product_id,
                    range_label,
                    subrange_label,
                    product_description,
                    brand,
                    product_status
                FROM products 
                WHERE 
                    product_description ILIKE '%bus bar%' OR
                    product_description ILIKE '%busbar%' OR
                    product_description ILIKE '%double bus%' OR
                    range_label ILIKE '%bus%'
                ORDER BY range_label
                LIMIT 20
            """).fetchall()
            
            logger.info(f"📦 Bus bar related products: {len(bus_bar_products)}")
            
            for product in bus_bar_products:
                logger.info(f"   🔸 {product[0]} | {product[1]} | {product[2]} | {product[5]}")
            
            # 6. BRAND ANALYSIS
            logger.info("\n🔍 6. BRAND ANALYSIS FOR SWITCHGEAR")
            logger.info("-" * 40)
            
            brand_analysis = conn.execute("""
                SELECT 
                    brand,
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN product_description ILIKE '%switchgear%' THEN 1 END) as switchgear_products,
                    COUNT(CASE WHEN pl_services ILIKE '%PSIBS%' THEN 1 END) as psibs_products
                FROM products 
                WHERE brand IS NOT NULL
                GROUP BY brand
                HAVING switchgear_products > 0 OR psibs_products > 0
                ORDER BY switchgear_products DESC, psibs_products DESC
                LIMIT 15
            """).fetchall()
            
            for brand, total, switchgear, psibs in brand_analysis:
                logger.info(f"   🔸 {brand}: {total:,} total | {switchgear:,} switchgear | {psibs:,} PSIBS")
            
            # 7. VOLTAGE LEVEL ANALYSIS
            logger.info("\n🔍 7. VOLTAGE LEVEL PATTERNS")
            logger.info("-" * 40)
            
            voltage_patterns = conn.execute("""
                SELECT 
                    product_description,
                    COUNT(*) as count
                FROM products 
                WHERE 
                    product_description ~ '\\d+(\\.\\d+)?\\s*kV' OR
                    product_description ~ '\\d+(\\.\\d+)?\\s*KV'
                GROUP BY product_description
                HAVING COUNT(*) > 5
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            
            for desc, count in voltage_patterns:
                # Extract voltage values
                voltage_match = re.search(r'(\d+(?:\.\d+)?)\s*k?V', desc, re.IGNORECASE)
                voltage = voltage_match.group(1) if voltage_match else "N/A"
                logger.info(f"   🔸 {voltage}kV: {count} products")
            
            # 8. DETAILED PIX INVESTIGATION
            logger.info("\n🔍 8. DETAILED PIX INVESTIGATION")
            logger.info("-" * 40)
            
            detailed_pix = conn.execute("""
                SELECT DISTINCT
                    range_label,
                    subrange_label,
                    COUNT(*) as count,
                    STRING_AGG(DISTINCT product_status, ', ') as statuses,
                    MIN(product_description) as sample_description
                FROM products 
                WHERE 
                    range_label ILIKE '%PIX%' OR 
                    subrange_label ILIKE '%PIX%' OR
                    product_id ILIKE '%PIX%'
                GROUP BY range_label, subrange_label
                ORDER BY count DESC
            """).fetchall()
            
            logger.info(f"📦 PIX product combinations: {len(detailed_pix)}")
            
            for range_label, subrange, count, statuses, desc in detailed_pix:
                logger.info(f"   🔸 Range: {range_label} | Sub: {subrange} | Count: {count}")
                logger.info(f"      Status: {statuses}")
                logger.info(f"      Sample: {desc[:100]}...")
                logger.info("")
            
            # 9. SEARCH FOR PIX 2B SPECIFICALLY
            logger.info("\n🔍 9. SPECIFIC PIX 2B / DOUBLE BUS SEARCH")  
            logger.info("-" * 40)
            
            pix2b_search = conn.execute("""
                SELECT 
                    product_id,
                    range_label,
                    subrange_label,
                    product_description,
                    brand,
                    product_status,
                    pl_services
                FROM products 
                WHERE 
                    (product_description ILIKE '%pix%2b%' OR
                     product_description ILIKE '%pix%double%' OR
                     product_description ILIKE '%pix 2b%' OR
                     range_label ILIKE '%pix%2b%' OR
                     range_label ILIKE '%double%bus%' OR
                     subrange_label ILIKE '%2b%' OR
                     subrange_label ILIKE '%double%') AND
                    (product_description ILIKE '%bus%' OR 
                     range_label ILIKE '%bus%')
                ORDER BY range_label, subrange_label
            """).fetchall()
            
            logger.info(f"📦 PIX 2B / Double Bus specific matches: {len(pix2b_search)}")
            
            for product in pix2b_search:
                logger.info(f"   🔸 {product[0]}")
                logger.info(f"      Range: {product[1]} | Sub: {product[2]}")  
                logger.info(f"      Brand: {product[4]} | Status: {product[5]}")
                logger.info(f"      PL: {product[6]}")
                logger.info(f"      Desc: {product[3][:150]}...")
                logger.info("")
            
            # 10. SAVE DETAILED ANALYSIS
            logger.info("\n💾 SAVING DETAILED ANALYSIS")
            logger.info("-" * 40)
            
            # Save comprehensive PIX analysis
            all_pix_data = conn.execute("""
                SELECT * FROM products 
                WHERE 
                    range_label ILIKE '%PIX%' OR 
                    subrange_label ILIKE '%PIX%' OR
                    product_description ILIKE '%PIX%' OR
                    product_id ILIKE '%PIX%'
            """).fetchall()
            
            columns = [desc[0] for desc in conn.description]
            pix_df = pd.DataFrame(all_pix_data, columns=columns)
            
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            pix_file = f"pix_analysis_{timestamp}.xlsx"
            
            with pd.ExcelWriter(pix_file, engine='openpyxl') as writer:
                pix_df.to_excel(writer, sheet_name='All PIX Products', index=False)
                
                # Summary statistics
                summary_data = {
                    'Metric': [
                        'Total PIX Products',
                        'Unique Ranges', 
                        'Unique Subranges',
                        'Unique Brands',
                        'Active Products',
                        'Obsolete Products'
                    ],
                    'Value': [
                        len(pix_df),
                        pix_df['range_label'].nunique(),
                        pix_df['subrange_label'].nunique(), 
                        pix_df['brand'].nunique(),
                        len(pix_df[pix_df['product_status'] == 'Active']),
                        len(pix_df[pix_df['product_status'].isin(['Obsolete', 'End of Sale'])])
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"📄 PIX analysis saved: {pix_file}")
            
            # Create switchgear intelligence summary
            intelligence_summary = {
                "database_overview": {
                    "total_products": total_products,
                    "total_psibs_products": total_psibs,
                    "pix_products_found": len(pix_products),
                    "analysis_timestamp": timestamp
                },
                "pix_analysis": {
                    "total_pix_products": len(pix_products),
                    "range_distribution": dict(pix_ranges.most_common(10)),
                    "status_distribution": dict(pix_status.most_common())
                },
                "switchgear_keywords": switchgear_analysis,
                "findings": {
                    "pix_2b_specific_matches": len(pix2b_search),
                    "medium_voltage_ranges": len(mv_products),
                    "bus_bar_products": len(bus_bar_products)
                }
            }
            
            intelligence_file = f"switchgear_intelligence_{timestamp}.json"
            with open(intelligence_file, 'w') as f:
                json.dump(intelligence_summary, f, indent=2)
            
            logger.info(f"📄 Intelligence summary saved: {intelligence_file}")
            
            # FINAL INSIGHTS
            logger.info("\n🎯 KEY INSIGHTS")
            logger.info("=" * 40)
            logger.info(f"📊 Total PIX products in database: {len(pix_products):,}")
            logger.info(f"📊 Total PSIBS products: {total_psibs:,}")
            logger.info(f"📊 PIX 2B specific matches: {len(pix2b_search)}")
            logger.info(f"📊 Bus bar related products: {len(bus_bar_products)}")
            
            if len(pix_products) > 1:
                logger.info(f"⚠️  FINDING: Database contains {len(pix_products)} PIX products")
                logger.info(f"⚠️  ISSUE: PSIBS filter only found 1 product from grok metadata")
                logger.info(f"💡 RECOMMENDATION: Enhance filter to search database for related products")
            
    except Exception as e:
        logger.error(f"❌ Database analysis failed: {e}")
        raise


if __name__ == "__main__":
    analyze_switchgear_database() 