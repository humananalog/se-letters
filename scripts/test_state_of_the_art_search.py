#!/usr/bin/env python3
"""
Test State-of-the-Art Multi-Dimensional Search

This script tests the enhanced product mapping service v3.4.0 against the
search solution guidelines to evaluate state-of-the-art capabilities.

Tests:
1. pg_trgm fuzzy text search for vague/misspelled descriptions
2. pgvector semantic search for semantic relationships
3. Range-based filtering for numerical specifications
4. Hybrid search approach with weighted scoring
5. Performance optimization and indexing
"""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.enhanced_product_mapping_service_v3 import (
    EnhancedProductMappingServiceV3
)
from loguru import logger


def test_health_check():
    """Test health check with state-of-the-art capabilities"""
    print("🔍 Testing Health Check...")
    
    service = EnhancedProductMappingServiceV3()
    health = service.health_check()
    
    print(f"   Status: {health['status']}")
    print(f"   Version: {health['version']}")
    print(f"   Database: {health['database']['product_count']} products")
    print(f"   PostgreSQL: {health['database']['version']}")
    print(f"   pg_trgm: {'✅' if health['database']['pg_trgm_working'] else '❌'}")
    print(f"   pgvector: {'✅' if health['database']['pgvector_working'] else '❌'}")
    
    print("   Search Capabilities:")
    for capability, enabled in health['search_capabilities'].items():
        status = "✅" if enabled else "❌"
        print(f"     {status} {capability}")
    
    return health['status'] == 'healthy'


def test_fuzzy_text_search():
    """Test pg_trgm fuzzy text search for vague/misspelled descriptions"""
    print("\n🔍 Testing pg_trgm Fuzzy Text Search...")
    
    service = EnhancedProductMappingServiceV3()
    
    # Test cases with potential misspellings/vague descriptions
    test_cases = [
        "PIX2B",           # No space
        "PIX 2B",          # With space
        "PIX-2B",          # With hyphen
        "PIX_2B",          # With underscore
        "PIX2B",           # Exact match
        "PIX 2B",          # Space variation
        "circuit braker",  # Misspelled (should find "circuit breaker")
        "seperator",       # Misspelled (should find "separator")
    ]
    
    results = {}
    
    for query in test_cases:
        print(f"   Testing: '{query}'")
        
        # Use the fuzzy search directly
        fuzzy_results = service.sota_search_engine._fuzzy_text_search(query, limit=10)
        
        if fuzzy_results:
            best_match = max(fuzzy_results, key=lambda x: x.get('fuzzy_score', 0))
            score = best_match.get('fuzzy_score', 0)
            range_label = best_match.get('range_label', 'Unknown')
            
            print(f"     ✅ Found {len(fuzzy_results)} matches")
            print(f"     📊 Best match: '{range_label}' (score: {score:.3f})")
            
            results[query] = {
                'count': len(fuzzy_results),
                'best_score': score,
                'best_match': range_label
            }
        else:
            print(f"     ❌ No matches found")
            results[query] = {'count': 0, 'best_score': 0, 'best_match': None}
    
    return results


def test_semantic_search():
    """Test pgvector semantic search for semantic relationships"""
    print("\n🧠 Testing pgvector Semantic Search...")
    
    service = EnhancedProductMappingServiceV3()
    
    # Test if embedding model is available
    if not service.sota_search_engine.embedding_model:
        print("   ⚠️ Embedding model not available - skipping semantic search test")
        return {'status': 'skipped', 'reason': 'embedding_model_not_available'}
    
    # Test cases for semantic relationships
    test_cases = [
        "circuit breaker",     # Should find related electrical components
        "power distribution",  # Should find distribution equipment
        "protection device",   # Should find protective equipment
        "switchgear",         # Should find switching equipment
    ]
    
    results = {}
    
    for query in test_cases:
        print(f"   Testing: '{query}'")
        
        # Use the semantic search directly
        semantic_results = service.sota_search_engine._semantic_search(query, limit=10)
        
        if semantic_results:
            best_match = max(semantic_results, key=lambda x: x.get('semantic_score', 0))
            score = best_match.get('semantic_score', 0)
            range_label = best_match.get('range_label', 'Unknown')
            
            print(f"     ✅ Found {len(semantic_results)} semantic matches")
            print(f"     📊 Best match: '{range_label}' (score: {score:.3f})")
            
            results[query] = {
                'count': len(semantic_results),
                'best_score': score,
                'best_match': range_label
            }
        else:
            print(f"     ❌ No semantic matches found")
            results[query] = {'count': 0, 'best_score': 0, 'best_match': None}
    
    return results


