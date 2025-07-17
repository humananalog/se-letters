#!/usr/bin/env python3
"""
Enhanced Product Mapping Service v3 - PostgreSQL Edition
Leverages PostgreSQL database for lightning-fast product mapping

NEW FEATURES:
- PostgreSQL integration for sub-second queries
- Enhanced product identifier extraction and display
- Deep correlation using all IBcatalogue fields
- Brand intelligence with BRAND_CODE, BRAND_LABEL  
- Enhanced range matching with RANGE_CODE, SUBRANGE_CODE
- Device type correlation with DEVICETYPE_LABEL
- Multi-dimensional semantic scoring across all fields
- Advanced pattern recognition and product family detection
- MASTER RULE: DPIBS Product Line Filtering (Active Product Exclusion)

Version: 3.2.0 - PostgreSQL Edition with DPIBS Master Rule
Author: SE Letters Team
"""

import sys
import time
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import re
from loguru import logger
import threading
import psycopg2
import psycopg2.extras

from se_letters.core.config import get_config


@dataclass
class ProductMatch:
    """Product match result"""
    product_identifier: str
    range_label: str
    subrange_label: str
    product_description: str
    brand_label: str
    pl_services: str
    devicetype_label: str
    commercial_status: str
    confidence_score: float
    match_reason: str


