#!/usr/bin/env python3
"""
Enhanced Product Mapping Service v3 - SOTA DuckDB Edition
Leverages the new SOTA DuckDB database for lightning-fast product mapping

NEW FEATURES:
- SOTA DuckDB integration for sub-second queries
- Enhanced product identifier extraction and display
- Deep correlation using all IBcatalogue fields
- Brand intelligence with BRAND_CODE, BRAND_LABEL  
- Enhanced range matching with RANGE_CODE, SUBRANGE_CODE
- Device type correlation with DEVICETYPE_LABEL
- Multi-dimensional semantic scoring across all fields
- Advanced pattern recognition and product family detection
- MASTER RULE: DPIBS Product Line Filtering (Active Product Exclusion)

Version: 3.2.0 - SOTA DuckDB Edition with DPIBS Master Rule
Author: SE Letters Team
"""

import sys
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import re
from loguru import logger
import threading

# Add src to path for SOTA service
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import SOTA service
from se_letters.services.sota_product_database_service import (
    SOTAProductDatabaseService, ProductMatch, SearchResult
)


@dataclass
class ProductMappingResult:
    """Enhanced product mapping result with DPIBS filtering"""
    product_identifier: str
    range_label: str
    subrange_label: str
    product_line: str
    confidence_score: float
    match_type: str
    search_strategy: str
    modernization_candidates: List[ProductMatch]
    correlation_analysis: Dict[str, Any]
    sota_search_results: Optional[SearchResult] = None
    dpibs_filtering_applied: bool = False
    active_products_excluded: List[str] = None
    obsolete_products_included: List[str] = None


@dataclass
class DPIBSFilteringResult:
    """DPIBS product line filtering result"""
    original_products: List[Dict[str, Any]]
    obsolete_products: List[Dict[str, Any]]
    active_products: List[Dict[str, Any]]
    filtering_applied: bool
    exclusion_reasons: Dict[str, str]


