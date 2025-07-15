#!/usr/bin/env python3
"""
Explore MiCOM Protection Relays
Analyze MiCOM protection relay products in the DuckDB database to understand 
nomenclature patterns and discover CORTEC code structures for better product 
mapping.

Author: SE Letters Team
"""

import sys
from pathlib import Path
import re
from collections import defaultdict
from typing import List

import duckdb
from loguru import logger

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def analyze_micom_products():
    """Analyze MiCOM protection relay products in the database"""
    logger.info("🔍 ANALYZING MICOM PROTECTION RELAYS")
    logger.info("=" * 60)
    
    # Connect to database
    conn = duckdb.connect('data/IBcatalogue.duckdb')
    
    # 1. Find all MiCOM products
    logger.info("1️⃣ ALL MiCOM Products Overview:")
    micom_overview = conn.execute("""
        SELECT 
            PL_SERVICES,
            COUNT(*) as count,
            COUNT(DISTINCT RANGE_LABEL) as unique_ranges
        FROM products 
        WHERE (RANGE_LABEL ILIKE '%micom%' OR 
               PRODUCT_IDENTIFIER ILIKE '%micom%' OR
               PRODUCT_DESCRIPTION ILIKE '%micom%')
        GROUP BY PL_SERVICES
        ORDER BY count DESC
    """).fetchall()
    
    for row in micom_overview:
        logger.info(f"   📦 {row[0]}: {row[1]} products, "
                    f"{row[2]} unique ranges")
    
    # 2. Focus on DPIBS MiCOM products (protection relays)
    logger.info("\n2️⃣ DPIBS MiCOM Protection Relays:")
    dpibs_micom = conn.execute("""
        SELECT 
            PRODUCT_IDENTIFIER, 
            RANGE_LABEL, 
            SUBRANGE_LABEL,
            PRODUCT_DESCRIPTION,
            COMMERCIAL_STATUS
        FROM products 
        WHERE PL_SERVICES = 'DPIBS' 
        AND (RANGE_LABEL ILIKE '%micom%' OR 
             PRODUCT_IDENTIFIER ILIKE '%micom%' OR
             PRODUCT_DESCRIPTION ILIKE '%micom%')
        ORDER BY RANGE_LABEL, PRODUCT_IDENTIFIER
        LIMIT 50
    """).fetchall()
    
    logger.info(f"   Found {len(dpibs_micom)} DPIBS MiCOM products:")
    
    # Analyze patterns
    range_patterns = defaultdict(list)
    identifier_patterns = []
    
    for row in dpibs_micom:
        product_id, range_label, subrange_label, description, status = row
        range_patterns[range_label].append(product_id)
        identifier_patterns.append(product_id)
        
        logger.info(f"   🔧 {product_id}")
        logger.info(f"      Range: {range_label} | "
                    f"Subrange: {subrange_label}")
        logger.info(f"      Status: {status}")
        logger.info(f"      Description: {description[:80]}...")
        logger.info("      ---")
    
    # 3. Analyze CORTEC-like patterns
    logger.info("\n3️⃣ CORTEC Pattern Analysis:")
    analyze_cortec_patterns(identifier_patterns)
    
    # 4. Check for specific MiCOM series mentioned in grok_metadata.json
    logger.info("\n4️⃣ Specific MiCOM Series from Document:")
    target_series = ["P20", "P521"]
    
    for series in target_series:
        logger.info(f"\n🎯 MiCOM {series} Analysis:")
        series_query = conn.execute(f"""
            SELECT 
                PRODUCT_IDENTIFIER, 
                RANGE_LABEL, 
                SUBRANGE_LABEL,
                PRODUCT_DESCRIPTION,
                COMMERCIAL_STATUS
            FROM products 
            WHERE (PRODUCT_IDENTIFIER ILIKE '%micom%{series}%' OR
                   PRODUCT_IDENTIFIER ILIKE '%{series}%' OR
                   RANGE_LABEL ILIKE '%{series}%' OR
                   SUBRANGE_LABEL ILIKE '%{series}%')
            AND PL_SERVICES = 'DPIBS'
            ORDER BY PRODUCT_IDENTIFIER
            LIMIT 20
        """).fetchall()
        
        logger.info(f"   Found {len(series_query)} products for "
                    f"MiCOM {series}:")
        for product in series_query:
            product_id, range_label, subrange_label, description, status = product
            logger.info(f"   ✅ {product_id} | {range_label} | {status}")
    
    # 5. Check SEPAM products for comparison
    logger.info("\n5️⃣ SEPAM Protection Relays for Comparison:")
    sepam_products = conn.execute("""
        SELECT 
            PRODUCT_IDENTIFIER, 
            RANGE_LABEL, 
            SUBRANGE_LABEL,
            COMMERCIAL_STATUS
        FROM products 
        WHERE (RANGE_LABEL ILIKE '%sepam%' OR 
               PRODUCT_IDENTIFIER ILIKE '%sepam%')
        AND PL_SERVICES = 'DPIBS'
        ORDER BY RANGE_LABEL, PRODUCT_IDENTIFIER
        LIMIT 30
    """).fetchall()
    
    logger.info(f"   Found {len(sepam_products)} DPIBS SEPAM products:")
    for product in sepam_products[:10]:  # Show first 10
        product_id, range_label, subrange_label, status = product
        logger.info(f"   🔧 {product_id} | {range_label} | {status}")
    
    # 6. PowerLogic products
    logger.info("\n6️⃣ PowerLogic Protection Products:")
    powerlogic_products = conn.execute("""
        SELECT 
            PRODUCT_IDENTIFIER, 
            RANGE_LABEL, 
            SUBRANGE_LABEL,
            COMMERCIAL_STATUS
        FROM products 
        WHERE (RANGE_LABEL ILIKE '%powerlogic%' OR 
               PRODUCT_IDENTIFIER ILIKE '%powerlogic%')
        AND PL_SERVICES = 'DPIBS'
        ORDER BY RANGE_LABEL, PRODUCT_IDENTIFIER
        LIMIT 20
    """).fetchall()
    
    logger.info(f"   Found {len(powerlogic_products)} DPIBS PowerLogic "
                f"products:")
    for product in powerlogic_products:
        product_id, range_label, subrange_label, status = product
        logger.info(f"   🔧 {product_id} | {range_label} | {status}")
    
    conn.close()


