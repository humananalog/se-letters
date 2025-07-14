#!/usr/bin/env python3
"""
Test suite for Letter Database Service
Comprehensive tests for all letter database functionality

Test Coverage:
- Search and filtering
- Statistics and analytics
- Bulk operations
- Database operations
- Error handling
- Performance testing

Author: SE Letters Team
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import duckdb

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.letter_database_service import (
    LetterDatabaseService,
    SearchFilters,
    SortOrder,
    OperationType,
    SearchResult,
    DatabaseStats,
    OperationResult
)
from se_letters.core.exceptions import ProcessingError, ValidationError


class TestLetterDatabaseService:
    """Test suite for LetterDatabaseService"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_letters.duckdb"
        
        # Create test database with sample data
        with duckdb.connect(str(db_path)) as conn:
            # Create sequences
            conn.execute("CREATE SEQUENCE letters_id_seq START 1")
            conn.execute("CREATE SEQUENCE products_id_seq START 1")
            conn.execute("CREATE SEQUENCE debug_id_seq START 1")
            
            # Create tables
            conn.execute("""
                CREATE TABLE letters (
                    id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
                    document_name TEXT NOT NULL,
                    document_type TEXT,
                    document_title TEXT,
                    source_file_path TEXT NOT NULL,
                    file_hash TEXT,
                    file_size INTEGER,
                    processing_method TEXT DEFAULT 'production_pipeline',
                    processing_time_ms REAL,
                    extraction_confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'processed',
                    raw_grok_json TEXT,
                    validation_details_json TEXT,
                    processing_steps_json TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE letter_products (
                    id INTEGER PRIMARY KEY DEFAULT nextval('products_id_seq'),
                    letter_id INTEGER NOT NULL,
                    product_identifier TEXT,
                    range_label TEXT,
                    subrange_label TEXT,
                    product_line TEXT,
                    product_description TEXT,
                    obsolescence_status TEXT,
                    end_of_service_date TEXT,
                    replacement_suggestions TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    validation_status TEXT DEFAULT 'validated',
                    FOREIGN KEY (letter_id) REFERENCES letters(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE processing_debug (
                    id INTEGER PRIMARY KEY DEFAULT nextval('debug_id_seq'),
                    letter_id INTEGER NOT NULL,
                    processing_step TEXT NOT NULL,
                    step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    step_duration_ms REAL,
                    step_success BOOLEAN DEFAULT TRUE,
                    step_details TEXT,
                    error_message TEXT,
                    FOREIGN KEY (letter_id) REFERENCES letters(id)
                )
            """)
            
            # Insert sample data
            sample_letters = [
                (1, 'test_letter_1.pdf', 'PDF', 'Test Letter 1', '/path/to/test1.pdf', 'hash1', 1024, 'production_pipeline', 5000.0, 0.95, 'processed'),
                (2, 'test_letter_2.docx', 'DOCX', 'Test Letter 2', '/path/to/test2.docx', 'hash2', 2048, 'production_pipeline', 7500.0, 0.88, 'processed'),
                (3, 'test_letter_3.pdf', 'PDF', 'Test Letter 3', '/path/to/test3.pdf', 'hash3', 1536, 'production_pipeline', 3000.0, 0.92, 'failed'),
                (4, 'test_letter_4.doc', 'DOC', 'Test Letter 4', '/path/to/test4.doc', 'hash4', 3072, 'production_pipeline', 12000.0, 0.85, 'processed'),
                (5, 'test_letter_5.pdf', 'PDF', 'Test Letter 5', '/path/to/test5.pdf', 'hash5', 2560, 'production_pipeline', 8000.0, 0.90, 'archived')
            ]
            
            for letter_data in sample_letters:
                conn.execute("""
                    INSERT INTO letters (id, document_name, document_type, document_title, source_file_path, file_hash, file_size, processing_method, processing_time_ms, extraction_confidence, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, letter_data)
            
            # Insert sample products
            sample_products = [
                (1, 1, 'PROD001', 'TeSys D', 'D-Line', 'Contactors', 'TeSys D contactor', 'obsolete', '2024-12-31', 'TeSys F', 0.95),
                (2, 1, 'PROD002', 'TeSys D', 'D-Line', 'Contactors', 'TeSys D auxiliary', 'obsolete', '2024-12-31', 'TeSys F', 0.90),
                (3, 2, 'PROD003', 'Schneider', 'S-Line', 'Switches', 'Schneider switch', 'active', '', '', 0.88),
                (4, 3, 'PROD004', 'Modicon', 'M-Line', 'PLCs', 'Modicon PLC', 'obsolete', '2025-06-30', 'Modicon X80', 0.92),
                (5, 4, 'PROD005', 'Altivar', 'A-Line', 'Drives', 'Altivar drive', 'active', '', '', 0.85)
            ]
            
            for product_data in sample_products:
                conn.execute("""
                    INSERT INTO letter_products (id, letter_id, product_identifier, range_label, subrange_label, product_line, product_description, obsolescence_status, end_of_service_date, replacement_suggestions, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, product_data)
            
            # Insert sample debug records
            sample_debug = [
                (1, 1, 'document_validation', datetime.now(), 500.0, True, 'Validation successful', None),
                (2, 1, 'grok_processing', datetime.now(), 4000.0, True, 'Processing complete', None),
                (3, 2, 'document_validation', datetime.now(), 300.0, True, 'Validation successful', None),
                (4, 3, 'grok_processing', datetime.now(), 2000.0, False, 'Processing failed', 'Invalid document format')
            ]
            
            for debug_data in sample_debug:
                conn.execute("""
                    INSERT INTO processing_debug (id, letter_id, processing_step, step_timestamp, step_duration_ms, step_success, step_details, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, debug_data)
        
        yield str(db_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_db_path):
        """Create service instance with test database"""
        return LetterDatabaseService(temp_db_path)
    
    def test_init_database(self, service):
        """Test database initialization"""
        assert service.db_path
        assert service._lock
        assert service._cache == {}
        assert service._cache_ttl == 300
    
    def test_search_letters_basic(self, service):
        """Test basic letter search functionality"""
        filters = SearchFilters()
        result = service.search_letters(filters)
        
        assert isinstance(result, SearchResult)
        assert len(result.letters) == 5
        assert result.total_count == 5
        assert result.page == 1
        assert result.limit == 50
        assert result.search_time_ms > 0
    
    def test_search_letters_with_filters(self, service):
        """Test letter search with various filters"""
        # Test status filter
        filters = SearchFilters(status=['processed'])
        result = service.search_letters(filters)
        assert len(result.letters) == 3
        assert all(letter['status'] == 'processed' for letter in result.letters)
        
        # Test search query
        filters = SearchFilters(search_query='test_letter_1')
        result = service.search_letters(filters)
        assert len(result.letters) == 1
        assert result.letters[0]['document_name'] == 'test_letter_1.pdf'
        
        # Test confidence range
        filters = SearchFilters(confidence_range={'min': 0.9, 'max': 1.0})
        result = service.search_letters(filters)
        assert len(result.letters) >= 1
        assert all(letter['extraction_confidence'] >= 0.9 for letter in result.letters)
        
        # Test processing time range
        filters = SearchFilters(processing_time_range={'min': 0, 'max': 5000})
        result = service.search_letters(filters)
        assert len(result.letters) >= 1
        assert all(letter['processing_time_ms'] <= 5000 for letter in result.letters)
    
    def test_search_letters_sorting(self, service):
        """Test letter search with sorting"""
        # Test ascending sort by confidence
        filters = SearchFilters(sort_by='extraction_confidence', sort_order=SortOrder.ASC)
        result = service.search_letters(filters)
        confidences = [letter['extraction_confidence'] for letter in result.letters]
        assert confidences == sorted(confidences)
        
        # Test descending sort by processing time
        filters = SearchFilters(sort_by='processing_time_ms', sort_order=SortOrder.DESC)
        result = service.search_letters(filters)
        times = [letter['processing_time_ms'] for letter in result.letters]
        assert times == sorted(times, reverse=True)
    
    def test_search_letters_pagination(self, service):
        """Test letter search with pagination"""
        filters = SearchFilters(page=1, limit=2)
        result = service.search_letters(filters)
        
        assert len(result.letters) == 2
        assert result.page == 1
        assert result.limit == 2
        assert result.total_count == 5
        assert result.total_pages == 3
        
        # Test second page
        filters = SearchFilters(page=2, limit=2)
        result = service.search_letters(filters)
        assert len(result.letters) == 2
        assert result.page == 2
    
    def test_get_letter_by_id(self, service):
        """Test getting letter by ID"""
        # Test existing letter
        letter = service.get_letter_by_id(1, include_products=True, include_debug=True)
        assert letter is not None
        assert letter['id'] == 1
        assert letter['document_name'] == 'test_letter_1.pdf'
        assert 'products' in letter
        assert len(letter['products']) == 2
        assert 'processing_debug' in letter
        
        # Test non-existing letter
        letter = service.get_letter_by_id(999)
        assert letter is None
        
        # Test without products and debug
        letter = service.get_letter_by_id(1, include_products=False, include_debug=False)
        assert letter is not None
        assert 'products' not in letter
        assert 'processing_debug' not in letter
    
    def test_get_database_stats(self, service):
        """Test database statistics"""
        stats = service.get_database_stats()
        
        assert isinstance(stats, DatabaseStats)
        assert stats.total_letters == 5
        assert stats.total_products == 5
        assert stats.avg_confidence > 0
        assert stats.success_rate > 0
        assert stats.avg_processing_time > 0
        assert isinstance(stats.status_distribution, dict)
        assert len(stats.recent_activity) <= 10
        assert len(stats.top_ranges) <= 10
        assert isinstance(stats.processing_performance, dict)
    
    def test_get_analytics_data(self, service):
        """Test analytics data retrieval"""
        analytics = service.get_analytics_data(days=30)
        
        assert isinstance(analytics, dict)
        assert 'processing_trends' in analytics
        assert 'range_distribution' in analytics
        assert 'confidence_distribution' in analytics
        assert 'processing_performance' in analytics
        assert 'error_analysis' in analytics
        
        # Test with different time periods
        analytics_7d = service.get_analytics_data(days=7)
        assert isinstance(analytics_7d, dict)
    
    def test_bulk_delete_operation(self, service):
        """Test bulk delete operation"""
        letter_ids = [1, 2]
        result = service.bulk_operation(OperationType.DELETE, letter_ids)
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert result.operation == 'delete'
        assert result.affected_count == 2
        assert result.processing_time_ms > 0
        
        # Verify letters are deleted
        letter = service.get_letter_by_id(1)
        assert letter is None
        
        # Verify related products are deleted
        remaining_letters = service.search_letters(SearchFilters())
        assert remaining_letters.total_count == 3
    
    def test_bulk_archive_operation(self, service):
        """Test bulk archive operation"""
        letter_ids = [1, 2]
        result = service.bulk_operation(OperationType.ARCHIVE, letter_ids)
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert result.operation == 'archive'
        assert result.affected_count == 2
        
        # Verify letters are archived
        letter = service.get_letter_by_id(1)
        assert letter is not None
        assert letter['status'] == 'archived'
    
    def test_bulk_export_operation(self, service):
        """Test bulk export operation"""
        letter_ids = [1, 2]
        options = {'format': 'json', 'include_products': True}
        result = service.bulk_operation(OperationType.EXPORT, letter_ids, options)
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert result.operation == 'export'
        assert result.affected_count == 2
        assert result.results is not None
        assert len(result.results) == 1
        assert 'export_file' in result.results[0]
        assert 'file_size' in result.results[0]
        
        # Verify export file exists
        export_file = Path(result.results[0]['export_file'])
        assert export_file.exists()
        
        # Verify export content
        with open(export_file, 'r') as f:
            export_data = json.load(f)
        assert len(export_data) == 2
        assert export_data[0]['products'] is not None
        
        # Cleanup
        export_file.unlink()
    
    def test_bulk_export_csv_format(self, service):
        """Test bulk export in CSV format"""
        letter_ids = [1, 2]
        options = {'format': 'csv', 'include_products': True}
        result = service.bulk_operation(OperationType.EXPORT, letter_ids, options)
        
        assert result.success is True
        export_file = Path(result.results[0]['export_file'])
        assert export_file.exists()
        assert export_file.suffix == '.csv'
        
        # Cleanup
        export_file.unlink()
    
    def test_bulk_export_xlsx_format(self, service):
        """Test bulk export in Excel format"""
        letter_ids = [1, 2]
        options = {'format': 'xlsx', 'include_products': True}
        result = service.bulk_operation(OperationType.EXPORT, letter_ids, options)
        
        assert result.success is True
        export_file = Path(result.results[0]['export_file'])
        assert export_file.exists()
        assert export_file.suffix == '.xlsx'
        
        # Cleanup
        export_file.unlink()
    
    def test_get_available_ranges(self, service):
        """Test getting available product ranges"""
        ranges = service.get_available_ranges()
        
        assert isinstance(ranges, list)
        assert len(ranges) > 0
        assert 'TeSys D' in ranges
        assert 'Schneider' in ranges
        assert 'Modicon' in ranges
        assert 'Altivar' in ranges
    
    def test_get_available_document_types(self, service):
        """Test getting available document types"""
        doc_types = service.get_available_document_types()
        
        assert isinstance(doc_types, list)
        assert len(doc_types) > 0
        assert 'PDF' in doc_types
        assert 'DOCX' in doc_types
        assert 'DOC' in doc_types
    
    def test_cache_functionality(self, service):
        """Test caching functionality"""
        # Clear cache
        service.clear_cache()
        assert len(service._cache) == 0
        
        # Test cache key generation
        key = service._get_cache_key('test_operation', param1='value1', param2='value2')
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length
        
        # Test cache set and get
        service._set_cached_result(key, {'test': 'data'})
        result = service._get_cached_result(key)
        assert result == {'test': 'data'}
        
        # Test cache expiration (mock time)
        with patch('time.time', return_value=1000000):
            service._set_cached_result(key, {'test': 'data'})
        
        with patch('time.time', return_value=1000000 + 400):  # Beyond TTL
            result = service._get_cached_result(key)
            assert result is None
    
    def test_health_check(self, service):
        """Test health check functionality"""
        health = service.health_check()
        
        assert isinstance(health, dict)
        assert health['status'] == 'healthy'
        assert 'database_path' in health
        assert 'tables' in health
        assert 'cache_size' in health
        assert 'timestamp' in health
        
        # Verify table counts
        assert health['tables']['letters'] == 5
        assert health['tables']['letter_products'] == 5
        assert health['tables']['processing_debug'] == 4
    
    def test_error_handling(self, service):
        """Test error handling"""
        # Test invalid operation type
        with pytest.raises(ValidationError):
            service.bulk_operation('invalid_operation', [1, 2])
        
        # Test search with invalid filters
        filters = SearchFilters(sort_by='invalid_field')
        result = service.search_letters(filters)
        # Should use default sort field
        assert result.letters is not None
    
    def test_thread_safety(self, service):
        """Test thread safety with concurrent operations"""
        import threading
        import time
        
        results = []
        errors = []
        
        def search_operation():
            try:
                filters = SearchFilters(page=1, limit=10)
                result = service.search_letters(filters)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        def stats_operation():
            try:
                stats = service.get_database_stats()
                results.append(stats)
            except Exception as e:
                errors.append(e)
        
        # Run concurrent operations
        threads = []
        for _ in range(5):
            t1 = threading.Thread(target=search_operation)
            t2 = threading.Thread(target=stats_operation)
            threads.extend([t1, t2])
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no errors and all operations completed
        assert len(errors) == 0
        assert len(results) == 10
    
    def test_performance_benchmarks(self, service):
        """Test performance benchmarks"""
        import time
        
        # Test search performance
        start_time = time.time()
        for _ in range(10):
            filters = SearchFilters(page=1, limit=50)
            result = service.search_letters(filters)
        search_time = time.time() - start_time
        
        # Should complete 10 searches in under 1 second
        assert search_time < 1.0
        
        # Test stats performance
        start_time = time.time()
        for _ in range(5):
            stats = service.get_database_stats()
        stats_time = time.time() - start_time
        
        # Should complete 5 stats calls in under 0.5 seconds (with caching)
        assert stats_time < 0.5
    
    def test_large_dataset_handling(self, service):
        """Test handling of larger datasets"""
        # Insert more test data
        with duckdb.connect(service.db_path) as conn:
            # Insert 100 more letters
            for i in range(6, 106):
                conn.execute("""
                    INSERT INTO letters (document_name, document_type, document_title, source_file_path, file_hash, file_size, processing_time_ms, extraction_confidence, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [f'test_letter_{i}.pdf', 'PDF', f'Test Letter {i}', f'/path/to/test{i}.pdf', f'hash{i}', 1024, 5000.0, 0.9, 'processed'])
        
        # Test search with large dataset
        filters = SearchFilters(page=1, limit=50)
        result = service.search_letters(filters)
        
        assert result.total_count == 105
        assert len(result.letters) == 50
        assert result.total_pages == 3
        
        # Test pagination with large dataset
        filters = SearchFilters(page=3, limit=50)
        result = service.search_letters(filters)
        
        assert len(result.letters) == 5  # Remaining letters
        assert result.page == 3


class TestLetterDatabaseServiceIntegration:
    """Integration tests for LetterDatabaseService"""
    
    def test_full_workflow(self, temp_db_path):
        """Test complete workflow from search to export"""
        service = LetterDatabaseService(temp_db_path)
        
        # 1. Search letters
        filters = SearchFilters(status=['processed'])
        search_result = service.search_letters(filters)
        assert len(search_result.letters) == 3
        
        # 2. Get detailed letter info
        letter_ids = [letter['id'] for letter in search_result.letters]
        detailed_letter = service.get_letter_by_id(letter_ids[0], include_products=True)
        assert detailed_letter is not None
        assert 'products' in detailed_letter
        
        # 3. Get statistics
        stats = service.get_database_stats()
        assert stats.total_letters == 5
        
        # 4. Export selected letters
        export_result = service.bulk_operation(
            OperationType.EXPORT, 
            letter_ids[:2], 
            {'format': 'json', 'include_products': True}
        )
        assert export_result.success is True
        
        # 5. Archive letters
        archive_result = service.bulk_operation(
            OperationType.ARCHIVE, 
            letter_ids[:1]
        )
        assert archive_result.success is True
        
        # 6. Verify archive
        archived_letter = service.get_letter_by_id(letter_ids[0])
        assert archived_letter['status'] == 'archived'
        
        # 7. Clean up export file
        if export_result.results:
            export_file = Path(export_result.results[0]['export_file'])
            if export_file.exists():
                export_file.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 