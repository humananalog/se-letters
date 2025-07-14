#!/usr/bin/env python3
"""
Integration tests for Letter Database API endpoints
Tests the API layer integration with the backend service

Test Coverage:
- GET /api/letter-database (search, stats, analytics)
- POST /api/letter-database (bulk operations)
- GET /api/letter-database/[id] (individual letter)
- DELETE /api/letter-database/[id] (delete letter)
- PATCH /api/letter-database/[id] (update letter)

Author: SE Letters Team
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import duckdb

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.letter_database_service import LetterDatabaseService


class TestLetterDatabaseAPI:
    """Test suite for Letter Database API endpoints"""
    
    @pytest.fixture
    def test_service(self):
        """Create test service with sample data"""
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
            conn.execute("""
                INSERT INTO letters (id, document_name, document_type, document_title, source_file_path, file_hash, file_size, processing_method, processing_time_ms, extraction_confidence, status)
                VALUES (1, 'test_letter_1.pdf', 'PDF', 'Test Letter 1', '/path/to/test1.pdf', 'hash1', 1024, 'production_pipeline', 5000.0, 0.95, 'processed')
            """)
            
            conn.execute("""
                INSERT INTO letter_products (id, letter_id, product_identifier, range_label, subrange_label, product_line, product_description, obsolescence_status, end_of_service_date, replacement_suggestions, confidence_score)
                VALUES (1, 1, 'PROD001', 'TeSys D', 'D-Line', 'Contactors', 'TeSys D contactor', 'obsolete', '2024-12-31', 'TeSys F', 0.95)
            """)
        
        service = LetterDatabaseService(str(db_path))
        
        yield service
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_search_api_functionality(self, test_service):
        """Test search API functionality"""
        # Test basic search
        from se_letters.services.letter_database_service import SearchFilters
        
        filters = SearchFilters()
        result = test_service.search_letters(filters)
        
        assert result.total_count == 1
        assert len(result.letters) == 1
        assert result.letters[0]['document_name'] == 'test_letter_1.pdf'
        
        # Test search with filters
        filters = SearchFilters(search_query='test_letter_1')
        result = test_service.search_letters(filters)
        
        assert result.total_count == 1
        assert result.letters[0]['document_name'] == 'test_letter_1.pdf'
        
        # Test search with status filter
        filters = SearchFilters(status=['processed'])
        result = test_service.search_letters(filters)
        
        assert result.total_count == 1
        assert result.letters[0]['status'] == 'processed'
    
    def test_stats_api_functionality(self, test_service):
        """Test statistics API functionality"""
        stats = test_service.get_database_stats()
        
        assert stats.total_letters == 1
        assert stats.total_products == 1
        assert stats.avg_confidence == 0.95
        assert stats.success_rate == 100.0
        assert stats.avg_processing_time == 5000.0
        assert 'processed' in stats.status_distribution
        assert stats.status_distribution['processed'] == 1
    
    def test_analytics_api_functionality(self, test_service):
        """Test analytics API functionality"""
        analytics = test_service.get_analytics_data(days=30)
        
        assert isinstance(analytics, dict)
        assert 'processing_trends' in analytics
        assert 'range_distribution' in analytics
        assert 'confidence_distribution' in analytics
        assert 'processing_performance' in analytics
        assert 'error_analysis' in analytics
    
    def test_individual_letter_api_functionality(self, test_service):
        """Test individual letter API functionality"""
        # Test get letter by ID
        letter = test_service.get_letter_by_id(1, include_products=True, include_debug=False)
        
        assert letter is not None
        assert letter['id'] == 1
        assert letter['document_name'] == 'test_letter_1.pdf'
        assert 'products' in letter
        assert len(letter['products']) == 1
        assert letter['products'][0]['range_label'] == 'TeSys D'
        
        # Test non-existent letter
        letter = test_service.get_letter_by_id(999)
        assert letter is None
    
    def test_bulk_operations_api_functionality(self, test_service):
        """Test bulk operations API functionality"""
        from se_letters.services.letter_database_service import OperationType
        
        # Test bulk export
        result = test_service.bulk_operation(
            OperationType.EXPORT,
            [1],
            {'format': 'json', 'include_products': True}
        )
        
        assert result.success is True
        assert result.operation == 'export'
        assert result.affected_count == 1
        assert result.results is not None
        assert len(result.results) == 1
        assert 'export_file' in result.results[0]
        
        # Verify export file exists and contains data
        export_file = Path(result.results[0]['export_file'])
        assert export_file.exists()
        
        with open(export_file, 'r') as f:
            export_data = json.load(f)
        
        assert len(export_data) == 1
        assert export_data[0]['document_name'] == 'test_letter_1.pdf'
        assert 'products' in export_data[0]
        assert len(export_data[0]['products']) == 1
        
        # Cleanup
        export_file.unlink()
        
        # Test bulk archive
        result = test_service.bulk_operation(
            OperationType.ARCHIVE,
            [1]
        )
        
        assert result.success is True
        assert result.operation == 'archive'
        assert result.affected_count == 1
        
        # Verify letter is archived
        letter = test_service.get_letter_by_id(1)
        assert letter['status'] == 'archived'
    
    def test_filter_options_api_functionality(self, test_service):
        """Test filter options API functionality"""
        # Test available ranges
        ranges = test_service.get_available_ranges()
        assert isinstance(ranges, list)
        assert 'TeSys D' in ranges
        
        # Test available document types
        doc_types = test_service.get_available_document_types()
        assert isinstance(doc_types, list)
        assert 'PDF' in doc_types
    
    def test_health_check_api_functionality(self, test_service):
        """Test health check API functionality"""
        health = test_service.health_check()
        
        assert isinstance(health, dict)
        assert health['status'] == 'healthy'
        assert 'database_path' in health
        assert 'tables' in health
        assert 'cache_size' in health
        assert 'timestamp' in health
        
        # Verify table counts
        assert health['tables']['letters'] == 1
        assert health['tables']['letter_products'] == 1
    
    def test_error_handling_api_functionality(self, test_service):
        """Test API error handling"""
        from se_letters.services.letter_database_service import OperationType
        
        # Test invalid operation
        with pytest.raises(Exception):
            test_service.bulk_operation('invalid_operation', [1])
        
        # Test non-existent letter operations
        result = test_service.bulk_operation(
            OperationType.DELETE,
            [999]  # Non-existent letter ID
        )
        
        # Should succeed but affect 0 records
        assert result.success is True
        assert result.affected_count == 0
    
    def test_pagination_api_functionality(self, test_service):
        """Test pagination API functionality"""
        # Add more test data
        with duckdb.connect(test_service.db_path) as conn:
            for i in range(2, 6):
                conn.execute("""
                    INSERT INTO letters (id, document_name, document_type, document_title, source_file_path, file_hash, file_size, processing_method, processing_time_ms, extraction_confidence, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [i, f'test_letter_{i}.pdf', 'PDF', f'Test Letter {i}', f'/path/to/test{i}.pdf', f'hash{i}', 1024, 'production_pipeline', 5000.0, 0.9, 'processed'])
        
        from se_letters.services.letter_database_service import SearchFilters
        
        # Test first page
        filters = SearchFilters(page=1, limit=2)
        result = test_service.search_letters(filters)
        
        assert len(result.letters) == 2
        assert result.page == 1
        assert result.limit == 2
        assert result.total_count == 5
        assert result.total_pages == 3
        
        # Test second page
        filters = SearchFilters(page=2, limit=2)
        result = test_service.search_letters(filters)
        
        assert len(result.letters) == 2
        assert result.page == 2
        
        # Test last page
        filters = SearchFilters(page=3, limit=2)
        result = test_service.search_letters(filters)
        
        assert len(result.letters) == 1
        assert result.page == 3
    
    def test_sorting_api_functionality(self, test_service):
        """Test sorting API functionality"""
        # Add more test data with different confidence scores
        with duckdb.connect(test_service.db_path) as conn:
            conn.execute("""
                INSERT INTO letters (id, document_name, document_type, document_title, source_file_path, file_hash, file_size, processing_method, processing_time_ms, extraction_confidence, status)
                VALUES (2, 'test_letter_2.pdf', 'PDF', 'Test Letter 2', '/path/to/test2.pdf', 'hash2', 1024, 'production_pipeline', 3000.0, 0.85, 'processed')
            """)
        
        from se_letters.services.letter_database_service import SearchFilters, SortOrder
        
        # Test sort by confidence ascending
        filters = SearchFilters(sort_by='extraction_confidence', sort_order=SortOrder.ASC)
        result = test_service.search_letters(filters)
        
        confidences = [letter['extraction_confidence'] for letter in result.letters]
        assert confidences == sorted(confidences)
        
        # Test sort by confidence descending
        filters = SearchFilters(sort_by='extraction_confidence', sort_order=SortOrder.DESC)
        result = test_service.search_letters(filters)
        
        confidences = [letter['extraction_confidence'] for letter in result.letters]
        assert confidences == sorted(confidences, reverse=True)


