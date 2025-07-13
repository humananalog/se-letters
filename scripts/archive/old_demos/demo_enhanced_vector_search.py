#!/usr/bin/env python3
"""
Enhanced Vector Search Engine Demo
Demonstrates hierarchical vector spaces, PPIBS gap analysis, and intelligent
product-to-letter mapping
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.services.enhanced_vector_search_engine import (
    EnhancedVectorSearchEngine
)


def demo_hierarchy_analysis():
    """Demonstrate product hierarchy analysis"""
    print("\n🌳 PRODUCT HIERARCHY ANALYSIS DEMO")
    print("=" * 60)
    
    engine = EnhancedVectorSearchEngine()
    
    try:
        engine.connect_database()
        engine.analyze_product_hierarchy()
        
        print("\n📊 PL_SERVICES DISTRIBUTION:")
        print("-" * 40)
        for pl_service, data in engine.pl_services_distribution.items():
            print(f"{pl_service:<15}: {data['product_count']:>8,} products "
                  f"({data['obsolescence_rate']:>5.1f}% obsolete)")
        
        print("\n🎯 PPIBS ANALYSIS (Top 10 Ranges):")
        print("-" * 50)
        for i, range_data in enumerate(engine.ppibs_gap_analysis['top_ranges'][:10]):
            print(f"{i+1:2d}. {range_data['range_label']:<30} "
                  f"{range_data['product_count']:>6,} products")
        
        print(f"\n✅ Hierarchy analysis complete: "
              f"{len(engine.pl_services_distribution)} PL services analyzed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if engine.conn:
            engine.conn.close()


def demo_vector_spaces():
    """Demonstrate hierarchical vector space creation"""
    print("\n🔍 HIERARCHICAL VECTOR SPACES DEMO")
    print("=" * 60)
    
    engine = EnhancedVectorSearchEngine()
    
    try:
        engine.connect_database()
        engine.analyze_product_hierarchy()
        
        print("🚀 Building hierarchical vector spaces...")
        vector_spaces = engine.build_hierarchical_vector_spaces()
        
        print(f"\n📊 VECTOR SPACES CREATED ({vector_spaces['total_spaces']} total):")
        print("-" * 60)
        
        for space_name in vector_spaces['spaces_created']:
            space_data = engine.hierarchical_indices[space_name]
            print(f"{space_name:<35}: {space_data['size']:>6,} products, {space_data['n_clusters']:>3} clusters")
        
        print("\n✅ Vector spaces built successfully!")
        print(f"📏 Embedding dimension: {vector_spaces['embedding_dimension']}")
        print(f"🔢 Total products embedded: "
              f"{vector_spaces['total_products_embedded']:,}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if engine.conn:
            engine.conn.close()


def demo_enhanced_search():
    """Demonstrate enhanced search capabilities"""
    print("\n🔍 ENHANCED SEARCH DEMO")
    print("=" * 60)
    
    engine = EnhancedVectorSearchEngine()
    
    try:
        engine.connect_database()
        engine.analyze_product_hierarchy()
        engine.build_hierarchical_vector_spaces()
        
        # Demo queries
        demo_queries = [
            ("TeSys D contactor 9A", "hierarchical"),
            ("PIX switchgear medium voltage", "ppibs_focused"),
            ("Galaxy UPS power supply", "hybrid"),
            ("Compact circuit breaker NSX", "hierarchical")
        ]
        
        print("🔍 SEARCH DEMONSTRATIONS:")
        print("-" * 50)
        
        for query, strategy in demo_queries:
            print(f"\n📝 Query: '{query}' (Strategy: {strategy})")
            print("-" * 40)
            
            start_time = time.time()
            results = engine.enhanced_search(query, top_k=5, search_strategy=strategy)
            search_time = time.time() - start_time
            
            print(f"⏱️  Search time: {search_time:.3f}s")
            print(f"📊 Results: {len(results)}")
            
            for i, result in enumerate(results[:3]):
                print(f"{i+1}. {result.range_label} - {result.description[:50]}...")
                print(f"   Score: {result.similarity_score:.3f} | Confidence: {result.confidence_level}")
                print(f"   Status: {result.commercial_status} | PL: {result.pl_services}")
        
        print(f"\n✅ Enhanced search demo complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if engine.conn:
            engine.conn.close()


def demo_gap_analysis():
    """Demonstrate letter coverage gap analysis"""
    print("\n📊 LETTER COVERAGE GAP ANALYSIS DEMO")
    print("=" * 60)
    
    engine = EnhancedVectorSearchEngine()
    
    try:
        engine.connect_database()
        engine.analyze_product_hierarchy()
        
        print("🔍 Analyzing letter coverage across product database...")
        coverage = engine.analyze_letter_coverage()
        
        print(f"\n📈 COVERAGE STATISTICS:")
        print("-" * 40)
        print(f"Total Products:     {coverage.total_products:>10,}")
        print(f"Covered Products:   {coverage.covered_products:>10,}")
        print(f"Uncovered Products: {coverage.uncovered_products:>10,}")
        print(f"Coverage Percentage: {coverage.coverage_percentage:>9.1f}%")
        print(f"Missing Ranges:     {len(coverage.missing_ranges):>10,}")
        
        print(f"\n🚨 PPIBS GAP ANALYSIS:")
        print("-" * 40)
        ppibs_gap = coverage.ppibs_gap_analysis
        print(f"Total PPIBS Ranges:     {ppibs_gap['total_ppibs_ranges']:>6,}")
        print(f"Covered PPIBS Ranges:   {ppibs_gap['covered_ppibs_ranges']:>6,}")
        print(f"PPIBS Coverage:         {ppibs_gap['ppibs_coverage_percentage']:>6.1f}%")
        
        print(f"\n🎯 TOP PRIORITY GAPS (Top 10):")
        print("-" * 50)
        for i, gap in enumerate(coverage.priority_gaps[:10]):
            print(f"{i+1:2d}. {gap['range_label']:<30} {gap['product_count']:>6,} products ({gap['pl_services']})")
        
        print(f"\n✅ Gap analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if engine.conn:
            engine.conn.close()


def demo_complete_analysis():
    """Demonstrate complete enhanced vector search analysis"""
    print("\n🚀 COMPLETE ENHANCED VECTOR SEARCH ANALYSIS")
    print("=" * 80)
    
    engine = EnhancedVectorSearchEngine()
    
    try:
        print("🔄 Running complete analysis...")
        results = engine.run_complete_analysis()
        
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"⏱️  Total time: {results['analysis_time']:.2f}s")
        print(f"📊 Vector spaces: {results['vector_spaces']['total_spaces']}")
        print(f"📋 Report: {results['report_path']}")
        
        # Show key insights
        hierarchy = results['hierarchy_analysis']
        coverage = results['coverage_analysis']
        
        print(f"\n📈 KEY INSIGHTS:")
        print("-" * 40)
        print(f"• PL Services analyzed: {len(hierarchy['pl_services_distribution'])}")
        print(f"• PPIBS products: {hierarchy['pl_services_distribution']['PPIBS']['product_count']:,}")
        print(f"• Coverage percentage: {coverage.coverage_percentage:.1f}%")
        print(f"• Priority gaps identified: {len(coverage.priority_gaps)}")
        
        print(f"\n🔍 SEARCH PERFORMANCE:")
        print("-" * 40)
        perf = results['performance_metrics']
        print(f"• Total searches: {perf['total_searches']}")
        print(f"• Average search time: {perf['avg_search_time']:.3f}s")
        
        print(f"\n✅ Complete analysis demonstration successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def main():
    """Main demo function"""
    print("🚀 ENHANCED VECTOR SEARCH ENGINE DEMONSTRATION")
    print("=" * 80)
    
    demos = [
        ("Product Hierarchy Analysis", demo_hierarchy_analysis),
        ("Hierarchical Vector Spaces", demo_vector_spaces),
        ("Enhanced Search Capabilities", demo_enhanced_search),
        ("Letter Coverage Gap Analysis", demo_gap_analysis),
        ("Complete Analysis", demo_complete_analysis)
    ]
    
    print("\nAvailable demonstrations:")
    for i, (name, _) in enumerate(demos):
        print(f"{i+1}. {name}")
    
    try:
        choice = input("\nSelect demo (1-5, or 'all' for all demos): ").strip().lower()
        
        if choice == 'all':
            for name, demo_func in demos:
                print(f"\n{'='*20} {name} {'='*20}")
                demo_func()
        elif choice.isdigit() and 1 <= int(choice) <= len(demos):
            name, demo_func = demos[int(choice) - 1]
            print(f"\n{'='*20} {name} {'='*20}")
            return demo_func()
        else:
            print("Invalid choice. Running complete analysis...")
            return demo_complete_analysis()
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        return 0
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 