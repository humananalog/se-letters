#!/usr/bin/env python3
"""
Product Mapping Test - SOTA DuckDB Edition
Test product mapping capabilities using the new SOTA product database

Features:
- Test with real obsolescence letters
- Demonstrate hierarchical search strategy
- Show confidence scoring and candidate ranking
- Business intelligence analysis
- Performance benchmarking

Version: 1.0.0
Author: SE Letters Team
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.services.production_pipeline_service import ProductionPipelineService
from se_letters.services.document_processor import DocumentProcessor
from se_letters.core.config import get_config

# Import the production-ready service we created
sys.path.append(str(project_root / "scripts/sandbox"))
from production_ready_product_service import ProductionReadyProductService, ProductMappingResult


@dataclass
class MappingTestResult:
    """Test result for product mapping"""
    document_name: str
    success: bool
    processing_time_ms: float
    products_found: int
    high_confidence_matches: int
    total_candidates: int
    error: Optional[str] = None
    mapping_details: Optional[Dict[str, Any]] = None


class ProductMappingTester:
    """Comprehensive product mapping tester using SOTA database"""
    
    def __init__(self):
        """Initialize the product mapping tester"""
        self.config = get_config()
        
        # Initialize services
        self.db_service = SOTAProductDatabaseService()
        self.pipeline_service = ProductionPipelineService()
        self.document_processor = DocumentProcessor()
        self.mapping_service = ProductionReadyProductService()
        
        # Test configuration
        self.test_documents_dir = Path("data/test/documents")
        self.results_dir = Path("data/output/mapping_tests")
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("🧪 Product Mapping Tester initialized with SOTA database")
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive product mapping tests"""
        logger.info("🚀 Starting comprehensive product mapping tests")
        
        # Test 1: Database health check
        logger.info("📊 Test 1: Database Health Check")
        db_health = self._test_database_health()
        
        # Test 2: Performance benchmarks
        logger.info("⚡ Test 2: Performance Benchmarks")
        performance_results = self._test_performance()
        
        # Test 3: Document mapping tests
        logger.info("📄 Test 3: Document Mapping Tests")
        mapping_results = self._test_document_mapping()
        
        # Test 4: Search strategy analysis
        logger.info("🔍 Test 4: Search Strategy Analysis")
        strategy_results = self._test_search_strategies()
        
        # Test 5: Business intelligence
        logger.info("🎯 Test 5: Business Intelligence Analysis")
        bi_results = self._test_business_intelligence()
        
        # Compile comprehensive results
        results = {
            "test_timestamp": time.time(),
            "database_health": db_health,
            "performance_benchmarks": performance_results,
            "document_mapping": mapping_results,
            "search_strategies": strategy_results,
            "business_intelligence": bi_results,
            "summary": self._generate_test_summary(mapping_results, performance_results)
        }
        
        # Save results
        results_file = self.results_dir / f"mapping_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Test results saved to: {results_file}")
        return results
    
    def _test_database_health(self) -> Dict[str, Any]:
        """Test database health and basic statistics"""
        try:
            health_check = self.db_service.health_check()
            stats = self.db_service.get_basic_statistics()
            
            return {
                "health_status": health_check["status"],
                "database_size_mb": health_check.get("database_size_mb", 0),
                "total_products": stats["total_products"],
                "total_ranges": stats["unique_ranges"],
                "pl_services_distribution": stats["pl_services_distribution"],
                "obsolescence_status": stats["obsolescence_analysis"],
                "modernization_candidates": stats.get("modernization_candidates", 0)
            }
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return {"health_status": "unhealthy", "error": str(e)}
    
    def _test_performance(self) -> Dict[str, Any]:
        """Test database performance with various queries"""
        performance_tests = [
            ("Basic Product Count", "SELECT COUNT(*) FROM products"),
            ("Galaxy 6000 Lookup", "SELECT * FROM products WHERE RANGE_LABEL ILIKE '%Galaxy%' LIMIT 10"),
            ("PL Services Analysis", "SELECT PL_SERVICES, COUNT(*) FROM products GROUP BY PL_SERVICES"),
            ("Complex Search", """
                SELECT * FROM products 
                WHERE PRODUCT_DESCRIPTION ILIKE '%protection%' 
                AND RANGE_LABEL IS NOT NULL 
                LIMIT 20
            """),
            ("Obsolescence Analysis", """
                SELECT OBSOLETE, COUNT(*) FROM products 
                GROUP BY OBSOLETE
            """)
        ]
        
        results = {}
        for test_name, query in performance_tests:
            try:
                start_time = time.time()
                result = self.db_service.execute_query(query)
                end_time = time.time()
                
                query_time_ms = (end_time - start_time) * 1000
                results[test_name] = {
                    "query_time_ms": query_time_ms,
                    "result_count": len(result) if result else 0,
                    "performance_rating": "EXCELLENT" if query_time_ms < 10 else "GOOD" if query_time_ms < 50 else "NEEDS_OPTIMIZATION"
                }
                logger.info(f"  ✅ {test_name}: {query_time_ms:.2f}ms")
            except Exception as e:
                results[test_name] = {"error": str(e)}
                logger.error(f"  ❌ {test_name}: {e}")
        
        return results
    
    def _test_document_mapping(self) -> List[MappingTestResult]:
        """Test product mapping with real documents"""
        test_documents = list(self.test_documents_dir.glob("*"))
        results = []
        
        for doc_path in test_documents:
            if doc_path.suffix.lower() in ['.pdf', '.doc', '.docx']:
                logger.info(f"📄 Testing mapping for: {doc_path.name}")
                result = self._test_single_document(doc_path)
                results.append(result)
        
        return results
    
    def _test_single_document(self, doc_path: Path) -> MappingTestResult:
        """Test product mapping for a single document"""
        start_time = time.time()
        
        try:
            # Extract text content
            content_result = self.document_processor.extract_content(str(doc_path))
            if not content_result.success:
                return MappingTestResult(
                    document_name=doc_path.name,
                    success=False,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    products_found=0,
                    high_confidence_matches=0,
                    total_candidates=0,
                    error="Content extraction failed"
                )
            
            text_content = content_result.content
            
            # Test different mapping strategies
            mapping_results = {}
            
            # Strategy 1: Galaxy 6000 specific test
            if "galaxy" in doc_path.name.lower():
                galaxy_results = self._test_galaxy_mapping(text_content)
                mapping_results["galaxy_specific"] = galaxy_results
            
            # Strategy 2: PIX specific test
            if "pix" in doc_path.name.lower():
                pix_results = self._test_pix_mapping(text_content)
                mapping_results["pix_specific"] = pix_results
            
            # Strategy 3: SEPAM specific test
            if "sepam" in doc_path.name.lower():
                sepam_results = self._test_sepam_mapping(text_content)
                mapping_results["sepam_specific"] = sepam_results
            
            # Strategy 4: General intelligent mapping
            general_results = self._test_intelligent_mapping(text_content, doc_path.name)
            mapping_results["general_intelligent"] = general_results
            
            # Compile results
            total_candidates = sum(len(r.get("candidates", [])) for r in mapping_results.values())
            high_confidence = sum(
                len([c for c in r.get("candidates", []) if c.get("confidence_score", 0) > 0.8])
                for r in mapping_results.values()
            )
            products_found = sum(len(r.get("matched_products", [])) for r in mapping_results.values())
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return MappingTestResult(
                document_name=doc_path.name,
                success=True,
                processing_time_ms=processing_time_ms,
                products_found=products_found,
                high_confidence_matches=high_confidence,
                total_candidates=total_candidates,
                mapping_details=mapping_results
            )
            
        except Exception as e:
            logger.error(f"❌ Mapping test failed for {doc_path.name}: {e}")
            return MappingTestResult(
                document_name=doc_path.name,
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000,
                products_found=0,
                high_confidence_matches=0,
                total_candidates=0,
                error=str(e)
            )
    
    def _test_galaxy_mapping(self, text_content: str) -> Dict[str, Any]:
        """Test Galaxy 6000 specific mapping"""
        try:
            # Search for Galaxy products
            galaxy_search = self.mapping_service.search_products_by_text("Galaxy 6000")
            
            # Analyze results
            candidates = []
            for product in galaxy_search.get("products", []):
                candidates.append({
                    "product_identifier": product.get("PRODUCT_IDENTIFIER"),
                    "range_label": product.get("RANGE_LABEL"),
                    "product_description": product.get("PRODUCT_DESCRIPTION"),
                    "confidence_score": 0.95,  # High confidence for exact match
                    "match_reason": "Direct Galaxy product match"
                })
            
            return {
                "strategy": "Galaxy 6000 Direct Search",
                "candidates": candidates,
                "matched_products": [c for c in candidates if c["confidence_score"] > 0.8],
                "search_terms": ["Galaxy 6000", "Galaxy", "UPS"],
                "confidence_explanation": "Direct product name matching with Galaxy range"
            }
        except Exception as e:
            return {"strategy": "Galaxy 6000 Direct Search", "error": str(e)}
    
    def _test_pix_mapping(self, text_content: str) -> Dict[str, Any]:
        """Test PIX specific mapping"""
        try:
            # Search for PIX products
            pix_search = self.mapping_service.search_products_by_text("PIX")
            
            candidates = []
            for product in pix_search.get("products", []):
                confidence = 0.9 if "PIX" in product.get("RANGE_LABEL", "") else 0.7
                candidates.append({
                    "product_identifier": product.get("PRODUCT_IDENTIFIER"),
                    "range_label": product.get("RANGE_LABEL"),
                    "product_description": product.get("PRODUCT_DESCRIPTION"),
                    "confidence_score": confidence,
                    "match_reason": "PIX range match"
                })
            
            return {
                "strategy": "PIX Range Search",
                "candidates": candidates,
                "matched_products": [c for c in candidates if c["confidence_score"] > 0.8],
                "search_terms": ["PIX", "PIX2B", "Double Bus Bar"],
                "confidence_explanation": "PIX range and subrange matching"
            }
        except Exception as e:
            return {"strategy": "PIX Range Search", "error": str(e)}
    
    def _test_sepam_mapping(self, text_content: str) -> Dict[str, Any]:
        """Test SEPAM specific mapping"""
        try:
            # Search for SEPAM products
            sepam_search = self.mapping_service.search_products_by_text("SEPAM")
            
            candidates = []
            for product in sepam_search.get("products", []):
                confidence = 0.95 if "SEPAM" in product.get("RANGE_LABEL", "") else 0.8
                candidates.append({
                    "product_identifier": product.get("PRODUCT_IDENTIFIER"),
                    "range_label": product.get("RANGE_LABEL"),
                    "product_description": product.get("PRODUCT_DESCRIPTION"),
                    "confidence_score": confidence,
                    "match_reason": "SEPAM protection relay match"
                })
            
            return {
                "strategy": "SEPAM Protection Search",
                "candidates": candidates,
                "matched_products": [c for c in candidates if c["confidence_score"] > 0.8],
                "search_terms": ["SEPAM", "SEPAM 20", "SEPAM 40", "Protection Relay"],
                "confidence_explanation": "SEPAM protection relay family matching"
            }
        except Exception as e:
            return {"strategy": "SEPAM Protection Search", "error": str(e)}
    
    def _test_intelligent_mapping(self, text_content: str, document_name: str) -> Dict[str, Any]:
        """Test intelligent mapping using hierarchical search"""
        try:
            # Extract potential product terms from text
            product_terms = self._extract_product_terms(text_content)
            
            all_candidates = []
            for term in product_terms:
                search_result = self.mapping_service.search_products_by_text(term)
                
                for product in search_result.get("products", []):
                    confidence = self._calculate_intelligent_confidence(term, product, text_content)
                    all_candidates.append({
                        "product_identifier": product.get("PRODUCT_IDENTIFIER"),
                        "range_label": product.get("RANGE_LABEL"),
                        "product_description": product.get("PRODUCT_DESCRIPTION"),
                        "confidence_score": confidence,
                        "match_reason": f"Intelligent match for term: {term}",
                        "search_term": term
                    })
            
            # Deduplicate and rank
            unique_candidates = {}
            for candidate in all_candidates:
                key = candidate["product_identifier"]
                if key not in unique_candidates or candidate["confidence_score"] > unique_candidates[key]["confidence_score"]:
                    unique_candidates[key] = candidate
            
            ranked_candidates = sorted(unique_candidates.values(), key=lambda x: x["confidence_score"], reverse=True)
            
            return {
                "strategy": "Intelligent Hierarchical Search",
                "candidates": ranked_candidates[:20],  # Top 20 candidates
                "matched_products": [c for c in ranked_candidates if c["confidence_score"] > 0.7],
                "search_terms": product_terms,
                "confidence_explanation": "Intelligent term extraction with hierarchical product matching"
            }
        except Exception as e:
            return {"strategy": "Intelligent Hierarchical Search", "error": str(e)}
    
    def _extract_product_terms(self, text_content: str) -> List[str]:
        """Extract potential product terms from document text"""
        # Common product patterns in Schneider Electric documents
        potential_terms = []
        
        # Look for common product patterns
        import re
        
        # Range patterns
        range_patterns = [
            r'\b[A-Z]{2,}\s*\d+[A-Z]*\b',  # e.g., SEPAM20, PIX2B
            r'\b[A-Z][a-z]+\s*\d+\b',      # e.g., Galaxy 6000
            r'\b[A-Z]{3,}\b',               # e.g., SEPAM, MiCOM
        ]
        
        for pattern in range_patterns:
            matches = re.findall(pattern, text_content)
            potential_terms.extend(matches)
        
        # Add specific known terms
        known_terms = ["Galaxy", "PIX", "SEPAM", "MiCOM", "PowerLogic", "Masterpact", "Compact"]
        for term in known_terms:
            if term.lower() in text_content.lower():
                potential_terms.append(term)
        
        # Remove duplicates and return top 10
        unique_terms = list(set(potential_terms))
        return unique_terms[:10]
    
    def _calculate_intelligent_confidence(self, term: str, product: Dict[str, Any], text_content: str) -> float:
        """Calculate intelligent confidence score for product match"""
        confidence = 0.5  # Base confidence
        
        # Exact range match
        if term.upper() in product.get("RANGE_LABEL", "").upper():
            confidence += 0.3
        
        # Description match
        if term.lower() in product.get("PRODUCT_DESCRIPTION", "").lower():
            confidence += 0.2
        
        # Product identifier match
        if term.upper() in product.get("PRODUCT_IDENTIFIER", "").upper():
            confidence += 0.4
        
        # Context boost
        if "obsolete" in text_content.lower() and product.get("OBSOLETE") == "YES":
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _test_search_strategies(self) -> Dict[str, Any]:
        """Test different search strategies"""
        strategies = {
            "exact_range_search": self._test_exact_range_search(),
            "fuzzy_description_search": self._test_fuzzy_description_search(),
            "pl_services_filtering": self._test_pl_services_filtering(),
            "obsolescence_analysis": self._test_obsolescence_analysis()
        }
        return strategies
    
    def _test_exact_range_search(self) -> Dict[str, Any]:
        """Test exact range search strategy"""
        test_ranges = ["Galaxy", "PIX", "SEPAM", "MiCOM", "PowerLogic"]
        results = {}
        
        for range_name in test_ranges:
            search_result = self.mapping_service.search_products_by_text(range_name)
            results[range_name] = {
                "products_found": len(search_result.get("products", [])),
                "search_time_ms": search_result.get("search_time_ms", 0),
                "success": len(search_result.get("products", [])) > 0
            }
        
        return results
    
    def _test_fuzzy_description_search(self) -> Dict[str, Any]:
        """Test fuzzy description search"""
        test_descriptions = ["protection relay", "circuit breaker", "power monitoring", "UPS system"]
        results = {}
        
        for description in test_descriptions:
            search_result = self.mapping_service.search_products_by_text(description)
            results[description] = {
                "products_found": len(search_result.get("products", [])),
                "search_time_ms": search_result.get("search_time_ms", 0),
                "success": len(search_result.get("products", [])) > 0
            }
        
        return results
    
    def _test_pl_services_filtering(self) -> Dict[str, Any]:
        """Test PL services filtering capability"""
        pl_services = ["PPIBS", "IDPAS", "IDIBS", "PSIBS", "SPIBS"]
        results = {}
        
        for pl_service in pl_services:
            query = f"SELECT COUNT(*) as count FROM products WHERE PL_SERVICES = '{pl_service}'"
            result = self.db_service.execute_query(query)
            count = result[0]["count"] if result else 0
            results[pl_service] = {
                "product_count": count,
                "percentage": (count / 342229) * 100  # Total products
            }
        
        return results
    
    def _test_obsolescence_analysis(self) -> Dict[str, Any]:
        """Test obsolescence analysis capabilities"""
        obsolescence_query = """
            SELECT 
                OBSOLETE,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
            FROM products 
            GROUP BY OBSOLETE
        """
        
        results = self.db_service.execute_query(obsolescence_query)
        return {row["OBSOLETE"]: {"count": row["count"], "percentage": row["percentage"]} for row in results}
    
    def _test_business_intelligence(self) -> Dict[str, Any]:
        """Test business intelligence capabilities"""
        try:
            # Get modernization intelligence
            modernization_analysis = self.mapping_service.analyze_modernization_opportunities()
            
            # Range distribution analysis
            range_analysis = self.mapping_service.analyze_range_distribution()
            
            # Product lifecycle analysis
            lifecycle_query = """
                SELECT 
                    CASE 
                        WHEN OBSOLETE = 'YES' THEN 'Obsolete'
                        WHEN PRODUCTION_PHASE = 'YES' THEN 'In Production'
                        WHEN COMMERCIALIZATION_PHASE = 'YES' THEN 'Commercial'
                        ELSE 'Other'
                    END as lifecycle_stage,
                    COUNT(*) as count
                FROM products
                GROUP BY lifecycle_stage
            """
            lifecycle_results = self.db_service.execute_query(lifecycle_query)
            
            return {
                "modernization_opportunities": modernization_analysis,
                "range_distribution": range_analysis,
                "lifecycle_analysis": {row["lifecycle_stage"]: row["count"] for row in lifecycle_results}
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_test_summary(self, mapping_results: List[MappingTestResult], performance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        successful_tests = [r for r in mapping_results if r.success]
        failed_tests = [r for r in mapping_results if not r.success]
        
        avg_processing_time = sum(r.processing_time_ms for r in successful_tests) / len(successful_tests) if successful_tests else 0
        total_products_found = sum(r.products_found for r in successful_tests)
        total_high_confidence = sum(r.high_confidence_matches for r in successful_tests)
        
        # Performance summary
        performance_times = [r.get("query_time_ms", 0) for r in performance_results.values() if isinstance(r, dict) and "query_time_ms" in r]
        avg_query_time = sum(performance_times) / len(performance_times) if performance_times else 0
        
        return {
            "test_success_rate": len(successful_tests) / len(mapping_results) * 100 if mapping_results else 0,
            "total_documents_tested": len(mapping_results),
            "successful_mappings": len(successful_tests),
            "failed_mappings": len(failed_tests),
            "average_processing_time_ms": avg_processing_time,
            "total_products_found": total_products_found,
            "high_confidence_matches": total_high_confidence,
            "average_query_time_ms": avg_query_time,
            "performance_rating": "EXCELLENT" if avg_query_time < 10 else "GOOD" if avg_query_time < 50 else "NEEDS_OPTIMIZATION",
            "database_performance": "Sub-10ms queries" if avg_query_time < 10 else f"{avg_query_time:.2f}ms average"
        }
    
    def display_results(self, results: Dict[str, Any]) -> None:
        """Display test results in a formatted way"""
        print("\n" + "="*80)
        print("🧪 PRODUCT MAPPING TEST RESULTS - SOTA DuckDB Edition")
        print("="*80)
        
        # Summary
        summary = results["summary"]
        print(f"\n📊 TEST SUMMARY:")
        print(f"  Success Rate: {summary['test_success_rate']:.1f}%")
        print(f"  Documents Tested: {summary['total_documents_tested']}")
        print(f"  Products Found: {summary['total_products_found']}")
        print(f"  High Confidence Matches: {summary['high_confidence_matches']}")
        print(f"  Average Processing Time: {summary['average_processing_time_ms']:.2f}ms")
        print(f"  Database Performance: {summary['database_performance']}")
        
        # Database Health
        db_health = results["database_health"]
        print(f"\n🏥 DATABASE HEALTH:")
        print(f"  Status: {db_health.get('health_status', 'Unknown')}")
        print(f"  Total Products: {db_health.get('total_products', 0):,}")
        print(f"  Total Ranges: {db_health.get('total_ranges', 0):,}")
        
        # Document Mapping Results
        print(f"\n📄 DOCUMENT MAPPING RESULTS:")
        for result in results["document_mapping"]:
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.document_name}:")
            print(f"      Products Found: {result.products_found}")
            print(f"      High Confidence: {result.high_confidence_matches}")
            print(f"      Processing Time: {result.processing_time_ms:.2f}ms")
            if result.error:
                print(f"      Error: {result.error}")
        
        # Performance Benchmarks
        print(f"\n⚡ PERFORMANCE BENCHMARKS:")
        for test_name, result in results["performance_benchmarks"].items():
            if isinstance(result, dict) and "query_time_ms" in result:
                rating = result["performance_rating"]
                time_ms = result["query_time_ms"]
                print(f"  {test_name}: {time_ms:.2f}ms ({rating})")
        
        print("\n" + "="*80)


def main():
    """Main test execution"""
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    print("🚀 Starting SOTA Product Database Mapping Tests")
    print("="*60)
    
    # Initialize tester
    tester = ProductMappingTester()
    
    # Run comprehensive tests
    results = tester.run_comprehensive_tests()
    
    # Display results
    tester.display_results(results)
    
    print(f"\n💾 Detailed results saved to: {tester.results_dir}")
    
    return results


if __name__ == "__main__":
    results = main() 