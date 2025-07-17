#!/usr/bin/env python3
"""
Test Enhanced Space Search v3.3.0
Comprehensive test for advanced space search capabilities

This script tests the enhanced product mapping service's ability to handle
space variations like "PIX2B" vs "PIX 2B" and demonstrates the massive
improvements in product matching accuracy.

Author: Alexandre Huther
Version: 1.0.0
Date: 2025-07-17
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.enhanced_product_mapping_service_v3 import (
    EnhancedProductMappingServiceV3
)
from loguru import logger


class SpaceSearchTester:
    """Test suite for enhanced space search functionality"""
    
    def __init__(self):
        """Initialize the test suite"""
        self.mapping_service = EnhancedProductMappingServiceV3()
        self.test_results = []
        
    def test_space_variations(self):
        """Test space variations handling for PIX products"""
        logger.info("🧪 Testing space variations handling")
        
        # Test cases with different space patterns
        test_cases = [
            {
                'name': 'PIX2B (no space)',
                'product_identifier': 'PIX2B',
                'range_label': 'PIX2B',
                'subrange_label': '2B',
                'product_line': 'PSIBS'
            },
            {
                'name': 'PIX 2B (with space)',
                'product_identifier': 'PIX 2B',
                'range_label': 'PIX 2B',
                'subrange_label': '2B',
                'product_line': 'PSIBS'
            },
            {
                'name': 'PIX-2B (with hyphen)',
                'product_identifier': 'PIX-2B',
                'range_label': 'PIX-2B',
                'subrange_label': '2B',
                'product_line': 'PSIBS'
            },
            {
                'name': 'PIX_2B (with underscore)',
                'product_identifier': 'PIX_2B',
                'range_label': 'PIX_2B',
                'subrange_label': '2B',
                'product_line': 'PSIBS'
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"\n🔍 Testing: {test_case['name']}")
            
            start_time = time.time()
            
            # Process product mapping
            result = self.mapping_service.process_product_mapping(
                product_identifier=test_case['product_identifier'],
                range_label=test_case['range_label'],
                subrange_label=test_case['subrange_label'],
                product_line=test_case['product_line'],
                max_candidates=10
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Log results
            logger.info(f"⚡ Processing time: {processing_time:.2f}ms")
            logger.info(f"📊 Confidence: {result.confidence_score:.3f}")
            logger.info(f"🎯 Search strategy: {result.search_strategy}")
            logger.info(f"🔍 Candidates found: {len(result.modernization_candidates)}")
            
            # Show top matches
            if result.modernization_candidates:
                logger.info("🏆 Top matches:")
                for i, candidate in enumerate(result.modernization_candidates[:3]):
                    logger.info(f"  {i+1}. {candidate.range_label} "
                              f"(confidence: {candidate.confidence_score:.3f})")
            
            # Store result
            self.test_results.append({
                'test_case': test_case['name'],
                'success': result.confidence_score > 0.0,
                'confidence': result.confidence_score,
                'candidates_found': len(result.modernization_candidates),
                'processing_time_ms': processing_time,
                'search_strategy': result.search_strategy
            })
    
    def test_pattern_generation(self):
        """Test pattern generation capabilities"""
        logger.info("\n🧪 Testing pattern generation")
        
        # Test space search engine directly
        space_engine = self.mapping_service.space_search_engine
        
        test_queries = ['PIX2B', 'SEPAM40', 'Galaxy6000']
        
        for query in test_queries:
            logger.info(f"\n🔍 Testing pattern generation for: '{query}'")
            
            variations = space_engine.generate_space_variations(query)
            logger.info(f"📋 Generated {len(variations)} variations:")
            
            for i, variation in enumerate(variations[:10]):  # Show first 10
                logger.info(f"  {i+1}. '{variation}'")
    
    def test_similarity_calculation(self):
        """Test similarity calculation between different patterns"""
        logger.info("\n🧪 Testing similarity calculation")
        
        space_engine = self.mapping_service.space_search_engine
        
        # Test similarity between different PIX patterns
        test_pairs = [
            ('PIX2B', 'PIX 2B'),
            ('PIX2B', 'PIX-2B'),
            ('PIX2B', 'PIX_2B'),
            ('PIX 2B', 'PIX 2 B'),
            ('SEPAM40', 'SEPAM 40'),
            ('Galaxy6000', 'Galaxy 6000')
        ]
        
        for text1, text2 in test_pairs:
            similarity = space_engine.calculate_similarity(text1, text2)
            logger.info(f"🔍 Similarity '{text1}' vs '{text2}': {similarity:.3f}")
    
    def test_database_connectivity(self):
        """Test database connectivity and sample queries"""
        logger.info("\n🧪 Testing database connectivity")
        
        # Test health check
        health = self.mapping_service.health_check()
        
        logger.info(f"📊 Database status: {health['status']}")
        logger.info(f"📋 Total products: {health.get('total_products', 0):,}")
        
        if 'pix_samples' in health:
            logger.info("🔍 PIX product samples in database:")
            for range_label, count in health['pix_samples']:
                logger.info(f"  - {range_label}: {count} products")
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        logger.info("🚀 Starting Enhanced Space Search Test Suite v3.3.0")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            # Test 1: Database connectivity
            self.test_database_connectivity()
            
            # Test 2: Pattern generation
            self.test_pattern_generation()
            
            # Test 3: Similarity calculation
            self.test_similarity_calculation()
            
            # Test 4: Space variations
            self.test_space_variations()
            
            # Generate summary
            self._generate_test_summary()
            
            total_time = (time.time() - start_time) * 1000
            logger.info(f"\n✅ Test suite completed in {total_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise
    
    def _generate_test_summary(self):
        """Generate test summary"""
        logger.info("\n📊 Test Summary")
        logger.info("=" * 40)
        
        if not self.test_results:
            logger.warning("⚠️ No test results to summarize")
            return
        
        successful_tests = sum(1 for r in self.test_results if r['success'])
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests) * 100
        
        avg_confidence = sum(r['confidence'] for r in self.test_results) / total_tests
        avg_processing_time = sum(r['processing_time_ms'] for r in self.test_results) / total_tests
        
        logger.info(f"📋 Total tests: {total_tests}")
        logger.info(f"✅ Successful: {successful_tests}")
        logger.info(f"❌ Failed: {total_tests - successful_tests}")
        logger.info(f"📈 Success rate: {success_rate:.1f}%")
        logger.info(f"📊 Average confidence: {avg_confidence:.3f}")
        logger.info(f"⚡ Average processing time: {avg_processing_time:.2f}ms")
        
        # Show detailed results
        logger.info("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"  {status} {result['test_case']}: "
                      f"confidence={result['confidence']:.3f}, "
                      f"candidates={result['candidates_found']}, "
                      f"time={result['processing_time_ms']:.2f}ms")


def main():
    """Main entry point"""
    tester = SpaceSearchTester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main() 