#!/usr/bin/env python3
"""
Production-Ready Product Service
Integrates the SOTA DuckDB product database with the SE Letters pipeline

Features:
- High-performance product queries using DuckDB
- Seamless integration with existing pipeline
- Enhanced range mapping and analysis
- Comprehensive business intelligence
- Production-ready error handling

Version: 1.0.0
Author: SE Letters Team
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

import duckdb
from loguru import logger

from se_letters.core.config import get_config
from se_letters.core.exceptions import ProcessingError
from se_letters.services.sota_product_database_service import (
    SOTAProductDatabaseService, ProductMatch, RangeAnalysis, SearchResult
)


@dataclass
class ProductMappingResult:
    """Enhanced product mapping result"""
    success: bool
    range_name: str
    total_products: int
    active_products: int
    obsolete_products: int
    confidence_score: float
    search_time_ms: float
    modernization_candidates: List[ProductMatch]
    business_analysis: Dict[str, Any]
    performance_metrics: Dict[str, float]


class ProductionReadyProductService:
    """
    Production-ready product service using SOTA DuckDB database
    Replaces Excel-based approach with high-performance database queries
    """
    
    def __init__(self):
        """Initialize the production-ready product service"""
        self.config = get_config()
        
        # Initialize SOTA database service
        self.db_service = SOTAProductDatabaseService("data/IBcatalogue.duckdb")
        
        # Performance tracking
        self.service_metrics = {
            'total_mappings': 0,
            'successful_mappings': 0,
            'avg_response_time_ms': 0.0,
            'cache_hit_rate': 0.0
        }
        
        logger.info("🚀 Production-Ready Product Service initialized")
        logger.info(f"📊 Database: {self.db_service.total_products:,} products")
        logger.info(f"🔢 Ranges: {self.db_service.total_ranges:,}")
        logger.info(f"⚡ Performance: Sub-second queries enabled")
    
    def map_product_range(self, range_name: str, include_analysis: bool = True) -> ProductMappingResult:
        """
        Map a product range with comprehensive analysis
        
        Args:
            range_name: Name of the product range to map
            include_analysis: Whether to include detailed business analysis
            
        Returns:
            ProductMappingResult with comprehensive mapping information
        """
        start_time = time.time()
        
        try:
            logger.info(f"🎯 Mapping product range: {range_name}")
            
            # Step 1: Search for products in the range
            search_result = self.db_service.find_products_by_range(
                range_name, 
                include_obsolete=True
            )
            
            # Step 2: Perform comprehensive range analysis if requested
            range_analysis = None
            if include_analysis and search_result.total_count > 0:
                range_analysis = self.db_service.analyze_range(range_name)
            
            # Step 3: Calculate metrics
            total_products = search_result.total_count
            active_products = 0
            obsolete_products = 0
            
            for product in search_result.products:
                if self._is_obsolete_status(product.commercial_status):
                    obsolete_products += 1
                else:
                    active_products += 1
            
            # Step 4: Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                range_name, search_result.products
            )
            
            # Step 5: Get modernization candidates
            modernization_candidates = []
            if range_analysis:
                modernization_candidates = range_analysis.modernization_candidates
            
            # Step 6: Generate business analysis
            business_analysis = {}
            if include_analysis:
                business_analysis = self._generate_business_analysis(
                    range_name, search_result, range_analysis
                )
            
            # Step 7: Update service metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_service_metrics(processing_time_ms, True)
            
            # Step 8: Create comprehensive result
            result = ProductMappingResult(
                success=True,
                range_name=range_name,
                total_products=total_products,
                active_products=active_products,
                obsolete_products=obsolete_products,
                confidence_score=confidence_score,
                search_time_ms=processing_time_ms,
                modernization_candidates=modernization_candidates,
                business_analysis=business_analysis,
                performance_metrics=self.db_service.get_performance_metrics()
            )
            
            logger.info(f"✅ Mapping completed: {total_products} products found in {processing_time_ms:.2f}ms")
            logger.info(f"📊 Confidence: {confidence_score:.2f}")
            logger.info(f"🔄 Modernization candidates: {len(modernization_candidates)}")
            
            return result
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_service_metrics(processing_time_ms, False)
            
            logger.error(f"❌ Mapping failed for {range_name}: {e}")
            
            return ProductMappingResult(
                success=False,
                range_name=range_name,
                total_products=0,
                active_products=0,
                obsolete_products=0,
                confidence_score=0.0,
                search_time_ms=processing_time_ms,
                modernization_candidates=[],
                business_analysis={'error': str(e)},
                performance_metrics={}
            )
    
    def map_multiple_ranges(self, range_names: List[str]) -> List[ProductMappingResult]:
        """
        Map multiple product ranges efficiently
        
        Args:
            range_names: List of range names to map
            
        Returns:
            List of ProductMappingResult objects
        """
        logger.info(f"🎯 Mapping {len(range_names)} product ranges")
        start_time = time.time()
        
        results = []
        for range_name in range_names:
            result = self.map_product_range(range_name, include_analysis=False)
            results.append(result)
        
        total_time = (time.time() - start_time) * 1000
        successful_mappings = sum(1 for r in results if r.success)
        
        logger.info(f"✅ Multi-mapping completed: {successful_mappings}/{len(range_names)} successful in {total_time:.2f}ms")
        
        return results
    
    def search_products_by_text(self, search_term: str, limit: int = 100) -> SearchResult:
        """
        Search products by text across multiple fields
        
        Args:
            search_term: Text to search for
            limit: Maximum number of results
            
        Returns:
            SearchResult with matching products
        """
        logger.info(f"🔍 Searching products: '{search_term}'")
        
        result = self.db_service.search_products_semantic(search_term, limit)
        
        logger.info(f"✅ Search completed: {result.total_count} results in {result.search_time_ms:.2f}ms")
        
        return result
    
    def get_pl_services_intelligence(self) -> Dict[str, Any]:
        """
        Get comprehensive PL services business intelligence
        
        Returns:
            Dictionary with PL services statistics and analysis
        """
        logger.info("📊 Generating PL services intelligence")
        
        return self.db_service.get_pl_services_statistics()
    
    def analyze_obsolescence_impact(self, range_names: List[str]) -> Dict[str, Any]:
        """
        Analyze obsolescence impact across multiple ranges
        
        Args:
            range_names: List of range names to analyze
            
        Returns:
            Comprehensive obsolescence impact analysis
        """
        logger.info(f"📈 Analyzing obsolescence impact for {len(range_names)} ranges")
        start_time = time.time()
        
        total_products = 0
        total_obsolete = 0
        range_analyses = []
        
        for range_name in range_names:
            mapping_result = self.map_product_range(range_name, include_analysis=True)
            if mapping_result.success:
                total_products += mapping_result.total_products
                total_obsolete += mapping_result.obsolete_products
                range_analyses.append({
                    'range_name': range_name,
                    'total_products': mapping_result.total_products,
                    'obsolete_products': mapping_result.obsolete_products,
                    'obsolescence_rate': (mapping_result.obsolete_products / mapping_result.total_products * 100) if mapping_result.total_products > 0 else 0,
                    'modernization_candidates': len(mapping_result.modernization_candidates)
                })
        
        analysis_time = (time.time() - start_time) * 1000
        overall_obsolescence_rate = (total_obsolete / total_products * 100) if total_products > 0 else 0
        
        analysis = {
            'summary': {
                'total_ranges_analyzed': len(range_names),
                'total_products': total_products,
                'total_obsolete_products': total_obsolete,
                'overall_obsolescence_rate': overall_obsolescence_rate,
                'analysis_time_ms': analysis_time
            },
            'range_analyses': range_analyses,
            'recommendations': self._generate_obsolescence_recommendations(range_analyses),
            'timestamp': time.time()
        }
        
        logger.info(f"✅ Obsolescence analysis completed in {analysis_time:.2f}ms")
        logger.info(f"📊 Overall obsolescence rate: {overall_obsolescence_rate:.1f}%")
        
        return analysis
    
    def _is_obsolete_status(self, commercial_status: str) -> bool:
        """Check if a commercial status indicates obsolescence"""
        obsolete_statuses = {
            '18-End of commercialisation',
            '19-end of commercialization block',
            '14-End of commerc. announced',
            '20-Temporary block'
        }
        return commercial_status in obsolete_statuses
    
    def _calculate_confidence_score(self, range_name: str, products: List[ProductMatch]) -> float:
        """Calculate confidence score for range mapping"""
        if not products:
            return 0.0
        
        # Calculate based on product matches and their individual confidence scores
        total_confidence = sum(product.confidence_score for product in products)
        avg_confidence = total_confidence / len(products)
        
        # Boost confidence for exact range matches
        exact_matches = sum(1 for product in products if product.range_label.lower() == range_name.lower())
        exact_match_boost = (exact_matches / len(products)) * 0.2
        
        # Penalty for very few results
        count_factor = min(len(products) / 10, 1.0)  # Penalize if < 10 products
        
        final_confidence = min(avg_confidence + exact_match_boost * count_factor, 1.0)
        
        return final_confidence
    
    def _generate_business_analysis(
        self, 
        range_name: str, 
        search_result: SearchResult, 
        range_analysis: Optional[RangeAnalysis]
    ) -> Dict[str, Any]:
        """Generate comprehensive business analysis"""
        
        analysis = {
            'search_performance': {
                'search_time_ms': search_result.search_time_ms,
                'cache_hit': search_result.cache_hit,
                'search_strategy': search_result.search_strategy
            },
            'product_distribution': {},
            'business_impact': {},
            'recommendations': []
        }
        
        if range_analysis:
            # Product distribution analysis
            analysis['product_distribution'] = {
                'subranges': len(range_analysis.subranges),
                'brands': len(range_analysis.brands),
                'pl_services': list(range_analysis.pl_services),
                'commercial_statuses': range_analysis.commercial_statuses
            }
            
            # Business impact assessment
            obsolescence_rate = (range_analysis.obsolete_products / range_analysis.total_products * 100) if range_analysis.total_products > 0 else 0
            
            if obsolescence_rate > 75:
                impact_level = 'CRITICAL'
            elif obsolescence_rate > 50:
                impact_level = 'HIGH'
            elif obsolescence_rate > 25:
                impact_level = 'MEDIUM'
            else:
                impact_level = 'LOW'
            
            analysis['business_impact'] = {
                'obsolescence_rate': obsolescence_rate,
                'impact_level': impact_level,
                'modernization_urgency': 'HIGH' if obsolescence_rate > 60 else 'MEDIUM' if obsolescence_rate > 30 else 'LOW'
            }
            
            # Generate recommendations
            if obsolescence_rate > 50:
                analysis['recommendations'].append('Immediate modernization planning required')
            if len(range_analysis.modernization_candidates) > 0:
                analysis['recommendations'].append(f'{len(range_analysis.modernization_candidates)} modernization candidates identified')
            if range_analysis.active_products > 0:
                analysis['recommendations'].append(f'{range_analysis.active_products} active products available for migration')
        
        return analysis
    
    def _generate_obsolescence_recommendations(self, range_analyses: List[Dict[str, Any]]) -> List[str]:
        """Generate obsolescence management recommendations"""
        recommendations = []
        
        # Sort ranges by obsolescence rate
        sorted_ranges = sorted(range_analyses, key=lambda x: x['obsolescence_rate'], reverse=True)
        
        # High-priority ranges (>75% obsolete)
        critical_ranges = [r for r in sorted_ranges if r['obsolescence_rate'] > 75]
        if critical_ranges:
            recommendations.append(f"CRITICAL: {len(critical_ranges)} ranges have >75% obsolescence rate - immediate action required")
        
        # Medium-priority ranges (50-75% obsolete)
        high_priority_ranges = [r for r in sorted_ranges if 50 <= r['obsolescence_rate'] <= 75]
        if high_priority_ranges:
            recommendations.append(f"HIGH: {len(high_priority_ranges)} ranges have 50-75% obsolescence rate - plan modernization within 6 months")
        
        # Ranges with good modernization options
        ranges_with_candidates = [r for r in range_analyses if r['modernization_candidates'] > 0]
        if ranges_with_candidates:
            recommendations.append(f"OPPORTUNITY: {len(ranges_with_candidates)} ranges have modernization candidates available")
        
        return recommendations
    
    def _update_service_metrics(self, processing_time_ms: float, success: bool) -> None:
        """Update service performance metrics"""
        self.service_metrics['total_mappings'] += 1
        
        if success:
            self.service_metrics['successful_mappings'] += 1
        
        # Update rolling average response time
        total_mappings = self.service_metrics['total_mappings']
        current_avg = self.service_metrics['avg_response_time_ms']
        new_avg = ((current_avg * (total_mappings - 1)) + processing_time_ms) / total_mappings
        self.service_metrics['avg_response_time_ms'] = new_avg
        
        # Update cache hit rate from database service
        db_metrics = self.db_service.get_performance_metrics()
        self.service_metrics['cache_hit_rate'] = db_metrics.get('cache_hit_rate', 0.0)
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics"""
        db_metrics = self.db_service.get_performance_metrics()
        
        return {
            'service_metrics': self.service_metrics,
            'database_metrics': db_metrics,
            'success_rate': (self.service_metrics['successful_mappings'] / self.service_metrics['total_mappings'] * 100) if self.service_metrics['total_mappings'] > 0 else 0.0,
            'timestamp': time.time()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        db_health = self.db_service.health_check()
        
        return {
            'status': 'healthy' if db_health['status'] == 'healthy' else 'degraded',
            'service_metrics': self.get_service_metrics(),
            'database_health': db_health,
            'timestamp': time.time()
        }


def demo_production_service():
    """Demonstrate the production-ready product service"""
    logger.info("🚀 Production-Ready Product Service Demo")
    
    service = ProductionReadyProductService()
    
    # Demo 1: Single range mapping
    logger.info("\n📋 Demo 1: Galaxy 6000 Range Mapping")
    galaxy_result = service.map_product_range("Galaxy 6000")
    logger.info(f"Result: {galaxy_result.success}")
    logger.info(f"Products: {galaxy_result.total_products}")
    logger.info(f"Confidence: {galaxy_result.confidence_score:.2f}")
    
    # Demo 2: Multiple range mapping
    logger.info("\n📋 Demo 2: Multiple Range Mapping")
    ranges = ["Galaxy", "SEPAM", "Masterpact"]
    multi_results = service.map_multiple_ranges(ranges)
    for result in multi_results:
        logger.info(f"{result.range_name}: {result.total_products} products")
    
    # Demo 3: Text search
    logger.info("\n📋 Demo 3: Text Search")
    search_result = service.search_products_by_text("UPS")
    logger.info(f"Search results: {search_result.total_count} products")
    
    # Demo 4: PL Services intelligence
    logger.info("\n📋 Demo 4: PL Services Intelligence")
    pl_intel = service.get_pl_services_intelligence()
    logger.info(f"PL Services: {len(pl_intel['distribution'])} categories")
    
    # Demo 5: Service metrics
    logger.info("\n📋 Demo 5: Service Metrics")
    metrics = service.get_service_metrics()
    logger.info(f"Success rate: {metrics['success_rate']:.1f}%")
    logger.info(f"Avg response time: {metrics['service_metrics']['avg_response_time_ms']:.2f}ms")
    
    logger.info("\n🎉 Production-Ready Product Service Demo Completed!")


if __name__ == "__main__":
    demo_production_service() 