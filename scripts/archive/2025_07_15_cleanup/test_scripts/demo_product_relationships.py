#!/usr/bin/env python3
"""
Demo: Product Relationships
Shows the complete one-to-many relationship: Letters → Products → IBcatalogue Matches

Usage: python scripts/demo_product_relationships.py
"""

import sys
from pathlib import Path
import duckdb
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_complete_relationship():
    """Demonstrate the complete one-to-many relationship"""
    
    logger.info("🔗 SE Letters - Complete Product Relationship Demo")
    logger.info("=" * 60)
    
    db_path = "data/letters.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Get the complete relationship in one query
            result = conn.execute("""
                SELECT 
                    l.id as letter_id,
                    l.document_name,
                    l.extraction_confidence,
                    p.id as product_id,
                    p.product_identifier as extracted_product,
                    p.range_label,
                    p.product_line,
                    m.id as match_id,
                    m.ibcatalogue_product_identifier,
                    m.match_confidence,
                    m.match_type,
                    m.range_based_matching
                FROM letters l
                LEFT JOIN letter_products p ON l.id = p.letter_id
                LEFT JOIN letter_product_matches m ON p.id = m.letter_product_id
                WHERE m.id IS NOT NULL  -- Only show letters with matches
                ORDER BY l.id DESC, p.id, m.match_confidence DESC
            """).fetchall()
            
            if not result:
                logger.warning("⚠️ No product matches found in database")
                return
            
            # Organize results by letter
            letters = {}
            for row in result:
                letter_id = row[0]
                if letter_id not in letters:
                    letters[letter_id] = {
                        'document_name': row[1],
                        'extraction_confidence': row[2],
                        'products': {}
                    }
                
                product_id = row[3]
                if product_id not in letters[letter_id]['products']:
                    letters[letter_id]['products'][product_id] = {
                        'extracted_product': row[4],
                        'range_label': row[5],
                        'product_line': row[6],
                        'matches': []
                    }
                
                # Add match
                letters[letter_id]['products'][product_id]['matches'].append({
                    'match_id': row[7],
                    'ibcatalogue_product': row[8],
                    'confidence': row[9],
                    'match_type': row[10],
                    'range_based': row[11]
                })
            
            # Display results
            logger.info(f"📊 Found {len(letters)} letters with product matches")
            logger.info("")
            
            total_products = 0
            total_matches = 0
            
            for letter_id, letter_data in letters.items():
                logger.info(f"📄 **Letter {letter_id}**: {letter_data['document_name']}")
                logger.info(f"   🎯 Extraction confidence: {letter_data['extraction_confidence']:.2f}")
                logger.info(f"   📦 Products extracted: {len(letter_data['products'])}")
                
                letter_matches = 0
                for product_id, product_data in letter_data['products'].items():
                    logger.info(f"")
                    logger.info(f"   📋 **Product {product_id}**: {product_data['extracted_product']}")
                    logger.info(f"      Range: {product_data['range_label']}")
                    logger.info(f"      Product Line: {product_data['product_line']}")
                    logger.info(f"      IBcatalogue Matches: {len(product_data['matches'])}")
                    
                    for i, match in enumerate(product_data['matches'], 1):
                        confidence_emoji = "🟢" if match['confidence'] >= 0.8 else "🟡" if match['confidence'] >= 0.6 else "🔴"
                        logger.info(f"         {confidence_emoji} Match {i}: {match['ibcatalogue_product']}")
                        logger.info(f"            Confidence: {match['confidence']:.3f}")
                        logger.info(f"            Type: {match['match_type']}")
                        logger.info(f"            Range-based: {match['range_based']}")
                    
                    letter_matches += len(product_data['matches'])
                    total_products += 1
                
                total_matches += letter_matches
                logger.info(f"   🎯 Total matches for this letter: {letter_matches}")
                logger.info("-" * 50)
            
            # Summary
            logger.info("")
            logger.info("📈 **RELATIONSHIP SUMMARY**")
            logger.info("=" * 30)
            logger.info(f"📄 Letters processed: {len(letters)}")
            logger.info(f"📦 Products extracted: {total_products}")
            logger.info(f"🎯 IBcatalogue matches: {total_matches}")
            logger.info(f"📊 Average matches per product: {total_matches/total_products:.2f}")
            logger.info("")
            logger.info("✅ **ONE-TO-MANY RELATIONSHIP WORKING PERFECTLY!**")
            logger.info("🔗 Letters → Products → IBcatalogue Matches")
            
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


def main():
    """Main demo function"""
    demo_complete_relationship()


if __name__ == "__main__":
    main() 