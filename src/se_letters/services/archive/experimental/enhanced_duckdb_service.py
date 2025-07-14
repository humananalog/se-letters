#!/usr/bin/env python3
"""
Enhanced DuckDB Service for Multi-Dimensional Product Search.

Leverages subrange, device type, brand, and PL services for refined search.
"""

import time
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass
import duckdb
from loguru import logger


@dataclass
class SearchCriteria:
    """Multi-dimensional search criteria."""

    ranges: List[str] = None
    subranges: List[str] = None
    device_types: List[str] = None
    brands: List[str] = None
    pl_services: List[str] = None
    technical_specs: List[str] = None
    obsolete_only: bool = True


@dataclass
class SearchResult:
    """Enhanced search result with multi-dimensional context."""

    products: List[Dict[str, Any]]
    total_count: int
    search_space_reduction: float
    criteria_used: SearchCriteria
    processing_time_ms: float
    search_strategy: str


class EnhancedDuckDBService:
    """Enhanced DuckDB service with multi-dimensional search capabilities."""

    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        self.conn = duckdb.connect(db_path)
        self.obsolete_statuses = [
            '18-End of commercialisation',
            '19-end of commercialization block',
            '14-End of commerc. announced',
            '20-Temporary block'
        ]
        self._initialize_search_space()

    def _initialize_search_space(self):
        """Initialize search space statistics."""
        # Total products
        self.total_products = self.conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        # Total obsolete products
        status_placeholders = ','.join(['?' for _ in self.obsolete_statuses])
        self.total_obsolete = self.conn.execute(
            f"SELECT COUNT(*) FROM products WHERE COMMERCIAL_STATUS IN "
            f"({status_placeholders})",
            self.obsolete_statuses
        ).fetchone()[0]

        logger.info(
            f"Search space: {self.total_products:,} total products, "
            f"{self.total_obsolete:,} obsolete products"
        )

    def search_products(self, criteria: SearchCriteria) -> SearchResult:
        """Search products using multi-dimensional criteria."""
        start_time = time.time()

        # Build dynamic query based on available criteria
        query_parts = []
        params = []

        # Base query
        base_query = "SELECT * FROM products WHERE 1=1"

        # Add obsolete filter if requested
        if criteria.obsolete_only:
            status_placeholders = ','.join(['?' for _ in self.obsolete_statuses])
            query_parts.append(f"COMMERCIAL_STATUS IN ({status_placeholders})")
            params.extend(self.obsolete_statuses)

        # Add range criteria
        if criteria.ranges:
            range_placeholders = ','.join(['?' for _ in criteria.ranges])
            query_parts.append(f"RANGE_LABEL IN ({range_placeholders})")
            params.extend(criteria.ranges)

        # Add subrange criteria (more granular)
        if criteria.subranges:
            subrange_placeholders = ','.join(['?' for _ in criteria.subranges])
            query_parts.append(f"SUBRANGE_LABEL IN ({subrange_placeholders})")
            params.extend(criteria.subranges)

        # Add device type criteria
        if criteria.device_types:
            device_placeholders = ','.join(['?' for _ in criteria.device_types])
            query_parts.append(f"DEVICETYPE_LABEL IN ({device_placeholders})")
            params.extend(criteria.device_types)

        # Add brand criteria
        if criteria.brands:
            brand_placeholders = ','.join(['?' for _ in criteria.brands])
            query_parts.append(f"BRAND_LABEL IN ({brand_placeholders})")
            params.extend(criteria.brands)

        # Add PL services criteria
        if criteria.pl_services:
            pl_placeholders = ','.join(['?' for _ in criteria.pl_services])
            query_parts.append(f"PL_SERVICES IN ({pl_placeholders})")
            params.extend(criteria.pl_services)

        # Add technical specifications (voltage, current, etc.)
        if criteria.technical_specs:
            tech_conditions = []
            for spec in criteria.technical_specs:
                if spec.startswith('voltage:'):
                    voltage = spec.split(':')[1].strip()
                    tech_conditions.append(
                        f"PRODUCT_DESCRIPTION ILIKE '%{voltage}%'"
                    )
                elif spec.startswith('current:'):
                    current = spec.split(':')[1].strip()
                    tech_conditions.append(
                        f"PRODUCT_DESCRIPTION ILIKE '%{current}%'"
                    )
            if tech_conditions:
                query_parts.append(f"({' OR '.join(tech_conditions)})")

        # Combine query parts
        if query_parts:
            full_query = f"{base_query} AND {' AND '.join(query_parts)}"
        else:
            full_query = base_query

        # Add ordering
        full_query += " ORDER BY RANGE_LABEL, SUBRANGE_LABEL, PRODUCT_IDENTIFIER"

        # Execute query
        try:
            result = self.conn.execute(full_query, params).fetchdf()
            products = result.to_dict('records')
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            products = []

        processing_time = (time.time() - start_time) * 1000

        # Calculate search space reduction
        baseline = self.total_obsolete if criteria.obsolete_only else self.total_products
        reduction = 1.0 - (len(products) / baseline) if baseline > 0 else 0.0

        return SearchResult(
            products=products,
            total_count=len(products),
            search_space_reduction=reduction,
            criteria_used=criteria,
            processing_time_ms=processing_time,
            search_strategy=self._get_search_strategy(criteria)
        )

    def _get_search_strategy(self, criteria: SearchCriteria) -> str:
        """Determine search strategy based on criteria."""
        strategies = []

        if criteria.ranges:
            strategies.append(f"range({len(criteria.ranges)})")
        if criteria.subranges:
            strategies.append(f"subrange({len(criteria.subranges)})")
        if criteria.device_types:
            strategies.append(f"device_type({len(criteria.device_types)})")
        if criteria.brands:
            strategies.append(f"brand({len(criteria.brands)})")
        if criteria.pl_services:
            strategies.append(f"pl_service({len(criteria.pl_services)})")
        if criteria.technical_specs:
            strategies.append(f"tech_spec({len(criteria.technical_specs)})")

        if criteria.obsolete_only:
            strategies.append("obsolete_only")

        return " + ".join(strategies) if strategies else "full_scan"

    def get_search_space_analysis(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """Analyze search space for given criteria."""
        analysis = {
            'total_products': self.total_products,
            'total_obsolete': self.total_obsolete,
            'dimension_counts': {}
        }

        # Count products by dimension
        if criteria.ranges:
            range_placeholders = ','.join(['?' for _ in criteria.ranges])
            count = self.conn.execute(
                f"SELECT COUNT(*) FROM products WHERE RANGE_LABEL IN "
                f"({range_placeholders})",
                criteria.ranges
            ).fetchone()[0]
            analysis['dimension_counts']['ranges'] = count

        if criteria.subranges:
            subrange_placeholders = ','.join(['?' for _ in criteria.subranges])
            count = self.conn.execute(
                f"SELECT COUNT(*) FROM products WHERE SUBRANGE_LABEL IN "
                f"({subrange_placeholders})",
                criteria.subranges
            ).fetchone()[0]
            analysis['dimension_counts']['subranges'] = count

        if criteria.device_types:
            device_placeholders = ','.join(['?' for _ in criteria.device_types])
            count = self.conn.execute(
                f"SELECT COUNT(*) FROM products WHERE DEVICETYPE_LABEL IN "
                f"({device_placeholders})",
                criteria.device_types
            ).fetchone()[0]
            analysis['dimension_counts']['device_types'] = count

        if criteria.brands:
            brand_placeholders = ','.join(['?' for _ in criteria.brands])
            count = self.conn.execute(
                f"SELECT COUNT(*) FROM products WHERE BRAND_LABEL IN "
                f"({brand_placeholders})",
                criteria.brands
            ).fetchone()[0]
            analysis['dimension_counts']['brands'] = count

        if criteria.pl_services:
            pl_placeholders = ','.join(['?' for _ in criteria.pl_services])
            count = self.conn.execute(
                f"SELECT COUNT(*) FROM products WHERE PL_SERVICES IN "
                f"({pl_placeholders})",
                criteria.pl_services
            ).fetchone()[0]
            analysis['dimension_counts']['pl_services'] = count

        return analysis

    def get_dimension_statistics(self) -> Dict[str, Any]:
        """Get statistics for all dimensions."""
        stats = {}

        # Range statistics
        result = self.conn.execute(
            "SELECT COUNT(DISTINCT RANGE_LABEL) FROM products "
            "WHERE RANGE_LABEL IS NOT NULL"
        ).fetchone()
        stats['unique_ranges'] = result[0]

        # Subrange statistics
        result = self.conn.execute(
            "SELECT COUNT(DISTINCT SUBRANGE_LABEL) FROM products "
            "WHERE SUBRANGE_LABEL IS NOT NULL"
        ).fetchone()
        stats['unique_subranges'] = result[0]

        # Device type statistics
        result = self.conn.execute(
            "SELECT COUNT(DISTINCT DEVICETYPE_LABEL) FROM products "
            "WHERE DEVICETYPE_LABEL IS NOT NULL"
        ).fetchone()
        stats['unique_device_types'] = result[0]

        # Brand statistics
        result = self.conn.execute(
            "SELECT COUNT(DISTINCT BRAND_LABEL) FROM products "
            "WHERE BRAND_LABEL IS NOT NULL"
        ).fetchone()
        stats['unique_brands'] = result[0]

        # PL services statistics
        result = self.conn.execute(
            "SELECT COUNT(DISTINCT PL_SERVICES) FROM products "
            "WHERE PL_SERVICES IS NOT NULL"
        ).fetchone()
        stats['unique_pl_services'] = result[0]

        return stats

    def find_related_products(self, product_id: str) -> List[Dict[str, Any]]:
        """Find products related to a given product across dimensions."""
        # Get the reference product
        ref_product = self.conn.execute(
            "SELECT * FROM products WHERE PRODUCT_IDENTIFIER = ?",
            [product_id]
        ).fetchone()

        if not ref_product:
            return []

        # Build criteria based on reference product
        criteria = SearchCriteria(
            ranges=[ref_product[6]] if ref_product[6] else None,  # RANGE_LABEL
            subranges=[ref_product[8]] if ref_product[8] else None,  # SUBRANGE_LABEL
            device_types=[ref_product[10]] if ref_product[10] else None,  # DEVICETYPE_LABEL
            brands=[ref_product[4]] if ref_product[4] else None,  # BRAND_LABEL
            pl_services=[ref_product[24]] if ref_product[24] else None,  # PL_SERVICES
            obsolete_only=False
        )

        # Search for related products
        result = self.search_products(criteria)
        
        # Filter out the reference product itself
        related = [p for p in result.products if p['PRODUCT_IDENTIFIER'] != product_id]
        
        return related

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close() 