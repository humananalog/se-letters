#!/usr/bin/env python3
"""
SOTA Product Database Service - Production Version
High-performance service for querying the IBcatalogue database
and discovering product candidates for intelligent matching

Version: 2.0.0
Author: SE Letters Team
Status: Production Ready
"""

import duckdb
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
    """Production service for SOTA product database operations"""
    
    def __init__(self, db_path: str = None):
        """Initialize SOTA product database service"""
        self.config = get_config()
        
        # Use config path if not provided
        if db_path is None:
            try:
                self.db_path = self.config.data.database.product_database
            except (AttributeError, KeyError):
                # Fallback to default path
                self.db_path = "data/IBcatalogue.duckdb"
        else:
            self.db_path = db_path
        
        # Verify database exists
        if not Path(self.db_path).exists():
            logger.error(f"❌ Database not found: {self.db_path}")
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        logger.info("📊 SOTA Product Database Service initialized")
        logger.info(f"🗄️ Database: {self.db_path}")
    
    def discover_product_candidates(self, 
                                    letter_product_info: Any,
                                    max_candidates: int = 1000) -> ProductDiscoveryResult:
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
            filters['product_identifier'] = letter_product_info.product_identifier
        
        if hasattr(letter_product_info, 'range_label'):
            filters['range_label'] = letter_product_info.range_label
        
        if hasattr(letter_product_info, 'product_line'):
            filters['product_line'] = letter_product_info.product_line
        
        if hasattr(letter_product_info, 'product_description'):
            filters['product_description'] = letter_product_info.product_description
        
        return filters
    
    def _execute_discovery_query(self, filters: Dict[str, Any], 
                               max_candidates: int) -> List[ProductCandidate]:
        """Execute product discovery query against database"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Build dynamic query based on filters
                query = self._build_discovery_query(filters, max_candidates)
                
                logger.debug(f"🔍 Executing discovery query: {query}")
                
                # Execute query
                results = conn.execute(query).fetchall()
                
                # Convert to ProductCandidate objects
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
                        pl_services=row[10] or ''
                    )
                    candidates.append(candidate)
                
                return candidates
                
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            return []
    
    def _build_discovery_query(self, filters: Dict[str, Any], 
                             max_candidates: int) -> str:
        """Build dynamic discovery query with improved logic"""
        base_query = """
        SELECT 
            PRODUCT_IDENTIFIER,
            PRODUCT_TYPE,
            PRODUCT_DESCRIPTION,
            BRAND_CODE,
            BRAND_LABEL,
            RANGE_CODE,
            RANGE_LABEL,
            SUBRANGE_CODE,
            SUBRANGE_LABEL,
            DEVICETYPE_LABEL,
            PL_SERVICES
        FROM products
        WHERE 1=1
        """
        
        primary_conditions = []
        secondary_conditions = []
        
        # Primary conditions: Exact matches on key identifiers
        if 'product_identifier' in filters and filters['product_identifier']:
            primary_conditions.append(
                f"PRODUCT_IDENTIFIER ILIKE "
                f"'%{filters['product_identifier']}%'"
            )
        
        if 'range_label' in filters and filters['range_label']:
            primary_conditions.append(
                f"RANGE_LABEL ILIKE '%{filters['range_label']}%'"
            )
        
        # Secondary conditions: Support filters
        if 'product_line' in filters and filters['product_line']:
            # Extract main product line identifier (e.g., "PSIBS" from "PSIBS (Power Systems)")
            pl_main = filters['product_line'].split('(')[0].strip()
            secondary_conditions.append(
                f"PL_SERVICES ILIKE '%{pl_main}%'"
            )
        
        # Extract device type from description for filtering
        device_type_filter = None
        if 'product_description' in filters and filters['product_description']:
            desc = filters['product_description'].lower()
            if 'switchgear' in desc:
                device_type_filter = "DEVICETYPE_LABEL ILIKE '%switchgear%'"
            elif 'transformer' in desc:
                device_type_filter = "DEVICETYPE_LABEL ILIKE '%transformer%'"
            elif 'drive' in desc or 'vsd' in desc:
                device_type_filter = "DEVICETYPE_LABEL ILIKE '%drive%'"
            elif 'contactor' in desc:
                device_type_filter = "DEVICETYPE_LABEL ILIKE '%contactor%'"
            elif 'relay' in desc:
                device_type_filter = "DEVICETYPE_LABEL ILIKE '%relay%'"
        
        # Build the final query logic
        if primary_conditions:
            # If we have primary conditions, use them with AND logic
            base_query += " AND (" + " OR ".join(primary_conditions) + ")"
            
            # Add device type filter if available
            if device_type_filter:
                base_query += f" AND {device_type_filter}"
            
            # Add secondary conditions with OR logic for broader matching
            if secondary_conditions:
                base_query += " OR (" + " OR ".join(secondary_conditions) + ")"
        
        elif secondary_conditions:
            # Fallback to secondary conditions if no primary ones
            base_query += " AND (" + " OR ".join(secondary_conditions) + ")"
            
            # Add device type filter if available
            if device_type_filter:
                base_query += f" AND {device_type_filter}"
        
        else:
            # Last resort: broad search with device type filter
            if device_type_filter:
                base_query += f" AND {device_type_filter}"
        
        # Add ordering and limit
        base_query += f" ORDER BY PRODUCT_IDENTIFIER LIMIT {max_candidates}"
        
        return base_query
    
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
            with duckdb.connect(self.db_path) as conn:
                # Get total product count
                total_count = conn.execute(
                    "SELECT COUNT(*) FROM products"
                ).fetchone()[0]
                
                # Get product line distribution
                pl_distribution = conn.execute("""
                    SELECT PL_SERVICES, COUNT(*) as count
                    FROM products
                    GROUP BY PL_SERVICES
                    ORDER BY count DESC
                    LIMIT 10
                """).fetchall()
                
                # Get brand distribution
                brand_distribution = conn.execute("""
                    SELECT BRAND_LABEL, COUNT(*) as count
                    FROM products
                    GROUP BY BRAND_LABEL
                    ORDER BY count DESC
                    LIMIT 10
                """).fetchall()
                
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
            with duckdb.connect(self.db_path) as conn:
                result = conn.execute("SELECT 1").fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False 