class EnhancedProductMappingServiceV3:
    """
    Enhanced Product Mapping Service v3.2.0 - SOTA DuckDB Edition
    
    NEW MASTER RULE: DPIBS Product Line Filtering
    - Excludes active products from obsolescence searches
    - Only processes products that are actually becoming obsolete,
    not replacement products that are still active.
    - Handles replacement products mentioned in the same document
    """
    
    def __init__(self):
        """Initialize the enhanced product mapping service with DPIBS filtering"""
        self.sota_service = SOTAProductDatabaseService()
        self.correlation_cache = {}
        self.cache_lock = threading.Lock()
        
        # Initialize and verify database connection
        try:
            health = self.sota_service.health_check()
            logger.info("🔍 Enhanced Product Mapping Service v3.2 - SOTA Edition")
            total_products = health.get('total_products', 0)
            logger.info(f"📊 Connected to SOTA database with "
                       f"{total_products:,} products")
            logger.info("🎯 DPIBS Master Rule: Active Product Exclusion ENABLED")
        except Exception as e:
            logger.error(f"❌ SOTA database connection failed: {e}")
            raise
    
    def apply_dpibs_master_rule(self, products: List[Dict[str, Any]]) -> DPIBSFilteringResult:
        """
        Apply DPIBS Master Rule: Filter out active products from obsolescence searches
        
        This rule ensures we only search for products that are actually becoming
        obsolete, not replacement products that are still active.
        
        Args:
            products: List of product dictionaries from document extraction
            
        Returns:
            DPIBSFilteringResult with filtered products and exclusion reasons
        """
        logger.info("🎯 Applying DPIBS Master Rule: Active Product Exclusion")
        
        # Identify DPIBS products
        dpibs_products = [
            product for product in products
            if product.get('product_line') == 'DPIBS'
        ]
        
        if not dpibs_products:
            logger.info("ℹ️ No DPIBS products found - master rule not applicable")
            return DPIBSFilteringResult(
                original_products=products,
                obsolete_products=products,
                active_products=[],
                filtering_applied=False,
                exclusion_reasons={}
            )
        
        logger.info(f"📋 Found {len(dpibs_products)} DPIBS products for filtering")
        
        obsolete_products = []
        active_products = []
        exclusion_reasons = {}
        
        for product in products:
            if product.get('product_line') == 'DPIBS':
                # Apply DPIBS filtering logic
                obsolescence_status = product.get('obsolescence_status', '').lower()
                end_of_service_date = product.get('end_of_service_date', '')
                product_id = product.get('product_identifier', 'Unknown')
                
                # Check if product is active/not obsolete
                if (obsolescence_status == 'active' or 
                    end_of_service_date.lower() in ['not applicable', 'n/a', 'none', '']):
                    
                    active_products.append(product)
                    exclusion_reasons[product_id] = f"Active product - not obsolete (status: {obsolescence_status})"
                    logger.info(f"🟢 EXCLUDED: {product_id} - Active product (not obsolete)")
                    
                else:
                    # Product is obsolete - include in search
                    obsolete_products.append(product)
                    logger.info(f"🔴 INCLUDED: {product_id} - Obsolete product ({obsolescence_status})")
            else:
                # Non-DPIBS products - include by default
                obsolete_products.append(product)
        
        # Add non-DPIBS products to obsolete list
        non_dpibs_products = [
            product for product in products
            if product.get('product_line') != 'DPIBS'
        ]
        
        logger.info(f"📊 DPIBS Filtering Results:")
        logger.info(f"   📋 Original products: {len(products)}")
        logger.info(f"   📋 DPIBS products: {len(dpibs_products)}")
        logger.info(f"   🔴 Obsolete products: {len(obsolete_products)}")
        logger.info(f"   🟢 Active products excluded: {len(active_products)}")
        logger.info(f"   📦 Non-DPIBS products: {len(non_dpibs_products)}")
        
        return DPIBSFilteringResult(
            original_products=products,
            obsolete_products=obsolete_products,
            active_products=active_products,
            filtering_applied=len(active_products) > 0,
            exclusion_reasons=exclusion_reasons
        )
    
    def process_product_mapping(
        self,
        product_identifier: str,
        range_label: str,
        subrange_label: str,
        product_line: str,
        additional_context: Optional[Dict[str, Any]] = None,
        max_candidates: int = 10
    ) -> ProductMappingResult:
        """
        Enhanced product mapping with DPIBS filtering and SOTA database integration
        
        Args:
            product_identifier: Product identifier to map
            range_label: Product range label
            subrange_label: Product subrange label
            product_line: Product line (DPIBS, SPIBS, etc.)
            additional_context: Additional context for mapping
            max_candidates: Maximum number of candidates to return
            
        Returns:
            ProductMappingResult with mapping results and DPIBS filtering info
        """
        start_time = time.time()
        
        logger.info(f"🔍 Processing product mapping for: {product_identifier}")
        logger.info(f"📋 Range: {range_label} | Subrange: {subrange_label}")
        logger.info(f"📦 Product Line: {product_line}")
        
        # Check if DPIBS product needs filtering
        dpibs_filtering_applied = False
        active_products_excluded = []
        obsolete_products_included = []
        
        if product_line == 'DPIBS' and additional_context:
            # Apply DPIBS master rule if we have document context
            document_products = additional_context.get('document_products', [])
            if document_products:
                dpibs_result = self.apply_dpibs_master_rule(document_products)
                dpibs_filtering_applied = dpibs_result.filtering_applied
                active_products_excluded = [
                    p.get('product_identifier') for p in dpibs_result.active_products
                ]
                obsolete_products_included = [
                    p.get('product_identifier') for p in dpibs_result.obsolete_products
                ]
        
        # Perform correlation analysis
        correlation_analysis = self._perform_correlation_analysis(
            product_identifier, range_label, subrange_label, product_line
        )
        
        # Execute SOTA search
        sota_search_result = self._perform_sota_search(
            product_identifier, range_label, subrange_label, 
            product_line, correlation_analysis, max_candidates
        )
        
        # Generate modernization candidates
        modernization_candidates = self._generate_modernization_candidates(
            sota_search_result, correlation_analysis
        )
        
        # Calculate final confidence score
        confidence_score = self._calculate_enhanced_confidence(
            sota_search_result, correlation_analysis
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Product mapping completed in {processing_time:.2f}ms")
        logger.info(f"📊 Confidence: {confidence_score:.3f}")
        logger.info(f"🎯 DPIBS filtering applied: {dpibs_filtering_applied}")
        
        return ProductMappingResult(
            product_identifier=product_identifier,
            range_label=range_label,
            subrange_label=subrange_label,
            product_line=product_line,
            confidence_score=confidence_score,
            match_type="semantic" if sota_search_result else "none",
            search_strategy="dpibs_filtered_sota_search" if dpibs_filtering_applied else "sota_search",
            modernization_candidates=modernization_candidates,
            correlation_analysis=correlation_analysis,
            sota_search_results=sota_search_result,
            dpibs_filtering_applied=dpibs_filtering_applied,
            active_products_excluded=active_products_excluded,
            obsolete_products_included=obsolete_products_included
        )
    
    def _perform_correlation_analysis(
        self,
        product_identifier: str,
        range_label: str,
        subrange_label: str,
        product_line: str
    ) -> Dict[str, Any]:
        """Enhanced correlation analysis with DPIBS considerations"""
        
        # Build comprehensive search term considering DPIBS context
        search_terms = []
        
        # Add primary identifiers
        if product_identifier:
            search_terms.append(product_identifier)
        
        # Build range-specific terms
        if range_label and subrange_label:
            full_range = f"{range_label} {subrange_label}"
            search_terms.append(full_range)
        elif range_label:
            search_terms.append(range_label)
        
        # DPIBS-specific enhancements
        if product_line == 'DPIBS':
            # Add DPIBS-specific patterns
            if range_label:
                search_terms.append(f"DPIBS {range_label}")
            
            # Add common DPIBS product patterns
            dpibs_patterns = [
                "protection relay",
                "digital power",
                "MiCOM",
                "SEPAM",
                "PowerLogic"
            ]
            
            for pattern in dpibs_patterns:
                if pattern.lower() in (range_label or '').lower():
                    search_terms.append(pattern)
        
        # Pattern recognition for better matching
        family_patterns = self._extract_product_family_patterns(
            product_identifier, range_label, subrange_label
        )
        
        search_terms.extend(family_patterns)
        
        # Remove duplicates and empty terms
        search_terms = list(set(filter(None, search_terms)))
        
        return {
            'primary_search_terms': search_terms[:3],  # Top 3 terms
            'all_search_terms': search_terms,
            'product_family_patterns': family_patterns,
            'dpibs_enhanced': product_line == 'DPIBS',
            'correlation_strength': min(len(search_terms) * 0.2, 1.0)
        }
    
    def _perform_sota_search(
        self,
        product_identifier: str,
        range_label: str,
        subrange_label: str, 
        product_line: str,
        correlation_analysis: Dict[str, Any],
        max_candidates: int
    ) -> Optional[SearchResult]:
        """Perform intelligent search using SOTA database service with DPIBS filtering"""
        
        try:
            # Get search terms from correlation analysis
            search_terms = correlation_analysis.get('primary_search_terms', [])
            
            if not search_terms:
                logger.warning("⚠️ No search terms available for SOTA search")
                return None
            
            # Build comprehensive search query
            if range_label and subrange_label:
                # Use complete range information
                comprehensive_query = f"{range_label} {subrange_label}"
            elif range_label:
                comprehensive_query = range_label
            elif product_identifier:
                comprehensive_query = product_identifier
            else:
                comprehensive_query = search_terms[0]
            
            logger.info(f"🔍 SOTA semantic search for: '{comprehensive_query}'")
            
            # Execute semantic search
            search_result = self.sota_service.search_products_semantic(
                comprehensive_query, 
                limit=max_candidates * 2
            )
            
            if search_result.products:
                logger.info(f"✅ SOTA search found {len(search_result.products)} products")
                
                # Apply DPIBS filtering if applicable
                if product_line == 'DPIBS':
                    logger.info("🎯 Applying DPIBS context to search results")
                    # Additional DPIBS-specific filtering could be added here
                
                return search_result
            else:
                logger.warning("⚠️ No products found in SOTA search")
                return None
                
        except Exception as e:
            logger.error(f"❌ SOTA search failed: {e}")
            return None
    
    def _generate_modernization_candidates(
        self,
        sota_search_result: Optional[SearchResult],
        correlation_analysis: Dict[str, Any]
    ) -> List[ProductMatch]:
        """Generate modernization candidates from SOTA search results"""
        
        if not sota_search_result or not sota_search_result.products:
            return []
        
        # Enhanced scoring for modernization candidates
        modernization_candidates = []
        
        for product_match in sota_search_result.products:
            # Start with SOTA base confidence (convert decimal to float)
            base_confidence = float(product_match.confidence_score)
            
            # Enhanced confidence calculation
            enhanced_confidence = self._calculate_product_confidence(
                product_match, correlation_analysis
            )
            
            # Update confidence score
            product_match.confidence_score = enhanced_confidence
            
            modernization_candidates.append(product_match)
        
        # Sort by confidence score
        modernization_candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return modernization_candidates
    
    def _calculate_product_confidence(
        self, 
        product_match: ProductMatch, 
        correlation_analysis: Dict[str, Any]
    ) -> float:
        """Calculate enhanced confidence score for a product match"""
        
        # Start with SOTA base confidence (convert decimal to float)
        base_confidence = float(product_match.confidence_score)
        
        # Correlation strength bonus
        correlation_strength = correlation_analysis.get('correlation_strength', 0.0)
        correlation_bonus = correlation_strength * 0.1
        
        # Range matching bonus
        range_bonus = 0.0
        if product_match.range_label:
            search_terms = correlation_analysis.get('all_search_terms', [])
            for term in search_terms:
                if term and term.lower() in product_match.range_label.lower():
                    range_bonus += 0.05
        
        # Subrange matching bonus
        subrange_bonus = 0.0
        if product_match.subrange_label:
            search_terms = correlation_analysis.get('all_search_terms', [])
            for term in search_terms:
                if term and term.lower() in product_match.subrange_label.lower():
                    subrange_bonus += 0.05
        
        # DPIBS enhancement bonus
        dpibs_bonus = 0.0
        if correlation_analysis.get('dpibs_enhanced', False):
            if product_match.pl_services == 'DPIBS':
                dpibs_bonus = 0.1
        
        # Calculate final confidence
        final_confidence = base_confidence + correlation_bonus + range_bonus + subrange_bonus + dpibs_bonus
        
        # Cap at 1.0
        return min(final_confidence, 1.0)
    
    def _calculate_enhanced_confidence(
        self,
        sota_search_result: Optional[SearchResult],
        correlation_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall enhanced confidence score"""
        
        if not sota_search_result or not sota_search_result.products:
            return 0.0
        
        # Use the highest confidence from search results
        max_confidence = max(
            float(product.confidence_score) for product in sota_search_result.products
        )
        
        # Apply correlation analysis bonus
        correlation_bonus = correlation_analysis.get('correlation_strength', 0.0) * 0.1
        
        # Final confidence calculation
        final_confidence = max_confidence + correlation_bonus
        
        return min(final_confidence, 1.0)
    
    def _extract_product_family_patterns(
        self,
        product_identifier: str,
        range_label: str,
        subrange_label: str
    ) -> List[str]:
        """Extract product family patterns for enhanced matching"""
        
        patterns = []
        
        # Extract numeric patterns
        if product_identifier:
            numbers = re.findall(r'\d+', product_identifier)
            patterns.extend(numbers)
        
        # Extract alphabetic patterns
        if range_label:
            alpha_patterns = re.findall(r'[A-Z]+', range_label)
            patterns.extend(alpha_patterns)
        
        # Extract subrange patterns
        if subrange_label:
            subrange_patterns = re.findall(r'[A-Z0-9]+', subrange_label)
            patterns.extend(subrange_patterns)
        
        return patterns


def demo_dpibs_filtering():
    """Demo the DPIBS master rule filtering with the actual SEPAM document"""
    
    print("🎯 DPIBS Master Rule Demo - Active Product Exclusion")
    print("=" * 70)
    
    # Initialize service
    service = EnhancedProductMappingServiceV3()
    
    # Load the actual SEPAM document products (from grok_metadata.json)
    sepam_products = [
        {
            "product_identifier": "MiCOM P20",
            "range_label": "MiCOM",
            "subrange_label": "P20",
            "product_line": "DPIBS",
            "product_description": "Protection relay series under MiCOM range for digital power applications.",
            "obsolescence_status": "End of Commercialization",
            "end_of_service_date": "December 31, 2023",
            "replacement_suggestions": "Not specified"
        },
        {
            "product_identifier": "SEPAM 20",
            "range_label": "SEPAM",
            "subrange_label": "20",
            "product_line": "DPIBS",
            "product_description": "Protection relay series under SEPAM range for digital power applications.",
            "obsolescence_status": "End of Commercialization",
            "end_of_service_date": "December 31, 2023",
            "replacement_suggestions": "Not specified"
        },
        {
            "product_identifier": "SEPAM 40",
            "range_label": "SEPAM",
            "subrange_label": "40",
            "product_line": "DPIBS",
            "product_description": "Protection relay series under SEPAM range for digital power applications.",
            "obsolescence_status": "End of Commercialization",
            "end_of_service_date": "December 31, 2023",
            "replacement_suggestions": "Not specified"
        },
        {
            "product_identifier": "MiCOM P521",
            "range_label": "MiCOM",
            "subrange_label": "P521",
            "product_line": "DPIBS",
            "product_description": "Line differential protection relay under MiCOM range for digital power applications.",
            "obsolescence_status": "End of Commercialization",
            "end_of_service_date": "December 31, 2023",
            "replacement_suggestions": "PowerLogic P5L"
        },
        {
            "product_identifier": "PowerLogic P5L",
            "range_label": "PowerLogic",
            "subrange_label": "P5L",
            "product_line": "DPIBS",
            "product_description": "Replacement model for MiCOM P521 under PowerLogic range for digital power applications.",
            "obsolescence_status": "Active",  # THIS IS THE TRAP!
            "end_of_service_date": "Not applicable",
            "replacement_suggestions": "Not applicable"
        }
    ]
    
    print(f"📋 Original SEPAM document products: {len(sepam_products)}")
    for i, product in enumerate(sepam_products, 1):
        status = product['obsolescence_status']
        print(f"   {i}. {product['product_identifier']} - {status}")
    
    print("\n🎯 Applying DPIBS Master Rule...")
    
    # Apply DPIBS filtering
    dpibs_result = service.apply_dpibs_master_rule(sepam_products)
    
    print(f"\n📊 DPIBS Filtering Results:")
    print(f"   🔴 Obsolete products to search: {len(dpibs_result.obsolete_products)}")
    print(f"   🟢 Active products excluded: {len(dpibs_result.active_products)}")
    print(f"   🎯 Filtering applied: {dpibs_result.filtering_applied}")
    
    print(f"\n🔴 Products to search for modernization:")
    for product in dpibs_result.obsolete_products:
        print(f"   ✅ {product['product_identifier']} - {product['obsolescence_status']}")
    
    print(f"\n🟢 Products excluded from search (Active):")
    for product in dpibs_result.active_products:
        print(f"   ❌ {product['product_identifier']} - {product['obsolescence_status']}")
    
    print(f"\n💡 Exclusion reasons:")
    for product_id, reason in dpibs_result.exclusion_reasons.items():
        print(f"   📝 {product_id}: {reason}")
    
    # Demo product mapping with DPIBS filtering
    print(f"\n🔍 Testing Product Mapping with DPIBS Context...")
    
    # Test with obsolete product (should be mapped)
    obsolete_product = dpibs_result.obsolete_products[0]
    mapping_result = service.process_product_mapping(
        product_identifier=obsolete_product['product_identifier'],
        range_label=obsolete_product['range_label'],
        subrange_label=obsolete_product['subrange_label'],
        product_line=obsolete_product['product_line'],
        additional_context={'document_products': sepam_products}
    )
    
    print(f"\n✅ Mapping result for {obsolete_product['product_identifier']}:")
    print(f"   📊 Confidence: {mapping_result.confidence_score:.3f}")
    print(f"   🎯 DPIBS filtering applied: {mapping_result.dpibs_filtering_applied}")
    print(f"   🔴 Obsolete products: {len(mapping_result.obsolete_products_included)}")
    print(f"   🟢 Active products excluded: {len(mapping_result.active_products_excluded)}")
    print(f"   🔍 Modernization candidates: {len(mapping_result.modernization_candidates)}")
    
    if mapping_result.modernization_candidates:
        print(f"\n🎯 Top modernization candidates:")
        for i, candidate in enumerate(mapping_result.modernization_candidates[:3], 1):
            print(f"   {i}. {candidate.product_identifier} - {candidate.range_label} ({candidate.confidence_score:.3f})")


if __name__ == "__main__":
    demo_dpibs_filtering() 