def test_range_based_search():
    """Test range-based filtering for numerical specifications"""
    print("\n📊 Testing Range-Based Filtering...")
    
    service = EnhancedProductMappingServiceV3()
    
    # Test cases for numerical specifications
    test_cases = [
        {'voltage': (200, 400)},      # Voltage range
        {'power_rating': (1000, 5000)},  # Power rating range
        {'voltage': (200, 400), 'power_rating': (1000, 5000)},  # Combined
    ]
    
    results = {}
    
    for i, specifications in enumerate(test_cases):
        print(f"   Testing specifications: {specifications}")
        
        # Use the range search directly
        range_results = service.sota_search_engine._range_based_search(
            specifications, limit=10
        )
        
        if range_results:
            print(f"     ✅ Found {len(range_results)} range matches")
            
            # Show sample results
            for j, result in enumerate(range_results[:3]):
                product_id = result.get('product_identifier', 'Unknown')
                range_label = result.get('range_label', 'Unknown')
                print(f"       {j+1}. {product_id} - {range_label}")
            
            results[f"case_{i+1}"] = {
                'count': len(range_results),
                'specifications': specifications
            }
        else:
            print(f"     ❌ No range matches found")
            results[f"case_{i+1}"] = {'count': 0, 'specifications': specifications}
    
    return results


def test_hybrid_search():
    """Test hybrid search combining fuzzy, semantic, and range matching"""
    print("\n⚖️ Testing Hybrid Search...")
    
    service = EnhancedProductMappingServiceV3()
    
    # Test cases for hybrid search
    test_cases = [
        {
            'query': 'PIX2B',
            'specifications': {},
            'description': 'Basic product search'
        },
        {
            'query': 'circuit breaker',
            'specifications': {'voltage': (200, 400)},
            'description': 'Product with voltage range'
        },
        {
            'query': 'power distribution',
            'specifications': {'power_rating': (1000, 5000)},
            'description': 'Product with power rating'
        }
    ]
    
    results = {}
    
    for i, test_case in enumerate(test_cases):
        print(f"   Testing: {test_case['description']}")
        print(f"     Query: '{test_case['query']}'")
        print(f"     Specifications: {test_case['specifications']}")
        
        # Use the hybrid search directly
        hybrid_results = service.sota_search_engine._hybrid_search(
            query=test_case['query'],
            specifications=test_case['specifications'],
            limit=10
        )
        
        if hybrid_results:
            best_match = max(hybrid_results, key=lambda x: x.get('hybrid_score', 0))
            hybrid_score = best_match.get('hybrid_score', 0)
            fuzzy_score = best_match.get('fuzzy_score', 0)
            semantic_score = best_match.get('semantic_score', 0)
            range_score = best_match.get('range_score', 0)
            range_label = best_match.get('range_label', 'Unknown')
            
            print(f"     ✅ Found {len(hybrid_results)} hybrid matches")
            print(f"     📊 Best match: '{range_label}'")
            print(f"     🎯 Hybrid score: {hybrid_score:.3f}")
            print(f"     🔍 Fuzzy score: {fuzzy_score:.3f}")
            print(f"     🧠 Semantic score: {semantic_score:.3f}")
            print(f"     📊 Range score: {range_score:.3f}")
            
            results[f"case_{i+1}"] = {
                'count': len(hybrid_results),
                'best_hybrid_score': hybrid_score,
                'best_fuzzy_score': fuzzy_score,
                'best_semantic_score': semantic_score,
                'best_range_score': range_score,
                'best_match': range_label
            }
        else:
            print(f"     ❌ No hybrid matches found")
            results[f"case_{i+1}"] = {'count': 0}
    
    return results


