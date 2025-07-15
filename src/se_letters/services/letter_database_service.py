#!/usr/bin/env python3
"""
Letter Database Service
Comprehensive service for letter database management with efficient querying, analytics, and operations

Features:
- Advanced search and filtering
- Real-time analytics and statistics
- Bulk operations (delete, reprocess, export)
- Performance optimization with caching
- Comprehensive error handling
- Export functionality (JSON, CSV, Excel)

Version: 1.0.0
Author: SE Letters Team
"""

import json
import time
import csv
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from functools import lru_cache

import duckdb
import pandas as pd
from loguru import logger

from se_letters.core.config import get_config
from se_letters.core.exceptions import ProcessingError, ValidationError


class SortOrder(Enum):
    """Sort order enumeration"""
    ASC = "asc"
    DESC = "desc"


class OperationType(Enum):
    """Database operation types"""
    DELETE = "delete"
    REPROCESS = "reprocess"
    EXPORT = "export"
    ARCHIVE = "archive"


@dataclass
class SearchFilters:
    """Search filters for letter database queries"""
    search_query: Optional[str] = None
    status: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None
    confidence_range: Optional[Dict[str, float]] = None
    processing_time_range: Optional[Dict[str, float]] = None
    product_ranges: Optional[List[str]] = None
    document_types: Optional[List[str]] = None
    sort_by: str = "created_at"
    sort_order: SortOrder = SortOrder.DESC
    page: int = 1
    limit: int = 50


@dataclass
class SearchResult:
    """Search result with pagination and metadata"""
    letters: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    total_pages: int
    filters_applied: SearchFilters
    search_time_ms: float


@dataclass
class DatabaseStats:
    """Database statistics and analytics"""
    total_letters: int
    total_products: int
    avg_confidence: float
    success_rate: float
    avg_processing_time: float
    status_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    top_ranges: List[Dict[str, Any]]
    processing_performance: Dict[str, float]


@dataclass
class OperationResult:
    """Result of database operation"""
    success: bool
    operation: str
    affected_count: int
    results: Optional[List[Any]] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0


