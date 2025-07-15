#!/usr/bin/env python3
"""
Debug Galaxy Search Issue
Investigate why Galaxy 6000 search returns Galaxy 300 products

Author: SE Letters Team
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import duckdb
from se_letters.services.sota_product_database_service import SOTAProductDatabaseService

def main():
    """Debug Galaxy search results"""
    print("🔍 DEBUGGING GALAXY SEARCH ISSUE")
    print("=" * 50)
    
    # Connect to database directly
    conn = duckdb.connect('data/IBcatalogue.duckdb')
    
    print("1️⃣ ALL Galaxy product ranges:")
    result = conn.execute("""
        SELECT DISTINCT range_label, COUNT(*) as count
        FROM products 
        WHERE range_label ILIKE '%galaxy%'
        GROUP BY range_label
        ORDER BY count DESC
    """).fetchall()
    
    for row in result:
        print(f"   📦 {row[0]}: {row[1]} products")
    
    print(f"\n2️⃣ Searching for Galaxy 6000 specifically:")
    result = conn.execute("""
        SELECT product_identifier, range_label, subrange_label, product_description
        FROM products 
        WHERE (product_identifier ILIKE '%galaxy%6000%' OR 
               range_label ILIKE '%galaxy%6000%' OR
               subrange_label ILIKE '%6000%' OR
               product_description ILIKE '%galaxy%6000%')
        LIMIT 20
    """).fetchall()
    
    print(f"   Found {len(result)} Galaxy 6000 products:")
    for row in result:
        print(f"   🆔 {row[0]} | {row[1]} | {row[2]} | {row[3][:50]}...")
    
    print(f"\n3️⃣ Searching for any products with '6000':")
    result = conn.execute("""
        SELECT product_identifier, range_label, subrange_label, product_description
        FROM products 
        WHERE (product_identifier ILIKE '%6000%' OR 
               range_label ILIKE '%6000%' OR
               subrange_label ILIKE '%6000%' OR
               product_description ILIKE '%6000%')
        AND range_label ILIKE '%galaxy%'
        LIMIT 20
    """).fetchall()
    
    print(f"   Found {len(result)} products with 6000 in Galaxy range:")
    for row in result:
        print(f"   🆔 {row[0]} | {row[1]} | {row[2]} | {row[3][:50]}...")
    
    print(f"\n4️⃣ Testing SOTA service search:")
    sota_service = SOTAProductDatabaseService()
    
    # Test different search terms
    search_terms = ["Galaxy 6000", "Galaxy", "6000"]
    
    for term in search_terms:
        print(f"\n   🔍 Searching for: '{term}'")
        result = sota_service.search_products_semantic(term, limit=5)
        print(f"   📊 Found: {len(result.products)} products")
        for i, product in enumerate(result.products[:3], 1):
            print(f"   {i}. {product.product_identifier} | {product.range_label} | {product.subrange_label}")
    
    conn.close()
    
    print(f"\n🎯 ANALYSIS:")
    print("The search algorithm needs to be more precise!")
    print("It should prioritize exact matches and subrange specificity.")

if __name__ == "__main__":
    main() 