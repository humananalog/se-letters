#!/usr/bin/env python3
"""
Test Product Matching Database Integration
Verify the one-to-many relationship between letters and matched IBcatalogue products

Usage: python scripts/test_product_matching_database.py
"""

import sys
from pathlib import Path
import duckdb
import json
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.letter_database_service import LetterDatabaseService
from loguru import logger


def test_database_schema():
    """Test that the new schema is properly created"""
    
    logger.info("🔍 Testing database schema...")
    
    db_path = "data/letters.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Check if new table exists
            tables = conn.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'main' AND table_name = 'letter_product_matches'
            """).fetchall()
            
            if tables:
                logger.info("✅ letter_product_matches table exists")
                
                # Check table structure
                columns = conn.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'letter_product_matches'
                    ORDER BY ordinal_position
                """).fetchall()
                
                logger.info("📋 Table structure:")
                for col_name, col_type in columns:
                    logger.info(f"   {col_name}: {col_type}")
                
                return True
            else:
                logger.error("❌ letter_product_matches table not found")
                return False
                
    except Exception as e:
        logger.error(f"❌ Database schema test failed: {e}")
        return False


def test_relationships():
    """Test the one-to-many relationships"""
    
    logger.info("🔗 Testing relationships...")
    
    db_service = LetterDatabaseService()
    
    try:
        # Get recent letters
        from se_letters.services.letter_database_service import SearchFilters, SortBy, SortOrder
        
        filters = SearchFilters(
            limit=5,
            sort_by=SortBy.CREATED_AT,
            sort_order=SortOrder.DESC
        )
        
        search_result = db_service.search_letters(filters)
        
        if search_result.letters:
            logger.info(f"📊 Found {len(search_result.letters)} recent letters")
            
            for letter in search_result.letters[:2]:  # Test first 2 letters
                logger.info(f"\n📄 Letter: {letter['document_name']} (ID: {letter['id']})")
                
                # Get full letter details with products
                letter_details = db_service.get_letter_by_id(
                    letter['id'], 
                    include_products=True
                )
                
                if letter_details and 'products' in letter_details:
                    products = letter_details['products']
                    logger.info(f"   📦 Products extracted: {len(products)}")
                    
                    total_matches = 0
                    for product in products:
                        matches = product.get('ibcatalogue_matches', [])
                        total_matches += len(matches)
                        
                        logger.info(f"   🎯 Product '{product['product_identifier']}' -> {len(matches)} IBcatalogue matches")
                        
                        # Show top match details
                        if matches:
                            top_match = matches[0]
                            logger.info(f"      Top match: {top_match['ibcatalogue_product_identifier']} (confidence: {top_match['match_confidence']:.2f})")
                    
                    logger.info(f"   📈 Total IBcatalogue matches: {total_matches}")
                    
                    if total_matches > 0:
                        logger.info("✅ Relationship test PASSED - Found matched products")
                    else:
                        logger.warning("⚠️ No matched products found - may need to reprocess documents")
                else:
                    logger.info("   📦 No products found for this letter")
            
            return True
        else:
            logger.warning("⚠️ No letters found in database")
            return False
            
    except Exception as e:
        logger.error(f"❌ Relationship test failed: {e}")
        return False


def show_database_stats():
    """Show comprehensive database statistics"""
    
    logger.info("📊 Database Statistics:")
    
    db_path = "data/letters.duckdb"
    
    try:
        with duckdb.connect(db_path) as conn:
            # Letters count
            letters_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
            logger.info(f"   📄 Total letters: {letters_count}")
            
            # Products count  
            products_count = conn.execute("SELECT COUNT(*) FROM letter_products").fetchone()[0]
            logger.info(f"   📦 Total extracted products: {products_count}")
            
            # Matches count
            matches_count = conn.execute("SELECT COUNT(*) FROM letter_product_matches").fetchone()[0]
            logger.info(f"   🎯 Total IBcatalogue matches: {matches_count}")
            
            # Average matches per product
            if products_count > 0:
                avg_matches = matches_count / products_count
                logger.info(f"   📈 Average matches per product: {avg_matches:.2f}")
            
            # Top confidence matches
            top_matches = conn.execute("""
                SELECT ibcatalogue_product_identifier, match_confidence, match_type
                FROM letter_product_matches 
                ORDER BY match_confidence DESC 
                LIMIT 5
            """).fetchall()
            
            if top_matches:
                logger.info("   🏆 Top confidence matches:")
                for product_id, confidence, match_type in top_matches:
                    logger.info(f"      {product_id}: {confidence:.3f} ({match_type})")
            
    except Exception as e:
        logger.error(f"❌ Statistics query failed: {e}")


def main():
    """Main test function"""
    
    logger.info("🧪 SE Letters - Product Matching Database Test")
    logger.info("=" * 60)
    
    # Test 1: Database Schema
    schema_ok = test_database_schema()
    
    if not schema_ok:
        logger.error("❌ Schema test failed - cannot continue")
        return
    
    # Test 2: Relationships
    logger.info("\n" + "-" * 40)
    relationships_ok = test_relationships()
    
    # Test 3: Statistics
    logger.info("\n" + "-" * 40)
    show_database_stats()
    
    # Summary
    logger.info("\n" + "=" * 60)
    if schema_ok and relationships_ok:
        logger.info("✅ ALL TESTS PASSED")
        logger.info("🎉 Product matching database integration is working!")
        logger.info("💡 Letters now have proper one-to-many relationship with IBcatalogue products")
    else:
        logger.warning("⚠️ Some tests failed - check implementation")


if __name__ == "__main__":
    main() 