#!/usr/bin/env python3
"""
SOTA Product Database Service
High-performance service for accessing the IBcatalogue DuckDB database

Features:
- Lightning-fast product queries (sub-second performance)
- Intelligent caching with automatic invalidation
- Business intelligence and analytics
- Range mapping and modernization path detection
- Comprehensive product search capabilities
- Production-ready error handling and logging

Version: 1.0.0
Author: SE Letters Team
"""

import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from functools import lru_cache
import threading
from contextlib import contextmanager

import duckdb
import pandas as pd
from loguru import logger

from se_letters.core.config import get_config
from se_letters.core.exceptions import ProcessingError, ValidationError


@dataclass
class ProductMatch:
    """Product match result with confidence scoring"""
    product_identifier: str
    range_label: str
    subrange_label: str
    brand_label: str
    commercial_status: str
    pl_services: str
    confidence_score: float
    match_type: str  # 'exact', 'fuzzy', 'semantic'
    match_fields: List[str]


@dataclass
class RangeAnalysis:
    """Comprehensive range analysis result"""
    range_label: str
    total_products: int
    active_products: int
    obsolete_products: int
    subranges: List[str]
    brands: Set[str]
    pl_services: Set[str]
    commercial_statuses: Dict[str, int]
    modernization_candidates: List[ProductMatch]


@dataclass
class SearchResult:
    """Search result with metadata"""
    products: List[ProductMatch]
    total_count: int
    search_time_ms: float
    cache_hit: bool
    search_strategy: str