class TestLetterDatabaseAPIScenarios:
    """Test realistic API usage scenarios"""
    
    def test_search_and_export_workflow(self):
        """Test complete search and export workflow"""
        # This would typically be tested with actual API calls
        # For now, we test the service layer that powers the API
        
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_letters.duckdb"
        
        # Create test database
        with duckdb.connect(str(db_path)) as conn:
            conn.execute("CREATE SEQUENCE letters_id_seq START 1")
            conn.execute("CREATE SEQUENCE products_id_seq START 1")
            
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
            
            # Insert multiple letters
            for i in range(1, 4):
                conn.execute("""
                    INSERT INTO letters (id, document_name, document_type, document_title, source_file_path, file_hash, file_size, processing_method, processing_time_ms, extraction_confidence, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [i, f'letter_{i}.pdf', 'PDF', f'Letter {i}', f'/path/to/letter{i}.pdf', f'hash{i}', 1024, 'production_pipeline', 5000.0, 0.9, 'processed'])
                
                conn.execute("""
                    INSERT INTO letter_products (id, letter_id, product_identifier, range_label, subrange_label, product_line, product_description, obsolescence_status, end_of_service_date, replacement_suggestions, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [i, i, f'PROD{i:03d}', f'Range{i}', f'Sub{i}', f'Line{i}', f'Description {i}', 'obsolete', '2024-12-31', f'Replacement{i}', 0.9])
        
        service = LetterDatabaseService(str(db_path))
        
        try:
            # 1. Search for letters
            from se_letters.services.letter_database_service import SearchFilters
            filters = SearchFilters(status=['processed'])
            search_result = service.search_letters(filters)
            
            assert search_result.total_count == 3
            assert len(search_result.letters) == 3
            
            # 2. Select letters for export
            selected_ids = [letter['id'] for letter in search_result.letters[:2]]
            
            # 3. Export selected letters
            from se_letters.services.letter_database_service import OperationType
            export_result = service.bulk_operation(
                OperationType.EXPORT,
                selected_ids,
                {'format': 'json', 'include_products': True}
            )
            
            assert export_result.success is True
            assert export_result.affected_count == 2
            
            # 4. Verify export file
            export_file = Path(export_result.results[0]['export_file'])
            assert export_file.exists()
            
            with open(export_file, 'r') as f:
                export_data = json.load(f)
            
            assert len(export_data) == 2
            assert all('products' in letter for letter in export_data)
            
            # Cleanup
            export_file.unlink()
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 