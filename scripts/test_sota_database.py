#!/usr/bin/env python3
"""
SOTA Product Database Test Script
Quick verification and performance demonstration of the new DuckDB product database
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import duckdb
from loguru import logger


def test_sota_database():
    """Test the SOTA product database"""
    logger.info("🚀 Testing SOTA Product Database")
    
    db_path = "data/IBcatalogue.duckdb"
    
    if not Path(db_path).exists():
        logger.error(f"❌ Database not found: {db_path}")
        return False
    
    logger.info(f"📊 Database: {db_path}")
    file_size_mb = Path(db_path).stat().st_size / 1024 / 1024
    logger.info(f"💾 Size: {file_size_mb:.1f} MB")
    
    with duckdb.connect(db_path) as conn:
        # Test 1: Basic connectivity and record count
        logger.info("\n🔍 Test 1: Basic Connectivity")
        start_time = time.time()
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        test1_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Total products: {total_products:,} (Query time: {test1_time:.2f}ms)")
        
        # Test 2: Galaxy 6000 range lookup (exact match)
        logger.info("\n🔍 Test 2: Galaxy 6000 Range Lookup")
        start_time = time.time()
        galaxy_products = conn.execute("""
            SELECT COUNT(*) FROM products 
            WHERE range_label = 'Galaxy 6000'
        """).fetchone()[0]
        test2_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Galaxy 6000 products: {galaxy_products} (Query time: {test2_time:.2f}ms)")
        
        # Test 3: Complex multi-field search
        logger.info("\n🔍 Test 3: Complex Multi-field Search")
        start_time = time.time()
        complex_results = conn.execute("""
            SELECT COUNT(*) FROM products 
            WHERE range_label_norm LIKE '%GALAXY%' 
            AND brand_label_norm LIKE '%SCHNEIDER%'
            AND commercial_status NOT IN ('18-End of commercialisation')
        """).fetchone()[0]
        test3_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Complex search results: {complex_results} (Query time: {test3_time:.2f}ms)")
        
        # Test 4: PL Services distribution
        logger.info("\n🔍 Test 4: PL Services Distribution")
        start_time = time.time()
        pl_services = conn.execute("""
            SELECT pl_services, COUNT(*) as count
            FROM products 
            WHERE pl_services != '' AND pl_services IS NOT NULL
            GROUP BY pl_services 
            ORDER BY count DESC
            LIMIT 5
        """).fetchall()
        test4_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Top PL Services: (Query time: {test4_time:.2f}ms)")
        for service, count in pl_services:
            logger.info(f"   - {service}: {count:,} products")
        
        # Test 5: Range analysis
        logger.info("\n🔍 Test 5: Range Analysis")
        start_time = time.time()
        range_stats = conn.execute("""
            SELECT 
                COUNT(DISTINCT range_label) as total_ranges,
                COUNT(DISTINCT subrange_label) as total_subranges,
                COUNT(DISTINCT brand_label) as total_brands,
                AVG(CASE WHEN is_schneider_brand = true THEN 1.0 ELSE 0.0 END) * 100 as schneider_pct
            FROM products 
            WHERE range_label != ''
        """).fetchone()
        test5_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Database Statistics: (Query time: {test5_time:.2f}ms)")
        logger.info(f"   - Total Ranges: {range_stats[0]:,}")
        logger.info(f"   - Total Subranges: {range_stats[1]:,}")
        logger.info(f"   - Total Brands: {range_stats[2]:,}")
        logger.info(f"   - Schneider Products: {range_stats[3]:.1f}%")
        
        # Test 6: Index performance verification
        logger.info("\n🔍 Test 6: Index Performance Verification")
        start_time = time.time()
        index_count = conn.execute("""
            SELECT COUNT(*) FROM duckdb_indexes() 
            WHERE table_name = 'products'
        """).fetchone()[0]
        test6_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Performance indexes: {index_count} (Query time: {test6_time:.2f}ms)")
        
        # Test 7: Sample data quality
        logger.info("\n🔍 Test 7: Sample Galaxy 6000 Products")
        start_time = time.time()
        galaxy_samples = conn.execute("""
            SELECT product_identifier, range_label, subrange_label, brand_label, commercial_status
            FROM products 
            WHERE range_label = 'Galaxy 6000'
            ORDER BY product_identifier
            LIMIT 3
        """).fetchall()
        test7_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Sample products: (Query time: {test7_time:.2f}ms)")
        for product in galaxy_samples:
            logger.info(f"   - {product[0]} | {product[1]} | {product[2]} | {product[3]} | {product[4]}")
        
        # Performance Summary
        avg_query_time = (test1_time + test2_time + test3_time + test4_time + test5_time + test6_time + test7_time) / 7
        logger.info(f"\n📈 Performance Summary:")
        logger.info(f"   - Average Query Time: {avg_query_time:.2f}ms")
        logger.info(f"   - Fastest Query: {min(test1_time, test2_time, test3_time, test4_time, test5_time, test6_time, test7_time):.2f}ms")
        logger.info(f"   - Database Size: {file_size_mb:.1f} MB")
        logger.info(f"   - Products: {total_products:,}")
        
        if avg_query_time < 10:  # Sub-10ms average
            logger.info("🚀 PERFORMANCE: EXCELLENT (Sub-10ms average)")
        elif avg_query_time < 100:  # Sub-100ms average
            logger.info("✅ PERFORMANCE: GOOD (Sub-100ms average)")
        else:
            logger.info("⚠️ PERFORMANCE: ACCEPTABLE (>100ms average)")
    
    logger.info("\n🎉 SOTA Product Database Test Completed Successfully!")
    return True


if __name__ == "__main__":
    success = test_sota_database()
    if not success:
        sys.exit(1) 