class SOTAProductDatabaseService:
    """State-of-the-art product database service"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        """Initialize the SOTA product database service"""
        self.db_path = Path(db_path)
        self.config = get_config()
        
        # Validate database exists
        if not self.db_path.exists():
            raise ProcessingError(f"Product database not found: {self.db_path}")
        
        # Thread safety
        self._lock = threading.RLock()
        self._connection_pool = {}
        
        # Caching system
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_stats = {'hits': 0, 'misses': 0}
        
        # Performance metrics
        self.performance_metrics = {
            'total_queries': 0,
            'avg_query_time_ms': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # Load database metadata
        self._load_database_metadata()
        
        logger.info(f"🚀 SOTA Product Database Service initialized")
        logger.info(f"📊 Database: {self.db_path} ({self._get_file_size_mb():.1f} MB)")
        logger.info(f"🔢 Products: {self.total_products:,}")
        logger.info(f"📈 Performance: Sub-second queries enabled")
    
    def _load_database_metadata(self) -> None:
        """Load database metadata for quick access"""
        with self._get_connection() as conn:
            # Get basic counts
            self.total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            self.total_ranges = conn.execute("SELECT COUNT(DISTINCT range_label) FROM products WHERE range_label != ''").fetchone()[0]
            
            # Get PL services
            pl_results = conn.execute("SELECT DISTINCT pl_services FROM products WHERE pl_services != ''").fetchall()
            self.available_pl_services = {row[0] for row in pl_results}
            
            # Get obsolete statuses
            self.obsolete_statuses = {
                '18-End of commercialisation',
                '19-end of commercialization block',
                '14-End of commerc. announced',
                '20-Temporary block'
            }
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup"""
        thread_id = threading.get_ident()
        
        if thread_id not in self._connection_pool:
            self._connection_pool[thread_id] = duckdb.connect(str(self.db_path))
        
        conn = self._connection_pool[thread_id]
        try:
            yield conn
        finally:
            # Connection remains in pool for reuse
            pass
    
    def _get_file_size_mb(self) -> float:
        """Get database file size in MB"""
        return self.db_path.stat().st_size / 1024 / 1024
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operation"""
        key_data = f"{operation}:{hash(frozenset(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid"""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                self._cache_stats['hits'] += 1
                return result
            else:
                del self._cache[cache_key]
        
        self._cache_stats['misses'] += 1
        return None
    
    def _set_cached_result(self, cache_key: str, result: Any) -> None:
        """Set cached result with timestamp"""
        self._cache[cache_key] = (result, time.time())
    
    def _update_performance_metrics(self, query_time_ms: float) -> None:
        """Update performance metrics"""
        self.performance_metrics['total_queries'] += 1
        
        # Calculate rolling average
        total_queries = self.performance_metrics['total_queries']
        current_avg = self.performance_metrics['avg_query_time_ms']
        new_avg = ((current_avg * (total_queries - 1)) + query_time_ms) / total_queries
        self.performance_metrics['avg_query_time_ms'] = new_avg
        
        # Update cache hit rate
        total_cache_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        if total_cache_requests > 0:
            self.performance_metrics['cache_hit_rate'] = self._cache_stats['hits'] / total_cache_requests
    
    def find_products_by_range(self, range_name: str, include_obsolete: bool = True) -> SearchResult:
        """Find products by range name with intelligent matching"""
        cache_key = self._get_cache_key('find_by_range', range=range_name, include_obsolete=include_obsolete)
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result:
            cached_result.cache_hit = True
            return cached_result
        
        start_time = time.time()
        
        with self._get_connection() as conn:
            # Build query with multiple matching strategies
            where_conditions = [
                "range_label = ?",
                "range_label_norm LIKE ?",
                "range_label_norm LIKE ?",
                "range_label_norm LIKE ?"
            ]
            
            params = [
                range_name,
                f"%{range_name.upper()}%",
                f"{range_name.upper()}%",
                f"%{range_name.upper()}"
            ]
            
            if not include_obsolete:
                obsolete_placeholders = ','.join(['?' for _ in self.obsolete_statuses])
                where_conditions.append(f"commercial_status NOT IN ({obsolete_placeholders})")
                params.extend(self.obsolete_statuses)
            
            query = f"""
                SELECT 
                    product_identifier, range_label, subrange_label, brand_label,
                    commercial_status, pl_services, product_description,
                    CASE 
                        WHEN range_label = ? THEN 1.0
                        WHEN range_label_norm = ? THEN 0.9
                        WHEN range_label_norm LIKE ? THEN 0.8
                        ELSE 0.7
                    END as confidence_score
                FROM products 
                WHERE ({' OR '.join(where_conditions[:4])})
                {"AND " + where_conditions[4] if not include_obsolete else ""}
                ORDER BY confidence_score DESC, range_label, product_identifier
                LIMIT 1000
            """
            
            # Add confidence calculation parameters
            confidence_params = [range_name, range_name.upper(), f"%{range_name.upper()}%"]
            final_params = confidence_params + params
            
            results = conn.execute(query, final_params).fetchall()
            
            # Convert to ProductMatch objects
            products = []
            for row in results:
                match_fields = self._determine_match_fields(row, range_name)
                confidence_score = float(row[7]) if row[7] is not None else 0.0
                match_type = 'exact' if confidence_score >= 0.9 else 'fuzzy'
                
                products.append(ProductMatch(
                    product_identifier=row[0] or '',
                    range_label=row[1] or '',
                    subrange_label=row[2] or '',
                    brand_label=row[3] or '',
                    commercial_status=row[4] or '',
                    pl_services=row[5] or '',
                    confidence_score=confidence_score,
                    match_type=match_type,
                    match_fields=match_fields
                ))
        
        search_time_ms = (time.time() - start_time) * 1000
        self._update_performance_metrics(search_time_ms)
        
        result = SearchResult(
            products=products,
            total_count=len(products),
            search_time_ms=search_time_ms,
            cache_hit=False,
            search_strategy='range_matching'
        )
        
        self._set_cached_result(cache_key, result)
        return result
    
    def find_products_by_multiple_ranges(self, range_names: List[str], include_obsolete: bool = True) -> SearchResult:
        """Find products by multiple range names efficiently"""
        if not range_names:
            return SearchResult([], 0, 0.0, False, 'empty_query')
        
        cache_key = self._get_cache_key('find_by_multiple_ranges', ranges=tuple(sorted(range_names)), include_obsolete=include_obsolete)
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result:
            cached_result.cache_hit = True
            return cached_result
        
        start_time = time.time()
        
        with self._get_connection() as conn:
            # Build dynamic query for multiple ranges
            range_conditions = []
            params = []
            
            for range_name in range_names:
                range_conditions.extend([
                    "range_label = ?",
                    "range_label_norm LIKE ?",
                    "range_label_norm LIKE ?",
                    "range_label_norm LIKE ?"
                ])
                params.extend([
                    range_name,
                    f"%{range_name.upper()}%",
                    f"{range_name.upper()}%",
                    f"%{range_name.upper()}"
                ])
            
            where_clause = f"({' OR '.join(range_conditions)})"
            
            if not include_obsolete:
                obsolete_placeholders = ','.join(['?' for _ in self.obsolete_statuses])
                where_clause += f" AND commercial_status NOT IN ({obsolete_placeholders})"
                params.extend(self.obsolete_statuses)
            
            query = f"""
                SELECT DISTINCT
                    product_identifier, range_label, subrange_label, brand_label,
                    commercial_status, pl_services, product_description,
                    0.8 as confidence_score
                FROM products 
                WHERE {where_clause}
                ORDER BY range_label, product_identifier
                LIMIT 5000
            """
            
            results = conn.execute(query, params).fetchall()
            
            # Convert to ProductMatch objects
            products = []
            for row in results:
                products.append(ProductMatch(
                    product_identifier=row[0] or '',
                    range_label=row[1] or '',
                    subrange_label=row[2] or '',
                    brand_label=row[3] or '',
                    commercial_status=row[4] or '',
                    pl_services=row[5] or '',
                    confidence_score=row[6],
                    match_type='multi_range',
                    match_fields=['range_label']
                ))
        
        search_time_ms = (time.time() - start_time) * 1000
        self._update_performance_metrics(search_time_ms)
        
        result = SearchResult(
            products=products,
            total_count=len(products),
            search_time_ms=search_time_ms,
            cache_hit=False,
            search_strategy='multi_range_matching'
        )
        
        self._set_cached_result(cache_key, result)
        return result
    
    def analyze_range(self, range_name: str) -> RangeAnalysis:
        """Perform comprehensive analysis of a product range"""
        cache_key = self._get_cache_key('analyze_range', range=range_name)
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result:
            return cached_result
        
        with self._get_connection() as conn:
            # Get range products
            range_products = conn.execute("""
                SELECT product_identifier, subrange_label, brand_label, commercial_status, pl_services
                FROM products 
                WHERE range_label_norm LIKE ?
                ORDER BY product_identifier
            """, [f"%{range_name.upper()}%"]).fetchall()
            
            if not range_products:
                return RangeAnalysis(
                    range_label=range_name,
                    total_products=0,
                    active_products=0,
                    obsolete_products=0,
                    subranges=[],
                    brands=set(),
                    pl_services=set(),
                    commercial_statuses={},
                    modernization_candidates=[]
                )
            
            # Analyze products
            total_products = len(range_products)
            obsolete_count = 0
            subranges = set()
            brands = set()
            pl_services = set()
            commercial_statuses = {}
            
            for product in range_products:
                # Count obsolete products
                if product[3] in self.obsolete_statuses:
                    obsolete_count += 1
                
                # Collect unique values
                if product[1]:  # subrange_label
                    subranges.add(product[1])
                if product[2]:  # brand_label
                    brands.add(product[2])
                if product[4]:  # pl_services
                    pl_services.add(product[4])
                
                # Count commercial statuses
                status = product[3] or 'Unknown'
                commercial_statuses[status] = commercial_statuses.get(status, 0) + 1
            
            active_products = total_products - obsolete_count
            
            # Find modernization candidates (similar ranges that are active)
            modernization_candidates = self._find_modernization_candidates(range_name, conn)
        
        result = RangeAnalysis(
            range_label=range_name,
            total_products=total_products,
            active_products=active_products,
            obsolete_products=obsolete_count,
            subranges=list(subranges),
            brands=brands,
            pl_services=pl_services,
            commercial_statuses=commercial_statuses,
            modernization_candidates=modernization_candidates
        )
        
        self._set_cached_result(cache_key, result)
        return result
    
    def _find_modernization_candidates(self, range_name: str, conn: duckdb.DuckDBPyConnection) -> List[ProductMatch]:
        """Find potential modernization candidates for a range"""
        # Extract base range name for similarity matching
        base_name = range_name.split()[0]  # Get first word
        
        candidates = conn.execute("""
            SELECT DISTINCT range_label, COUNT(*) as product_count
            FROM products 
            WHERE range_label_norm LIKE ?
              AND range_label_norm NOT LIKE ?
              AND commercial_status NOT IN ('18-End of commercialisation', 
                                            '19-end of commercialization block',
                                            '14-End of commerc. announced',
                                            '20-Temporary block')
            GROUP BY range_label
            HAVING COUNT(*) > 5
            ORDER BY product_count DESC
            LIMIT 10
        """, [f"%{base_name.upper()}%", f"%{range_name.upper()}%"]).fetchall()
        
        modernization_candidates = []
        for candidate_range, count in candidates:
            modernization_candidates.append(ProductMatch(
                product_identifier='',
                range_label=candidate_range,
                subrange_label='',
                brand_label='',
                commercial_status='Active',
                pl_services='',
                confidence_score=0.7,
                match_type='modernization_candidate',
                match_fields=['range_similarity']
            ))
        
        return modernization_candidates
    
    def _determine_match_fields(self, row: Tuple, search_term: str) -> List[str]:
        """Determine which fields matched the search term"""
        match_fields = []
        search_upper = search_term.upper()
        
        if row[1] and search_upper in row[1].upper():  # range_label
            match_fields.append('range_label')
        if row[2] and search_upper in row[2].upper():  # subrange_label
            match_fields.append('subrange_label')
        if row[3] and search_upper in row[3].upper():  # brand_label
            match_fields.append('brand_label')
        
        return match_fields or ['range_label']  # Default to range_label
    
    def search_products_semantic(self, search_term: str, limit: int = 100) -> SearchResult:
        """Perform semantic search across multiple product fields"""
        cache_key = self._get_cache_key('semantic_search', term=search_term, limit=limit)
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result:
            cached_result.cache_hit = True
            return cached_result
        
        start_time = time.time()
        
        with self._get_connection() as conn:
            search_upper = search_term.upper()
            
            query = """
                SELECT 
                    product_identifier, range_label, subrange_label, brand_label,
                    commercial_status, pl_services, product_description,
                    CASE 
                        WHEN range_label_norm LIKE ? THEN 1.0
                        WHEN LOWER(subrange_label) LIKE ? THEN 0.9
                        WHEN brand_label_norm LIKE ? THEN 0.8
                        WHEN product_description_norm LIKE ? THEN 0.7
                        ELSE 0.6
                    END as confidence_score
                FROM products 
                WHERE range_label_norm LIKE ?
                   OR LOWER(subrange_label) LIKE ?
                   OR brand_label_norm LIKE ?
                   OR product_description_norm LIKE ?
                   OR product_identifier LIKE ?
                ORDER BY confidence_score DESC, range_label
                LIMIT ?
            """
            
            search_pattern = f"%{search_upper}%"
            params = [search_pattern] * 9 + [limit]
            
            results = conn.execute(query, params).fetchall()
            
            # Convert to ProductMatch objects
            products = []
            for row in results:
                match_fields = self._determine_match_fields(row, search_term)
                
                products.append(ProductMatch(
                    product_identifier=row[0] or '',
                    range_label=row[1] or '',
                    subrange_label=row[2] or '',
                    brand_label=row[3] or '',
                    commercial_status=row[4] or '',
                    pl_services=row[5] or '',
                    confidence_score=row[7],
                    match_type='semantic',
                    match_fields=match_fields
                ))
        
        search_time_ms = (time.time() - start_time) * 1000
        self._update_performance_metrics(search_time_ms)
        
        result = SearchResult(
            products=products,
            total_count=len(products),
            search_time_ms=search_time_ms,
            cache_hit=False,
            search_strategy='semantic_search'
        )
        
        self._set_cached_result(cache_key, result)
        return result
    
    def get_pl_services_statistics(self) -> Dict[str, Any]:
        """Get comprehensive PL services statistics"""
        cache_key = self._get_cache_key('pl_services_stats')
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result:
            return cached_result
        
        with self._get_connection() as conn:
            # Get PL services distribution
            pl_stats = conn.execute("""
                SELECT 
                    pl_services,
                    COUNT(*) as total_products,
                    SUM(CASE WHEN commercial_status IN ('18-End of commercialisation', 
                                                        '19-end of commercialization block',
                                                        '14-End of commerc. announced',
                                                        '20-Temporary block') 
                        THEN 1 ELSE 0 END) as obsolete_products,
                    COUNT(DISTINCT range_label) as unique_ranges
                FROM products 
                WHERE pl_services != '' AND pl_services IS NOT NULL
                GROUP BY pl_services
                ORDER BY total_products DESC
            """).fetchall()
            
            result = {
                'distribution': {},
                'total_products_with_pl': sum(row[1] for row in pl_stats),
                'summary': {}
            }
            
            for pl_service, total, obsolete, ranges in pl_stats:
                active = total - obsolete
                result['distribution'][pl_service] = {
                    'total_products': total,
                    'active_products': active,
                    'obsolete_products': obsolete,
                    'unique_ranges': ranges,
                    'obsolescence_rate': (obsolete / total) * 100 if total > 0 else 0
                }
        
        self._set_cached_result(cache_key, result)
        return result
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.performance_metrics,
            'cache_stats': self._cache_stats,
            'database_size_mb': self._get_file_size_mb(),
            'total_products': self.total_products,
            'available_pl_services': list(self.available_pl_services)
        }
    
    def clear_cache(self) -> None:
        """Clear all cached results"""
        with self._lock:
            self._cache.clear()
            self._cache_stats = {'hits': 0, 'misses': 0}
            logger.info("🧹 Cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            start_time = time.time()
            
            with self._get_connection() as conn:
                # Test basic connectivity
                product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                
                # Test index performance
                index_test_time = time.time()
                conn.execute("SELECT COUNT(*) FROM products WHERE range_label = 'Galaxy 6000'").fetchone()
                index_performance_ms = (time.time() - index_test_time) * 1000
                
                # Test complex query performance
                complex_test_time = time.time()
                conn.execute("""
                    SELECT pl_services, COUNT(*) 
                    FROM products 
                    WHERE commercial_status NOT IN ('18-End of commercialisation')
                    GROUP BY pl_services 
                    LIMIT 5
                """).fetchall()
                complex_performance_ms = (time.time() - complex_test_time) * 1000
            
            total_check_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'database_path': str(self.db_path),
                'product_count': product_count,
                'performance': {
                    'total_check_time_ms': total_check_time,
                    'index_performance_ms': index_performance_ms,
                    'complex_query_performance_ms': complex_performance_ms
                },
                'cache_stats': self._cache_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close(self) -> None:
        """Close all database connections"""
        for conn in self._connection_pool.values():
            conn.close()
        self._connection_pool.clear()
        logger.info("🔌 Database connections closed") 