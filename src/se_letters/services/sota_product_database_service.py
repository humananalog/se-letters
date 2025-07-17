#!/usr/bin/env python3
"""
SOTA Product Database Service - PostgreSQL Version
High-performance service for querying the IBcatalogue database
and discovering product candidates for intelligent matching

Version: 2.3.0
Author: Alexandre Huther
Status: Production Ready - PostgreSQL Migration
"""

import psycopg2
import psycopg2.extras
import time
from pathlib import Path
from typing import Dict, List, Any

from loguru import logger

from se_letters.core.config import get_config
from se_letters.models.product_matching import (
    ProductCandidate,
    ProductDiscoveryResult
)


class SOTAProductDatabaseService:
    """Production service for SOTA product database operations with PostgreSQL"""
    
    def __init__(self, connection_string: str = None):
        """Initialize SOTA product database service"""
        self.config = get_config()
        
        # Use config connection string if not provided
        if connection_string is None:
            try:
                # Try to get PostgreSQL connection from environment
                import os
                self.connection_string = os.getenv('DATABASE_URL', "postgresql://ahuther:bender1980@localhost:5432/se_letters_dev")
            except (AttributeError, KeyError):
                # Fallback to default connection
                self.connection_string = "postgresql://ahuther:bender1980@localhost:5432/se_letters_dev"
        else:
            self.connection_string = connection_string
        
        logger.info("📊 SOTA Product Database Service initialized (PostgreSQL)")
        logger.info(f"🗄️ Database: {self.connection_string}")
    
    def discover_product_candidates(
        self, 
        letter_product_info: Any,
        max_candidates: int = 1000
    ) -> ProductDiscoveryResult:
        """Discover product candidates based on letter product information"""
        start_time = time.time()
        
        try:
            logger.info(
                f"🔍 Discovering product candidates for: "
                f"{letter_product_info.product_identifier}"
            )
            
            # Create search filters
            search_filters = self._create_search_filters(letter_product_info)
            
            # Execute discovery query
            candidates = self._execute_discovery_query(
                search_filters, max_candidates
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            result = ProductDiscoveryResult(
                candidates=candidates,
                total_count=len(candidates),
                search_strategy=self._get_search_strategy(search_filters),
                processing_time_ms=processing_time,
                query_filters=search_filters
            )
            
            logger.info(
                f"✅ Product discovery completed in {processing_time:.2f}ms"
            )
            logger.info(f"📊 Found {len(candidates)} product candidates")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Product discovery failed: {e}")
            return ProductDiscoveryResult(
                candidates=[],
                total_count=0,
                search_strategy="error",
                processing_time_ms=(time.time() - start_time) * 1000,
                query_filters={}
            )
    
    def _create_search_filters(self, letter_product_info: Any) -> Dict[str, Any]:
        """Create search filters based on letter product information"""
        filters = {}
        
        # Extract key search terms
        if hasattr(letter_product_info, 'product_identifier'):
            filters['product_identifier'] = (
                letter_product_info.product_identifier
            )
        
        if hasattr(letter_product_info, 'range_label'):
            filters['range_label'] = letter_product_info.range_label
        
        if hasattr(letter_product_info, 'subrange_label'):
            filters['subrange_label'] = letter_product_info.subrange_label
        
        if hasattr(letter_product_info, 'product_line'):
            filters['product_line'] = letter_product_info.product_line
        
        if hasattr(letter_product_info, 'product_description'):
            filters['product_description'] = (
                letter_product_info.product_description
            )
        
        return filters
    
    def _build_discovery_query(
        self, filters: Dict[str, Any], 
        max_candidates: int
    ) -> str:
        """Build dynamic discovery query with multi-factor scoring system"""
        
        # Build the base query with scoring
        base_query = """
        SELECT 
            product_identifier,
            product_type,
            product_description,
            brand_code,
            brand_label,
            range_code,
            range_label,
            subrange_code,
            subrange_label,
            devicetype_label,
            pl_services,
            -- Multi-factor scoring system
            (
                -- Exact matches (highest priority)
                CASE WHEN range_label = %s THEN 3.0 ELSE 0.0 END +
                CASE WHEN subrange_label = %s THEN 3.0 ELSE 0.0 END +
                CASE WHEN product_identifier = %s THEN 4.0 ELSE 0.0 END +
                
                -- Fuzzy similarity matches (medium priority)
                CASE WHEN %s != '' AND range_label ILIKE '%%' || %s || '%%' THEN 2.0 ELSE 0.0 END +
                CASE WHEN %s != '' AND subrange_label ILIKE '%%' || %s || '%%' THEN 2.0 ELSE 0.0 END +
                CASE WHEN %s != '' AND product_identifier ILIKE '%%' || %s || '%%' THEN 2.5 ELSE 0.0 END +
                
                -- Product line alignment
                CASE WHEN pl_services = %s THEN 1.5 ELSE 0.0 END +
                CASE WHEN %s != '' AND pl_services ILIKE '%%' || %s || '%%' THEN 1.0 ELSE 0.0 END +
                
                -- Brand alignment
                CASE WHEN brand_label = %s THEN 1.0 ELSE 0.0 END +
                CASE WHEN %s != '' AND brand_label ILIKE '%%' || %s || '%%' THEN 0.5 ELSE 0.0 END +
                
                -- Device type alignment (if specified)
                CASE WHEN %s != '' AND devicetype_label ILIKE '%%' || %s || '%%' THEN 0.5 ELSE 0.0 END +
                
                -- Description relevance
                CASE WHEN %s != '' AND product_description ILIKE '%%' || %s || '%%' THEN 0.5 ELSE 0.0 END
            ) AS match_score
        FROM products
        WHERE 1=1
        """
        
        # Add PRECISE filtering to reduce search space
        where_conditions = []
        
        # CRITICAL FIX 1: Obsolescence Status Filtering - Only get OBSOLETE products
        obsolescence_conditions = [
            # Exact status codes from database analysis
            "COMMERCIAL_STATUS = '19-end of commercialization block'",
            "COMMERCIAL_STATUS = '18-End of commercialisation'", 
            "COMMERCIAL_STATUS = '14-End of commerc. announced'",
            "COMMERCIAL_STATUS = '16-Post commercialisation'",
            # Fallback patterns for other obsolescence indicators
            "COMMERCIAL_STATUS ILIKE '%obsolescence%'",
            "COMMERCIAL_STATUS ILIKE '%discontinued%'",
            "COMMERCIAL_STATUS ILIKE '%end of service%'"
        ]
        where_conditions.append(f"({' OR '.join(obsolescence_conditions)})")
        
        # CRITICAL FIX 2: Precise Range Label Filtering
        if filters.get('range_label'):
            range_label = filters['range_label'].strip()
            
            # Use EXACT range matching first, then precise contains
            range_conditions = []
            
            # Exact range match (highest priority)
            range_conditions.append(f"RANGE_LABEL = '{range_label}'")
            
            # Precise contains match (only if range is part of the actual range name)
            range_conditions.append(f"RANGE_LABEL ILIKE '{range_label} %'")  # Range followed by space
            range_conditions.append(f"RANGE_LABEL ILIKE '% {range_label}'")  # Space followed by range
            range_conditions.append(f"RANGE_LABEL ILIKE '% {range_label} %'")  # Space on both sides
            
            # For specific known patterns
            if range_label.upper() == 'GALAXY':
                range_conditions.append("RANGE_LABEL ILIKE 'MGE Galaxy%'")
                range_conditions.append("RANGE_LABEL ILIKE 'APC Galaxy%'")
            elif range_label.upper() == 'MICOM':
                range_conditions.append("RANGE_LABEL ILIKE 'MiCOM%'")
                range_conditions.append("RANGE_LABEL ILIKE 'MICOM%'")
            elif range_label.upper() == 'SEPAM':
                range_conditions.append("RANGE_LABEL ILIKE 'SEPAM%'")
            elif range_label.upper() == 'PIX':
                range_conditions.append("RANGE_LABEL ILIKE 'PIX%'")
            
            where_conditions.append(f"({' OR '.join(range_conditions)})")
        
        # CRITICAL FIX 3: Exact Product Line Filtering
        if filters.get('product_line'):
            pl_main = filters['product_line'].split('(')[0].strip()
            # Use EXACT matching for product lines
            where_conditions.append(f"PL_SERVICES = '{pl_main}'")
        
        # CRITICAL FIX 4: Precise Subrange Filtering (only if subrange is provided AND not empty)
        if filters.get('subrange_label') and filters.get('subrange_label').strip():
            subrange_label = filters['subrange_label'].strip()
            
            # Check if the range already includes the subrange (like 'MGE Galaxy 6000')
            range_includes_subrange = False
            if filters.get('range_label'):
                range_label = filters['range_label'].strip()
                if subrange_label in range_label:
                    range_includes_subrange = True
            
            if not range_includes_subrange:
                subrange_conditions = [
                    f"SUBRANGE_LABEL = '{subrange_label}'",
                    f"SUBRANGE_LABEL ILIKE '{subrange_label} %'",
                    f"SUBRANGE_LABEL ILIKE '% {subrange_label}'",
                    f"SUBRANGE_LABEL ILIKE '% {subrange_label} %'"
                ]
                where_conditions.append(f"({' OR '.join(subrange_conditions)})")
        
        # Add device type filter if available (keep as is)
        device_type = self._extract_device_type(filters.get('product_description', ''))
        if device_type:
            where_conditions.append(f"DEVICETYPE_LABEL ILIKE '%{device_type}%'")
        
        # Add WHERE conditions
        if where_conditions:
            base_query += " AND (" + " AND ".join(where_conditions) + ")"
        
        # Add ordering by score and limit
        base_query += " ORDER BY match_score DESC LIMIT %s"
        
        return base_query
    
    def _extract_device_type(self, description: str) -> str:
        """Extract device type from product description"""
        if not description:
            return ""
        
        desc = description.lower()
        if 'switchgear' in desc:
            return 'switchgear'
        elif 'transformer' in desc:
            return 'transformer'
        elif 'drive' in desc or 'vsd' in desc:
            return 'drive'
        elif 'contactor' in desc:
            return 'contactor'
        elif 'relay' in desc:
            return 'relay'
        elif 'ups' in desc:
            return 'ups'
        elif 'circuit breaker' in desc or 'acb' in desc:
            return 'circuit breaker'
        elif 'motor' in desc:
            return 'motor'
        elif 'sensor' in desc:
            return 'sensor'
        elif 'controller' in desc:
            return 'controller'
        
        return ""
    
    def _execute_discovery_query(
        self, filters: Dict[str, Any], 
        max_candidates: int
    ) -> List[ProductCandidate]:
        """Execute product discovery query with scoring"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                # Build dynamic query based on filters
                query = self._build_discovery_query(filters, max_candidates)
                
                # Prepare parameters for the query (PostgreSQL uses %s placeholders)
                params = [
                    filters.get('range_label', ''),  # Exact range match
                    filters.get('subrange_label', ''),  # Exact subrange match
                    filters.get('product_identifier', ''),  # Exact product ID match
                    filters.get('range_label', ''),  # Fuzzy range check
                    filters.get('range_label', ''),  # Fuzzy range value
                    filters.get('subrange_label', ''),  # Fuzzy subrange check
                    filters.get('subrange_label', ''),  # Fuzzy subrange value
                    filters.get('product_identifier', ''),  # Fuzzy product ID check
                    filters.get('product_identifier', ''),  # Fuzzy product ID value
                    filters.get('product_line', '').split('(')[0].strip(),  # Exact PL match
                    filters.get('product_line', '').split('(')[0].strip(),  # Fuzzy PL check
                    filters.get('product_line', '').split('(')[0].strip(),  # Fuzzy PL value
                    filters.get('brand_label', ''),  # Exact brand match
                    filters.get('brand_label', ''),  # Fuzzy brand check
                    filters.get('brand_label', ''),  # Fuzzy brand value
                    self._extract_device_type(filters.get('product_description', '')),  # Device type check
                    self._extract_device_type(filters.get('product_description', '')),  # Device type value
                    filters.get('product_description', ''),  # Description check
                    filters.get('product_description', ''),  # Description value
                    max_candidates  # Limit
                ]
                
                logger.debug(f"🔍 Executing scored discovery query")
                logger.debug(f"📊 Parameters: {params[:5]}...")  # Log first 5 params
                
                # Execute query with parameters
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                
                # Convert to ProductCandidate objects with scores
                candidates = []
                for row in results:
                    candidate = ProductCandidate(
                        product_identifier=row[0] or '',
                        product_type=row[1] or '',
                        product_description=row[2] or '',
                        brand_code=row[3] or '',
                        brand_label=row[4] or '',
                        range_code=row[5] or '',
                        range_label=row[6] or '',
                        subrange_code=row[7] or '',
                        subrange_label=row[8] or '',
                        devicetype_label=row[9] or '',
                        pl_services=row[10] or '',
                        match_score=float(row[11]) if row[11] else 0.0
                    )
                    candidates.append(candidate)
                
                # Log scoring results
                if candidates:
                    top_score = max(c.match_score for c in candidates)
                    avg_score = sum(c.match_score for c in candidates) / len(candidates)
                    logger.info(f"📊 Scoring results - Top: {top_score:.2f}, Avg: {avg_score:.2f}")
                    logger.info(f"🎯 Top 3 candidates:")
                    for i, candidate in enumerate(candidates[:3]):
                        logger.info(f"  {i+1}. {candidate.range_label} {candidate.subrange_label} (Score: {candidate.match_score:.2f})")
                
                return candidates
                
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            return []
    
    def _get_search_strategy(self, filters: Dict[str, Any]) -> str:
        """Get search strategy description"""
        strategies = []
        
        if 'product_identifier' in filters:
            strategies.append("product_identifier")
        
        if 'range_label' in filters:
            strategies.append("range_label")
        
        if 'product_line' in filters:
            strategies.append("product_line")
        
        if 'product_description' in filters:
            strategies.append("product_description")
        
        return " + ".join(strategies) if strategies else "fallback"
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    # Get total product count
                    cursor.execute("SELECT COUNT(*) FROM products")
                    total_count = cursor.fetchone()[0]
                    
                    # Get product line distribution
                    cursor.execute("""
                        SELECT pl_services, COUNT(*) as count
                        FROM products
                        GROUP BY pl_services
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    pl_distribution = cursor.fetchall()
                    
                    # Get brand distribution
                    cursor.execute("""
                        SELECT brand_label, COUNT(*) as count
                        FROM products
                        GROUP BY brand_label
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    brand_distribution = cursor.fetchall()
                    
                    return {
                        'total_products': total_count,
                        'product_line_distribution': pl_distribution,
                        'brand_distribution': brand_distribution
                    }
                
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {
                'total_products': 0,
                'product_line_distribution': [],
                'brand_distribution': []
            }
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False 