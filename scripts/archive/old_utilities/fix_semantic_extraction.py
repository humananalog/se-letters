#!/usr/bin/env python3
"""
Fix for Semantic Extraction - Proper Range Validation and Product Counting
Demonstrates the correct approach to avoid the 918,855 product counting error
"""

import duckdb
from typing import List, Dict, Any, Set

def get_valid_ranges_from_db(conn) -> Set[str]:
    """Get all valid product ranges from the database"""
    query = "SELECT DISTINCT RANGE_LABEL FROM products WHERE RANGE_LABEL IS NOT NULL"
    result = conn.execute(query).fetchall()
    return set(r[0] for r in result)

def get_obsolete_statuses() -> List[str]:
    """Get the correct obsolete status codes"""
    return [
        '18-End of commercialisation',
        '19-end of commercialization block', 
        '14-End of commerc. announced',
        '20-Temporary block'
    ]

def validate_and_filter_ranges(extracted_ranges: List[str], valid_ranges: Set[str]) -> List[str]:
    """Validate extracted ranges against database and filter out invalid ones"""
    valid_extracted = []
    invalid_extracted = []
    
    for range_name in extracted_ranges:
        # Check exact match
        if range_name in valid_ranges:
            valid_extracted.append(range_name)
        # Check if it's a substring of any valid range
        elif any(range_name.upper() in valid_range.upper() for valid_range in valid_ranges):
            # Find the matching valid range
            for valid_range in valid_ranges:
                if range_name.upper() in valid_range.upper():
                    if valid_range not in valid_extracted:
                        valid_extracted.append(valid_range)
                    break
        else:
            invalid_extracted.append(range_name)
    
    print(f"✅ Valid ranges found: {len(valid_extracted)} - {valid_extracted}")
    print(f"❌ Invalid ranges filtered out: {len(invalid_extracted)} - {invalid_extracted[:10]}...")
    
    return valid_extracted

def count_obsolete_products_correctly(conn, ranges: List[str]) -> Dict[str, Any]:
    """Count obsolete products correctly with proper validation"""
    if not ranges:
        return {"total_products": 0, "ranges_found": [], "breakdown": {}}
    
    obsolete_statuses = get_obsolete_statuses()
    
    # Build proper query with validation
    range_placeholders = ','.join(['?' for _ in ranges])
    status_placeholders = ','.join(['?' for _ in obsolete_statuses])
    
    query = f"""
    SELECT 
        RANGE_LABEL,
        COUNT(DISTINCT PRODUCT_IDENTIFIER) as product_count,
        COUNT(DISTINCT CASE WHEN COMMERCIAL_STATUS IN ({status_placeholders}) THEN PRODUCT_IDENTIFIER END) as obsolete_count
    FROM products 
    WHERE RANGE_LABEL IN ({range_placeholders})
    GROUP BY RANGE_LABEL
    ORDER BY obsolete_count DESC
    """
    
    params = ranges + obsolete_statuses
    result = conn.execute(query, params).fetchall()
    
    breakdown = {}
    total_obsolete = 0
    ranges_found = []
    
    for range_label, total_count, obsolete_count in result:
        if obsolete_count > 0:  # Only count ranges with obsolete products
            breakdown[range_label] = {
                "total_products": total_count,
                "obsolete_products": obsolete_count,
                "active_products": total_count - obsolete_count
            }
            total_obsolete += obsolete_count
            ranges_found.append(range_label)
    
    return {
        "total_obsolete_products": total_obsolete,
        "ranges_with_obsolete_products": ranges_found,
        "breakdown": breakdown
    }

def main():
    """Demonstrate the correct approach"""
    print("🔧 FIXING SEMANTIC EXTRACTION ISSUES")
    print("=" * 80)
    
    # Connect to database
    conn = duckdb.connect('data/IBcatalogue.duckdb')
    
    # Get valid ranges from database
    print("📊 Loading valid ranges from database...")
    valid_ranges = get_valid_ranges_from_db(conn)
    print(f"✅ Found {len(valid_ranges)} valid ranges in database")
    
    # Get obsolete status counts
    obsolete_statuses = get_obsolete_statuses()
    total_obsolete = conn.execute(
        f"SELECT COUNT(*) FROM products WHERE COMMERCIAL_STATUS IN ({','.join(['?' for _ in obsolete_statuses])})",
        obsolete_statuses
    ).fetchone()[0]
    print(f"✅ Total obsolete products in database: {total_obsolete:,}")
    
    # Example: The problematic extracted ranges from the semantic pipeline
    problematic_extracted = [
        'Custom', 'Masterpact NT', 'ID', 'Masterpact M', 'CT', 'A', 'Micrologic', 'DS', 
        'RED', 'Unica', 'WI', 'SEL', 'F', 'DA', 'AK', 'RL', 'K', 'GI', 'CO', 'R range', 
        'GL', 'L', 'PI', 'RT', 'SCU', 'Fit', 'SC', 'ME', 'B-Control', 'AS', 'PAC', 'LA', 
        'J', 'RET', 'MM', 'VA', 'SION', 'OSA', 'AL', 'CB', 'CH', 'RK', 'E', 'NDS', 'CE-B', 
        'T', 'BS', 'CC', 'DL', 'STI', 'APP', 'OR', 'ITH', 'FR', 'MA', 'CS', 'C', 'REC', 
        'RAD', 'CR', 'G', 'FA', 'UA', 'M I', 'D', 'S Range', 'HN', 'IL', 'NE', 'CL', 
        'L Series', 'REA', 'GE', 'HAR', 'LOS', 'M', 'MIC', 'CBS', 'Master', 'CI', 'IS', 
        'HAT', 'DU', 'FE', 'PE', 'S', 'RIT', 'AC', 'LS', 'PL', 'SP', 'CA', 'AV', 'BR', 
        'HE', 'OB', 'STE', 'P', 'PA', 'spe'
    ]
    
    print(f"\n❌ PROBLEMATIC: Semantic extraction found {len(problematic_extracted)} ranges")
    
    # Validate and filter ranges
    print("\n🔍 Validating extracted ranges against database...")
    valid_extracted = validate_and_filter_ranges(problematic_extracted, valid_ranges)
    
    # Count products correctly
    print(f"\n📊 Counting obsolete products for {len(valid_extracted)} valid ranges...")
    result = count_obsolete_products_correctly(conn, valid_extracted)
    
    print(f"\n✅ CORRECT RESULTS:")
    print(f"🎯 Total obsolete products found: {result['total_obsolete_products']:,}")
    print(f"📋 Ranges with obsolete products: {len(result['ranges_with_obsolete_products'])}")
    print(f"📊 Breakdown:")
    
    for range_name, stats in result['breakdown'].items():
        print(f"  • {range_name}: {stats['obsolete_products']:,} obsolete, {stats['active_products']:,} active")
    
    # Show the difference
    print(f"\n🚨 COMPARISON:")
    print(f"❌ Semantic pipeline reported: 918,855 products (WRONG)")
    print(f"✅ Correct count should be: {result['total_obsolete_products']:,} products")
    print(f"🔥 Error magnitude: {918855 / max(result['total_obsolete_products'], 1):.1f}x overcounting")
    
    conn.close()

if __name__ == "__main__":
    main() 