class LetterDatabaseService:
    """Comprehensive letter database service with advanced querying and management"""
    
    def __init__(self, db_path: str = "data/letters.duckdb"):
        """Initialize the letter database service"""
        self.db_path = db_path
        
        # Initialize config with defaults if not available
        try:
            self.config = get_config()
        except Exception as e:
            logger.warning(f"⚠️ Could not load config, using defaults: {e}")
            # Create minimal config for basic operations
            from se_letters.core.config import DataConfig, DatabaseConfig
            self.config = None  # We'll handle this gracefully
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Cache settings
        self._cache_ttl = 300  # 5 minutes
        self._cache = {}
        
        # Initialize database connection
        self._init_database()
        
        logger.info(f"📊 Letter Database Service initialized with {self.db_path}")
    
    def _init_database(self) -> None:
        """Initialize database connection and verify schema"""
        try:
            # Test connection
            with duckdb.connect(self.db_path) as conn:
                # Verify main tables exist
                tables = conn.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'main'
                """).fetchall()
                
                table_names = [table[0] for table in tables]
                required_tables = ['letters', 'letter_products', 'processing_debug']
                
                missing_tables = [t for t in required_tables if t not in table_names]
                if missing_tables:
                    raise ProcessingError(f"Missing required tables: {missing_tables}")
                
                logger.info(f"✅ Database schema verified: {len(table_names)} tables found")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise ProcessingError(f"Database initialization failed: {e}")
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operation"""
        key_data = json.dumps({"op": operation, **kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid"""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            else:
                del self._cache[cache_key]
        return None
    
    def _set_cached_result(self, cache_key: str, result: Any) -> None:
        """Set cached result with timestamp"""
        self._cache[cache_key] = (result, time.time())
    
    def search_letters(self, filters: SearchFilters) -> SearchResult:
        """Search letters with advanced filtering and pagination"""
        start_time = time.time()
        
        try:
            with self._lock:
                with duckdb.connect(self.db_path) as conn:
                    # Build base query
                    base_query = """
                        SELECT 
                            l.id, l.document_name, l.document_type, l.document_title,
                            l.source_file_path, l.file_hash, l.file_size,
                            l.processing_method, l.processing_time_ms, l.extraction_confidence,
                            l.created_at, l.updated_at, l.status,
                            l.raw_grok_json, l.validation_details_json, l.processing_steps_json,
                            COUNT(p.id) as product_count
                        FROM letters l
                        LEFT JOIN letter_products p ON l.id = p.letter_id
                    """
                    
                    # Build WHERE clause
                    where_conditions = []
                    params = []
                    
                    if filters.search_query:
                        where_conditions.append("""
                            (l.document_name ILIKE ? OR l.document_title ILIKE ? OR l.source_file_path ILIKE ?)
                        """)
                        search_pattern = f"%{filters.search_query}%"
                        params.extend([search_pattern, search_pattern, search_pattern])
                    
                    if filters.status:
                        placeholders = ','.join(['?' for _ in filters.status])
                        where_conditions.append(f"l.status IN ({placeholders})")
                        params.extend(filters.status)
                    
                    if filters.date_range:
                        if filters.date_range.get('start'):
                            where_conditions.append("l.created_at >= ?")
                            params.append(filters.date_range['start'])
                        if filters.date_range.get('end'):
                            where_conditions.append("l.created_at <= ?")
                            params.append(filters.date_range['end'])
                    
                    if filters.confidence_range:
                        if filters.confidence_range.get('min') is not None:
                            where_conditions.append("l.extraction_confidence >= ?")
                            params.append(filters.confidence_range['min'])
                        if filters.confidence_range.get('max') is not None:
                            where_conditions.append("l.extraction_confidence <= ?")
                            params.append(filters.confidence_range['max'])
                    
                    if filters.processing_time_range:
                        if filters.processing_time_range.get('min') is not None:
                            where_conditions.append("l.processing_time_ms >= ?")
                            params.append(filters.processing_time_range['min'])
                        if filters.processing_time_range.get('max') is not None:
                            where_conditions.append("l.processing_time_ms <= ?")
                            params.append(filters.processing_time_range['max'])
                    
                    if filters.document_types:
                        placeholders = ','.join(['?' for _ in filters.document_types])
                        where_conditions.append(f"l.document_type IN ({placeholders})")
                        params.extend(filters.document_types)
                    
                    if filters.product_ranges:
                        where_conditions.append("""
                            EXISTS (
                                SELECT 1 FROM letter_products lp 
                                WHERE lp.letter_id = l.id 
                                AND lp.range_label IN ({})
                            )
                        """.format(','.join(['?' for _ in filters.product_ranges])))
                        params.extend(filters.product_ranges)
                    
                    # Combine query parts
                    if where_conditions:
                        query = base_query + " WHERE " + " AND ".join(where_conditions)
                    else:
                        query = base_query
                    
                    query += " GROUP BY l.id, l.document_name, l.document_type, l.document_title, l.source_file_path, l.file_hash, l.file_size, l.processing_method, l.processing_time_ms, l.extraction_confidence, l.created_at, l.updated_at, l.status, l.raw_grok_json, l.validation_details_json, l.processing_steps_json"
                    
                    # Add sorting
                    valid_sort_fields = {
                        'created_at': 'l.created_at',
                        'processing_time_ms': 'l.processing_time_ms',
                        'extraction_confidence': 'l.extraction_confidence',
                        'document_name': 'l.document_name'
                    }
                    
                    sort_field = valid_sort_fields.get(filters.sort_by, 'l.created_at')
                    # Handle both string and enum values for sort_order
                    if hasattr(filters.sort_order, 'value'):
                        sort_order = filters.sort_order.value.upper()
                    else:
                        sort_order = str(filters.sort_order).upper()
                    query += f" ORDER BY {sort_field} {sort_order}"
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM ({query}) as subquery"
                    total_count = conn.execute(count_query, params).fetchone()[0]
                    
                    # Add pagination
                    offset = (filters.page - 1) * filters.limit
                    query += f" LIMIT {filters.limit} OFFSET {offset}"
                    
                    # Execute query
                    results = conn.execute(query, params).fetchall()
                    columns = [desc[0] for desc in conn.description]
                    
                    # Convert to dictionaries
                    letters = []
                    for row in results:
                        letter_dict = dict(zip(columns, row))
                        
                        # Convert timestamps to strings
                        for field in ['created_at', 'updated_at']:
                            if letter_dict.get(field):
                                letter_dict[field] = str(letter_dict[field])
                        
                        letters.append(letter_dict)
                    
                    # Calculate pagination info
                    total_pages = (total_count + filters.limit - 1) // filters.limit
                    search_time_ms = (time.time() - start_time) * 1000
                    
                    return SearchResult(
                        letters=letters,
                        total_count=total_count,
                        page=filters.page,
                        limit=filters.limit,
                        total_pages=total_pages,
                        filters_applied=filters,
                        search_time_ms=search_time_ms
                    )
                    
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise ProcessingError(f"Search failed: {e}")
    
    def get_letter_by_id(self, letter_id: int, include_products: bool = True, include_debug: bool = False) -> Optional[Dict[str, Any]]:
        """Get detailed letter information by ID"""
        try:
            with self._lock:
                with duckdb.connect(self.db_path) as conn:
                    # Get letter details
                    letter_query = """
                        SELECT * FROM letters WHERE id = ?
                    """
                    
                    result = conn.execute(letter_query, [letter_id]).fetchone()
                    if not result:
                        return None
                    
                    columns = [desc[0] for desc in conn.description]
                    letter_data = dict(zip(columns, result))
                    
                    # Convert timestamps to strings
                    for field in ['created_at', 'updated_at']:
                        if letter_data.get(field):
                            letter_data[field] = str(letter_data[field])
                    
                    # Get products if requested
                    if include_products:
                        products_query = """
                            SELECT * FROM letter_products WHERE letter_id = ?
                            ORDER BY confidence_score DESC
                        """
                        products_result = conn.execute(products_query, [letter_id]).fetchall()
                        product_columns = [desc[0] for desc in conn.description]
                        
                        letter_data['products'] = []
                        for product_row in products_result:
                            product_data = dict(zip(product_columns, product_row))
                            
                            # Get matched IBcatalogue products for this letter product
                            matches_query = """
                                SELECT * FROM letter_product_matches 
                                WHERE letter_product_id = ?
                                ORDER BY match_confidence DESC
                            """
                            matches_result = conn.execute(matches_query, [product_data['id']]).fetchall()
                            
                            if matches_result:
                                match_columns = [desc[0] for desc in conn.description]
                                product_data['ibcatalogue_matches'] = [
                                    dict(zip(match_columns, match_row)) for match_row in matches_result
                                ]
                            else:
                                product_data['ibcatalogue_matches'] = []
                            
                            letter_data['products'].append(product_data)
                    
                    # Get debug info if requested
                    if include_debug:
                        debug_query = """
                            SELECT * FROM processing_debug WHERE letter_id = ?
                            ORDER BY step_timestamp ASC
                        """
                        debug_result = conn.execute(debug_query, [letter_id]).fetchall()
                        debug_columns = [desc[0] for desc in conn.description]
                        
                        letter_data['processing_debug'] = [
                            dict(zip(debug_columns, row)) for row in debug_result
                        ]
                    
                    return letter_data
                    
        except Exception as e:
            logger.error(f"❌ Failed to get letter {letter_id}: {e}")
            raise ProcessingError(f"Failed to get letter: {e}")
    
    @lru_cache(maxsize=10)
    def get_database_stats(self) -> DatabaseStats:
        """Get comprehensive database statistics with caching"""
        try:
            with self._lock:
                with duckdb.connect(self.db_path) as conn:
                    # Basic stats
                    basic_stats = conn.execute("""
                        SELECT 
                            COUNT(*) as total_letters,
                            COUNT(DISTINCT p.id) as total_products,
                            AVG(l.extraction_confidence) as avg_confidence,
                            AVG(l.processing_time_ms) as avg_processing_time,
                            SUM(CASE WHEN l.status = 'processed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                        FROM letters l
                        LEFT JOIN letter_products p ON l.id = p.letter_id
                    """).fetchone()
                    
                    # Status distribution
                    status_dist = conn.execute("""
                        SELECT status, COUNT(*) as count
                        FROM letters
                        GROUP BY status
                    """).fetchall()
                    
                    status_distribution = {row[0]: row[1] for row in status_dist}
                    
                    # Recent activity (last 10 letters)
                    recent_activity = conn.execute("""
                        SELECT id, document_name, document_type, created_at, status, extraction_confidence
                        FROM letters
                        ORDER BY created_at DESC
                        LIMIT 10
                    """).fetchall()
                    
                    recent_columns = [desc[0] for desc in conn.description]
                    recent_list = [dict(zip(recent_columns, row)) for row in recent_activity]
                    
                    # Top ranges
                    top_ranges = conn.execute("""
                        SELECT 
                            p.range_label,
                            COUNT(*) as count,
                            AVG(p.confidence_score) as avg_confidence
                        FROM letter_products p
                        WHERE p.range_label IS NOT NULL
                        GROUP BY p.range_label
                        ORDER BY count DESC
                        LIMIT 10
                    """).fetchall()
                    
                    top_ranges_list = [
                        {
                            'range_label': row[0],
                            'count': row[1],
                            'avg_confidence': row[2] or 0.0
                        }
                        for row in top_ranges
                    ]
                    
                    # Processing performance
                    perf_stats = conn.execute("""
                        SELECT 
                            MIN(processing_time_ms) as fastest_processing,
                            MAX(processing_time_ms) as slowest_processing,
                            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY processing_time_ms) as median_processing
                        FROM letters
                        WHERE processing_time_ms IS NOT NULL
                    """).fetchone()
                    
                    processing_performance = {
                        'fastest_processing': perf_stats[0] or 0.0,
                        'slowest_processing': perf_stats[1] or 0.0,
                        'median_processing': perf_stats[2] or 0.0
                    }
                    
                    return DatabaseStats(
                        total_letters=basic_stats[0] or 0,
                        total_products=basic_stats[1] or 0,
                        avg_confidence=basic_stats[2] or 0.0,
                        avg_processing_time=basic_stats[3] or 0.0,
                        success_rate=basic_stats[4] or 0.0,
                        status_distribution=status_distribution,
                        recent_activity=recent_list,
                        top_ranges=top_ranges_list,
                        processing_performance=processing_performance
                    )
                    
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            raise ProcessingError(f"Failed to get database stats: {e}")
    
    def get_analytics_data(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics data for the specified number of days"""
        try:
            with self._lock:
                with duckdb.connect(self.db_path) as conn:
                    # Processing trends
                    trends_query = """
                        SELECT 
                            DATE_TRUNC('day', created_at) as date,
                            COUNT(*) as count,
                            AVG(extraction_confidence) as avg_confidence,
                            SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                        FROM letters
                        WHERE created_at >= CURRENT_DATE - INTERVAL '{} days'
                        GROUP BY DATE_TRUNC('day', created_at)
                        ORDER BY date
                    """.format(days)
                    
                    trends_result = conn.execute(trends_query).fetchall()
                    processing_trends = [
                        {
                            'date': str(row[0]),
                            'count': row[1],
                            'avg_confidence': row[2] or 0.0,
                            'success_rate': row[3] or 0.0
                        }
                        for row in trends_result
                    ]
                    
                    # Range distribution
                    range_dist = conn.execute("""
                        SELECT 
                            p.range_label,
                            COUNT(*) as count,
                            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
                        FROM letter_products p
                        WHERE p.range_label IS NOT NULL
                        GROUP BY p.range_label
                        ORDER BY count DESC
                        LIMIT 20
                    """).fetchall()
                    
                    range_distribution = [
                        {
                            'range_label': row[0],
                            'count': row[1],
                            'percentage': row[2] or 0.0
                        }
                        for row in range_dist
                    ]
                    
                    # Confidence distribution
                    confidence_dist = conn.execute("""
                        SELECT 
                            CASE 
                                WHEN extraction_confidence >= 0.9 THEN '90-100%'
                                WHEN extraction_confidence >= 0.8 THEN '80-90%'
                                WHEN extraction_confidence >= 0.7 THEN '70-80%'
                                WHEN extraction_confidence >= 0.6 THEN '60-70%'
                                ELSE 'Below 60%'
                            END as confidence_range,
                            COUNT(*) as count,
                            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
                        FROM letters
                        WHERE extraction_confidence IS NOT NULL
                        GROUP BY confidence_range
                        ORDER BY MIN(extraction_confidence) DESC
                    """).fetchall()
                    
                    confidence_distribution = [
                        {
                            'confidence_range': row[0],
                            'count': row[1],
                            'percentage': row[2] or 0.0
                        }
                        for row in confidence_dist
                    ]
                    
                    # Processing performance
                    perf_dist = conn.execute("""
                        SELECT 
                            CASE 
                                WHEN processing_time_ms < 5000 THEN '< 5s'
                                WHEN processing_time_ms < 10000 THEN '5-10s'
                                WHEN processing_time_ms < 30000 THEN '10-30s'
                                WHEN processing_time_ms < 60000 THEN '30-60s'
                                ELSE '> 60s'
                            END as time_range,
                            COUNT(*) as count,
                            AVG(processing_time_ms) as avg_time
                        FROM letters
                        WHERE processing_time_ms IS NOT NULL
                        GROUP BY time_range
                        ORDER BY MIN(processing_time_ms)
                    """).fetchall()
                    
                    processing_performance = [
                        {
                            'time_range': row[0],
                            'count': row[1],
                            'avg_time': row[2] or 0.0
                        }
                        for row in perf_dist
                    ]
                    
                    # Error analysis
                    error_analysis = conn.execute("""
                        SELECT 
                            COALESCE(error_message, 'Unknown Error') as error_type,
                            COUNT(*) as count,
                            ARRAY_AGG(step_details ORDER BY step_timestamp DESC LIMIT 3) as recent_examples
                        FROM processing_debug
                        WHERE step_success = false
                        GROUP BY error_message
                        ORDER BY count DESC
                        LIMIT 10
                    """).fetchall()
                    
                    error_list = [
                        {
                            'error_type': row[0],
                            'count': row[1],
                            'recent_examples': row[2] or []
                        }
                        for row in error_analysis
                    ]
                    
                    return {
                        'processing_trends': processing_trends,
                        'range_distribution': range_distribution,
                        'confidence_distribution': confidence_distribution,
                        'processing_performance': processing_performance,
                        'error_analysis': error_list
                    }
                    
        except Exception as e:
            logger.error(f"❌ Failed to get analytics data: {e}")
            raise ProcessingError(f"Failed to get analytics data: {e}")
    
    def bulk_operation(self, operation: OperationType, letter_ids: List[int], options: Optional[Dict[str, Any]] = None) -> OperationResult:
        """Perform bulk operations on letters"""
        start_time = time.time()
        
        try:
            with self._lock:
                with duckdb.connect(self.db_path) as conn:
                    if operation == OperationType.DELETE:
                        return self._bulk_delete(conn, letter_ids)
                    elif operation == OperationType.ARCHIVE:
                        return self._bulk_archive(conn, letter_ids)
                    elif operation == OperationType.EXPORT:
                        return self._bulk_export(conn, letter_ids, options or {})
                    else:
                        raise ValidationError(f"Unsupported operation: {operation}")
                        
        except Exception as e:
            logger.error(f"❌ Bulk operation {operation} failed: {e}")
            return OperationResult(
                success=False,
                operation=operation.value,
                affected_count=0,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _bulk_delete(self, conn: duckdb.DuckDBPyConnection, letter_ids: List[int]) -> OperationResult:
        """Delete letters and related data"""
        start_time = time.time()
        
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Delete related records first
            placeholders = ','.join(['?' for _ in letter_ids])
            
            # Delete products
            products_deleted = conn.execute(f"""
                DELETE FROM letter_products WHERE letter_id IN ({placeholders})
            """, letter_ids).rowcount
            
            # Delete debug records
            debug_deleted = conn.execute(f"""
                DELETE FROM processing_debug WHERE letter_id IN ({placeholders})
            """, letter_ids).rowcount
            
            # Delete letters
            letters_deleted = conn.execute(f"""
                DELETE FROM letters WHERE id IN ({placeholders})
            """, letter_ids).rowcount
            
            conn.execute("COMMIT")
            
            logger.info(f"🗑️ Deleted {letters_deleted} letters, {products_deleted} products, {debug_deleted} debug records")
            
            return OperationResult(
                success=True,
                operation="delete",
                affected_count=letters_deleted,
                results=[{
                    'letters_deleted': letters_deleted,
                    'products_deleted': products_deleted,
                    'debug_deleted': debug_deleted
                }],
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            conn.execute("ROLLBACK")
            raise ProcessingError(f"Delete operation failed: {e}")
    
    def _bulk_archive(self, conn: duckdb.DuckDBPyConnection, letter_ids: List[int]) -> OperationResult:
        """Archive letters (mark as archived)"""
        start_time = time.time()
        
        try:
            placeholders = ','.join(['?' for _ in letter_ids])
            
            # Update status to archived
            archived_count = conn.execute(f"""
                UPDATE letters 
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            """, letter_ids).rowcount
            
            logger.info(f"📦 Archived {archived_count} letters")
            
            return OperationResult(
                success=True,
                operation="archive",
                affected_count=archived_count,
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            raise ProcessingError(f"Archive operation failed: {e}")
    
    def _bulk_export(self, conn: duckdb.DuckDBPyConnection, letter_ids: List[int], options: Dict[str, Any]) -> OperationResult:
        """Export letters to specified format"""
        start_time = time.time()
        
        try:
            export_format = options.get('format', 'json')
            include_products = options.get('include_products', True)
            include_debug = options.get('include_debug', False)
            
            # Get letter data
            placeholders = ','.join(['?' for _ in letter_ids])
            
            letters_query = f"""
                SELECT * FROM letters WHERE id IN ({placeholders})
                ORDER BY created_at DESC
            """
            
            letters_result = conn.execute(letters_query, letter_ids).fetchall()
            letters_columns = [desc[0] for desc in conn.description]
            
            export_data = []
            for row in letters_result:
                letter_data = dict(zip(letters_columns, row))
                
                # Convert timestamps
                for field in ['created_at', 'updated_at']:
                    if letter_data.get(field):
                        letter_data[field] = str(letter_data[field])
                
                # Add products if requested
                if include_products:
                    products_result = conn.execute("""
                        SELECT * FROM letter_products WHERE letter_id = ?
                    """, [letter_data['id']]).fetchall()
                    
                    if products_result:
                        product_columns = [desc[0] for desc in conn.description]
                        letter_data['products'] = [
                            dict(zip(product_columns, prod_row)) for prod_row in products_result
                        ]
                
                # Add debug info if requested
                if include_debug:
                    debug_result = conn.execute("""
                        SELECT * FROM processing_debug WHERE letter_id = ?
                    """, [letter_data['id']]).fetchall()
                    
                    if debug_result:
                        debug_columns = [desc[0] for desc in conn.description]
                        letter_data['debug'] = [
                            dict(zip(debug_columns, debug_row)) for debug_row in debug_result
                        ]
                
                export_data.append(letter_data)
            
            # Generate export file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = Path("data/exports")
            export_dir.mkdir(exist_ok=True)
            
            if export_format == 'json':
                export_file = export_dir / f"letters_export_{timestamp}.json"
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            elif export_format == 'csv':
                export_file = export_dir / f"letters_export_{timestamp}.csv"
                # Flatten data for CSV
                flattened_data = []
                for letter in export_data:
                    base_data = {k: v for k, v in letter.items() if k not in ['products', 'debug']}
                    if letter.get('products'):
                        for product in letter['products']:
                            row_data = {**base_data, **{f"product_{k}": v for k, v in product.items()}}
                            flattened_data.append(row_data)
                    else:
                        flattened_data.append(base_data)
                
                if flattened_data:
                    df = pd.DataFrame(flattened_data)
                    df.to_csv(export_file, index=False)
            
            elif export_format == 'xlsx':
                export_file = export_dir / f"letters_export_{timestamp}.xlsx"
                
                with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
                    # Letters sheet
                    letters_df = pd.DataFrame([
                        {k: v for k, v in letter.items() if k not in ['products', 'debug']}
                        for letter in export_data
                    ])
                    letters_df.to_excel(writer, sheet_name='Letters', index=False)
                    
                    # Products sheet
                    if include_products:
                        products_data = []
                        for letter in export_data:
                            if letter.get('products'):
                                for product in letter['products']:
                                    products_data.append({
                                        'letter_id': letter['id'],
                                        'document_name': letter['document_name'],
                                        **product
                                    })
                        
                        if products_data:
                            products_df = pd.DataFrame(products_data)
                            products_df.to_excel(writer, sheet_name='Products', index=False)
            
            else:
                raise ValidationError(f"Unsupported export format: {export_format}")
            
            file_size = export_file.stat().st_size
            
            logger.info(f"📤 Exported {len(export_data)} letters to {export_file} ({file_size} bytes)")
            
            return OperationResult(
                success=True,
                operation="export",
                affected_count=len(export_data),
                results=[{
                    'export_file': str(export_file),
                    'file_size': file_size,
                    'format': export_format,
                    'record_count': len(export_data)
                }],
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            raise ProcessingError(f"Export operation failed: {e}")
    
    def get_available_ranges(self) -> List[str]:
        """Get all available product ranges for filtering"""
        try:
            with duckdb.connect(self.db_path) as conn:
                result = conn.execute("""
                    SELECT DISTINCT range_label
                    FROM letter_products
                    WHERE range_label IS NOT NULL
                    ORDER BY range_label
                """).fetchall()
                
                return [row[0] for row in result]
                
        except Exception as e:
            logger.error(f"❌ Failed to get available ranges: {e}")
            return []
    
    def get_available_document_types(self) -> List[str]:
        """Get all available document types for filtering"""
        try:
            with duckdb.connect(self.db_path) as conn:
                result = conn.execute("""
                    SELECT DISTINCT document_type
                    FROM letters
                    WHERE document_type IS NOT NULL
                    ORDER BY document_type
                """).fetchall()
                
                return [row[0] for row in result]
                
        except Exception as e:
            logger.error(f"❌ Failed to get available document types: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear all cached results"""
        with self._lock:
            self._cache.clear()
            # Clear LRU cache
            self.get_database_stats.cache_clear()
            logger.info("🧹 Cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the database service"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Test basic connectivity
                conn.execute("SELECT 1").fetchone()
                
                # Get table counts
                tables_info = {}
                for table in ['letters', 'letter_products', 'processing_debug']:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    tables_info[table] = count
                
                return {
                    'status': 'healthy',
                    'database_path': self.db_path,
                    'tables': tables_info,
                    'cache_size': len(self._cache),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 