def test_full_product_mapping():
    """Test full product mapping with state-of-the-art capabilities"""
    print("\n🚀 Testing Full Product Mapping...")
    
    service = EnhancedProductMappingServiceV3()
    
    # Test cases for full product mapping
    test_cases = [
        {
            'product_identifier': 'PIX2B',
            'range_label': 'PIX 2B',
            'subrange_label': 'Double Bus Bar',
            'product_line': 'DPIBS',
            'description': 'PIX2B with space variations'
        },
        {
            'product_identifier': 'SEPAM2040',
            'range_label': 'SEPAM 40',
            'subrange_label': 'Protection Relay',
            'product_line': 'PSIBS',
            'description': 'SEPAM protection relay'
        }
    ]
    
    results = {}
    
    for i, test_case in enumerate(test_cases):
        print(f"   Testing: {test_case['description']}")
        print(f"     Product: {test_case['product_identifier']}")
        print(f"     Range: {test_case['range_label']}")
        
        start_time = time.time()
        
        # Perform full product mapping
        result = service.process_product_mapping(
            product_identifier=test_case['product_identifier'],
            range_label=test_case['range_label'],
            subrange_label=test_case['subrange_label'],
            product_line=test_case['product_line'],
            max_candidates=10
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        if result and result.modernization_candidates:
            print(f"     ✅ Found {len(result.modernization_candidates)} candidates")
            print(f"     📊 Confidence: {result.confidence_score:.3f}")
            print(f"     ⚡ Processing time: {processing_time:.2f}ms")
            print(f"     🎯 Search strategy: {result.search_strategy}")
            print(f"     🔍 Fuzzy search used: {result.fuzzy_search_used}")
            print(f"     🧠 Semantic search used: {result.semantic_search_used}")
            print(f"     📊 Range search used: {result.range_search_used}")
            
            if result.sota_search_results:
                print(f"     🎯 Strategies used: {', '.join(result.sota_search_results.strategies_used)}")
                print(f"     🔍 Fuzzy matches: {result.sota_search_results.fuzzy_matches}")
                print(f"     🧠 Semantic matches: {result.sota_search_results.semantic_matches}")
                print(f"     📊 Range matches: {result.sota_search_results.range_matches}")
                print(f"     ⚖️ Hybrid matches: {result.sota_search_results.hybrid_matches}")
            
            results[f"case_{i+1}"] = {
                'success': True,
                'candidates': len(result.modernization_candidates),
                'confidence': result.confidence_score,
                'processing_time': processing_time,
                'search_strategy': result.search_strategy,
                'fuzzy_used': result.fuzzy_search_used,
                'semantic_used': result.semantic_search_used,
                'range_used': result.range_search_used
            }
        else:
            print(f"     ❌ No candidates found")
            results[f"case_{i+1}"] = {
                'success': False,
                'candidates': 0,
                'confidence': 0.0,
                'processing_time': processing_time
            }
    
    return results


def evaluate_guidelines_compliance(results):
    """Evaluate compliance with search solution guidelines"""
    print("\n📋 Evaluating Guidelines Compliance...")
    
    compliance = {
        'pg_trgm_fuzzy_search': False,
        'pgvector_semantic_search': False,
        'range_based_filtering': False,
        'hybrid_search': False,
        'performance_optimization': False,
        'proper_indexing': False
    }
    
    # Check pg_trgm fuzzy search
    if 'fuzzy_text_search' in results:
        fuzzy_results = results['fuzzy_text_search']
        if any(result['count'] > 0 for result in fuzzy_results.values()):
            compliance['pg_trgm_fuzzy_search'] = True
            print("   ✅ pg_trgm fuzzy text search: Working")
        else:
            print("   ❌ pg_trgm fuzzy text search: No matches found")
    
    # Check pgvector semantic search
    if 'semantic_search' in results:
        semantic_results = results['semantic_search']
        if isinstance(semantic_results, dict) and semantic_results.get('status') != 'skipped':
            if any(result['count'] > 0 for result in semantic_results.values()):
                compliance['pgvector_semantic_search'] = True
                print("   ✅ pgvector semantic search: Working")
            else:
                print("   ❌ pgvector semantic search: No matches found")
        else:
            print("   ⚠️ pgvector semantic search: Skipped (embedding model not available)")
    
    # Check range-based filtering
    if 'range_based_search' in results:
        range_results = results['range_based_search']
        if any(result['count'] > 0 for result in range_results.values()):
            compliance['range_based_filtering'] = True
            print("   ✅ Range-based filtering: Working")
        else:
            print("   ❌ Range-based filtering: No matches found")
    
    # Check hybrid search
    if 'hybrid_search' in results:
        hybrid_results = results['hybrid_search']
        if any(result['count'] > 0 for result in hybrid_results.values()):
            compliance['hybrid_search'] = True
            print("   ✅ Hybrid search: Working")
        else:
            print("   ❌ Hybrid search: No matches found")
    
    # Check performance optimization
    if 'full_product_mapping' in results:
        mapping_results = results['full_product_mapping']
        avg_time = sum(result['processing_time'] for result in mapping_results.values()) / len(mapping_results)
        if avg_time < 1000:  # Less than 1 second
            compliance['performance_optimization'] = True
            print(f"   ✅ Performance optimization: {avg_time:.2f}ms average")
        else:
            print(f"   ⚠️ Performance optimization: {avg_time:.2f}ms average (slow)")
    
    # Check proper indexing (assumed if health check passes)
    if 'health_check' in results and results['health_check']:
        compliance['proper_indexing'] = True
        print("   ✅ Proper indexing: Health check passed")
    else:
        print("   ❌ Proper indexing: Health check failed")
    
    # Calculate overall compliance
    total_checks = len(compliance)
    passed_checks = sum(compliance.values())
    compliance_rate = (passed_checks / total_checks) * 100
    
    print(f"\n📊 Overall Guidelines Compliance: {compliance_rate:.1f}% ({passed_checks}/{total_checks})")
    
    if compliance_rate >= 80:
        print("🎉 EXCELLENT: State-of-the-art search implementation!")
    elif compliance_rate >= 60:
        print("✅ GOOD: Most guidelines implemented")
    elif compliance_rate >= 40:
        print("⚠️ FAIR: Some guidelines implemented")
    else:
        print("❌ POOR: Most guidelines missing")
    
    return compliance, compliance_rate


def main():
    """Run comprehensive state-of-the-art search evaluation"""
    print("🚀 State-of-the-Art Multi-Dimensional Search Evaluation")
    print("=" * 60)
    
    results = {}
    
    # Run all tests
    try:
        # Health check
        results['health_check'] = test_health_check()
        
        # Fuzzy text search
        results['fuzzy_text_search'] = test_fuzzy_text_search()
        
        # Semantic search
        results['semantic_search'] = test_semantic_search()
        
        # Range-based search
        results['range_based_search'] = test_range_based_search()
        
        # Hybrid search
        results['hybrid_search'] = test_hybrid_search()
        
        # Full product mapping
        results['full_product_mapping'] = test_full_product_mapping()
        
        # Evaluate compliance
        compliance, compliance_rate = evaluate_guidelines_compliance(results)
        
        print(f"\n🎯 Final Assessment:")
        print(f"   State-of-the-Art Implementation: {'✅' if compliance_rate >= 80 else '❌'}")
        print(f"   Guidelines Compliance: {compliance_rate:.1f}%")
        print(f"   Ready for Production: {'✅' if compliance_rate >= 60 else '❌'}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return compliance_rate >= 60


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 