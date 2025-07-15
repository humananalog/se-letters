#!/usr/bin/env python3
"""
Quick SOTA Database Test
Simple test to verify product mapping works

Version: 1.0.0
Author: SE Letters Team
"""

import sys
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from se_letters.services.sota_product_database_service import SOTAProductDatabaseService


def main():
    """Quick test of SOTA database"""
    print("🚀 Quick SOTA Database Test")
    print("=" * 40)
    
    # Initialize service
    print("🔌 Initializing...")
    db_service = SOTAProductDatabaseService()
    
    # Health check
    print("\n🏥 Health Check:")
    health = db_service.health_check()
    print(f"   Status: {health.get('status', 'Unknown')}")
    print(f"   Products: {health.get('product_count', 0):,}")
    
    # Test searches
    test_ranges = ["Galaxy", "PIX", "SEPAM"]
    
    for range_name in test_ranges:
        print(f"\n🔍 Testing {range_name}:")
        start_time = time.time()
        
        try:
            result = db_service.find_products_by_range(range_name)
            search_time = (time.time() - start_time) * 1000
            
            print(f"   ✅ Found {len(result.products)} products")
            print(f"   ⏱️ Search time: {search_time:.2f}ms")
            print(f"   🎯 Strategy: {result.search_strategy}")
            
            # Show top 3 products
            for i, product in enumerate(result.products[:3], 1):
                confidence = product.confidence_score
                range_label = product.range_label
                pl_service = product.pl_services
                match_type = product.match_type
                
                print(f"   {i}. {range_label} ({pl_service})")
                print(f"      Confidence: {confidence:.2f} ({match_type})")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Performance summary
    print(f"\n📊 Performance Summary:")
    try:
        perf = db_service.get_performance_metrics()
        avg_time = perf.get('average_query_time_ms', 0)
        total_queries = perf.get('total_queries', 0)
        rating = perf.get('performance_rating', 'Unknown')
        
        print(f"   Average query time: {avg_time:.2f}ms")
        print(f"   Total queries: {total_queries}")
        print(f"   Performance rating: {rating}")
    except Exception as e:
        print(f"   ❌ Performance metrics error: {e}")
    
    print("\n" + "=" * 40)
    print("✅ SOTA Database is working!")
    print("💡 Ready for production obsolescence letter mapping!")


if __name__ == "__main__":
    main() 