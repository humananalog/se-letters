#!/usr/bin/env python3
"""
Simple test script for Enhanced Vector Search Engine
Tests basic functionality and generates gap analysis report
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))


def test_enhanced_vector_search():
    """Test enhanced vector search engine functionality"""
    print("🚀 TESTING ENHANCED VECTOR SEARCH ENGINE")
    print("=" * 60)
    
    try:
        from se_letters.services.enhanced_vector_search_engine import (
            EnhancedVectorSearchEngine
        )
        
        # Initialize engine
        engine = EnhancedVectorSearchEngine()
        print("✅ Engine initialized successfully")
        
        # Test database connection
        engine.connect_database()
        print("✅ Database connected successfully")
        
        # Test hierarchy analysis
        print("\n🔍 Running hierarchy analysis...")
        hierarchy = engine.analyze_product_hierarchy()
        pl_count = len(hierarchy['pl_services_distribution'])
        print(f"✅ Analyzed {pl_count} PL services")
        
        # Show PPIBS stats
        ppibs_data = hierarchy['pl_services_distribution'].get('PPIBS', {})
        print(f"📊 PPIBS: {ppibs_data.get('product_count', 0):,} products")
        
        # Test coverage analysis
        print("\n📊 Running coverage analysis...")
        coverage = engine.analyze_letter_coverage()
        print(f"✅ Coverage: {coverage.coverage_percentage:.1f}%")
        print(f"📈 Missing ranges: {len(coverage.missing_ranges)}")
        
        # Generate report
        print("\n📋 Generating gap analysis report...")
        report_path = engine.generate_gap_analysis_report()
        print(f"✅ Report saved: {report_path}")
        
        print("\n🎉 ALL TESTS PASSED!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    finally:
        if 'engine' in locals() and engine.conn:
            engine.conn.close()


if __name__ == "__main__":
    exit(test_enhanced_vector_search()) 