def analyze_cortec_patterns(identifiers: List[str]):
    """Analyze potential CORTEC patterns in product identifiers"""
    logger.info("📋 CORTEC Pattern Analysis:")
    
    # Pattern categories
    patterns = {
        'P_series': [],  # P + numbers (like P441, P20, P521)
        'alphanumeric': [],  # Mixed letters and numbers
        'with_dots': [],  # Contains dots (might be CORTEC)
        'long_codes': []  # Longer codes that might be CORTEC
    }
    
    # Regular expressions for CORTEC-like patterns
    p_series_pattern = re.compile(r'P\d+[A-Z]*\d*[A-Z]*\d*', re.IGNORECASE)
    
    for identifier in identifiers:
        if not identifier:
            continue
            
        # Check for P-series patterns (like P441J1M0)
        if p_series_pattern.search(identifier):
            patterns['P_series'].append(identifier)
        
        # Check for alphanumeric patterns
        if re.search(r'[A-Z].*\d.*[A-Z]', identifier, re.IGNORECASE):
            patterns['alphanumeric'].append(identifier)
        
        # Check for dots (configuration separators)
        if '.' in identifier:
            patterns['with_dots'].append(identifier)
        
        # Check for longer codes (potential CORTEC)
        if (len(identifier) >= 6 and 
                re.search(r'[A-Z].*\d', identifier, re.IGNORECASE)):
            patterns['long_codes'].append(identifier)
    
    # Report findings
    for pattern_type, products in patterns.items():
        if products:
            logger.info(f"\n   📊 {pattern_type.upper()} patterns "
                        f"({len(products)} found):")
            # Show unique patterns
            unique_patterns = list(set(products))[:10]  # Show first 10 unique
            for pattern in unique_patterns:
                logger.info(f"      🔹 {pattern}")
    
    # Extract potential CORTEC codes
    potential_cortec = []
    for identifier in identifiers:
        if identifier and len(identifier) >= 5:
            # Look for patterns like P441J1M0
            if re.match(r'P\d{3}[A-Z]\d[A-Z]\d', identifier, re.IGNORECASE):
                potential_cortec.append(identifier)
    
    if potential_cortec:
        logger.info(f"\n   🎯 POTENTIAL CORTEC CODES "
                    f"({len(potential_cortec)} found):")
        for code in potential_cortec[:10]:
            logger.info(f"      🔸 {code}")
            # Try to decode based on CORTEC guide
            decode_cortec_attempt(code)


def decode_cortec_attempt(code: str):
    """Attempt to decode a potential CORTEC code based on the guide"""
    if len(code) < 5:
        return
    
    try:
        # Extract components based on typical CORTEC structure
        model = code[:4]  # First 4 characters (e.g., P441)
        
        if len(code) >= 5:
            design_suffix = code[4]  # 5th character (e.g., J)
        
        if len(code) >= 6:
            input_config = code[5]  # 6th character (e.g., 1)
        
        if len(code) >= 7:
            hardware = code[6]  # 7th character (e.g., M)
        
        if len(code) >= 8:
            comm_lang = code[7]  # 8th character (e.g., 0)
        
        design_val = design_suffix if 'design_suffix' in locals() else '?'
        input_val = input_config if 'input_config' in locals() else '?'
        mount_val = hardware if 'hardware' in locals() else '?'
        comm_val = comm_lang if 'comm_lang' in locals() else '?'
        
        logger.info(f"         Decoded: Model={model}, "
                    f"Design={design_val}, Input={input_val}, "
                    f"Mount={mount_val}, Comm={comm_val}")
        
    except Exception as e:
        logger.info(f"         Decode failed: {e}")


if __name__ == "__main__":
    analyze_micom_products() 