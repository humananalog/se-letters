#!/usr/bin/env python3
"""
PostgreSQL Letter Database Service
PostgreSQL-compatible version of the letter database service
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

from loguru import logger

from se_letters.core.postgresql_database import PostgreSQLDatabase
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


class PostgreSQLLetterDatabaseService:
    """PostgreSQL-compatible letter database service"""
    
    def __init__(self, connection_string: str = "postgresql://alexandre@localhost:5432/se_letters_dev"):
        """Initialize the PostgreSQL letter database service"""
        self.connection_string = connection_string
        self.db = PostgreSQLDatabase(connection_string)
        
        # Initialize config with defaults if not available
        try:
            self.config = get_config()
        except Exception as e:
            logger.warning(f"⚠️ Could not load config, using defaults: {e}")
            self.config = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Cache settings
        self._cache_ttl = 300  # 5 minutes
        self._cache = {}
        
        # Initialize database connection
        self._init_database()
        
        logger.info(f"📊 PostgreSQL Letter Database Service initialized")
    
    def _init_database(self) -> None:
        """Initialize database connection and verify schema"""
        try:
            # Test connection
            result = self.db.execute_scalar("SELECT 1")
            if result != 1:
                raise ProcessingError("Database connection test failed")
            
            # Verify main tables exist
            tables = self.db.execute_query("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            table_names = [table['table_name'] for table in tables]
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
                        (l.document_name ILIKE %s OR l.document_title ILIKE %s OR l.source_file_path ILIKE %s)
                    """)
                    search_pattern = f"%{filters.search_query}%"
                    params.extend([search_pattern, search_pattern, search_pattern])
                
                if filters.status:
                    placeholders = ','.join(['%s' for _ in filters.status])
                    where_conditions.append(f"l.status IN ({placeholders})")
                    params.extend(filters.status)
                
                if filters.date_range:
                    if filters.date_range.get('start'):
                        where_conditions.append("l.created_at >= %s")
                        params.append(filters.date_range['start'])
                    if filters.date_range.get('end'):
                        where_conditions.append("l.created_at <= %s")
                        params.append(filters.date_range['end'])
                
                if filters.confidence_range:
                    if filters.confidence_range.get('min') is not None:
                        where_conditions.append("l.extraction_confidence >= %s")
                        params.append(filters.confidence_range['min'])
                    if filters.confidence_range.get('max') is not None:
                        where_conditions.append("l.extraction_confidence <= %s")
                        params.append(filters.confidence_range['max'])
                
                if filters.processing_time_range:
                    if filters.processing_time_range.get('min') is not None:
                        where_conditions.append("l.processing_time_ms >= %s")
                        params.append(filters.processing_time_range['min'])
                    if filters.processing_time_range.get('max') is not None:
                        where_conditions.append("l.processing_time_ms <= %s")
                        params.append(filters.processing_time_range['max'])
                
                if filters.document_types:
                    placeholders = ','.join(['%s' for _ in filters.document_types])
                    where_conditions.append(f"l.document_type IN ({placeholders})")
                    params.extend(filters.document_types)
                
                if filters.product_ranges:
                    where_conditions.append("""
                        EXISTS (
                            SELECT 1 FROM letter_products lp 
                            WHERE lp.letter_id = l.id 
                            AND lp.range_label IN ({})
                        )
                    """.format(','.join(['%s' for _ in filters.product_ranges])))
                    params.extend(filters.product_ranges)
                
                # Add WHERE clause if conditions exist
                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)
                
                # Add GROUP BY for product count
                base_query += " GROUP BY l.id, l.document_name, l.document_type, l.document_title, l.source_file_path, l.file_hash, l.file_size, l.processing_method, l.processing_time_ms, l.extraction_confidence, l.created_at, l.updated_at, l.status, l.raw_grok_json, l.validation_details_json, l.processing_steps_json"
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM ({base_query}) as subquery"
                total_count = self.db.execute_scalar(count_query, tuple(params))
                
                # Add ORDER BY and LIMIT
                order_clause = f"ORDER BY l.{filters.sort_by} {filters.sort_order.value.upper()}"
                limit_clause = f"LIMIT {filters.limit} OFFSET {(filters.page - 1) * filters.limit}"
                
                final_query = f"{base_query} {order_clause} {limit_clause}"
                
                # Execute query
                letters = self.db.execute_query(final_query, tuple(params))
                
                search_time = (time.time() - start_time) * 1000
                
                return SearchResult(
                    letters=letters,
                    total_count=total_count,
                    page=filters.page,
                    limit=filters.limit,
                    total_pages=(total_count + filters.limit - 1) // filters.limit,
                    filters_applied=filters,
                    search_time_ms=search_time
                )
                
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise ProcessingError(f"Search operation failed: {e}")
    
    def get_letter_by_id(self, letter_id: int, include_products: bool = True, include_debug: bool = False) -> Optional[Dict[str, Any]]:
        """Get letter by ID with optional related data"""
        try:
            # Get letter data
            letter_query = "SELECT * FROM letters WHERE id = %s"
            letters = self.db.execute_query(letter_query, (letter_id,))
            
            if not letters:
                return None
            
            letter = letters[0]
            
            # Get products if requested
            if include_products:
                products_query = "SELECT * FROM letter_products WHERE letter_id = %s"
                products = self.db.execute_query(products_query, (letter_id,))
                letter['products'] = products
                
                # Get product matches
                for product in products:
                    matches_query = """
                        SELECT * FROM letter_product_matches 
                        WHERE letter_product_id = %s
                    """
                    matches = self.db.execute_query(matches_query, (product['id'],))
                    product['matches'] = matches
            
            # Get debug info if requested
            if include_debug:
                debug_query = """
                    SELECT * FROM processing_debug 
                    WHERE letter_id = %s 
                    ORDER BY step_timestamp DESC
                """
                debug_info = self.db.execute_query(debug_query, (letter_id,))
                letter['debug_info'] = debug_info
            
            return letter
            
        except Exception as e:
            logger.error(f"❌ Failed to get letter {letter_id}: {e}")
            raise ProcessingError(f"Failed to get letter: {e}")
    
    def store_letter(self, letter_data: Dict[str, Any]) -> int:
        """Store letter and return ID"""
        try:
            sql = """
                INSERT INTO letters (
                    document_name, document_type, document_title, source_file_path,
                    file_size, file_hash, processing_method, processing_time_ms,
                    extraction_confidence, raw_grok_json, validation_details_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            params = (
                letter_data['document_name'],
                letter_data.get('document_type'),
                letter_data.get('document_title'),
                letter_data['source_file_path'],
                letter_data.get('file_size'),
                letter_data.get('file_hash'),
                letter_data.get('processing_method', 'production_pipeline'),
                letter_data.get('processing_time_ms'),
                letter_data.get('extraction_confidence'),
                json.dumps(letter_data.get('raw_grok_json')) if letter_data.get('raw_grok_json') else None,
                json.dumps(letter_data.get('validation_details_json')) if letter_data.get('validation_details_json') else None
            )
            
            # Use execute_query to get the returned ID with commit
            result = self.db.execute_query(sql, params, commit=True)
            if result and len(result) > 0:
                return result[0]['id']
            else:
                raise ProcessingError("Failed to get returned ID from INSERT")
            
        except Exception as e:
            logger.error(f"❌ Failed to store letter: {e}")
            raise ProcessingError(f"Failed to store letter: {e}")
    
    def get_database_stats(self) -> DatabaseStats:
        """Get comprehensive database statistics"""
        try:
            # Basic counts
            total_letters = self.db.execute_scalar("SELECT COUNT(*) FROM letters")
            total_products = self.db.execute_scalar("SELECT COUNT(*) FROM letter_products")
            
            # Averages
            avg_confidence = self.db.execute_scalar("""
                SELECT AVG(extraction_confidence) FROM letters 
                WHERE extraction_confidence IS NOT NULL
            """) or 0.0
            
            avg_processing_time = self.db.execute_scalar("""
                SELECT AVG(processing_time_ms) FROM letters 
                WHERE processing_time_ms IS NOT NULL
            """) or 0.0
            
            # Success rate
            success_count = self.db.execute_scalar("""
                SELECT COUNT(*) FROM letters WHERE status = 'processed'
            """)
            success_rate = (success_count / total_letters * 100) if total_letters > 0 else 0.0
            
            # Status distribution
            status_distribution = {}
            status_counts = self.db.execute_query("""
                SELECT status, COUNT(*) as count FROM letters 
                GROUP BY status
            """)
            for row in status_counts:
                status_distribution[row['status']] = row['count']
            
            # Recent activity
            recent_activity = self.db.execute_query("""
                SELECT id, document_name, created_at, status 
                FROM letters 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            # Top ranges
            top_ranges = self.db.execute_query("""
                SELECT range_label, COUNT(*) as count 
                FROM letter_products 
                WHERE range_label IS NOT NULL 
                GROUP BY range_label 
                ORDER BY count DESC 
                LIMIT 10
            """)
            
            # Processing performance
            processing_performance = {
                'avg_time': avg_processing_time,
                'success_rate': success_rate,
                'total_processed': total_letters
            }
            
            return DatabaseStats(
                total_letters=total_letters,
                total_products=total_products,
                avg_confidence=avg_confidence,
                success_rate=success_rate,
                avg_processing_time=avg_processing_time,
                status_distribution=status_distribution,
                recent_activity=recent_activity,
                top_ranges=top_ranges,
                processing_performance=processing_performance
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            raise ProcessingError(f"Failed to get database stats: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        logger.info("✅ Cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            result = self.db.execute_scalar("SELECT 1")
            if result != 1:
                raise Exception("Database connectivity test failed")
            
            # Test table access
            table_count = self.db.execute_scalar("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            # Test letter count
            letter_count = self.db.execute_scalar("SELECT COUNT(*) FROM letters")
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'table_count': table_count,
                'letter_count': letter_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 