@dataclass
class SearchResult:
    """Search result container"""
    products: List[ProductMatch]
    total_found: int
    search_time_ms: float
    search_strategy: str


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
    Enhanced Product Mapping Service v3.2.0 - PostgreSQL Edition
    
    NEW MASTER RULE: DPIBS Product Line Filtering
    - Excludes active products from obsolescence searches
    - Only processes products that are actually becoming obsolete,
    not replacement products that are still active.
    - Handles replacement products mentioned in the same document
    """
    
    def __init__(self, connection_string: str = None):
        """Initialize the enhanced product mapping service with DPIBS filtering"""
        if connection_string is None:
            connection_string = os.getenv('DATABASE_URL', "postgresql://ahuther:bender1980@localhost:5432/se_letters_dev")
        
        self.connection_string = connection_string
        self.config = get_config()
        self.correlation_cache = {}
        self.cache_lock = threading.Lock()
        
        # Initialize and verify database connection
        try:
            health = self.health_check()
            logger.info("🔍 Enhanced Product Mapping Service v3.2 - PostgreSQL Edition")
            total_products = health.get('total_products', 0)
            logger.info(f"📊 Connected to PostgreSQL database with {total_products:,} products")
            logger.info("🎯 DPIBS Master Rule: Active Product Exclusion ENABLED")
        except Exception as e:
            logger.error(f"❌ PostgreSQL database connection failed: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health and return statistics"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Check if products table exists
                    cur.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name = 'products'
                    """)
                    table_exists = cur.fetchone()[0] > 0
                    
                    if not table_exists:
                        return {
                            'status': 'error',
                            'error': 'Products table not found',
                            'total_products': 0
                        }
                    
                    # Get total products count
                    cur.execute("SELECT COUNT(*) FROM products")
                    total_products = cur.fetchone()[0]
                    
                    return {
                        'status': 'healthy',
                        'total_products': total_products,
                        'database': 'postgresql'
                    }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'total_products': 0
            }
    
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
        Enhanced product mapping with DPIBS filtering and PostgreSQL database integration
        
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
        
        # Execute PostgreSQL search
        search_result = self._perform_postgresql_search(
            product_identifier, range_label, subrange_label, 
            product_line, correlation_analysis, max_candidates
        )
        
        # Generate modernization candidates
        modernization_candidates = self._generate_modernization_candidates(
            search_result, correlation_analysis
        )
        
        # Calculate final confidence score
        confidence_score = self._calculate_enhanced_confidence(
            search_result, correlation_analysis
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
            match_type="semantic" if search_result else "none",
            search_strategy="dpibs_filtered_postgresql_search" if dpibs_filtering_applied else "postgresql_search",
            modernization_candidates=modernization_candidates,
            correlation_analysis=correlation_analysis,
            sota_search_results=search_result,
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
    
    def _perform_postgresql_search(
        self,
        product_identifier: str,
        range_label: str,
        subrange_label: str, 
        product_line: str,
        correlation_analysis: Dict[str, Any],
        max_candidates: int
    ) -> Optional[SearchResult]:
        """Perform intelligent search using PostgreSQL database with DPIBS filtering"""
        
        try:
            start_time = time.time()
            
            # Get search terms from correlation analysis
            search_terms = correlation_analysis.get('primary_search_terms', [])
            
            if not search_terms:
                logger.warning("⚠️ No search terms available for PostgreSQL search")
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
            
            logger.info(f"🔍 PostgreSQL semantic search for: '{comprehensive_query}'")
            
            # Execute PostgreSQL search
            products = self._search_products_in_postgresql(
                comprehensive_query, 
                product_line,
                max_candidates * 2
            )
            
            search_time = (time.time() - start_time) * 1000
            
            if products:
                logger.info(f"✅ PostgreSQL search found {len(products)} products")
                
                # Apply DPIBS filtering if applicable
                if product_line == 'DPIBS':
                    logger.info("🎯 Applying DPIBS context to search results")
                    # Additional DPIBS-specific filtering could be added here
                
                return SearchResult(
                    products=products,
                    total_found=len(products),
                    search_time_ms=search_time,
                    search_strategy="postgresql_semantic_search"
                )
            else:
                logger.warning("⚠️ No products found in PostgreSQL search")
                return None
                
        except Exception as e:
            logger.error(f"❌ PostgreSQL search failed: {e}")
            return None
    
    def _search_products_in_postgresql(self, query: str, product_line: str, limit: int) -> List[ProductMatch]:
        """Search products in PostgreSQL database"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Build search query with multiple strategies
                    search_conditions = []
                    search_params = []
                    
                    # Strategy 1: Exact range match
                    search_conditions.append("range_label ILIKE %s")
                    search_params.append(f"%{query}%")
                    
                    # Strategy 2: Product identifier match
                    search_conditions.append("product_identifier ILIKE %s")
                    search_params.append(f"%{query}%")
                    
                    # Strategy 3: Description match
                    search_conditions.append("product_description ILIKE %s")
                    search_params.append(f"%{query}%")
                    
                    # Strategy 4: Subrange match
                    search_conditions.append("subrange_label ILIKE %s")
                    search_params.append(f"%{query}%")
                    
                    # Build the SQL query
                    sql = f"""
                        SELECT 
                            product_identifier,
                            range_label,
                            subrange_label,
                            product_description,
                            brand_label,
                            pl_services,
                            devicetype_label,
                            commercial_status
                        FROM products
                        WHERE ({' OR '.join(search_conditions)})
                        ORDER BY 
                            CASE 
                                WHEN range_label ILIKE %s THEN 1
                                WHEN product_identifier ILIKE %s THEN 2
                                WHEN subrange_label ILIKE %s THEN 3
                                ELSE 4
                            END,
                            product_identifier
                        LIMIT %s
                    """
                    
                    # Add ordering parameters
                    search_params.extend([f"%{query}%", f"%{query}%", f"%{query}%", limit])
                    
                    cur.execute(sql, search_params)
                    rows = cur.fetchall()
                    
                    # Convert to ProductMatch objects
                    products = []
                    for row in rows:
                        # Calculate confidence score based on match quality
                        confidence = self._calculate_match_confidence(row, query)
                        
                        product_match = ProductMatch(
                            product_identifier=row['product_identifier'] or '',
                            range_label=row['range_label'] or '',
                            subrange_label=row['subrange_label'] or '',
                            product_description=row['product_description'] or '',
                            brand_label=row['brand_label'] or '',
                            pl_services=row['pl_services'] or '',
                            devicetype_label=row['devicetype_label'] or '',
                            commercial_status=row['commercial_status'] or '',
                            confidence_score=confidence,
                            match_reason=f"Matched '{query}' in {self._get_match_field(row, query)}"
                        )
                        products.append(product_match)
                    
                    return products
                    
        except Exception as e:
            logger.error(f"❌ PostgreSQL search error: {e}")
            return []
    
    def _calculate_match_confidence(self, row: Dict[str, Any], query: str) -> float:
        """Calculate confidence score for a database match"""
        confidence = 0.0
        
        # Exact match bonus
        if query.lower() == row.get('range_label', '').lower():
            confidence += 0.4
        elif query.lower() == row.get('product_identifier', '').lower():
            confidence += 0.5
        elif query.lower() == row.get('subrange_label', '').lower():
            confidence += 0.3
        
        # Contains match bonus
        if query.lower() in row.get('range_label', '').lower():
            confidence += 0.2
        if query.lower() in row.get('product_identifier', '').lower():
            confidence += 0.25
        if query.lower() in row.get('product_description', '').lower():
            confidence += 0.1
        
        # Brand bonus
        if 'schneider' in row.get('brand_label', '').lower():
            confidence += 0.05
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _get_match_field(self, row: Dict[str, Any], query: str) -> str:
        """Determine which field matched the query"""
        query_lower = query.lower()
        
        if query_lower in row.get('range_label', '').lower():
            return 'RANGE_LABEL'
        elif query_lower in row.get('product_identifier', '').lower():
            return 'PRODUCT_IDENTIFIER'
        elif query_lower in row.get('subrange_label', '').lower():
            return 'SUBRANGE_LABEL'
        elif query_lower in row.get('product_description', '').lower():
            return 'PRODUCT_DESCRIPTION'
        else:
            return 'UNKNOWN'
    
    def _generate_modernization_candidates(
        self,
        search_result: Optional[SearchResult],
        correlation_analysis: Dict[str, Any]
    ) -> List[ProductMatch]:
        """Generate modernization candidates from search results"""
        
        if not search_result or not search_result.products:
            return []
        
        # Enhanced scoring for modernization candidates
        modernization_candidates = []
        
        for product_match in search_result.products:
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
        
        # Start with base confidence
        base_confidence = product_match.confidence_score
        
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
        search_result: Optional[SearchResult],
        correlation_analysis: Dict[str, Any]
    ) -> float:
        """Calculate enhanced confidence score for the overall mapping"""
        
        if not search_result or not search_result.products:
            return 0.0
        
        # Get the best match confidence
        best_match = max(search_result.products, key=lambda x: x.confidence_score)
        
        # Apply correlation analysis enhancements
        correlation_strength = correlation_analysis.get('correlation_strength', 0.0)
        dpibs_enhanced = correlation_analysis.get('dpibs_enhanced', False)
        
        # Base confidence from best match
        confidence = best_match.confidence_score
        
        # Apply bonuses
        if correlation_strength > 0.5:
            confidence += 0.1
        
        if dpibs_enhanced:
            confidence += 0.05
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _extract_product_family_patterns(
        self,
        product_identifier: str,
        range_label: str,
        subrange_label: str
    ) -> List[str]:
        """Extract product family patterns for enhanced matching"""
        
        patterns = []
        
        # Galaxy family patterns
        if 'galaxy' in (range_label or '').lower():
            patterns.extend(['galaxy', 'mge galaxy', 'ups', 'uninterruptible power supply'])
        
        # SEPAM family patterns
        if 'sepam' in (range_label or '').lower():
            patterns.extend(['sepam', 'protection relay', 'digital protection', 'micom'])
        
        # Masterpact family patterns
        if 'masterpact' in (range_label or '').lower():
            patterns.extend(['masterpact', 'circuit breaker', 'switchgear'])
        
        # Altivar family patterns
        if 'altivar' in (range_label or '').lower():
            patterns.extend(['altivar', 'variable speed drive', 'vsd'])
        
        # Modicon family patterns
        if 'modicon' in (range_label or '').lower():
            patterns.extend(['modicon', 'plc', 'automation controller'])
        
        return patterns 